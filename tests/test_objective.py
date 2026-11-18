from pathlib import Path

from cbmp.graph import Graph, load_graph
from cbmp.objective import bandwidth, cyclic_distance


def test_wraparound_distance():
    assert cyclic_distance(0, 5, 6) == 1


def test_cycle6_natural_labels():
    graph = load_graph(Path(__file__).resolve().parents[1] / "data/toy/cycle6.json")
    assert graph.n == 6 and len(graph.edges) == 6 and (0, 5) in graph.edges
    assert bandwidth(graph, range(6)) == 1


def test_edgeless_bandwidth():
    assert bandwidth(Graph("empty", 3, ()), range(3)) == 0
