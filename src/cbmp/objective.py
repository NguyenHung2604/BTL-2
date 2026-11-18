"""Objective for vertex-to-position labelings."""

from collections.abc import Sequence

from .graph import Graph


def cyclic_distance(i: int, j: int, n: int) -> int:
    """Return the shorter distance between positions i and j on an n-cycle."""
    if not (0 <= i < n and 0 <= j < n):
        raise ValueError("Positions must belong to the cycle")
    delta = abs(i - j)
    return min(delta, n - delta)


def bandwidth(graph: Graph, labels: Sequence[int]) -> int:
    """Compute the largest edge distance for a valid labels[v] permutation."""
    return max(
        (cyclic_distance(labels[u], labels[v], graph.n) for u, v in graph.edges),
        default=0,
    )
