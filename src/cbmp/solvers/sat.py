"""CBMP decision and optimization with a shared Glucose backend."""

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from math import isfinite
from threading import Timer
from time import monotonic
from typing import Any, Literal

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
    build_time: float = 0.0
    solve_time: float = 0.0
    num_variables: int = 0
    num_clauses: int = 0


def _solver_version() -> str:
    try:
        return f"python-sat {version('python-sat')} / Glucose3"
    except PackageNotFoundError:
        return "Glucose3 (python-sat version unavailable)"


def decide(graph: Graph, encoding: str, k: int, time_limit_seconds: float) -> Decision:
    """Solve one threshold. UNKNOWN means the total threshold budget expired."""
    if not isfinite(time_limit_seconds) or time_limit_seconds < 0:
        raise ValueError("Expected a finite nonnegative budget")
    deadline = monotonic() + time_limit_seconds
    encoder = {"pairwise": pairwise, "order": order}[encoding]
    if time_limit_seconds == 0:
        expected_vars = graph.n * graph.n if encoding == "pairwise" else graph.n * (graph.n - 1)
        return Decision("UNKNOWN", num_variables=expected_vars)

    build_started = monotonic()
    clauses, metadata = encoder.build(graph, k)
    build_time = monotonic() - build_started
    if encoding == "pairwise":
        num_variables = graph.n * graph.n
    else:
        num_variables = len(metadata["var_map"])
    num_clauses = len(clauses)

    remaining = deadline - monotonic()
    if remaining <= 0:
        return Decision(
            "UNKNOWN", build_time=build_time, num_variables=num_variables,
            num_clauses=num_clauses,
        )

    with Glucose3(bootstrap_with=clauses) as solver:
        remaining = deadline - monotonic()
        if remaining <= 0:
            return Decision(
                "UNKNOWN", build_time=build_time, num_variables=num_variables,
                num_clauses=num_clauses,
            )
        timer = Timer(remaining, solver.interrupt)
        solve_started = monotonic()
        timer.start()
        try:
            feasible = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
            timer.join()
        solve_time = monotonic() - solve_started
        if feasible is None:
            return Decision(
                "UNKNOWN", build_time=build_time, solve_time=solve_time,
                num_variables=num_variables, num_clauses=num_clauses,
            )
        if not feasible:
            return Decision(
                "UNSAT", build_time=build_time, solve_time=solve_time,
                num_variables=num_variables, num_clauses=num_clauses,
            )
        labels = encoder.decode(solver.get_model(), metadata)
        value = bandwidth(graph, labels)
        if value > k or not validate_solution(graph, labels, value):
            raise ValueError("Invalid SAT witness")
        return Decision(
            "SAT", labels, build_time, solve_time, num_variables, num_clauses,
        )


def solve(
    graph: Graph,
    encoding: Literal["pairwise", "order"],
    time_limit_seconds: float,
) -> SolveResult:
    """Tighten a validated upper bound under one total wall-clock budget."""
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
    build_time = 0.0
    solve_time = 0.0
    num_variables = 0
    num_clauses_total = 0
    max_num_clauses = 0
    history: list[dict[str, Any]] = []

    while best > lower:
        remaining = max(0.0, time_limit_seconds - (monotonic() - start))
        threshold = best - 1
        answer = decide(graph, encoding, threshold, remaining)
        build_time += answer.build_time
        solve_time += answer.solve_time
        num_variables = max(num_variables, answer.num_variables)
        num_clauses_total += answer.num_clauses
        max_num_clauses = max(max_num_clauses, answer.num_clauses)
        history.append({
            "k": threshold,
            "status": answer.status,
            "build_time": answer.build_time,
            "solve_time": answer.solve_time,
            "num_variables": answer.num_variables,
            "num_clauses": answer.num_clauses,
        })

        if answer.status == "UNKNOWN":
            reason = "timeout"
            break
        if answer.status == "UNSAT":
            lower = best
            break
        labels = answer.labels
        best = bandwidth(graph, labels)

    status = "OPTIMAL" if best == lower else "FEASIBLE"
    return SolveResult(
        graph.name,
        f"sat_{encoding}",
        status,
        reason,
        monotonic() - start,
        labels,
        best,
        lower,
        build_time=build_time,
        solve_time=solve_time,
        num_variables=num_variables,
        num_clauses=num_clauses_total,
        max_num_clauses=max_num_clauses,
        decision_history=history,
        solver_version=_solver_version(),
    )
