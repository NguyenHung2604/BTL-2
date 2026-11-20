"""Normalize a matrix from the Harwell–Boeing collection in Matrix Market format."""

import gzip
import hashlib
from dataclasses import dataclass
from pathlib import Path

from scipy.io import mmread
from scipy.sparse import coo_matrix

from .graph import Graph


@dataclass(frozen=True)
class HBGraph:
    """Compatibility view used by the branch's existing benchmark runner."""

    n: int
    edges: tuple[tuple[int, int], ...]
    checksum: str
    matrix_type: str

    @property
    def num_edges(self) -> int:
        return len(self.edges)


def read_matrix(path: Path) -> Graph:
    """Combine duplicate coordinates, drop numeric zeros and build a simple graph."""
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rb") as stream:
        matrix = coo_matrix(mmread(stream, spmatrix=False))
    n, columns = matrix.shape
    if n != columns:
        raise ValueError("Expected a square matrix")
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    edges = {(int(min(i, j)), int(max(i, j))) for i, j in zip(matrix.row, matrix.col) if i != j}
    name = path.name.removesuffix(".gz").removesuffix(".mtx")
    return Graph(name, n, tuple(sorted(edges)))


def read_harwell_boeing(path: str | Path) -> HBGraph:
    """Compatibility adapter for Matrix Market inputs in benchmark scripts."""
    source = Path(path)
    graph = read_matrix(source)
    normalized = "".join(f"{u},{v}\n" for u, v in graph.edges).encode("ascii")
    checksum = hashlib.sha256(f"n={graph.n}\n".encode("ascii") + normalized).hexdigest()
    return HBGraph(
        n=graph.n,
        edges=graph.edges,
        checksum=checksum,
        matrix_type="MM",
    )
