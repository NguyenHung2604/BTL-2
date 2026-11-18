"""order SAT encoding for the CBMP decision problem."""

from collections.abc import Sequence
from typing import Any

from ..graph import Graph


def build(graph: Graph, k: int) -> tuple[list[list[int]], dict[str, Any]]:
    """Return signed-integer CNF clauses for bandwidth <= k and decoding metadata."""
    raise NotImplementedError


def decode(model: Sequence[int], metadata: dict[str, Any]) -> list[int]:
    """Map a satisfying signed-literal model and build metadata to positions labels[v]."""
    raise NotImplementedError
