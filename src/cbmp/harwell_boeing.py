"""Normalize a matrix from the Harwell–Boeing collection in Matrix Market format."""

import gzip
from pathlib import Path

from scipy.io import mmread
from scipy.sparse import coo_matrix

from .graph import Graph


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
