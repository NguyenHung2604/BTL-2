import csv
import hashlib
from pathlib import Path

import pytest

from cbmp.graph import load_graph
from cbmp.harwell_boeing import read_matrix

ROOT = Path(__file__).resolve().parents[1]


def test_real_matrix_matches_manifest():
    with (ROOT / "data/manifest.csv").open(encoding="utf-8") as stream:
        row = next(r for r in csv.DictReader(stream) if r["instance"] == "bcsstk01")
    path = ROOT / row["graph_path"]
    graph = read_matrix(ROOT / row["raw_path"])
    assert load_graph(path) == graph
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["graph_sha256"]
    degrees = [0] * graph.n
    for u, v in graph.edges:
        degrees[u] += 1
        degrees[v] += 1
    assert (graph.n, len(graph.edges), max(degrees)) == (48, 176, 11)
    assert tuple(map(int, (row["n"], row["m"], row["max_degree"]))) == (graph.n, len(graph.edges), max(degrees))


def test_asymmetry_cancellation_and_isolate(tmp_path):
    path = tmp_path / "sample.mtx"
    path.write_text("%%MatrixMarket matrix coordinate real general\n4 4 6\n"
                    "1 2 3\n1 2 -3\n2 1 4\n3 2 5\n4 4 1\n3 4 0\n")
    assert read_matrix(path).edges == ((0, 1), (1, 2))
    assert read_matrix(path).n == 4
    path.write_text("%%MatrixMarket matrix coordinate real general\n2 3 1\n1 2 1\n")
    with pytest.raises(ValueError, match="square"):
        read_matrix(path)
