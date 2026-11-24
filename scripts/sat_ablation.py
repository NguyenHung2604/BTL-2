"""Compare one SAT change at a time with identical descending thresholds."""

import argparse
import json
from contextlib import ExitStack
from functools import partial
from pathlib import Path
from time import monotonic

from pysat.solvers import Glucose3

from cbmp.encodings import order, pairwise
from cbmp.graph import Graph, load_graph
from cbmp.validator import validated_bandwidth
from core.search import run_solver


def _trial(encoding, variant, emit, graph, result, deadline):
    encoder = order if encoding == "order" else pairwise
    n = graph.n
    previous = n // 2
    persistent = variant == "incremental"
    with ExitStack() as resources:
        solver = None
        for k in range(result["incumbent"] - 1, result["lower_bound"] - 1, -1):
            began = monotonic()
            if began >= deadline:
                emit(("finish", "timeout"))
                return
            emit(("attempt", k, began))
            emit(("phase", "build_time", began))
            with ExitStack() as attempt:
                clauses = []
                if solver is None or not persistent:
                    clauses, meta = encoder.build(graph, previous if persistent else k)
                    if variant == "rotation":
                        # Rotate any layout so vertex 0 occupies position 0.
                        clauses.append([1])
                    owner = resources if persistent else attempt
                    solver = owner.enter_context(Glucose3(bootstrap_with=clauses))
                added = len(clauses)
                if persistent:
                    # Distances > previous are already forbidden. Add each ordered
                    # pair at a newly forbidden cyclic distance exactly once.
                    for u, v in graph.edges:
                        for d in range(k + 1, previous + 1):
                            offsets = (d,) if 2 * d == n else (d, -d)
                            for i in range(n):
                                for offset in offsets:
                                    j = (i + offset) % n
                                    solver.add_clause(order.different_from(u, i, n)
                                                      + order.different_from(v, j, n))
                                    added += 1
                    previous = k
                emit(("size", solver.nof_vars() if not persistent or k == result["incumbent"] - 1 else 0, added))
                emit(("phase", "solve_time", monotonic()))
                answer = solver.solve()
                if answer is True:
                    labels = encoder.decode(solver.get_model(), meta)
                    value = validated_bandwidth(n, graph.edges, labels)
                    if value > k:
                        raise ValueError("Witness exceeds the decision threshold")
                    emit(("incumbent", labels, value))
                now = monotonic()
                emit(("decision", {True: "SAT", False: "UNSAT", None: "UNKNOWN"}[answer], now))
                emit(("phase", None, now))
                if answer is None:
                    emit(("finish", "timeout"))
                    return
                if answer is False:
                    break
    emit(("finish", "completed"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    graphs = [
        Graph("scrambled_path", 5, ((0, 2), (2, 4), (4, 1), (1, 3))),
        Graph("scrambled_path8", 8, ((0, 4), (4, 1), (1, 5), (5, 2), (2, 6), (6, 3), (3, 7))),
        Graph("complete_bipartite_3_3", 6, tuple((u, v) for u in range(3) for v in range(3, 6))),
        load_graph("data/benchmarks/harwell_boeing/graphs/jgl009.json"),
    ]
    records = []
    for graph in graphs:
        for encoding, variant in (("pairwise", "rebuilt"), ("pairwise", "rotation"),
                                  ("order", "rebuilt"), ("order", "incremental")):
            record = run_solver(partial(_trial, encoding, variant), "sat_" + encoding,
                                "python-sat", graph.name, graph.n, graph.edges,
                                {}, 0, args.seconds, 1)
            record.update(encoding=encoding, variant=variant, wall_budget=args.seconds)
            records.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


if __name__ == "__main__":
    main()
