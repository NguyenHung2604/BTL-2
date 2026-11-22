"""CP-SAT optimization adapter for the Cyclic Bandwidth Minimization Problem."""

from importlib.metadata import PackageNotFoundError, version
from math import ceil, isfinite
from time import monotonic

from ortools.sat.python import cp_model

from ..graph import Graph
from ..objective import bandwidth
from ..result import SolveResult
from ..validator import validate_solution


def _solver_version() -> str:
    try:
        return f"OR-Tools {version('ortools')} / CP-SAT"
    except PackageNotFoundError:
        return "OR-Tools CP-SAT (version unavailable)"


def solve(graph: Graph, time_limit_seconds: float) -> SolveResult:
    """Minimize cyclic bandwidth within one wall-clock budget.

    Each vertex receives a distinct integer position on the cycle. For every
    edge, its cyclic distance is min(|p[u]-p[v]|, n-|p[u]-p[v]|).
    """
    if (
        isinstance(time_limit_seconds, bool)
        or not isinstance(time_limit_seconds, (int, float))
        or not isfinite(float(time_limit_seconds))
        or time_limit_seconds < 0
    ):
        raise ValueError("time_limit_seconds must be a finite nonnegative number")

    started = monotonic()
    n = graph.n

    # Empty-edge graphs have the trivial optimum 0; this also handles n == 0.
    if not graph.edges:
        labels = list(range(n))
        elapsed = monotonic() - started
        return SolveResult(
            instance=graph.name,
            method="cp_sat",
            status="OPTIMAL",
            termination_reason="completed",
            runtime_seconds=elapsed,
            labels=labels,
            bandwidth=0,
            lower_bound=0,
            build_time=0.0,
            solve_time=0.0,
            num_variables=0,
            solver_version=_solver_version(),
        )

    if n <= 0:
        raise ValueError("A graph with edges must have at least one vertex")

    build_started = monotonic()
    model = cp_model.CpModel()

    positions = [
        model.new_int_var(0, n - 1, f"position_{v}")
        for v in range(n)
    ]
    model.add_all_different(positions)

    edge_distances = []
    for edge_index, (u, v) in enumerate(graph.edges):
        absolute = model.new_int_var(0, n - 1, f"absolute_{edge_index}")
        model.add_abs_equality(absolute, positions[u] - positions[v])

        cyclic = model.new_int_var(0, n // 2, f"cyclic_{edge_index}")
        model.add_min_equality(cyclic, [absolute, n - absolute])
        edge_distances.append(cyclic)

    objective = model.new_int_var(0, n // 2, "bandwidth")
    model.add_max_equality(objective, edge_distances)
    model.minimize(objective)

    build_time = monotonic() - build_started
    remaining = float(time_limit_seconds) - build_time
    if remaining <= 0:
        return SolveResult(
            instance=graph.name,
            method="cp_sat",
            status="NO_SOLUTION",
            termination_reason="timeout",
            runtime_seconds=monotonic() - started,
            labels=None,
            bandwidth=None,
            lower_bound=None,
            build_time=build_time,
            solve_time=0.0,
            num_variables=len(model.proto.variables),
            solver_version=_solver_version(),
        )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = remaining
    solve_started = monotonic()
    status_code = solver.solve(model)
    solve_time = monotonic() - solve_started

    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        labels = [int(solver.value(position)) for position in positions]
        value = int(solver.value(objective))
        if not validate_solution(graph, labels, value):
            raise ValueError("CP-SAT returned an invalid CBMP labeling")

        if status_code == cp_model.OPTIMAL:
            status = "OPTIMAL"
            termination_reason = "completed"
            lower_bound = value
        else:
            status = "FEASIBLE"
            termination_reason = "timeout"
            # CP-SAT's bound is floating point; ceil is the safe integer
            # lower bound for this integer-valued minimization objective.
            lower_bound = max(0, min(value, int(ceil(solver.best_objective_bound - 1e-6))))

        return SolveResult(
            instance=graph.name,
            method="cp_sat",
            status=status,
            termination_reason=termination_reason,
            runtime_seconds=monotonic() - started,
            labels=labels,
            bandwidth=bandwidth(graph, labels),
            lower_bound=lower_bound,
            build_time=build_time,
            solve_time=solve_time,
            num_variables=len(model.proto.variables),
            solver_version=_solver_version(),
        )

    if status_code == cp_model.INFEASIBLE:
        status = "INFEASIBLE"
        reason = "completed"
        lower_bound = None
    elif status_code == cp_model.MODEL_INVALID:
        status = "NO_SOLUTION"
        reason = "error"
        lower_bound = None
    else:  # UNKNOWN: the time budget expired before a feasible solution existed.
        status = "NO_SOLUTION"
        reason = "timeout"
        lower_bound = None

    return SolveResult(
        instance=graph.name,
        method="cp_sat",
        status=status,
        termination_reason=reason,
        runtime_seconds=monotonic() - started,
        labels=None,
        bandwidth=None,
        lower_bound=lower_bound,
        build_time=build_time,
        solve_time=solve_time,
        num_variables=len(model.proto.variables),
        solver_version=_solver_version(),
    )
