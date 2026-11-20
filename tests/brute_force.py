"""Exhaustive reference for graphs with at most eight vertices."""

from itertools import permutations

from cbmp.graph import Graph
from cbmp.objective import bandwidth


def optimum(graph: Graph) -> int:
    """Return the best objective across all vertex-to-position permutations."""
    if graph.n > 8:
        raise ValueError("Brute-force oracle supports n <= 8")
    return min(bandwidth(graph, labels) for labels in permutations(graph.vertices))
