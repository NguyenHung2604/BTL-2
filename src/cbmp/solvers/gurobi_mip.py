
"""Gurobi MIP adapter for the Cyclic Bandwidth Minimization Problem."""

from time import perf_counter
from typing import Any, Dict, Optional

from ..models.mip import MIPFormulation
from ..validator import validate_solution


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

    Returns a dictionary containing the solution, bounds, timing,
    model statistics, and termination information.
    """
    total_start = perf_counter()
    result = _empty_result()

    if not isinstance(formulation, MIPFormulation):
        raise TypeError("formulation must be a MIPFormulation")

    if time_limit is not None:
        if not isinstance(time_limit, (int, float)) or time_limit <= 0:
            raise ValueError("time_limit must be a positive number")

    if not isinstance(threads, int) or isinstance(threads, bool) or threads < 1:
        raise ValueError("threads must be a positive integer")

    try:
        import gurobipy as gp
        from gurobipy import GRB

        result["solver_version"] = ".".join(
            str(part) for part in gp.gurobi.version()
        )

        n = formulation.n

        build_start = perf_counter()

        model = gp.Model("CBMP_Gurobi_MIP")

        model.Params.OutputFlag = int(output_flag)
        model.Params.Threads = threads

        if time_limit is not None:
            model.Params.TimeLimit = float(time_limit)

        # Binary assignment variables:
        # x[v, i] = 1 iff vertex v receives position i.
        x = model.addVars(
            n,
            n,
            vtype=GRB.BINARY,
            name="x",
        )

        # Integer objective variable.
        K = model.addVar(
            vtype=GRB.INTEGER,
            lb=0,
            ub=formulation.max_bandwidth,
            name="K",
        )

        # Each vertex receives exactly one position.
        for v in range(n):
            model.addConstr(
                gp.quicksum(x[v, i] for i in range(n)) == 1,
                name=f"assign_vertex_{v}",
            )

        # Each position is assigned to at most one vertex.
        for i in range(n):
            model.addConstr(
                gp.quicksum(x[v, i] for v in range(n)) <= 1,
                name=f"assign_position_{i}",
            )

        # Enforce cyclic distance constraints for every graph edge.
        for u, v, i, j, distance in formulation.iter_distance_constraints():
            model.addConstr(
                K >= distance * (x[u, i] + x[v, j] - 1),
                name=f"distance_{u}_{v}_{i}_{j}",
            )

        model.setObjective(K, GRB.MINIMIZE)

        model.update()

        result["build_time"] = perf_counter() - build_start
        result["num_variables"] = model.NumVars
        result["num_constraints"] = model.NumConstrs

        # Optimize.
        model.optimize()

        result["solve_time"] = float(model.Runtime)
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

        result["solver_status_name"] = status_names.get(
            model.Status,
            "OTHER",
        )

        if model.Status == GRB.TIME_LIMIT:
            result["termination_reason"] = "timeout"
        elif model.Status == getattr(GRB, "MEM_LIMIT", -999):
            result["termination_reason"] = "OOM"
        else:
            result["termination_reason"] = "completed"

        if model.SolCount > 0:
            # Decode the assignment variables.
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

            # Independently validate the solution.
            actual_bandwidth = validate_solution(
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

        model.dispose()

    except ModuleNotFoundError as exc:
        result["termination_reason"] = "error"
        result["error_type"] = "dependency_missing"
        result["error_message"] = str(exc)

    except Exception as exc:
        result["termination_reason"] = "error"
        result["error_type"] = type(exc).__name__
        result["error_message"] = str(exc)

        # Detect license failures separately from algorithm timeouts.
        message = str(exc).lower()
        error_code = getattr(exc, "errno", None)

        if (
            "license" in message
            or error_code == 10009
        ):
            result["termination_reason"] = "license_error"

    finally:
        result["total_time"] = perf_counter() - total_start

    return result
