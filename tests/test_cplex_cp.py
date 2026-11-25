import pytest

from cbmp.graph import Graph
from cbmp.solvers.cplex_cp import solve
from cbmp.validator import validated_bandwidth


def test_no_edges_proves_zero_without_an_engine():
    result = solve(Graph("empty", 4, ()), 0)
    assert (result.status, result.lower_bound, result.bandwidth) == ("OPTIMAL", 0, 0)
    assert result.termination_reason == "completed"


def test_zero_budget_retains_a_valid_witness_and_degree_bound():
    graph = Graph("edge", 6, ((0, 3),))
    result = solve(graph, 0)
    assert (result.status, result.termination_reason) == ("FEASIBLE", "timeout")
    assert result.lower_bound == 1
    assert validated_bandwidth(graph.n, graph.edges, result.labels) == result.bandwidth == 3


def test_negative_budget_is_rejected():
    with pytest.raises(ValueError):
        solve(Graph("empty", 0, ()), -1)


def test_cp_engine_on_path_takes_precedence(monkeypatch):
    from cbmp.solvers import cplex_cp

    def check_engine(model, **options):
        assert options["execfile"] == "installed/cpoptimizer"
        raise RuntimeError("verified engine selection")

    monkeypatch.setattr(cplex_cp, "which", lambda name: "installed/cpoptimizer")
    monkeypatch.setattr(cplex_cp.CpoModel, "solve", check_engine)
    with pytest.raises(RuntimeError, match="verified engine selection"):
        solve(Graph("edge", 6, ((0, 3),)), 10)
