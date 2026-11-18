
import tempfile
import unittest
from pathlib import Path

from src.cbmp.harwell_boeing import read_harwell_boeing


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


if __name__ == "__main__":
    unittest.main()
