"""Solve a CBMP graph or check a SAT threshold."""

import argparse
from dataclasses import asdict
import json

from cbmp.graph import load_graph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph")
    parser.add_argument("--method", choices=("sat_pairwise", "sat_order", "gurobi_mip", "cplex_mip", "cp_sat", "cplex_cp"),
                        required=True)
    parser.add_argument("--time-limit-seconds", type=float, required=True)
    parser.add_argument("--k", type=int, help="Check bandwidth <= K with a SAT encoding")
    args = parser.parse_args()
    graph = load_graph(args.graph)
    if args.method in ("cp_sat", "cplex_cp"):
        if args.k is not None:
            parser.error("--k requires a SAT encoding")
        if args.method == "cplex_cp":
            from cbmp.solvers.cplex_cp import solve
        else:
            from cbmp.solvers.cp_sat import solve
        result = solve(graph, args.time_limit_seconds)
    elif args.method.endswith("_mip"):
        if args.k is not None:
            parser.error("--k requires a SAT method")
        if args.method == "gurobi_mip":
            from cbmp.solvers.gurobi_mip import solve
        else:
            from cbmp.solvers.cplex_mip import solve
        result = solve(graph, args.time_limit_seconds)
    else:
        from cbmp.solvers.sat import decide, solve
        encoding = args.method.removeprefix("sat_")
        if args.k is None:
            result = solve(graph, encoding, args.time_limit_seconds)
        else:
            result = decide(graph, encoding, args.k, args.time_limit_seconds)
    print(json.dumps(asdict(result)))


if __name__ == "__main__":
    main()
