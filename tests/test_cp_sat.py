"""Tests for the CP-SAT CBMP adapter."""

from types import SimpleNamespace

from ortools.sat.python import cp_model

from cbmp.graph import Graph
from cbmp.solvers import cp_sat


def test_edgeless_graph_has_trivial_optimum_zero():
    graph = Graph("edgeless", 4, tuple())

    result = cp_sat.solve(graph, time_limit_seconds=1)

    assert result.status == "OPTIMAL"
    assert result.termination_reason == "completed"
    assert result.bandwidth == 0
    assert result.lower_bound == 0
    assert result.labels == [0, 1, 2, 3]


def test_graph_with_isolated_vertices_returns_valid_permutation():
    graph = Graph("one_edge_with_isolates", 4, ((0, 1),))

    result = cp_sat.solve(graph, time_limit_seconds=5)

    assert result.status == "OPTIMAL"
    assert result.bandwidth == 1
    assert sorted(result.labels) == list(range(graph.n))


def test_build_timeout_does_not_start_solver(monkeypatch):
    graph = Graph("build_timeout", 3, ((0, 1),))
    clock_values = iter((0.0, 0.0, 2.0, 2.0))
    monkeypatch.setattr(cp_sat, "monotonic", lambda: next(clock_values))

    class SolverMustNotStart:
        def __init__(self):
            raise AssertionError("CP-SAT solver must not start after build timeout")

    monkeypatch.setattr(cp_sat.cp_model, "CpSolver", SolverMustNotStart)

    result = cp_sat.solve(graph, time_limit_seconds=1)

    assert result.status == "NO_SOLUTION"
    assert result.termination_reason == "timeout"
    assert result.labels is None
    assert result.bandwidth is None
    assert result.build_time == 2.0
    assert result.solve_time == 0.0


def test_feasible_timeout_keeps_incumbent_and_integer_lower_bound(monkeypatch):
    graph = Graph("feasible_timeout", 4, ((0, 1),))

    class FakeVariable:
        def __init__(self, name):
            self.name = name

        # The fake model does not evaluate expressions; it only needs to
        # accept the arithmetic used to construct the real CP-SAT model.
        def __sub__(self, other):
            return ("sub", self, other)

        def __rsub__(self, other):
            return ("rsub", other, self)

    class FakeModel:
        def __init__(self):
            self.proto = SimpleNamespace(variables=[])

        def new_int_var(self, lower, upper, name):
            variable = FakeVariable(name)
            self.proto.variables.append(variable)
            return variable

        def add_all_different(self, variables):
            pass

        def add_abs_equality(self, target, expression):
            pass

        def add_min_equality(self, target, expressions):
            pass

        def add_max_equality(self, target, expressions):
            pass

        def minimize(self, expression):
            pass

    class FakeSolver:
        def __init__(self):
            self.parameters = SimpleNamespace(max_time_in_seconds=None)
            self.best_objective_bound = 1.0

        def solve(self, model):
            return cp_model.FEASIBLE

        def value(self, variable):
            if variable.name.startswith("position_"):
                labels = [0, 2, 1, 3]
                return labels[int(variable.name.rsplit("_", 1)[1])]
            if variable.name == "bandwidth":
                return 2
            raise AssertionError(f"Unexpected variable: {variable.name}")

    monkeypatch.setattr(cp_sat.cp_model, "CpModel", FakeModel)
    monkeypatch.setattr(cp_sat.cp_model, "CpSolver", FakeSolver)

    result = cp_sat.solve(graph, time_limit_seconds=5)

    assert result.status == "FEASIBLE"
    assert result.termination_reason == "timeout"
    assert result.labels == [0, 2, 1, 3]
    assert result.bandwidth == 2
    assert result.lower_bound == 1
    assert result.status != "OPTIMAL"
