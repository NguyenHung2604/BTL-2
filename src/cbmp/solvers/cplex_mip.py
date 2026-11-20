"""CPLEX MIP adapter for the Cyclic Bandwidth Minimization Problem."""

import math
from time import perf_counter
from typing import Any, Dict, Optional

from ..models.mip import MIPFormulation
from ..validator import validate_solution


class _BuildDeadlineExceeded(Exception):
    """Internal signal used when the adapter's total wall-clock budget expires."""


def _empty_result() -> Dict[str, Any]:
    return {
        "method": "cplex_mip",
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
        "solver_status_name": None,
        "solver_version": None,
        "error_type": None,
        "error_message": None,
    }


def solve_cplex(
    formulation: MIPFormulation,
    time_limit: Optional[float] = None,
    threads: int = 1,
    output_flag: bool = False,
) -> Dict[str, Any]:
    """
    Solve a CBMP instance using CPLEX and the shared MIP formulation.

    ``time_limit`` is a total adapter wall-clock budget: model construction
    and optimization both consume it. ``build_time`` and ``solve_time`` are
    reported separately, while ``total_time`` includes cleanup.
    """
    total_start = perf_counter()
    result = _empty_result()
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

    if (
        not isinstance(threads, int)
        or isinstance(threads, bool)
        or threads < 1
    ):
        raise ValueError("threads must be a positive integer")

    deadline = None if time_limit is None else total_start + float(time_limit)

    def check_deadline() -> None:
        if deadline is not None and perf_counter() >= deadline:
            raise _BuildDeadlineExceeded

    try:
        import cplex

        build_start = perf_counter()
        check_deadline()
        model = cplex.Cplex()
        result["solver_version"] = model.get_version()

        if not output_flag:
            model.set_log_stream(None)
            model.set_results_stream(None)
            model.set_warning_stream(None)
            model.set_error_stream(None)

        model.parameters.threads.set(threads)

        n = formulation.n
        num_x = n * n
        k_index = num_x

        # x[v, i] = 1 iff vertex v receives position i.
        variable_names = []
        for v in range(n):
            for i in range(n):
                if len(variable_names) % 256 == 0:
                    check_deadline()
                variable_names.append(f"x_{v}_{i}")
        variable_names.append("K")

        check_deadline()
        model.variables.add(
            obj=[0.0] * num_x + [1.0],
            lb=[0.0] * (num_x + 1),
            ub=[1.0] * num_x + [float(formulation.max_bandwidth)],
            types="B" * num_x + "I",
            names=variable_names,
        )
        check_deadline()

        # Collect assignment and cyclic-distance constraints.
        rows = []
        senses = []
        rhs = []
        constraint_names = []

        for v in range(n):
            check_deadline()
            indices = [v * n + i for i in range(n)]
            rows.append(cplex.SparsePair(ind=indices, val=[1.0] * n))
            senses.append("E")
            rhs.append(1.0)
            constraint_names.append(f"assign_vertex_{v}")

        for i in range(n):
            check_deadline()
            indices = [v * n + i for v in range(n)]
            rows.append(cplex.SparsePair(ind=indices, val=[1.0] * n))
            senses.append("L")
            rhs.append(1.0)
            constraint_names.append(f"assign_position_{i}")

        # K >= d * (x[u, i] + x[v, j] - 1), rearranged as:
        # K - d*x[u, i] - d*x[v, j] >= -d.
        for index, (u, v, i, j, distance) in enumerate(
            formulation.iter_distance_constraints()
        ):
            if index % 256 == 0:
                check_deadline()
            rows.append(
                cplex.SparsePair(
                    ind=[k_index, u * n + i, v * n + j],
                    val=[1.0, -float(distance), -float(distance)],
                )
            )
            senses.append("G")
            rhs.append(-float(distance))
            constraint_names.append(f"distance_{u}_{v}_{i}_{j}")

        check_deadline()
        model.linear_constraints.add(
            lin_expr=rows,
            senses="".join(senses),
            rhs=rhs,
            names=constraint_names,
        )
        check_deadline()

        result["build_time"] = perf_counter() - build_start
        result["num_variables"] = model.variables.get_num()
        result["num_constraints"] = model.linear_constraints.get_num()

        # Pass only the budget remaining after model construction.
        if deadline is not None:
            remaining_time = deadline - perf_counter()
            if remaining_time <= 0:
                raise _BuildDeadlineExceeded
            model.parameters.timelimit.set(float(remaining_time))

        solve_start = perf_counter()
        model.solve()
        result["solve_time"] = perf_counter() - solve_start

        status_code = model.solution.get_status()
        status_name = model.solution.get_status_string()
        result["solver_status"] = int(status_code)
        result["solver_status_name"] = str(status_name)

        status_lower = str(status_name).lower()
        if "time limit" in status_lower or "timelimit" in status_lower:
            result["termination_reason"] = "timeout"
        elif "infeasible" in status_lower:
            result["status"] = "INFEASIBLE"
            result["termination_reason"] = "completed"
        else:
            result["termination_reason"] = "completed"

        if model.solution.is_primal_feasible():
            x_indices = list(range(num_x))
            values = model.solution.get_values(x_indices)
            labeling = []

            for v in range(n):
                assigned_positions = [
                    i for i in range(n) if values[v * n + i] > 0.5
                ]
                if len(assigned_positions) != 1:
                    raise RuntimeError(
                        f"Cannot decode vertex {v}: "
                        f"found {len(assigned_positions)} assigned positions"
                    )
                labeling.append(assigned_positions[0])

            actual_bandwidth = validate_solution(
                n,
                formulation.edges,
                labeling,
            )
            result["labeling"] = labeling
            result["incumbent"] = actual_bandwidth
            result["solver_objective"] = float(
                model.solution.get_objective_value()
            )

            try:
                result["lower_bound"] = float(
                    model.solution.MIP.get_best_objective()
                )
            except Exception:
                result["lower_bound"] = None

            if "optimal" in status_lower:
                result["status"] = "OPTIMAL"
                result["optimality_proven"] = True
            else:
                result["status"] = "FEASIBLE"

    except _BuildDeadlineExceeded:
        result["termination_reason"] = "timeout"
        if build_start is not None:
            result["build_time"] = perf_counter() - build_start
        if model is not None:
            try:
                result["num_variables"] = model.variables.get_num()
                result["num_constraints"] = model.linear_constraints.get_num()
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
        if (
            "license" in message
            or "community edition" in message
            or "problem size limits" in message
            or "error 1016" in message
        ):
            result["termination_reason"] = "license_error"

    finally:
        if build_start is not None and result["build_time"] == 0.0:
            result["build_time"] = perf_counter() - build_start
        if model is not None:
            try:
                model.end()
            except Exception:
                pass
        result["total_time"] = perf_counter() - total_start

    return result
