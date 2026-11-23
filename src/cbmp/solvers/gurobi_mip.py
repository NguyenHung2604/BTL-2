"""Gurobi MIP adapter for the Cyclic Bandwidth Minimization Problem."""

import math
from time import perf_counter
from typing import Any, Dict, Optional

from ..models.mip import MIPFormulation
from ..graph import Graph
from ..result import SolveResult
from ..validator import validated_bandwidth


class _BuildDeadlineExceeded(Exception):
    """Internal signal used when the adapter's total wall-clock budget expires."""


def _empty_result() -> Dict[str, Any]:
    return {
        "method": "gurobi_mip",
        "status": "NO_SOLUTION",
        "termination_reason": "error",
        "incumbent": None,
        "lower_bound": None,
        "optimality_proven": False,
        "labeling": None,
        "build_time": 0.0,
        "solve_time": 0.0,
        "total_time": 0.0,
        "num_variables": None,
        "num_constraints": None,
        "solver_status": None,
        "solver_version": None,
        "error_type": None,
        "error_message": None,
    }


def solve_gurobi(
    formulation: MIPFormulation,
    time_limit: Optional[float] = None,
    threads: int = 1,
    output_flag: bool = False,
) -> Dict[str, Any]:
    """
    Solve a CBMP instance using Gurobi and the shared MIP formulation.

    ``time_limit`` is a total adapter wall-clock budget: model construction
    and optimization both consume it. ``build_time`` and ``solve_time`` are
    reported separately, while ``total_time`` includes cleanup.
    """
    total_start = perf_counter()
    result = _empty_result()
    env = None
    model = None
    build_start = None

    if not isinstance(formulation, MIPFormulation):
        raise TypeError("formulation must be a MIPFormulation")

    if time_limit is not None:
        if (
            not isinstance(time_limit, (int, float))
            or isinstance(time_limit, bool)
            or not math.isfinite(float(time_limit))
            or time_limit <= 0
        ):
            raise ValueError("time_limit must be a finite positive number")

    if not isinstance(threads, int) or isinstance(threads, bool) or threads < 1:
        raise ValueError("threads must be a positive integer")

    deadline = None if time_limit is None else total_start + float(time_limit)

    def check_deadline() -> None:
        if deadline is not None and perf_counter() >= deadline:
            raise _BuildDeadlineExceeded

    try:
        import gurobipy as gp
        from gurobipy import GRB

        result["solver_version"] = ".".join(
            str(part) for part in gp.gurobi.version()
        )

        n = formulation.n
        build_start = perf_counter()
        check_deadline()

        env = gp.Env(empty=True)
        env.setParam("OutputFlag", int(output_flag))
        env.start()
        model = gp.Model("CBMP_Gurobi_MIP", env=env)
        model.Params.OutputFlag = int(output_flag)
        model.Params.Threads = threads

        # Binary assignment variables:
        # x[v, i] = 1 iff vertex v receives position i.
        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
        check_deadline()

        # Integer objective variable.
        K = model.addVar(
            vtype=GRB.INTEGER,
            lb=0,
            ub=formulation.max_bandwidth,
            name="K",
        )
        check_deadline()

        # Each vertex receives exactly one position.
        for v in range(n):
            check_deadline()
            model.addConstr(
                gp.quicksum(x[v, i] for i in range(n)) == 1,
                name=f"assign_vertex_{v}",
            )

        # Each position is assigned to at most one vertex.
        for i in range(n):
            check_deadline()
            model.addConstr(
                gp.quicksum(x[v, i] for v in range(n)) <= 1,
                name=f"assign_position_{i}",
            )

        # Enforce cyclic distance constraints for every graph edge.
        for index, (u, v, i, j, distance) in enumerate(
            formulation.iter_distance_constraints()
        ):
            if index % 256 == 0:
                check_deadline()
            model.addConstr(
                K >= distance * (x[u, i] + x[v, j] - 1),
                name=f"distance_{u}_{v}_{i}_{j}",
            )

        check_deadline()
        model.setObjective(K, GRB.MINIMIZE)
        model.update()
        result["build_time"] = perf_counter() - build_start
        result["num_variables"] = model.NumVars
        result["num_constraints"] = model.NumConstrs

        # Pass only the budget remaining after model construction.
        check_deadline()
        if deadline is not None:
            remaining_time = deadline - perf_counter()
            if remaining_time <= 0:
                raise _BuildDeadlineExceeded
            model.Params.TimeLimit = remaining_time

        solve_start = perf_counter()
        model.optimize()
        result["solve_time"] = perf_counter() - solve_start
        result["solver_status"] = int(model.Status)

        status_names = {
            GRB.OPTIMAL: "OPTIMAL",
            GRB.INFEASIBLE: "INFEASIBLE",
            GRB.INF_OR_UNBD: "INF_OR_UNBD",
            GRB.UNBOUNDED: "UNBOUNDED",
            GRB.TIME_LIMIT: "TIME_LIMIT",
            GRB.INTERRUPTED: "INTERRUPTED",
            GRB.NUMERIC: "NUMERIC",
            GRB.SUBOPTIMAL: "SUBOPTIMAL",
        }
        result["solver_status_name"] = status_names.get(model.Status, "OTHER")

        if model.Status == GRB.TIME_LIMIT:
            result["termination_reason"] = "timeout"
        elif model.Status == getattr(GRB, "MEM_LIMIT", -999):
            result["termination_reason"] = "OOM"
        else:
            result["termination_reason"] = "completed"

        if model.SolCount > 0:
            labeling = []
            for v in range(n):
                assigned_positions = [
                    i for i in range(n) if x[v, i].X > 0.5
                ]
                if len(assigned_positions) != 1:
                    raise RuntimeError(
                        f"Cannot decode vertex {v}: "
                        f"found {len(assigned_positions)} assigned positions"
                    )
                labeling.append(assigned_positions[0])

            actual_bandwidth = validated_bandwidth(
                n,
                formulation.edges,
                labeling,
            )
            result["labeling"] = labeling
            result["incumbent"] = actual_bandwidth
            result["solver_objective"] = float(model.ObjVal)
            result["lower_bound"] = float(model.ObjBound)

            if model.Status == GRB.OPTIMAL:
                result["status"] = "OPTIMAL"
                result["optimality_proven"] = True
            else:
                result["status"] = "FEASIBLE"

        if model.Status == GRB.OPTIMAL:
            result["status"] = "OPTIMAL"
            result["optimality_proven"] = True

    except _BuildDeadlineExceeded:
        result["termination_reason"] = "timeout"
        if build_start is not None:
            result["build_time"] = perf_counter() - build_start
        if model is not None:
            try:
                result["num_variables"] = model.NumVars
                result["num_constraints"] = model.NumConstrs
            except Exception:
                pass

    except ModuleNotFoundError as exc:
        result["termination_reason"] = "error"
        result["error_type"] = "dependency_missing"
        result["error_message"] = str(exc)

    except Exception as exc:
        result["termination_reason"] = "error"
        result["error_type"] = type(exc).__name__
        result["error_message"] = str(exc)
        message = str(exc).lower()
        error_code = getattr(exc, "errno", None)
        if isinstance(exc, MemoryError) or error_code == 10001 or "out of memory" in message:
            result["termination_reason"] = "OOM"
        elif "license" in message or error_code in (10009, 10010):
            result["termination_reason"] = "license_error"

    finally:
        if build_start is not None and result["build_time"] == 0.0:
            result["build_time"] = perf_counter() - build_start
        if model is not None:
            try:
                model.dispose()
            except Exception:
                pass
        if env is not None:
            env.dispose()
        result["total_time"] = perf_counter() - total_start

    return result


def solve(graph: Graph, time_limit_seconds: float) -> SolveResult:
    """Run gurobi MIP through the Graph-based CLI interface."""
    if not math.isfinite(time_limit_seconds) or time_limit_seconds < 0:
        raise ValueError("Expected a finite nonnegative budget")
    if time_limit_seconds == 0:
        return SolveResult(graph.name, "gurobi_mip", "NO_SOLUTION", "timeout", 0)
    record = solve_gurobi(MIPFormulation(graph.n, graph.edges), time_limit=time_limit_seconds)
    bound = record["lower_bound"]
    return SolveResult(graph.name, record["method"], record["status"], record["termination_reason"],
                       record["total_time"], record["labeling"], record["incumbent"],
                       None if bound is None else math.ceil(bound - 1e-6))
