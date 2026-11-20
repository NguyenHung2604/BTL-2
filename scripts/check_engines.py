"""Run a tiny integer optimization on a selected engine. Expected optimum is one."""

import argparse
import shutil


def probe(engine: str) -> int:
    if engine == "cp_sat":
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()
        x = model.new_int_var(0, 2, "x")
        model.add(x >= 1)
        model.minimize(x)
        solver = cp_model.CpSolver()
        if solver.solve(model) != cp_model.OPTIMAL:
            raise RuntimeError("CP-SAT did not prove optimality")
        return solver.value(x)
    if engine == "cplex_cp":
        from docplex.cp.model import CpoModel
        model = CpoModel()
        x = model.integer_var(0, 2, "x")
        model.add(x >= 1)
        model.add(model.minimize(x))
        executable = shutil.which("cpoptimizer")
        if not executable:
            raise RuntimeError("cpoptimizer must be on PATH")
        solution = model.solve(execfile=executable, TimeLimit=10, LogVerbosity="Quiet")
        if solution.get_solve_status() != "Optimal":
            raise RuntimeError(str(solution.get_solve_status()))
        return solution[x]
    if engine == "cplex_mip":
        from docplex.mp.model import Model
        with Model() as model:
            x = model.integer_var(0, 2, "x")
            model.add_constraint(x >= 1)
            model.minimize(x)
            solution = model.solve()
            if solution is None or model.solve_details.status_code != 101:
                raise RuntimeError(model.solve_details.status)
            return round(solution[x])
    from cbmp.graph import Graph
    from cbmp.solvers.gurobi_mip import solve
    result = solve(Graph("edge", 2, ((0, 1),)), 10)
    if result.status != "OPTIMAL":
        raise RuntimeError(result.termination_reason)
    return result.bandwidth


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", choices=("cp_sat", "cplex_cp", "cplex_mip", "gurobi_mip"))
    engine = parser.parse_args().engine
    value = probe(engine)
    if value != 1:
        raise RuntimeError(f"Unexpected optimum {value}")
    print(f"{engine}: OPTIMAL, objective={value}")
