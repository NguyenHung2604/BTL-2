"""Normalize a square Harwell–Boeing matrix into a CBMP graph."""

import argparse


def main() -> None:
    """Parse command-line inputs for the planned workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_path", help="Original matrix")
    parser.add_argument("graph_path", help="Output graph JSON")
    parser.parse_args()
    raise NotImplementedError("Normalize a square Harwell–Boeing matrix into a CBMP graph.")


if __name__ == "__main__":
    main()
