"""Shared solver output."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


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


def normalize_result(
    adapter_result: Mapping[str, object],
    metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Compatibility normalizer for the branch's existing benchmark runner."""
    record = dict(adapter_result)
    if metadata:
        record.update(metadata)
    return record


def append_jsonl(path: str | Path, record: Mapping[str, object]) -> None:
    """Append one benchmark record for compatibility with the existing runner."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(dict(record), ensure_ascii=False, allow_nan=False))
        stream.write("\n")


def read_jsonl(path: str | Path) -> list[dict[str, object]]:
    """Read benchmark JSONL records for compatibility with the existing runner."""
    source = Path(path)
    if not source.exists():
        return []
    records = []
    with source.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                records.append(json.loads(line))
    return records
