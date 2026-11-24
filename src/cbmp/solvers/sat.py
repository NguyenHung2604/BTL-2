"""CBMP decision and optimization with a shared Glucose backend."""

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from math import isfinite
from threading import Timer
from time import perf_counter
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


def _append_clauses_with_deadline(
    solver: Glucose3,
    clauses: list[list[int]],
    deadline: float,
    chunk_size: int = 1024,
) -> bool:
    """Append clauses in chunks; return False if deadline is reached."""
    for offset in range(0, len(clauses), chunk_size):
        if perf_counter() >= deadline:
            return False
        solver.append_formula(clauses[offset : offset + chunk_size])
    return True


def _solve_limited_with_timer(solver: Glucose3, timeout: float) -> bool | None:
    if timeout <= 0:
        return None
    timer = Timer(timeout, solver.interrupt)
    timer.start()
    try:
        return solver.solve_limited(expect_interrupt=True)
    finally:
        timer.cancel()
        timer.join()


def decide(graph: Graph, encoding: str, k: int, time_limit_seconds: float) -> Decision:
    """Solve one threshold. UNKNOWN means the total threshold budget expired."""
    if not isfinite(time_limit_seconds) or time_limit_seconds < 0:
        raise ValueError("Expected a finite nonnegative budget")
    deadline = perf_counter() + time_limit_seconds
    encoder = {"pairwise": pairwise, "order": order}[encoding]
    if time_limit_seconds == 0:
        expected_vars = graph.n * graph.n if encoding == "pairwise" else graph.n * (graph.n - 1)
        return Decision("UNKNOWN", num_variables=expected_vars)

    build_started = perf_counter()
    try:
        clauses, metadata = encoder.build(graph, k, deadline=deadline)
    except TimeoutError:
        return Decision("UNKNOWN", build_time=perf_counter() - build_started)
    build_time = perf_counter() - build_started
    if encoding == "pairwise":
        num_variables = graph.n * graph.n
    else:
        num_variables = len(metadata["var_map"])
    num_clauses = len(clauses)

    remaining = deadline - perf_counter()
    if remaining <= 0:
        return Decision(
            "UNKNOWN", build_time=build_time, num_variables=num_variables,
            num_clauses=num_clauses,
        )

    with Glucose3() as solver:
        for offset in range(0, len(clauses), 1024):
            if perf_counter() >= deadline:
                return Decision("UNKNOWN", build_time=perf_counter() - build_started,
                                num_variables=num_variables, num_clauses=num_clauses)
            solver.append_formula(clauses[offset:offset + 1024])
        build_time = perf_counter() - build_started
        remaining = deadline - perf_counter()
        if remaining <= 0:
            return Decision(
                "UNKNOWN", build_time=build_time, num_variables=num_variables,
                num_clauses=num_clauses,
            )
        timer = Timer(remaining, solver.interrupt)
        solve_started = perf_counter()
        timer.start()
        try:
            feasible = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
            timer.join()
        solve_time = perf_counter() - solve_started
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


