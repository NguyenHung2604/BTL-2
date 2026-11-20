"""CBMP decision problems with a shared Glucose backend."""

from dataclasses import dataclass
from math import isfinite
from threading import Timer
from time import monotonic
from typing import Literal

from pysat.solvers import Glucose3

from ..encodings import order, pairwise
from ..graph import Graph
from ..objective import bandwidth
from ..result import SolveResult
from ..validator import validate_solution


@dataclass
class Decision:
    status: str
    labels: list[int] | None = None


def decide(graph: Graph, encoding: str, k: int, time_limit_seconds: float) -> Decision:
    """Solve one threshold. UNKNOWN means the time budget expired."""
    if not isfinite(time_limit_seconds) or time_limit_seconds < 0:
        raise ValueError("Expected a finite nonnegative budget")
    deadline = monotonic() + time_limit_seconds
    encoder = {"pairwise": pairwise, "order": order}[encoding]
    if time_limit_seconds == 0:
        return Decision("UNKNOWN")
    clauses, metadata = encoder.build(graph, k)
    with Glucose3(bootstrap_with=clauses) as solver:
        remaining = deadline - monotonic()
        if remaining <= 0:
            return Decision("UNKNOWN")
        timer = Timer(remaining, solver.interrupt)
        timer.start()
        try:
            feasible = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
            timer.join()
        if feasible is None:
            return Decision("UNKNOWN")
        if not feasible:
            return Decision("UNSAT")
        labels = encoder.decode(solver.get_model(), metadata)
        value = bandwidth(graph, labels)
        if value > k or not validate_solution(graph, labels, value):
            raise ValueError("Invalid SAT witness")
        return Decision("SAT", labels)


def solve(graph: Graph, encoding: Literal["pairwise", "order"], time_limit_seconds: float) -> SolveResult:
    """Tighten a validated upper bound until UNSAT or exhaustion of the total budget."""
    if not isfinite(time_limit_seconds) or time_limit_seconds < 0:
        raise ValueError("Expected a finite nonnegative budget")
    start = monotonic()
    labels = list(graph.vertices)
    best = bandwidth(graph, labels)
    degrees = [0] * graph.n
    for u, v in graph.edges:
        degrees[u] += 1
        degrees[v] += 1
    lower = (max(degrees, default=0) + 1) // 2
    reason = "completed"
    while best > lower:
        remaining = max(0.0, time_limit_seconds - (monotonic() - start))
        answer = decide(graph, encoding, best - 1, remaining)
        if answer.status == "UNKNOWN":
            reason = "timeout"
            break
        if answer.status == "UNSAT":
            lower = best
            break
        labels = answer.labels
        best = bandwidth(graph, labels)
    status = "OPTIMAL" if best == lower else "FEASIBLE"
    return SolveResult(graph.name, f"sat_{encoding}", status, reason, monotonic() - start,
                       labels, best, lower)
