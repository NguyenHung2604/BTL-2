"""Solve one CBMP graph within a shared time budget."""

import argparse


def main() -> None:
    """Parse command-line inputs for the planned workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="Input graph JSON")
    parser.add_argument("--method", choices=("sat_pairwise", "sat_order", "cp_sat", "cplex_cp", "cplex_mip", "gurobi_mip"), required=True, help="Solver method")
    parser.add_argument("--time-limit-seconds", type=float, required=True, help="Total time budget in seconds")
    parser.parse_args()
    raise NotImplementedError("Solve one CBMP graph within a shared time budget.")


if __name__ == "__main__":
    main()