def _solve_order_incremental(
    graph: Graph,
    time_limit_seconds: float,
    start: float,
    labels: list[int],
    best: int,
    lower: int,
) -> SolveResult:
    """Tighten upper bound incrementally on a single Glucose3 instance for order encoding."""
    deadline = start + time_limit_seconds
    reason = "completed"
    build_time = 0.0
    solve_time = 0.0
    num_variables = 0
    num_clauses_total = 0
    max_num_clauses = 0
    history: list[dict[str, Any]] = []

    if best <= lower:
        return SolveResult(
            graph.name,
            "sat_order",
            "OPTIMAL",
            reason,
            perf_counter() - start,
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

    build_started = perf_counter()
    try:
        fixed_clauses, metadata, diff_table = order.build_fixed(graph, deadline=deadline)
    except TimeoutError:
        return SolveResult(
            graph.name,
            "sat_order",
            "FEASIBLE",
            "timeout",
            perf_counter() - start,
            labels,
            best,
            lower,
            build_time=perf_counter() - build_started,
            solve_time=solve_time,
            num_variables=num_variables,
            num_clauses=num_clauses_total,
            max_num_clauses=max_num_clauses,
            decision_history=history,
            solver_version=_solver_version(),
        )

    num_variables = len(metadata["var_map"])
    fixed_build_time = perf_counter() - build_started
    build_time += fixed_build_time
    num_clauses_total += len(fixed_clauses)
    max_num_clauses = max(max_num_clauses, len(fixed_clauses))

    next_upper_forbidden = min(best, graph.n // 2)

    with Glucose3() as solver:
        if not _append_clauses_with_deadline(solver, fixed_clauses, deadline):
            build_time = perf_counter() - build_started
            return SolveResult(
                graph.name,
                "sat_order",
                "FEASIBLE",
                "timeout",
                perf_counter() - start,
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

        build_time = perf_counter() - build_started

        while best > lower:
            threshold = best - 1
            step_build_started = perf_counter()
            try:
                delta_clauses = (
                    order.build_distance_clauses(
                        graph,
                        min_forbidden_dist=threshold + 1,
                        max_forbidden_dist=next_upper_forbidden,
                        diff_table=diff_table,
                        deadline=deadline,
                    )
                    if threshold + 1 <= next_upper_forbidden
                    else []
                )
            except TimeoutError:
                step_build = perf_counter() - step_build_started
                build_time += step_build
                history.append({
                    "k": threshold,
                    "status": "UNKNOWN",
                    "build_time": step_build,
                    "solve_time": 0.0,
                    "num_variables": num_variables,
                    "num_clauses": 0,
                })
                reason = "timeout"
                break

            if delta_clauses and not _append_clauses_with_deadline(solver, delta_clauses, deadline):
                step_build = perf_counter() - step_build_started
                build_time += step_build
                history.append({
                    "k": threshold,
                    "status": "UNKNOWN",
                    "build_time": step_build,
                    "solve_time": 0.0,
                    "num_variables": num_variables,
                    "num_clauses": len(delta_clauses),
                })
                reason = "timeout"
                break

            step_build = perf_counter() - step_build_started
            build_time += step_build
            num_clauses_total += len(delta_clauses)
            max_num_clauses = max(max_num_clauses, len(delta_clauses))
            if threshold < next_upper_forbidden:
                next_upper_forbidden = threshold

            remaining = deadline - perf_counter()
            if remaining <= 0:
                history.append({
                    "k": threshold,
                    "status": "UNKNOWN",
                    "build_time": step_build,
                    "solve_time": 0.0,
                    "num_variables": num_variables,
                    "num_clauses": len(delta_clauses),
                })
                reason = "timeout"
                break

            solve_started = perf_counter()
            feasible = _solve_limited_with_timer(solver, remaining)
            step_solve = perf_counter() - solve_started
            solve_time += step_solve

            if feasible is None:
                history.append({
                    "k": threshold,
                    "status": "UNKNOWN",
                    "build_time": step_build,
                    "solve_time": step_solve,
                    "num_variables": num_variables,
                    "num_clauses": len(delta_clauses),
                })
                reason = "timeout"
                break

            if not feasible:
                history.append({
                    "k": threshold,
                    "status": "UNSAT",
                    "build_time": step_build,
                    "solve_time": step_solve,
                    "num_variables": num_variables,
                    "num_clauses": len(delta_clauses),
                })
                lower = best
                break

            candidate_labels = order.decode(solver.get_model(), metadata)
            value = bandwidth(graph, candidate_labels)
            if not validate_solution(graph, candidate_labels, value):
                raise ValueError("Invalid SAT witness")

            history.append({
                "k": threshold,
                "status": "SAT",
                "build_time": step_build,
                "solve_time": step_solve,
                "num_variables": num_variables,
                "num_clauses": len(delta_clauses),
            })
            if value < best:
                labels = candidate_labels
                best = value
            else:
                best = threshold

    status = "OPTIMAL" if best == lower else "FEASIBLE"
    return SolveResult(
        graph.name,
        "sat_order",
        status,
        reason,
        perf_counter() - start,
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


def solve(
    graph: Graph,
    encoding: Literal["pairwise", "order"],
    time_limit_seconds: float,
) -> SolveResult:
    """Tighten a validated upper bound under one total wall-clock budget."""
    if not isfinite(time_limit_seconds) or time_limit_seconds < 0:
        raise ValueError("Expected a finite nonnegative budget")
    start = perf_counter()
    labels = list(graph.vertices)
    best = bandwidth(graph, labels)
    degrees = [0] * graph.n
    for u, v in graph.edges:
        degrees[u] += 1
        degrees[v] += 1
    lower = (max(degrees, default=0) + 1) // 2

    if encoding == "order":
        return _solve_order_incremental(
            graph,
            time_limit_seconds,
            start,
            labels,
            best,
            lower,
        )

    reason = "completed"
    build_time = 0.0
    solve_time = 0.0
    num_variables = 0
    num_clauses_total = 0
    max_num_clauses = 0
    history: list[dict[str, Any]] = []

    while best > lower:
        remaining = max(0.0, time_limit_seconds - (perf_counter() - start))
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
        perf_counter() - start,
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