"""Validate candidate solutions independently of the solver."""

from collections.abc import Sequence

from .graph import Graph
from .objective import bandwidth


def validate_solution(graph: Graph, labels: Sequence[int], reported_bandwidth: int) -> bool:
    """Return whether labels[v] is a position permutation with the claimed objective."""
    return (
        len(labels) == graph.n
        and all(type(label) is int for label in labels)
        and set(labels) == set(graph.vertices)
        and type(reported_bandwidth) is int
        and bandwidth(graph, labels) == reported_bandwidth
    )
