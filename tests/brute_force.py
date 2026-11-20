
"""Brute-force reference solver for small CBMP instances.

Intended for validation on small graphs (typically n <= 8).
"""

from itertools import permutations
from typing import Iterable, Optional, Sequence, Tuple

from src.cbmp.objective import compute_bandwidth
from src.cbmp.graph import Graph
from src.cbmp.objective import bandwidth


Edge = Tuple[int, int]


def optimum(graph: Graph) -> int:
    """Main-branch Graph API."""
    if graph.n > 8:
        raise ValueError("Brute-force oracle supports n <= 8")
    return min(
        bandwidth(graph, labeling)
        for labeling in permutations(graph.vertices)
    )


def brute_force_optimum(
    n: int,
    edges: Iterable[Edge],
) -> Tuple[int, Tuple[int, ...]]:
    """
    Return the exact optimum and one optimal labeling.

    labeling[v] is the position assigned to vertex v.
    All n! permutations are examined.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be positive")
    if n > 8:
        raise ValueError("Brute force is restricted to n <= 8")

    edge_list = tuple(edges)

    best_bandwidth: Optional[int] = None
    best_labeling: Optional[Tuple[int, ...]] = None

    for labeling in permutations(range(n)):
        bandwidth = compute_bandwidth(n, edge_list, labeling)

        if best_bandwidth is None or bandwidth < best_bandwidth:
            best_bandwidth = bandwidth
            best_labeling = labeling

            # Zero is a global lower bound, so no better solution exists.
            if best_bandwidth == 0:
                break

    assert best_bandwidth is not None
    assert best_labeling is not None

    return best_bandwidth, best_labeling


def is_feasible_at_threshold(
    n: int,
    edges: Iterable[Edge],
    threshold: int,
) -> bool:
    """
    Decide whether a labeling with bandwidth <= threshold exists.

    This is the brute-force reference for the decision problem F(K).
    """
    if not isinstance(threshold, int) or isinstance(threshold, bool):
        raise TypeError("threshold must be an integer")

    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be positive")
    if n > 8:
        raise ValueError("Brute force is restricted to n <= 8")

    edge_list = tuple(edges)

    # Validate the graph before applying the maximum-threshold shortcut.
    compute_bandwidth(n, edge_list, tuple(range(n)))

    if threshold >= n // 2:
        return True

    for labeling in permutations(range(n)):
        if compute_bandwidth(n, edge_list, labeling) <= threshold:
            return True

    return False
