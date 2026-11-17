
"""Objective functions for the Cyclic Bandwidth Minimization Problem."""

from typing import Iterable, Sequence, Tuple


Edge = Tuple[int, int]


def cyclic_distance(n: int, i: int, j: int) -> int:
    """Return the shortest distance between positions i and j on a cycle C_n."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be positive")

    if not isinstance(i, int) or isinstance(i, bool):
        raise TypeError("Positions must be integers")
    if not isinstance(j, int) or isinstance(j, bool):
        raise TypeError("Positions must be integers")

    if not (0 <= i < n and 0 <= j < n):
        raise ValueError("Positions must belong to range(0, n)")

    return min(abs(i - j), n - abs(i - j))


def compute_bandwidth(
    n: int,
    edges: Iterable[Edge],
    labeling: Sequence[int],
) -> int:
    """
    Compute the cyclic bandwidth of a labeling.

    labeling[v] is the position assigned to vertex v.
    The labeling is expected to contain exactly n positions in range(0, n).
    Permutation validity is checked separately by the validator.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be positive")

    if len(labeling) != n:
        raise ValueError("Labeling must contain exactly n positions")

    for position in labeling:
        if not isinstance(position, int) or isinstance(position, bool):
            raise TypeError("Every position must be an integer")
        if not (0 <= position < n):
            raise ValueError("Every position must belong to range(0, n)")

    bandwidth = 0

    for edge in edges:
        if len(edge) != 2:
            raise ValueError("Each edge must contain two vertices")

        u, v = edge

        if not isinstance(u, int) or isinstance(u, bool):
            raise TypeError("Vertex IDs must be integers")
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError("Vertex IDs must be integers")

        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"Invalid edge: {edge}")
        if u == v:
            raise ValueError("Self-loops are not supported")

        distance = cyclic_distance(n, labeling[u], labeling[v])
        bandwidth = max(bandwidth, distance)

    # An edgeless graph has bandwidth 0.
    return bandwidth
