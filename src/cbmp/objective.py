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


def compute_bandwidth(
    n: int,
    edges: Sequence[tuple[int, int]],
    labeling: Sequence[int],
) -> int:
    """Compatibility wrapper for the branch's existing objective callers."""
    if n <= 0:
        raise ValueError("n must be positive")
    normalized_edges = []
    for edge in edges:
        if len(edge) != 2:
            raise ValueError("Each edge must contain two vertices")
        u, v = edge
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"Invalid edge: {edge}")
        if u == v:
            raise ValueError("Self-loops are not supported")
        normalized_edges.append((min(u, v), max(u, v)))
    graph = Graph("compat", n, tuple(sorted(set(normalized_edges))))
    return bandwidth(graph, labeling)
