"""Integer-position model solved by IBM CP Optimizer."""

from math import ceil, isfinite
from time import perf_counter

from docplex.cp import config as cpo_config
from docplex.cp.model import CpoModel

from ..graph import Graph
from ..result import SolveResult
from ..validator import validated_bandwidth

CPO_EXEC_PATH = "/home/barium/ibm/ILOG/CPLEX_Studio222/cpoptimizer/bin/x86-64_linux/cpoptimizer"

# CHÚ Ý: NẾU CHẠY TRÊN MÁY KHÁC, ĐỪNG XÓA PHẦN CODE TÔI VIẾT, MÁY TÔI (ĐỨC) DÙNG LINUX, ĐƯỜNG DẪN TẢI
# CPLEX OPTIMIZER KHÔNG Ở MẶC ĐỊNH. NẾU MUỐN CHẠY THÌ COMMENT CODE CỦA TÔI VÀ UNCOMMENT CÁI ĐỐNG BÊN DƯỚI

# def solve(graph: Graph, time_limit_seconds: float, *, seed=0, threads=1) -> SolveResult:
#     """Keep a validated upper bound and charge model building to the deadline."""
#     start = perf_counter()
#     if not isfinite(time_limit_seconds) or time_limit_seconds < 0 or threads < 1:
#         raise ValueError("Expected a nonnegative finite budget and positive thread count")
#     deadline = start + time_limit_seconds
#     labels = list(graph.vertices)
#     best = validated_bandwidth(graph.n, graph.edges, labels)
#     degrees = [0] * graph.n
#     for u, v in graph.edges:
#         degrees[u] += 1
#         degrees[v] += 1
#     lower = (max(degrees, default=0) + 1) // 2
#     result = SolveResult(graph.name, "cplex_cp", "FEASIBLE", "timeout", 0.0,
#                          labels, best, lower)
#     if graph.edges and perf_counter() < deadline:
#         from docplex.cp.model import CpoModel
#
#         model = CpoModel(name="CBMP_CP")
#         positions = [model.integer_var(0, graph.n - 1, name=f"p_{u}") for u in graph.vertices]
#         model.add(model.all_diff(positions))
#         bound = model.integer_var(lower, best, name="bandwidth")
#         model.add(model.minimize(bound))
#         for u, v in graph.edges:
#             if perf_counter() >= deadline:
#                 break
#             delta = model.abs(positions[u] - positions[v])
#             model.add(model.min(delta, graph.n - delta) <= bound)
#         result.num_variables = graph.n + 1
#         result.build_time = perf_counter() - start
#         remaining = deadline - perf_counter()
#         if remaining > 0:
#             solving = perf_counter()
#             solution = model.solve(TimeLimit=remaining, TimeMode="ElapsedTime",
#                                    Workers=threads, RandomSeed=seed, trace_log=False)
#             result.solve_time = perf_counter() - solving
#             result.solver_version = solution.get_process_infos().get_solver_version()
#             status = solution.get_solve_status()
#             if status in ("Optimal", "Feasible"):
#                 candidate = [int(solution[position]) for position in positions]
#                 value = validated_bandwidth(graph.n, graph.edges, candidate)
#                 if value <= best:
#                     result.labels, result.bandwidth = candidate, value
#                 if status == "Optimal":
#                     result.lower_bound = value
#             elif status != "Unknown":
#                 raise RuntimeError(f"Unexpected CP Optimizer status for a feasible model: {status}")
#             native_bound = solution.get_objective_bound()
#             if native_bound is not None and isfinite(native_bound):
#                 result.lower_bound = max(result.lower_bound, ceil(native_bound - 1e-6))
#     if result.lower_bound > result.bandwidth:
#         raise ValueError("CP Optimizer bound exceeds validated incumbent")
#     if result.lower_bound == result.bandwidth:
#         result.status, result.termination_reason = "OPTIMAL", "completed"
#     result.runtime_seconds = perf_counter() - start
#     return result


def solve(graph: Graph, time_limit_seconds: float, *, seed=0, threads=1) -> SolveResult:
    """Keep a validated upper bound and charge model building to the deadline."""
    start = perf_counter()
    if not isfinite(time_limit_seconds) or time_limit_seconds < 0 or threads < 1:
        raise ValueError("Expected a nonnegative finite budget and positive thread count")
    deadline = start + time_limit_seconds
    labels = list(graph.vertices)
    best = validated_bandwidth(graph.n, graph.edges, labels)
    degrees = [0] * graph.n
    for u, v in graph.edges:
        degrees[u] += 1
        degrees[v] += 1
    lower = (max(degrees, default=0) + 1) // 2
    result = SolveResult(graph.name, "cplex_cp", "FEASIBLE", "timeout", 0.0,
                         labels, best, lower)
    if graph.edges and perf_counter() < deadline:
        cpo_config.context.solver.local.execfile = CPO_EXEC_PATH

        model = CpoModel(name="CBMP_CP")
        positions = [model.integer_var(0, graph.n - 1, name=f"p_{u}") for u in graph.vertices]
        model.add(model.all_diff(positions))
        bound = model.integer_var(lower, best, name="bandwidth")
        model.add(model.minimize(bound))
        for u, v in graph.edges:
            if perf_counter() >= deadline:
                break
            delta = model.abs(positions[u] - positions[v])
            model.add(model.min(delta, graph.n - delta) <= bound)
        result.num_variables = graph.n + 1
        result.build_time = perf_counter() - start
        remaining = deadline - perf_counter()
        if remaining > 0:
            solving = perf_counter()
            solution = model.solve(TimeLimit=remaining, TimeMode="ElapsedTime",
                                   Workers=threads, RandomSeed=seed, trace_log=False)
            result.solve_time = perf_counter() - solving
            result.solver_version = solution.get_process_infos().get_solver_version()
            status = solution.get_solve_status()
            if status in ("Optimal", "Feasible"):
                candidate = [int(solution[position]) for position in positions]
                value = validated_bandwidth(graph.n, graph.edges, candidate)
                if value <= best:
                    result.labels, result.bandwidth = candidate, value
                if status == "Optimal":
                    result.lower_bound = value
            elif status != "Unknown":
                raise RuntimeError(f"Unexpected CP Optimizer status for a feasible model: {status}")
            native_bound = solution.get_objective_bound()
            if native_bound is not None and isfinite(native_bound):
                result.lower_bound = max(result.lower_bound, ceil(native_bound - 1e-6))
    if result.lower_bound > result.bandwidth:
        raise ValueError("CP Optimizer bound exceeds validated incumbent")
    if result.lower_bound == result.bandwidth:
        result.status, result.termination_reason = "OPTIMAL", "completed"
    result.runtime_seconds = perf_counter() - start
    return result


def solve_cplex_cp(graph_id, n, edges, config=None, seed=0, wall_budget=60.0, threads=1):
    """Project-wide record interface; solve() also serves existing Graph callers."""
    graph = Graph(graph_id, n, tuple(edges))
    result = solve(graph, wall_budget, seed=seed, threads=threads)
    return dict(graph_id=graph_id, method=result.method, encoding="integer_position",
                solver_version=result.solver_version, status=result.status,
                incumbent=result.bandwidth, lower_bound=result.lower_bound,
                optimality_proven=result.status == "OPTIMAL", labeling=result.labels,
                build_time=result.build_time, solve_time=result.solve_time,
                total_time=result.runtime_seconds, num_vars=result.num_variables,
                num_variables=result.num_variables, num_clauses=None,
                termination_reason=result.termination_reason,
                commit_hash=(config or {}).get("commit_hash"), seed=seed, threads=threads)