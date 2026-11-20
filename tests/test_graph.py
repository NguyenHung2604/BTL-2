import json
from pathlib import Path

from cbmp.graph import load_graph


def test_isolated_vertex_is_retained(tmp_path):
    path = tmp_path / "isolated.json"
    path.write_text(json.dumps({"name": "isolated", "n": 3, "edges": [[0, 1]]}))
    graph = load_graph(path)
    assert list(graph.vertices) == [0, 1, 2]
    assert graph.edges == ((0, 1),)


def test_path5_edges():
    graph = load_graph(Path(__file__).resolve().parents[1] / "data/toy/path5.json")
    assert graph.n == 5
    assert graph.edges == ((0, 1), (1, 2), (2, 3), (3, 4))
