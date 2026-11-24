"""Integer-position CP-SAT model for cyclic bandwidth minimization."""

import math
from threading import Lock
from time import monotonic

from core.search import run_solver


def _optimize(emit, graph, result, deadline):
    from ortools.sat.python import cp_model

    emit(("phase", "build_time", monotonic()))
    model = cp_model.CpModel()
    n = graph.n
    positions = [model.new_int_var(0, n - 1, f"p_{v}") for v in graph.vertices]
    model.add_all_different(positions)
    bound = model.new_int_var(result["lower_bound"], result["incumbent"], "bandwidth")
    for u, v in graph.edges:
        if monotonic() >= deadline:
            emit(("finish", "timeout"))
            return
        delta = model.new_int_var(0, n - 1, f"delta_{u}_{v}")
        distance = model.new_int_var(0, n // 2, f"distance_{u}_{v}")
        model.add_abs_equality(delta, positions[u] - positions[v])
        model.add_min_equality(distance, [delta, n - delta])
        model.add(distance <= bound)
    model.minimize(bound)
    emit(("size", len(model.proto.variables), None))

    # Native search workers can report bounds and witnesses independently.
    # Serialize messages to the supervisor's one-way pipe.
    progress_lock = Lock()
    last_bound = result["lower_bound"]

    def publish_bound(native_bound):
        nonlocal last_bound
        if not math.isfinite(native_bound):
            return
        lower = math.ceil(native_bound - 1e-6)
        with progress_lock:
            if lower > last_bound:
                emit(("bound", lower))
                last_bound = lower

    class Witness(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            labels = [self.value(p) for p in positions]
            with progress_lock:
                emit(("incumbent", labels, None))

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = result["seed"]
    solver.parameters.num_search_workers = result["threads"]
    solver.parameters.absolute_gap_limit = 0.0
    solver.parameters.relative_gap_limit = 0.0
    solver.best_bound_callback = publish_bound
    remaining = deadline - monotonic()
    if remaining <= 0:
        emit(("finish", "timeout"))
        return
    solver.parameters.max_time_in_seconds = remaining
    emit(("phase", "solve_time", monotonic()))
    status = solver.solve(model, Witness())
    emit(("phase", None, monotonic()))
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        emit(("incumbent", [solver.value(p) for p in positions], None))
    elif status != cp_model.UNKNOWN:
        raise RuntimeError(f"Unexpected CP-SAT status: {solver.status_name(status)}")
    # UNKNOWN can still carry a valid lower bound. Reading variable values
    # requires a feasible solution, whereas reading the bound does not.
    publish_bound(solver.best_objective_bound)
    emit(("finish", "completed" if status == cp_model.OPTIMAL else "timeout"))


def solve(graph_id, n, edges, config=None, seed=0, wall_budget=60.0, threads=1):
    """Minimize maximum cyclic distance under one wall-clock budget."""
    return run_solver(_optimize, "cp_sat", "ortools", graph_id, n, edges,
                      config, seed, wall_budget, threads)
