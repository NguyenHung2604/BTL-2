"""Convert an original Matrix Market file (.mtx or .mtx.gz) to CBMP JSON."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from cbmp.harwell_boeing import read_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_path", type=Path)
    parser.add_argument("graph_path", type=Path)
    args = parser.parse_args()
    graph = read_matrix(args.raw_path)
    args.graph_path.parent.mkdir(parents=True, exist_ok=True)
    args.graph_path.write_bytes((json.dumps(asdict(graph)) + "\n").encode("utf-8"))
    print(f"{graph.name}: n={graph.n}, m={len(graph.edges)}")


if __name__ == "__main__":
    main()
