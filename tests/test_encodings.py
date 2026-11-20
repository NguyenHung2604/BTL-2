from itertools import combinations
from pathlib import Path

import pytest

from brute_force import optimum
from cbmp.graph import Graph, load_graph
from cbmp.objective import bandwidth
from cbmp.solvers.sat import decide
from cbmp.validator import validate_solution

TOY = Path(__file__).resolve().parents[1] / "data/toy"


@pytest.mark.parametrize("graph", [
    Graph("empty", 0, ()), Graph("single", 1, ()), Graph("isolates", 4, ()),
    Graph("disconnected", 5, ((0, 3), (2, 4))),
    Graph("star", 6, tuple((0, v) for v in range(1, 6))),
    Graph("complete", 5, tuple(combinations(range(5), 2))),
    load_graph(TOY / "cycle6.json"), load_graph(TOY / "path5.json"),
    Graph("eight", 8, ((0, 7), (2, 4), (1, 5))),
], ids=lambda graph: graph.name)
@pytest.mark.parametrize("encoding", ["pairwise", "order"])
def test_all_thresholds_against_brute_force(graph, encoding):
    best = optimum(graph)
    for k in range(-1, graph.n // 2 + 1):
        result = decide(graph, encoding, k, 10)
        assert result.status == ("SAT" if best <= k else "UNSAT")
        if best <= k:
            value = bandwidth(graph, result.labels)
            assert value <= k and validate_solution(graph, result.labels, value)
