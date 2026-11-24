import tempfile
import unittest
from pathlib import Path

from cbmp.harwell_boeing import read_harwell_boeing


def make_hb_sample() -> str:
    """Create a small 4x4 real sparse matrix in HB format."""
    counts = f"{3:14d}{1:14d}{1:14d}{1:14d}{0:14d}"

    pointers = [1, 3, 4, 5, 5]
    row_indices = [1, 2, 3, 2]
    values = [9.0, 1.0, 2.0, 0.0]

    pointer_line = "".join(f"{x:3d}" for x in pointers)
    index_line = "".join(f"{x:3d}" for x in row_indices)
    value_line = "".join(f"{x:20.12E}" for x in values)

    return "\n".join([
        "Small sample matrix".ljust(72) + "SAMPLE",
        counts,
        "RSA 4 4 4 0",
        "(5I3) (4I3) (4E20.12) (0)",
        pointer_line,
        index_line,
        value_line,
    ]) + "\n"


class TestHarwellBoeingReader(unittest.TestCase):

    def test_reads_graph_and_preserves_isolated_vertex(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.hb"
            path.write_text(make_hb_sample(), encoding="ascii")

            graph = read_harwell_boeing(path)

        self.assertEqual(graph.n, 4)
        self.assertEqual(graph.edges, ((0, 1), (1, 2)))
        self.assertEqual(graph.num_edges, 2)
        self.assertEqual(graph.matrix_type, "RSA")
        self.assertEqual(len(graph.checksum), 64)

    def test_checksum_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.hb"
            path.write_text(make_hb_sample(), encoding="ascii")

            first = read_harwell_boeing(path)
            second = read_harwell_boeing(path)

        self.assertEqual(first.checksum, second.checksum)

    def test_rejects_non_square_matrix(self):
        content = make_hb_sample().replace(
            "RSA 4 4 4 0",
            "RSA 4 3 4 0",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nonsquare.hb"
            path.write_text(content, encoding="ascii")

            with self.assertRaisesRegex(ValueError, "square"):
                read_harwell_boeing(path)


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


def test_reads_gzipped_harwell_boeing(tmp_path):
    import gzip

    plain = tmp_path / "sample.pua"
    compressed = tmp_path / "sample.pua.gz"
    plain.write_text(make_hb_sample().replace("RSA", "RSA"), encoding="ascii")
    with gzip.open(compressed, "wt", encoding="ascii") as stream:
        stream.write(plain.read_text(encoding="ascii"))

    assert read_harwell_boeing(compressed) == read_harwell_boeing(plain)
