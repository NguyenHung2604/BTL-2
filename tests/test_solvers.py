import pytest

from cbmp.graph import Graph
from cbmp.solvers.sat import decide, solve
from cbmp.validator import validate_solution


@pytest.mark.parametrize("encoding", ["pairwise", "order"])
def test_optimize_and_timeout(encoding):
    graph = Graph("scrambled_path", 5, ((0, 2), (2, 4), (4, 1), (1, 3)))
    result = solve(graph, encoding, 10)
    assert result.status == "OPTIMAL"
    assert result.bandwidth == result.lower_bound == 1
    assert validate_solution(graph, result.labels, 1)
    assert decide(graph, encoding, 1, 0).status == "UNKNOWN"
    interrupted = solve(graph, encoding, 0)
    assert interrupted.status == "FEASIBLE"
    assert interrupted.termination_reason == "timeout"


def test_gurobi_against_oracle():
    pytest.importorskip("gurobipy")
    from brute_force import optimum
    from cbmp.solvers.gurobi_mip import solve as solve_mip
    graph = Graph("star", 5, tuple((0, v) for v in range(1, 5)))
    result = solve_mip(graph, 15)
    if result.termination_reason == "license_error":
        pytest.skip("Gurobi license unavailable")
    assert result.status == "OPTIMAL"
    assert result.bandwidth == result.lower_bound == optimum(graph)
    assert validate_solution(graph, result.labels, result.bandwidth)


def test_sat_optimization_records_per_threshold_metrics():
    graph = Graph("scrambled_path", 5, ((0, 2), (2, 4), (4, 1), (1, 3)))
    result = solve(graph, "pairwise", 10)
    assert result.build_time > 0
    assert result.solve_time >= 0
    assert result.num_variables == graph.n * graph.n
    assert result.num_clauses > 0
    assert result.max_num_clauses > 0
    assert result.decision_history
    assert result.decision_history[0]["k"] == 1
    assert result.decision_history[0]["status"] == "SAT"
    assert "Glucose3" in result.solver_version
