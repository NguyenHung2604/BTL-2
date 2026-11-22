"""Regenerate CBMP benchmark tables and publication figures with cnsplots.

Example::

    python scripts/plot_results.py --input results/benchmark.jsonl \
        --manifest data/manifest.csv --output-dir results/summary
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cbmp.manifest import load_manifest  # noqa: E402
from cbmp.result import read_jsonl  # noqa: E402


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)


def _dataset_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in manifest_rows:
        n = row["n"]
        possible_edges = n * (n - 1) / 2
        result.append({
            "instance": row["instance"],
            "matrix_type": row["matrix_type"],
            "n": n,
            "m": row["m"],
            "density": 0.0 if possible_edges == 0 else row["m"] / possible_edges,
            "max_degree": row["max_degree"],
            "isolated_vertices": row["isolated_vertices"],
            "source_url": row["source_url"],
            "raw_sha256": row["raw_sha256"],
            "graph_sha256": row["graph_sha256"],
            "normalized_graph_sha256": row["normalized_graph_sha256"],
        })
    return result


def _summary_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "graph_id": row.get("graph_id"),
            "method": row.get("method"),
            "encoding": row.get("encoding"),
            "status": row.get("status"),
            "termination_reason": row.get("termination_reason"),
            "optimality_proven": row.get("optimality_proven"),
            "incumbent": row.get("incumbent"),
            "lower_bound": row.get("lower_bound"),
            "build_time": row.get("build_time"),
            "solve_time": row.get("solve_time"),
            "validation_time": row.get("validation_time"),
            "total_time": row.get("total_time"),
            "time_limit": row.get("time_limit"),
            "num_variables": row.get("num_variables"),
            "num_constraints": row.get("num_constraints"),
            "estimated_num_variables": row.get("estimated_num_variables"),
            "estimated_num_constraints": row.get("estimated_num_constraints"),
            "num_clauses": row.get("num_clauses"),
            "max_num_clauses": row.get("max_num_clauses"),
            "estimated_num_clauses": row.get("estimated_num_clauses"),
            "solver_version": row.get("solver_version"),
            "decision_history": json.dumps(row.get("decision_history"), ensure_ascii=False),
            "peak_memory": row.get("peak_memory"),
            "seed": row.get("seed"),
            "threads": row.get("threads"),
            "commit_hash": row.get("commit_hash"),
            "error_type": row.get("error_type"),
            "error_message": row.get("error_message"),
        }
        for row in records
    ]


def _status_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str, str], int] = {}
    for row in records:
        key = (str(row.get("method") or "unknown"), str(row.get("status") or "unknown"),
               str(row.get("termination_reason") or "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return [
        {"method": method, "status": status, "termination_reason": reason, "count": count}
        for (method, status, reason), count in sorted(counts.items())
    ]


def _draw_figures(records: list[dict[str, Any]], dataset_rows: list[dict[str, Any]], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        import cnsplots as cns
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            'Plotting requires the project extra: py -m pip install -e ".[plots]"'
        ) from exc

    cns.setup_matplotlib()
    generated: list[str] = []

    def new_figure(width: int, height: int) -> tuple[Any, Any]:
        fig = cns.figure(width=width, height=height, unit="pt")
        return fig, fig.add_subplot(111)

    def save(fig: Any, filename: str) -> None:
        path = output_dir / filename
        cns.savefig(str(path), fig=fig)
        cns.savefig(str(path.with_suffix(".pdf")), fig=fig)
        plt.close(fig)
        generated.extend([str(path), str(path.with_suffix(".pdf"))])

    # A small explanatory CBMP diagram, independent of solver outcomes.
    fig, ax = new_figure(375, 300)
    n = 8
    import math
    points = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    edges = [(0, 1), (1, 3), (3, 5), (5, 7), (7, 0), (2, 6)]
    for u, v in edges:
        ax.plot([points[u][0], points[v][0]], [points[u][1], points[v][1]], linewidth=1.5)
    ax.scatter([p[0] for p in points], [p[1] for p in points], s=65, zorder=3)
    for i, (x, y) in enumerate(points):
        ax.text(1.15 * x, 1.15 * y, str(i), ha="center", va="center")
    ax.set_title("Vertices placed on a cycle")
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "cbmp_circular_layout.svg")

    if dataset_rows:
        dataset_frame = pd.DataFrame(dataset_rows)
        fig, ax = new_figure(470, 325)
        cns.scatterplot(data=dataset_frame, x="n", y="m", hue="instance", ax=ax)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Number of vertices n (log scale)")
        ax.set_ylabel("Unique undirected edges m (log scale)")
        ax.set_title("Verified benchmark graph sizes")
        save(fig, "dataset_size_profile.svg")

    if not records:
        return generated

    frame = pd.DataFrame(records)
    frame["total_time"] = pd.to_numeric(frame["total_time"], errors="coerce")
    frame["time_limit"] = pd.to_numeric(frame["time_limit"], errors="coerce")

    # Status composition per method: includes timeout, OOM and license failures.
    status_frame = pd.DataFrame(_status_rows(records))
    if not status_frame.empty:
        fig, ax = new_figure(500, 300)
        cns.barplot(data=status_frame, x="method", y="count", hue="status", errorbar=None, ax=ax)
        ax.set_ylabel("Number of instances")
        ax.set_xlabel("Method")
        ax.set_title("Benchmark outcomes by method")
        ax.tick_params(axis="x", rotation=20)
        save(fig, "status_by_method.svg")

    # Cactus plot: only instances for which optimality was actually proven.
    optimal = frame[frame["optimality_proven"].fillna(False).astype(bool)].copy()
    if not optimal.empty:
        optimal = optimal.dropna(subset=["total_time"])
        cactus_rows = []
        for method, group in optimal.groupby("method"):
            for rank, runtime in enumerate(sorted(group["total_time"].astype(float)), start=1):
                cactus_rows.append({"method": method, "instances_proven": rank, "seconds": runtime})
        cactus = pd.DataFrame(cactus_rows)
        if not cactus.empty:
            fig, ax = new_figure(500, 325)
            cns.lineplot(data=cactus, x="instances_proven", y="seconds", hue="method", marker="o", ax=ax)
            ax.set_xlabel("Instances with proven optimum")
            ax.set_ylabel("Total wall-clock time (s)")
            ax.set_title("Cactus plot of optimality proofs")
            save(fig, "cactus_optimality.svg")
            cactus.to_csv(output_dir / "cactus_data.csv", index=False)

    # Pairwise-vs-order scatter: matched instances retain timeout/non-proof outcomes.
    sat = frame[frame["method"].isin(["sat_pairwise", "sat_order"])].copy()
    if not sat.empty:
        sat["optimality_proven"] = sat["optimality_proven"].fillna(False).astype(bool)
        time_pivot = sat.pivot_table(index="graph_id", columns="method", values="total_time", aggfunc="median")
        proof_pivot = sat.pivot_table(index="graph_id", columns="method", values="optimality_proven", aggfunc="all")
        if {"sat_pairwise", "sat_order"} <= set(time_pivot.columns):
            paired = time_pivot.dropna(subset=["sat_pairwise", "sat_order"]).reset_index()
            proof_pivot = proof_pivot.reindex(paired["graph_id"])
            paired["pairwise_proven"] = proof_pivot["sat_pairwise"].to_numpy()
            paired["order_proven"] = proof_pivot["sat_order"].to_numpy()
            paired["outcome"] = paired.apply(
                lambda row: "both optimal" if row["pairwise_proven"] and row["order_proven"]
                else "pairwise not proven" if not row["pairwise_proven"] and row["order_proven"]
                else "order not proven" if row["pairwise_proven"] and not row["order_proven"]
                else "neither proven", axis=1
            )
            paired.to_csv(output_dir / "pairwise_order_data.csv", index=False)
            if not paired.empty:
                fig, ax = new_figure(400, 365)
                cns.scatterplot(data=paired, x="sat_pairwise", y="sat_order", hue="outcome", style="outcome", ax=ax)
                maximum = max(float(paired["sat_pairwise"].max()), float(paired["sat_order"].max()), 1e-9)
                ax.plot([0, maximum], [0, maximum], linestyle="--", linewidth=1)
                ax.set_xlabel("Pairwise total time (s)")
                ax.set_ylabel("Order total time (s)")
                ax.set_title("SAT encoding runtime comparison (all matched runs)")
                save(fig, "pairwise_vs_order.svg")

    # Keep SAT clauses and MIP constraints separate: these are different units.
    if "num_clauses" in frame.columns:
        sat_size = frame[frame["method"].isin(["sat_pairwise", "sat_order"])].dropna(subset=["num_clauses"]).copy()
        if not sat_size.empty:
            sat_size["num_clauses"] = pd.to_numeric(sat_size["num_clauses"], errors="coerce")
            sat_size = sat_size.dropna(subset=["num_clauses"])
            fig, ax = new_figure(470, 325)
            cns.scatterplot(data=sat_size, x="n", y="num_clauses", hue="method", ax=ax)
            ax.set_yscale("log")
            ax.set_xlabel("Number of vertices n")
            ax.set_ylabel("Total clauses generated across thresholds (log scale)")
            ax.set_title("SAT encoding size versus graph size")
            save(fig, "sat_clauses_vs_n.svg")

    if "num_constraints" in frame.columns:
        mip_size = frame[frame["method"].isin(["cplex_mip", "gurobi_mip"])].dropna(subset=["num_constraints"]).copy()
        if not mip_size.empty:
            mip_size["num_constraints"] = pd.to_numeric(mip_size["num_constraints"], errors="coerce")
            mip_size = mip_size.dropna(subset=["num_constraints"])
            fig, ax = new_figure(470, 325)
            cns.scatterplot(data=mip_size, x="n", y="num_constraints", hue="method", ax=ax)
            ax.set_yscale("log")
            ax.set_xlabel("Number of vertices n")
            ax.set_ylabel("MIP constraints (log scale)")
            ax.set_title("MIP model size versus graph size")
            save(fig, "mip_constraints_vs_n.svg")

    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=REPO_ROOT / "results" / "benchmark.jsonl")
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / "data" / "manifest.csv")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "results" / "summary")
    parser.add_argument("--check-only", action="store_true", help="Write reproducible CSV tables without importing cnsplots")
    args = parser.parse_args()

    input_path = args.input if args.input.is_absolute() else REPO_ROOT / args.input
    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    records = read_jsonl(input_path)
    manifest_rows = load_manifest(manifest_path, repo_root=REPO_ROOT)
    dataset_rows = _dataset_rows(manifest_rows)
    summary_rows = _summary_rows(records)
    status_rows = _status_rows(records)

    _write_csv(output_dir / "dataset_summary.csv", dataset_rows, [
        "instance", "matrix_type", "n", "m", "density", "max_degree",
        "isolated_vertices", "source_url", "raw_sha256", "graph_sha256",
        "normalized_graph_sha256",
    ])
    _write_csv(output_dir / "run_summary.csv", summary_rows, [
        "graph_id", "method", "encoding", "status", "termination_reason",
        "optimality_proven", "incumbent", "lower_bound", "build_time", "solve_time",
        "total_time", "validation_time", "time_limit", "num_variables", "num_constraints",
        "estimated_num_variables", "estimated_num_constraints", "num_clauses",
        "max_num_clauses", "estimated_num_clauses", "solver_version", "decision_history",
        "peak_memory", "seed", "threads", "commit_hash", "error_type", "error_message",
    ])
    _write_csv(output_dir / "status_summary.csv", status_rows,
               ["method", "status", "termination_reason", "count"])
    (output_dir / "metadata.json").write_text(json.dumps({
        "input": str(input_path),
        "manifest": str(manifest_path),
        "num_runs": len(records),
        "num_datasets": len(dataset_rows),
        "plot_library": "cnsplots",
    }, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote tables for {len(records)} run(s) and {len(dataset_rows)} dataset(s) to {output_dir}")
    if args.check_only:
        return 0
    try:
        generated = _draw_figures(records, dataset_rows, output_dir)
    except RuntimeError as exc:
        parser.error(str(exc))
    print("Generated figures:")
    for path in generated:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
