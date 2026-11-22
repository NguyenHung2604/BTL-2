from itertools import combinations

import pytest

from cbmp.solvers import cp_sat
from brute_force import optimum
from cbmp.graph import Graph
from cbmp.validator import validated_bandwidth
from core import search


@pytest.mark.parametrize("backend", [search, cp_sat])
@pytest.mark.parametrize("graph,expected", [
    (Graph("path", 5, ((0, 2), (2, 4), (4, 1), (1, 3))), 1),
    (Graph("cycle", 6, ((0, 2), (2, 4), (4, 1), (1, 5), (5, 3), (3, 0))), 1),
    (Graph("complete", 5, tuple(combinations(range(5), 2))), 2),
    (Graph("empty", 0, ()), 0),
    (Graph("eight", 8, ((0, 1), (1, 2), (0, 2), (4, 6))), 2),
])
def test_against_oracle(backend, graph, expected):
    if backend is cp_sat:
        pytest.importorskip("ortools")
    record = backend.solve(graph.name, graph.n, graph.edges, wall_budget=15)
    assert record["status"] == "OPTIMAL" and record["optimality_proven"]
    assert record["termination_reason"] == "completed"
    assert validated_bandwidth(graph.n, graph.edges, record["labeling"]) == expected
    assert record["incumbent"] == record["lower_bound"] == optimum(graph) == expected
    if backend is search:
        history = record["history"]
        assert all(row["elapsed"] >= 0 for row in history)
        if graph.name == "eight":
            assert history[-1]["status"] == "UNSAT" and history[-1]["k"] == expected - 1
        if graph.name == "path":
            assert history[0]["status"] == "SAT" and history[0]["k"] == 1


@pytest.mark.parametrize("backend", [search, cp_sat])
def test_zero_budget_keeps_valid_incumbent(backend):
    result = backend.solve("edge", 6, [(0, 3)], wall_budget=0)
    assert result["termination_reason"] == "timeout"
    assert not result["optimality_proven"] and result["status"] == "FEASIBLE"
    assert result["lower_bound"] == 1 and result["incumbent"] == 3


def _blocked_build(emit, graph, result, deadline):
    from time import monotonic, sleep
    began = monotonic()
    emit(("attempt", 2, began))
    emit(("phase", "build_time", began))
    sleep(30)


def test_deadline_interrupts_build():
    record = search.run_solver(_blocked_build, "sat_pairwise", "python-sat",
                               "edge", 6, [(0, 3)], {}, 0, 2, 1)
    assert record["termination_reason"] == "timeout"
    assert record["history"][0]["status"] == "UNKNOWN"
    assert record["lower_bound"] == 1 and record["incumbent"] == 3
    assert record["total_time"] < 8


def test_cp_sat_positive_wall_timeout_keeps_witness():
    graph = Graph("timeout", 8, ((0, 4), (4, 7)))
    record = cp_sat.solve(graph.name, graph.n, graph.edges, wall_budget=0.001)
    assert record["status"] == "FEASIBLE" and not record["optimality_proven"]
    assert record["termination_reason"] == "timeout"
    assert validated_bandwidth(graph.n, graph.edges, record["labeling"]) == record["incumbent"]
    assert record["lower_bound"] < record["incumbent"]


@pytest.mark.parametrize("native_status,expected_upper", [("UNKNOWN", 4), ("FEASIBLE", 2)])
def test_cp_sat_native_timeout(monkeypatch, native_status, expected_upper):
    """Exercise native statuses deterministically, independently of machine speed."""
    from time import monotonic
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")
    graph = Graph("triangle_and_edge", 8, ((0, 1), (1, 2), (0, 2), (3, 7)))
    labels = [0, 1, 2, 3, 5, 6, 7, 4]
    witness = validated_bandwidth(graph.n, graph.edges, labels)
    assert witness == 2
    events = []
    budget = 2.0

    class LimitedSolver(cp_model.CpSolver):
        def solve(self, model, callback):
            assert 0 < self.parameters.max_time_in_seconds <= budget
            if native_status == "FEASIBLE":
                self.best_bound_callback(2.0)
            return getattr(cp_model, native_status)

        def value(self, position):
            assert native_status == "FEASIBLE"
            return labels[position.index]

        @property
        def best_objective_bound(self):
            return 2.0

    monkeypatch.setattr(cp_model, "CpSolver", LimitedSolver)
    cp_sat._optimize(events.append, graph,
                     dict(lower_bound=1, incumbent=4, seed=0, threads=1),
                     monotonic() + budget)
    assert events[-1] == ("finish", "timeout")
    assert [e for e in events if e[0] == "bound"] == [("bound", 2)]
    incumbents = [validated_bandwidth(graph.n, graph.edges, e[1])
                  for e in events if e[0] == "incumbent"]
    assert min([4, *incumbents]) == expected_upper
