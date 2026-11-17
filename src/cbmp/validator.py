
"""Independent solution validator for CBMP."""

from typing import Iterable, Optional, Sequence, Tuple

from .objective import compute_bandwidth


Edge = Tuple[int, int]


def validate_solution(
    n: int,
    edges: Iterable[Edge],
    labeling: Sequence[int],
    claimed_bandwidth: Optional[int] = None,
) -> int:
    """
    Validate a CBMP labeling and return its independently computed bandwidth.

    labeling[v] is the position assigned to vertex v.

    Raises:
        ValueError: if the labeling is not a valid permutation or if the
                    claimed bandwidth does not match the computed value.
        TypeError: if an input has an invalid type.
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

    if sorted(labeling) != list(range(n)):
        raise ValueError(
            "Labeling must be a permutation of positions 0, 1, ..., n-1"
        )

    # Materialize edges so the same input can be safely inspected.
    edge_list = tuple(edges)

    bandwidth = compute_bandwidth(n, edge_list, labeling)

    if claimed_bandwidth is not None:
        if (
            not isinstance(claimed_bandwidth, int)
            or isinstance(claimed_bandwidth, bool)
        ):
            raise TypeError("claimed_bandwidth must be an integer")

        if claimed_bandwidth < 0:
            raise ValueError("claimed_bandwidth must be non-negative")

        if claimed_bandwidth != bandwidth:
            raise ValueError(
                f"Claimed bandwidth is {claimed_bandwidth}, "
                f"but computed bandwidth is {bandwidth}"
            )

    return bandwidth
