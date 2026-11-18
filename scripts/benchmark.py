"""Run reproducible CBMP solver benchmarks and persist results as JSONL.

Usage (from the repository root)::

    python scripts/benchmark.py --config configs/smoke.json
    python scripts/benchmark.py --config configs/benchmark.json

The runner currently wires the implemented Gurobi and CPLEX MIP adapters.
Other methods can be added to SOLVER_REGISTRY once their adapters exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cbmp.harwell_boeing import read_harwell_boeing  # noqa: E402
from cbmp.models.mip import MIPFormulation  # noqa: E402
from cbmp.result import append_jsonl, normalize_result, read_jsonl  # noqa: E402
from cbmp.solvers.cplex_mip import solve_cplex  # noqa: E402
from cbmp.solvers.gurobi_mip import solve_gurobi  # noqa: E402


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
        graph = read_harwell_boeing(source)
        graph_id = str(spec.get("graph_id", source.stem))
        return {
            "graph_id": graph_id,
            "n": graph.n,
            "edges": graph.edges,
            "num_edges": graph.num_edges,
            "graph_checksum": graph.checksum,
            "source_path": str(source.relative_to(REPO_ROOT))
            if source.is_relative_to(REPO_ROOT) else str(source),
            "matrix_type": graph.matrix_type,
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
    }


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
    )


def run_benchmark(
    config: dict[str, Any],
    config_path: Path,
    output_override: Path | None = None,
    resume_override: bool | None = None,
    dry_run: bool = False,
) -> int:
    base_dir = config_path.resolve().parent.parent
    instances = config.get("instances")
    methods = config.get("methods", ["gurobi_mip", "cplex_mip"])
    time_limit = config.get("time_limit", 300)
    threads = config.get("threads", 1)
    seed = config.get("seed", 0)
    output_value = output_override or Path(config.get("output", "results/benchmark.jsonl"))
    output_path = output_value if output_value.is_absolute() else base_dir / output_value
    resume = config.get("resume", True) if resume_override is None else resume_override
    max_constraints = config.get("max_constraints")
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
    if max_constraints is not None and (
        isinstance(max_constraints, bool)
        or not isinstance(max_constraints, int)
        or max_constraints < 1
    ):
        raise ValueError("max_constraints must be a positive integer or null")

    unknown = sorted(set(methods) - set(SOLVER_REGISTRY))
    if unknown:
        raise ValueError(
            "Methods are not implemented yet: " + ", ".join(unknown)
            + ". Available methods: " + ", ".join(sorted(SOLVER_REGISTRY))
        )

    loaded_instances = [_load_instance(item, base_dir) for item in instances]
    old_records = read_jsonl(output_path) if resume and output_path.exists() else []
    done = {_run_key(record) for record in old_records}
    commit_hash = _git_commit_hash()

    planned = len(loaded_instances) * len(methods)
    completed = 0
    print(f"Loaded {len(loaded_instances)} instance(s), {len(methods)} method(s).")
    print(f"Output: {output_path}")
    print(f"Resume: {'on' if resume else 'off'}; planned runs: {planned}")

    for instance in loaded_instances:
        n = instance["n"]
        edges = instance["edges"]
        estimated_variables = n * n + 1
        estimated_constraints = 2 * n + len(edges) * n * n

        for method in methods:
            metadata = {
                "graph_id": instance["graph_id"],
                "graph_checksum": instance["graph_checksum"],
                "source_path": instance["source_path"],
                "matrix_type": instance["matrix_type"],
                "n": n,
                "num_edges": len(edges),
                "method": method,
                "encoding": None,
                "seed": seed,
                "threads": threads,
                "time_limit": float(time_limit),
                "commit_hash": commit_hash,
            }
            key_record = dict(metadata)
            if resume and _run_key(key_record) in done:
                print(f"[SKIP] {instance['graph_id']} / {method}: already in JSONL")
                continue

            completed += 1
            if dry_run:
                if max_constraints is not None and estimated_constraints > max_constraints:
                    print(f"[DRY/GUARD] {instance['graph_id']} / {method}: "
                          f"{estimated_constraints:,} constraints exceeds limit "
                          f"{max_constraints:,}")
                else:
                    print(f"[DRY] {instance['graph_id']} / {method}: n={n}, "
                          f"m={len(edges)}, vars~{estimated_variables:,}, "
                          f"constraints~{estimated_constraints:,}")
                continue

            if max_constraints is not None and estimated_constraints > max_constraints:
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
                    "num_variables": estimated_variables,
                    "num_constraints": estimated_constraints,
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
                run_started = time.perf_counter()
                try:
                    formulation = MIPFormulation(n, tuple(edges))
                    adapter_result = SOLVER_REGISTRY[method](
                        formulation,
                        time_limit=float(time_limit),
                        threads=threads,
                        output_flag=solver_output,
                    )
                    # Normalize adapter output and keep runner-owned metadata authoritative.
                    record = normalize_result(adapter_result, metadata=metadata)
                except Exception as exc:  # keep a failed run in the audit trail
                    elapsed = time.perf_counter() - run_started
                    record = normalize_result(
                        {
                            "status": "NO_SOLUTION",
                            "termination_reason": "error",
                            "optimality_proven": False,
                            "incumbent": None,
                            "lower_bound": None,
                            "labeling": None,
                            # The failure may occur during build or solve, so do not
                            # invent a split. Preserve the measured end-to-end duration.
                            "build_time": None,
                            "solve_time": None,
                            "total_time": elapsed,
                            "num_variables": estimated_variables,
                            "num_constraints": estimated_constraints,
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
    args = parser.parse_args()

    config_path = args.config if args.config.is_absolute() else (Path.cwd() / args.config)
    config = _load_config(config_path)
    return run_benchmark(
        config,
        config_path,
        output_override=args.output,
        resume_override=False if args.no_resume else None,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
