"""Validate candidate solutions independently of the solver."""

from collections.abc import Sequence

from .graph import Graph
from .objective import bandwidth


def validate_solution(
    graph: Graph | int,
    labels: Sequence[int],
    reported_bandwidth: int,
    claimed_bandwidth: int | None = None,
) -> bool:
    """Return whether labels[v] is a position permutation with the claimed objective."""
    if isinstance(graph, int):
        n = graph
        edges = labels
        labeling = reported_bandwidth
        claimed = claimed_bandwidth
        graph = Graph("compat", n, tuple(edges))
        labels = labeling
        reported_bandwidth = claimed if claimed is not None else bandwidth(graph, labels)
    return (
        len(labels) == graph.n
        and all(type(label) is int for label in labels)
        and set(labels) == set(graph.vertices)
        and type(reported_bandwidth) is int
        and bandwidth(graph, labels) == reported_bandwidth
    )
