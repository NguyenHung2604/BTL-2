"""Run one trial of the independent day-6 pilot from the repository root."""

import argparse
import hashlib
import json
from pathlib import Path

from cbmp.graph import load_graph
from core import cp_sat
from cbmp.validator import validated_bandwidth
from core import search

SOURCES = {
    "jgl009": "data/benchmarks/harwell_boeing/graphs/jgl009.json",
    "bcsstm01": "data/excluded/bcsstm01.json",
    "bcsstk01": "data/benchmarks/harwell_boeing/graphs/bcsstk01.json",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance", choices=SOURCES)
    parser.add_argument("method", choices=("sat_pairwise", "cp_sat"))
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    path = Path(SOURCES[args.instance])
    graph = load_graph(path)

    backend = search if args.method == "sat_pairwise" else cp_sat
    record = backend.solve(graph.name, graph.n, graph.edges, seed=0,
                           threads=1, wall_budget=args.seconds)
    objective = validated_bandwidth(graph.n, graph.edges, record["labeling"], record["incumbent"])
    if record["lower_bound"] > objective or record["optimality_proven"] != (record["lower_bound"] == objective):
        raise ValueError("Inconsistent incumbent and bound")
    sources = ["src/core/search.py", "src/cbmp/validator.py", "src/cbmp/objective.py",
               "src/cbmp/encodings/pairwise.py" if backend is search else "src/core/cp_sat.py"]
    record.update(n=graph.n, m=len(graph.edges), path=path.as_posix(), validated=True,
                  wall_budget=args.seconds, input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  source_sha256={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources})
    print(json.dumps(record))


if __name__ == "__main__":
    main()
