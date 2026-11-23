"""Run reproducible CBMP solver benchmarks and persist results as JSONL.

Usage (from the repository root)::

    python scripts/benchmark.py --config configs/smoke.json
    python scripts/benchmark.py --config configs/benchmark.json

The runner supports both SAT encodings and the Gurobi and CPLEX MIP adapters.
Other methods can be added to SOLVER_REGISTRY once their adapters exist.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from time import monotonic
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cbmp.graph import Graph, load_graph
from cbmp.manifest import graph_statistics, load_manifest, normalized_graph_sha256
from cbmp.harwell_boeing import read_harwell_boeing, read_matrix  # noqa: E402
from cbmp.models.mip import MIPFormulation  # noqa: E402
from cbmp.result import append_jsonl, normalize_result, read_jsonl  # noqa: E402
from cbmp.solvers.cplex_mip import solve_cplex  # noqa: E402
from cbmp.solvers.gurobi_mip import solve_gurobi  # noqa: E402
from cbmp.validator import certify_record  # noqa: E402


SOLVER_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "gurobi_mip": solve_gurobi,
    "cplex_mip": solve_cplex,
}


def _load_config(path: Path) -> dict[str, Any]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("Benchmark config must be a JSON object")
    return config


def _resolve_repo_path(value: str, base_dir: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve()


def _load_instance(spec: Any, base_dir: Path) -> dict[str, Any]:
    """Load one inline graph or one Harwell-Boeing matrix."""
    if isinstance(spec, str):
        spec = {"path": spec}
    if not isinstance(spec, dict):
        raise ValueError("Each instance must be a path or a JSON object")

    if "path" in spec:
        source = _resolve_repo_path(str(spec["path"]), base_dir)
        if not source.is_file():
            raise FileNotFoundError(f"Instance file does not exist: {source}")
        if source.suffix.lower() == ".json":
            graph = load_graph(source)
            return {
                "graph_id": str(spec.get("graph_id", graph.name)), "n": graph.n,
                "edges": graph.edges, "num_edges": len(graph.edges),
                "graph_checksum": normalized_graph_sha256(graph.n, graph.edges),
                "source_path": str(source.relative_to(base_dir)) if source.is_relative_to(base_dir) else str(source),
                "matrix_type": spec.get("matrix_type"),
                "source_url": spec.get("source_url"),
                "raw_path": spec.get("raw_path"),
                "raw_sha256": spec.get("raw_sha256"),
                "graph_sha256": spec.get("manifest_graph_sha256") or hashlib.sha256(source.read_bytes()).hexdigest(),
                "normalized_graph_sha256": spec.get("normalized_graph_sha256") or normalized_graph_sha256(graph.n, graph.edges),
                "max_degree": spec.get("max_degree", graph_statistics(graph.n, graph.edges)["max_degree"]),
                "isolated_vertices": spec.get("isolated_vertices", graph_statistics(graph.n, graph.edges)["isolated_vertices"]),
            }
        lower_name = source.name.lower()
        if lower_name.endswith((".mtx", ".mtx.gz")):
            parsed = read_matrix(source)
            graph = Graph(parsed.name, parsed.n, parsed.edges)
            matrix_type = spec.get("matrix_type", "MatrixMarket")
            normalized_checksum = None
        else:
            parsed = read_harwell_boeing(source)
            graph_id_from_path = source.name.removesuffix(".gz")
            for suffix in (".rsa", ".rua", ".pua", ".rse", ".cua", ".psa"):
                if graph_id_from_path.lower().endswith(suffix):
                    graph_id_from_path = graph_id_from_path[:-len(suffix)]
                    break
            graph = Graph(graph_id_from_path, parsed.n, parsed.edges)
            matrix_type = spec.get("matrix_type", parsed.matrix_type)
            normalized_checksum = parsed.checksum
        graph_id = str(spec.get("graph_id", graph.name))
        return {
            "graph_id": graph_id,
            "n": graph.n,
            "edges": graph.edges,
            "num_edges": len(graph.edges),
            "graph_checksum": normalized_checksum or hashlib.sha256(
                (f"n={graph.n}\n" + "".join(f"{u},{v}\n" for u, v in graph.edges)).encode("ascii")
            ).hexdigest(),
            "source_path": str(source.relative_to(REPO_ROOT))
            if source.is_relative_to(REPO_ROOT) else str(source),
            "matrix_type": matrix_type,
            "source_url": spec.get("source_url"),
            "raw_path": spec.get("raw_path", str(source)),
            "raw_sha256": spec.get("raw_sha256") or hashlib.sha256(source.read_bytes()).hexdigest(),
            "graph_sha256": spec.get("manifest_graph_sha256"),
            "normalized_graph_sha256": normalized_checksum or normalized_graph_sha256(graph.n, graph.edges),
            "max_degree": spec.get("max_degree", graph_statistics(graph.n, graph.edges)["max_degree"]),
            "isolated_vertices": spec.get("isolated_vertices", graph_statistics(graph.n, graph.edges)["isolated_vertices"]),
        }

    if "n" not in spec or "edges" not in spec:
        raise ValueError("Inline instances require both 'n' and 'edges'")
    formulation = MIPFormulation(spec["n"], tuple(tuple(e) for e in spec["edges"]))
    canonical = f"n={formulation.n}\n" + "".join(
        f"{u},{v}\n" for u, v in formulation.edges
    )
    checksum = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    graph_id = str(spec.get("graph_id", f"inline-{checksum[:12]}"))
    return {
        "graph_id": graph_id,
        "n": formulation.n,
        "edges": formulation.edges,
        "num_edges": len(formulation.edges),
        "graph_checksum": checksum,
        "source_path": None,
        "matrix_type": None,
        "source_url": None,
        "raw_path": None,
        "raw_sha256": None,
        "graph_sha256": None,
        "normalized_graph_sha256": checksum,
        "max_degree": None,
        "isolated_vertices": None,
    }




def estimate_sat_model_size(n: int, m: int, encoding: str) -> tuple[int, int]:
    """Return variables and a conservative upper bound on clauses for one K."""
    if encoding == "pairwise":
        variables = n * n
        clauses = n + 2 * n * (n * (n - 1) // 2) + m * n * n
    elif encoding == "order":
        variables = n * (n - 1)
        monotonicity = n * max(0, n - 2)
        all_different = (n * (n - 1) // 2) * n
        edge_distance = m * n * n
        clauses = monotonicity + all_different + edge_distance
    else:
        raise ValueError(f"Unknown SAT encoding: {encoding}")
    return variables, clauses


def _git_commit_hash() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return completed.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _run_key(record: dict[str, Any]) -> tuple[Any, ...]:
    """Identity includes settings that change the meaning of a run."""
    return (
        record.get("graph_id"),
        record.get("graph_checksum"),
        record.get("method"),
        record.get("encoding"),
        record.get("seed"),
        record.get("threads"),
        record.get("time_limit"),
        record.get("commit_hash"),
        record.get("windows_job_memory_mib"),
        record.get("source_sha256"),
    )


def run_benchmark(
    config: dict[str, Any],
    config_path: Path,
    output_override: Path | None = None,
    resume_override: bool | None = None,
    dry_run: bool = False,
    windows_job_memory_mib: int | None = None,
) -> int:
    base_dir = config_path.resolve().parent.parent
    instances = config.get("instances")
    if "manifest" in config:
        manifest_path = _resolve_repo_path(config["manifest"], base_dir)
        manifest_rows = load_manifest(manifest_path, repo_root=base_dir)
        instances = [
            {
                "graph_id": row["instance"],
                "path": row["graph_path"],
                "source_url": row["source_url"],
                "raw_path": row["raw_path"],
                "raw_sha256": row["raw_sha256"],
                "manifest_graph_sha256": row["graph_sha256"],
                "normalized_graph_sha256": row["normalized_graph_sha256"],
                "matrix_type": row["matrix_type"],
                "max_degree": row["max_degree"],
                "isolated_vertices": row["isolated_vertices"],
            }
            for row in manifest_rows
        ]
    methods = config.get("methods", ["gurobi_mip", "cplex_mip"])
    time_limit = config.get("time_limit_seconds", config.get("time_limit", 300))
    threads = config.get("threads", 1)
    seed = config.get("seed", 0)
    output_value = output_override or Path(config.get("output", "results/benchmark.jsonl"))
    output_path = output_value if output_value.is_absolute() else base_dir / output_value
    resume = config.get("resume", True) if resume_override is None else resume_override
    max_constraints = config.get("max_constraints")
    max_sat_variables = config.get("max_sat_variables")
    max_sat_clauses = config.get("max_sat_clauses")
    solver_output = bool(config.get("solver_output", False))

    if not isinstance(instances, list) or not instances:
        raise ValueError("Config field 'instances' must be a non-empty list")
    if not isinstance(methods, list) or not methods:
        raise ValueError("Config field 'methods' must be a non-empty list")
    if (
        isinstance(time_limit, bool)
        or not isinstance(time_limit, (int, float))
        or not math.isfinite(float(time_limit))
        or time_limit <= 0
    ):
        raise ValueError("time_limit must be a finite positive number of seconds")
    if isinstance(threads, bool) or not isinstance(threads, int) or threads < 1:
        raise ValueError("threads must be a positive integer")
    for field_name, field_value in (
        ("max_constraints", max_constraints),
        ("max_sat_variables", max_sat_variables),
        ("max_sat_clauses", max_sat_clauses),
    ):
        if field_value is not None and (
            isinstance(field_value, bool)
            or not isinstance(field_value, int)
            or field_value < 1
        ):
            raise ValueError(f"{field_name} must be a positive integer or null")

    planned_methods = config.get("planned_methods", [])
    if not isinstance(planned_methods, list):
        raise ValueError("planned_methods must be a list when provided")

    supported_methods = set(SOLVER_REGISTRY) | {"sat_pairwise", "sat_order", "cp_sat", "cplex_cp"}
    unknown = sorted(set(methods) - supported_methods)
    if unknown:
        raise ValueError(
            "Methods are not implemented yet: " + ", ".join(unknown)
            + ". Available methods: " + ", ".join(sorted(supported_methods))
        )

    loaded_instances = [_load_instance(item, base_dir) for item in instances]
    old_records = read_jsonl(output_path) if resume and output_path.exists() else []
    done = {_run_key(record) for record in old_records}
    commit_hash = _git_commit_hash()
    digest = hashlib.sha256()
    for source in [Path(__file__), *sorted(SRC_ROOT.rglob("*.py"))]:
        digest.update(source.relative_to(REPO_ROOT).as_posix().encode() + b"\0")
        digest.update(source.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    source_sha256 = digest.hexdigest()

    planned = len(loaded_instances) * len(methods)
    completed = 0
    print(f"Loaded {len(loaded_instances)} instance(s), {len(methods)} method(s).")
    print(f"Output: {output_path}")
    print(f"Resume: {'on' if resume else 'off'}; planned runs: {planned}")
    if planned_methods:
        print("Pending methods (not included in this run): " + ", ".join(planned_methods))

    for instance in loaded_instances:
        n = instance["n"]
        edges = instance["edges"]
        estimated_variables = n * n + 1
        estimated_constraints = 2 * n + len(edges) * n * n

        for method in methods:
            sat_method = method in ("sat_pairwise", "sat_order")
            cp_method = method in ("cp_sat", "cplex_cp")
            metadata = {
                "graph_id": instance["graph_id"],
                "graph_checksum": instance["graph_checksum"],
                "source_path": instance["source_path"],
                "matrix_type": instance["matrix_type"],
                "source_url": instance.get("source_url"),
                "raw_path": instance.get("raw_path"),
                "raw_sha256": instance.get("raw_sha256"),
                "graph_sha256": instance.get("graph_sha256"),
                "normalized_graph_sha256": instance.get("normalized_graph_sha256"),
                "max_degree": instance.get("max_degree"),
                "isolated_vertices": instance.get("isolated_vertices"),
                "n": n,
                "num_edges": len(edges),
                "method": method,
                "encoding": (
                    method.removeprefix("sat_") if sat_method
                    else "integer_position" if cp_method
                    else None
                ),
                "seed": seed,
                "threads": threads,
                "time_limit": float(time_limit),
                "commit_hash": commit_hash,
                "source_sha256": source_sha256,
            }
            if windows_job_memory_mib is not None:
                metadata["windows_job_memory_mib"] = windows_job_memory_mib
            key_record = dict(metadata)
            if resume and _run_key(key_record) in done:
                print(f"[SKIP] {instance['graph_id']} / {method}: already in JSONL")
                continue

            completed += 1
            mip_method = method in ("cplex_mip", "gurobi_mip")
            sat_variables = sat_clauses = None
            sat_guarded = False
            if sat_method:
                sat_variables, sat_clauses = estimate_sat_model_size(
                    n, len(edges), metadata["encoding"]
                )
                sat_guarded = (
                    (max_sat_variables is not None and sat_variables > max_sat_variables)
                    or (max_sat_clauses is not None and sat_clauses > max_sat_clauses)
                )
            if dry_run and sat_method:
                if sat_guarded:
                    print(
                        f"[DRY/GUARD] {instance['graph_id']} / {method}: "
                        f"vars~{sat_variables:,}, clauses<={sat_clauses:,} exceed "
                        f"configured SAT model limits"
                    )
                else:
                    print(
                        f"[DRY] {method}: n={n}, m={len(edges)}, "
                        f"vars~{sat_variables:,}, clauses<={sat_clauses:,}"
                    )
                continue
            if dry_run and cp_method:
                print(f"[DRY] {instance['graph_id']} / {method}: n={n}, m={len(edges)}")
                continue
            if dry_run:
                if mip_method and max_constraints is not None and estimated_constraints > max_constraints:
                    print(f"[DRY/GUARD] {instance['graph_id']} / {method}: "
                          f"{estimated_constraints:,} constraints exceeds limit "
                          f"{max_constraints:,}")
                else:
                    print(f"[DRY] {instance['graph_id']} / {method}: n={n}, "
                          f"m={len(edges)}, vars~{estimated_variables:,}, "
                          f"constraints~{estimated_constraints:,}")
                continue

            if sat_method and sat_guarded:
                record = normalize_result({
                    "status": "NO_SOLUTION",
                    "termination_reason": "error",
                    "optimality_proven": False,
                    "incumbent": None,
                    "lower_bound": None,
                    "labeling": None,
                    "build_time": 0.0,
                    "solve_time": 0.0,
                    "total_time": 0.0,
                    "estimated_num_variables": sat_variables,
                    "estimated_num_clauses": sat_clauses,
                    "error_type": "preflight_model_size_limit",
                    "error_message": (
                        f"Conservative SAT size estimate: {sat_variables} variables and "
                        f"at most {sat_clauses} clauses; configured limits are "
                        f"{max_sat_variables} variables and {max_sat_clauses} clauses. "
                        "Solver was not started."
                    ),
                }, metadata=metadata)
                print(f"[GUARD] {instance['graph_id']} / {method}: "
                      f"vars~{sat_variables:,}, clauses<={sat_clauses:,}; solver not started")
            elif mip_method and max_constraints is not None and estimated_constraints > max_constraints:
                record = normalize_result({
                    "status": "NO_SOLUTION",
                    "termination_reason": "error",
                    "optimality_proven": False,
                    "incumbent": None,
                    "lower_bound": None,
                    "labeling": None,
                    "build_time": 0.0,
                    "solve_time": 0.0,
                    "total_time": 0.0,
                    "estimated_num_variables": estimated_variables,
                    "estimated_num_constraints": estimated_constraints,
                    "error_type": "preflight_model_size_limit",
                    "error_message": (
                        f"Estimated constraints ({estimated_constraints}) exceed "
                        f"configured max_constraints ({max_constraints}); solver was not started"
                    ),
                }, metadata=metadata)
                print(f"[GUARD] {instance['graph_id']} / {method}: "
                      f"{estimated_constraints:,} constraints exceeds limit")
            else:
                print(f"[RUN ] {instance['graph_id']} / {method}: "
                      f"n={n}, m={len(edges)}")
                run_started = monotonic()
                try:
                    if sat_method:
                        from cbmp.solvers.sat import solve

                        graph = Graph(instance["graph_id"], n, tuple(edges))
                        preparation_time = monotonic() - run_started
                        remaining_time = float(time_limit) - preparation_time

                        if remaining_time <= 0:
                            adapter_result = {
                                "status": "NO_SOLUTION",
                                "termination_reason": "timeout",
                                "optimality_proven": False,
                                "labeling": None,
                                "incumbent": None,
                                "lower_bound": None,
                                "build_time": preparation_time,
                                "solve_time": 0.0,
                                "total_time": preparation_time,
                            }
                        else:
                            result = solve(
                                graph,
                                metadata["encoding"],
                                remaining_time,
                            )
                            adapter_result = {
                                "status": result.status,
                                "termination_reason": result.termination_reason,
                                "labeling": result.labels,
                                "incumbent": result.bandwidth,
                                "lower_bound": result.lower_bound,
                                "optimality_proven": result.status == "OPTIMAL",
                                "total_time": result.runtime_seconds,
                                "build_time": result.build_time + preparation_time,
                                "solve_time": result.solve_time,
                                "num_variables": result.num_variables,
                                "num_clauses": result.num_clauses,
                                "max_num_clauses": result.max_num_clauses,
                                "decision_history": result.decision_history,
                                "solver_version": result.solver_version,
                            }
                    elif cp_method:
                        if method == "cplex_cp":
                            from cbmp.solvers.cplex_cp import solve_cplex_cp
                        else:
                            from cbmp.solvers.cp_sat import solve

                        graph = Graph(instance["graph_id"], n, tuple(edges))
                        preparation_time = monotonic() - run_started
                        remaining_time = float(time_limit) - preparation_time

                        if remaining_time <= 0:
                            adapter_result = {
                                "status": "NO_SOLUTION",
                                "termination_reason": "timeout",
                                "optimality_proven": False,
                                "labeling": None,
                                "incumbent": None,
                                "lower_bound": None,
                                "build_time": preparation_time,
                                "solve_time": 0.0,
                                "total_time": preparation_time,
                            }
                        elif method == "cplex_cp":
                            adapter_result = solve_cplex_cp(graph.name, graph.n, graph.edges,
                                                            metadata, seed, remaining_time, threads)
                            adapter_result["build_time"] += preparation_time
                        else:
                            result = solve(graph, remaining_time, seed=seed, threads=threads)
                            adapter_result = {
                                "status": result.status,
                                "termination_reason": result.termination_reason,
                                "labeling": result.labels,
                                "incumbent": result.bandwidth,
                                "lower_bound": result.lower_bound,
                                "optimality_proven": result.status == "OPTIMAL",
                                "total_time": result.runtime_seconds,
                                "build_time": result.build_time + preparation_time,
                                "solve_time": result.solve_time,
                                "num_variables": result.num_variables,
                                "solver_version": result.solver_version,
                            }
                    else:
                        formulation = MIPFormulation(n, tuple(edges))
                        preparation_time = monotonic() - run_started
                        remaining_time = float(time_limit) - preparation_time

                        if remaining_time <= 0:
                            adapter_result = {
                                "status": "NO_SOLUTION",
                                "termination_reason": "timeout",
                                "optimality_proven": False,
                                "labeling": None,
                                "incumbent": None,
                                "lower_bound": None,
                                "build_time": preparation_time,
                                "solve_time": 0.0,
                                "total_time": preparation_time,
                            }
                        else:
                            adapter_result = SOLVER_REGISTRY[method](
                                formulation,
                                time_limit=remaining_time,
                                threads=threads,
                                output_flag=solver_output,
                            )
                            adapter_result["build_time"] = (
                                float(adapter_result.get("build_time") or 0.0)
                                + preparation_time
                            )
                    # Validate every incumbent independently at the runner boundary.
                    validation_started = monotonic()
                    certify_record(adapter_result, n, edges)
                    validation_time = monotonic() - validation_started
                    adapter_result["validation_time"] = validation_time
                    adapter_total = adapter_result.get("total_time")
                    runner_total = monotonic() - run_started
                    adapter_result["total_time"] = max(
                        float(adapter_total) if adapter_total is not None else 0.0,
                        runner_total,
                    )
                    # Normalize adapter output and keep runner-owned metadata authoritative.
                    record = normalize_result(adapter_result, metadata=metadata)
                except Exception as exc:  # keep a failed run in the audit trail
                    elapsed = monotonic() - run_started
                    record = normalize_result(
                        {
                            "status": "NO_SOLUTION",
                            "termination_reason": "OOM" if isinstance(exc, MemoryError) else "error",
                            "optimality_proven": False,
                            "incumbent": None,
                            "lower_bound": None,
                            "labeling": None,
                            # The failure may occur during build or solve, so do not
                            # invent a split. Preserve the measured end-to-end duration.
                            "build_time": None,
                            "solve_time": None,
                            "total_time": elapsed,
                            "num_variables": estimated_variables if mip_method else None,
                            "num_constraints": estimated_constraints if mip_method else None,
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        },
                        metadata=metadata,
                    )

            if not dry_run:
                append_jsonl(output_path, record)
                done.add(_run_key(record))
                print(f"       {record.get('status')} / "
                      f"{record.get('termination_reason')} / "
                      f"total={record.get('total_time', 0.0):.3f}s")

    print(f"Finished. New records: {completed if not dry_run else 0}; "
          f"existing records: {len(old_records)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=REPO_ROOT / "configs" / "smoke.json",
        help="Path to a benchmark JSON config (default: configs/smoke.json)",
    )
    parser.add_argument("--output", type=Path, help="Override JSONL output path")
    parser.add_argument("--no-resume", action="store_true", help="Ignore existing JSONL records")
    parser.add_argument("--dry-run", action="store_true", help="Print planned model sizes without solving")
    parser.add_argument("--windows-job-memory-mib", type=int,
                        help="Limit committed memory of the Windows runner and its solver children")
    args = parser.parse_args()
    if args.windows_job_memory_mib is not None:
        if sys.platform != "win32" or args.windows_job_memory_mib < 1:
            parser.error("A Windows job requires Windows and a positive memory budget")
        import uuid
        import win32api
        import win32job

        job = win32job.CreateJobObject(None, str(uuid.uuid4()))
        info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
        info["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_JOB_MEMORY
        info["JobMemoryLimit"] = args.windows_job_memory_mib * 1024**2
        win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, info)
        win32job.AssignProcessToJobObject(job, win32api.GetCurrentProcess())

    config_path = args.config if args.config.is_absolute() else (Path.cwd() / args.config)
    config = _load_config(config_path)
    return run_benchmark(
        config,
        config_path,
        output_override=args.output,
        resume_override=False if args.no_resume else None,
        dry_run=args.dry_run,
        windows_job_memory_mib=args.windows_job_memory_mib,
    )


if __name__ == "__main__":
    raise SystemExit(main())
