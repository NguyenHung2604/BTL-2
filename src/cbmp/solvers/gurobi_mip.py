"""First Gurobi adapter for the common assignment ILP."""

from math import ceil, isfinite
from time import monotonic

import gurobipy as gp
from gurobipy import GRB

from ..graph import Graph
from ..models.mip import build
from ..objective import bandwidth
from ..result import SolveResult
from ..validator import validate_solution


def solve(graph: Graph, time_limit_seconds: float) -> SolveResult:
    """Return the validated incumbent and integer lower bound within a shared budget."""
    if not isfinite(time_limit_seconds) or time_limit_seconds < 0:
        raise ValueError("Expected a finite nonnegative budget")
    start = monotonic()
    def result(status, reason, labels=None, value=None, bound=None):
        return SolveResult(graph.name, "gurobi_mip", status, reason, monotonic() - start,
                           labels, value, bound)

    try:
        with gp.Env(empty=True) as env:
            env.setParam("OutputFlag", 0)
            env.start()
            with gp.Model(env=env) as model:
                x = model.addVars(graph.vertices, graph.vertices, vtype=GRB.BINARY)
                b = model.addVar(ub=graph.n // 2, vtype=GRB.INTEGER)
                model.setObjective(b, GRB.MINIMIZE)
                model.addConstrs(x.sum(v, "*") == 1 for v in graph.vertices)
                model.addConstrs(x.sum("*", i) == 1 for i in graph.vertices)
                for u, i, v, j, distance in build(graph):
                    if monotonic() - start >= time_limit_seconds:
                        return result("NO_SOLUTION", "timeout")
                    model.addConstr(b >= distance * (x[u, i] + x[v, j] - 1))
                remaining = time_limit_seconds - (monotonic() - start)
                if remaining <= 0:
                    return result("NO_SOLUTION", "timeout")
                model.Params.TimeLimit = remaining
                model.Params.Threads = 1
                model.Params.MIPGap = 0
                model.optimize()
                reason = {GRB.OPTIMAL: "completed", GRB.TIME_LIMIT: "timeout"}.get(
                    model.Status, f"gurobi_status_{model.Status}")
                lb = model.ObjBound
                bound = max(0, ceil(lb - 1e-6)) if isfinite(lb) and abs(lb) < GRB.INFINITY else 0
                if model.SolCount == 0:
                    return result("NO_SOLUTION", reason, bound=bound)
                labels = [next(i for i in graph.vertices if x[v, i].X > 0.5)
                          for v in graph.vertices]
                value = bandwidth(graph, labels)
                if not validate_solution(graph, labels, value) or bound > value:
                    raise ValueError("Invalid Gurobi incumbent or bound")
                return result("OPTIMAL" if bound == value else "FEASIBLE",
                              reason, labels, value, bound)
    except gp.GurobiError as exc:
        if exc.errno in (GRB.Error.NO_LICENSE, GRB.Error.SIZE_LIMIT_EXCEEDED):
            return result("NO_SOLUTION", "license_error")
        raise
