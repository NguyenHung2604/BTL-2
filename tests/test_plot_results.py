"""Data transformations for the cnsplots reporting pipeline."""

from scripts.plot_results import _dataset_rows, _status_rows, _summary_rows
from cbmp.manifest import load_manifest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dataset_summary_uses_verified_manifest_statistics():
    rows = _dataset_rows(load_manifest(ROOT / "data" / "manifest.csv", repo_root=ROOT))
    assert [(row["instance"], row["n"], row["m"]) for row in rows] == [
        ("jgl009", 9, 32), ("bcsstk01", 48, 176), ("bp___400", 822, 4015),
    ]
    assert rows[0]["density"] > rows[1]["density"] > rows[2]["density"]


def test_status_summary_keeps_termination_reasons_separate():
    records = [
        {"method": "gurobi_mip", "status": "FEASIBLE", "termination_reason": "timeout"},
        {"method": "gurobi_mip", "status": "NO_SOLUTION", "termination_reason": "license_error"},
    ]
    rows = _status_rows(records)
    assert {row["termination_reason"] for row in rows} == {"timeout", "license_error"}
    assert sum(row["count"] for row in rows) == 2


def test_run_summary_preserves_bounds_and_raw_status_fields():
    rows = _summary_rows([{
        "graph_id": "jgl009", "method": "gurobi_mip", "status": "OPTIMAL",
        "termination_reason": "completed", "optimality_proven": True,
        "incumbent": 4, "lower_bound": 4, "total_time": 0.2,
        "time_limit": 60, "commit_hash": "abc123",
    }])
    assert rows[0]["incumbent"] == rows[0]["lower_bound"] == 4
    assert rows[0]["optimality_proven"] is True
    assert rows[0]["commit_hash"] == "abc123"
