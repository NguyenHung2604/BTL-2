"""Shared solver output."""

from dataclasses import dataclass


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
