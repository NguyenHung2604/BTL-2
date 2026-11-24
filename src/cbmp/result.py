"""Shared result schema and JSONL helpers for CBMP solver runs.

The solver adapters remain responsible for solving and validating solutions.
This module only normalizes their dictionaries and persists benchmark records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


RESULT_STATUSES = {"OPTIMAL", "FEASIBLE", "NO_SOLUTION", "INFEASIBLE"}
TERMINATION_REASONS = {
    "completed",
    "timeout",
    "OOM",
    "license_error",
    "error",
}

# Fields shared by the project-wide benchmark interface. Adapter-specific
# diagnostic fields (for example solver_status_name and solver_objective) are
# deliberately preserved as well.
RESULT_DEFAULTS: Dict[str, Any] = {
    "method": None,
    "encoding": None,
    "solver_version": None,
    "status": "NO_SOLUTION",
    "termination_reason": "error",
    "incumbent": None,
    "lower_bound": None,
    "optimality_proven": False,
    "labeling": None,
    "build_time": 0.0,
    "solve_time": 0.0,
    "validation_time": 0.0,
    "total_time": 0.0,
    "peak_memory": None,
    "num_variables": None,
    "num_constraints": None,
    "estimated_num_variables": None,
    "estimated_num_constraints": None,
    "num_clauses": None,
    "max_num_clauses": None,
    "estimated_num_clauses": None,
    "decision_history": None,
    "graph_id": None,
    "source_url": None,
    "source_path": None,
    "raw_path": None,
    "raw_sha256": None,
    "graph_sha256": None,
    "normalized_graph_sha256": None,
    "matrix_type": None,
    "max_degree": None,
    "isolated_vertices": None,
    "n": None,
    "num_edges": None,
    "seed": None,
    "threads": None,
    "time_limit": None,
    "commit_hash": None,
    "error_type": None,
    "error_message": None,
}


def _validate_nonnegative_number(value: Any, field: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a non-negative number or None")
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{field} must be finite and non-negative")


def normalize_result(
    adapter_result: Mapping[str, Any],
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Return a project-schema record while preserving adapter diagnostics.

    ``metadata`` contains run/instance information supplied by the runner.
    It is applied after adapter fields so runner-owned metadata is authoritative.
    Unknown adapter fields are retained for debugging and future analysis.
    """
    if not isinstance(adapter_result, Mapping):
        raise TypeError("adapter_result must be a mapping")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping or None")

    record = dict(RESULT_DEFAULTS)
    record.update(dict(adapter_result))
    if metadata:
        record.update(dict(metadata))

    status = record["status"]
    if status not in RESULT_STATUSES:
        raise ValueError(
            f"unsupported result status {status!r}; expected one of "
            f"{sorted(RESULT_STATUSES)}"
        )

    reason = record["termination_reason"]
    if reason not in TERMINATION_REASONS:
        raise ValueError(
            f"unsupported termination_reason {reason!r}; expected one of "
            f"{sorted(TERMINATION_REASONS)}"
        )

    if not isinstance(record["optimality_proven"], bool):
        raise TypeError("optimality_proven must be a bool")
    if record["optimality_proven"] and status != "OPTIMAL":
        raise ValueError("optimality_proven=True requires status='OPTIMAL'")

    for field in ("build_time", "solve_time", "validation_time", "total_time", "peak_memory"):
        _validate_nonnegative_number(record[field], field)
    for field in ("incumbent", "lower_bound"):
        value = record[field]
        if value is not None:
            _validate_nonnegative_number(value, field)

    if record["labeling"] is not None:
        if not isinstance(record["labeling"], (list, tuple)):
            raise TypeError("labeling must be a list, tuple, or None")
        record["labeling"] = list(record["labeling"])

    return record


def append_jsonl(path: str | Path, record: Mapping[str, Any]) -> None:
    """Append one normalized result record to a JSON Lines file."""
    normalized = normalize_result(record)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(
                normalized,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
        )
        stream.write("\n")


def read_jsonl(path: str | Path) -> list[Dict[str, Any]]:
    """Read JSONL records, reporting the exact line on malformed input."""
    source = Path(path)
    if not source.exists():
        return []

    records: list[Dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL at {source}:{line_number}: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"expected a JSON object at {source}:{line_number}"
                )
            records.append(normalize_result(value))
    return records


def completed_run_keys(
    records: Iterable[Mapping[str, Any]],
    key_fields: tuple[str, ...] = ("graph_id", "method", "encoding", "seed"),
) -> set[tuple[Any, ...]]:
    """Build resume keys for records that reached a terminal run outcome.

    All recorded outcomes are terminal for resume purposes, including timeout,
    OOM and license errors. Callers can choose another key_fields tuple when
    their benchmark configuration defines a different instance identity.
    """
    keys: set[tuple[Any, ...]] = set()
    for record in records:
        if record.get("termination_reason") in TERMINATION_REASONS:
            keys.add(tuple(record.get(field) for field in key_fields))
    return keys


@dataclass
class SolveResult:
    """Use None for missing bounds or incumbents. runtime_seconds is total elapsed time."""

    instance: str
    method: str
    status: str
    termination_reason: str
    runtime_seconds: float
    labels: list[int] | None = None
    bandwidth: int | None = None
    lower_bound: int | None = None
    build_time: float = 0.0
    solve_time: float = 0.0
    num_variables: int | None = None
    num_clauses: int | None = None
    max_num_clauses: int | None = None
    decision_history: list[dict[str, Any]] = field(default_factory=list)
    solver_version: str | None = None
