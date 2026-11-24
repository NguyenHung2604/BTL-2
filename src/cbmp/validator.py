"""Independent solution validator for CBMP."""

from typing import Iterable, Optional, Sequence, Tuple

from .graph import Graph
from .manifest import graph_statistics
from .objective import compute_bandwidth


Edge = Tuple[int, int]


def validated_bandwidth(
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

    if n < 0:
        raise ValueError("n must be non-negative")

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


def certify_record(record, n, edges):
    """Keep native diagnostics alongside bounds independently certified by the graph."""
    if record.get("error_message") and "out of memory" in record["error_message"].lower():
        record["termination_reason"] = "OOM"
    labels = record.get("labeling")
    if labels is None:
        if record.get("status") in {"OPTIMAL", "FEASIBLE"}:
            raise ValueError("Solver reported a solution status without a labeling")
        return
    value = validated_bandwidth(n, edges, labels)
    claimed = record.get("incumbent")
    if claimed is not None and float(claimed) != value:
        raise ValueError(f"Solver claimed bandwidth {claimed}, validator computed {value}")
    record["incumbent"] = value
    degree_bound = (graph_statistics(n, edges)["max_degree"] + 1) // 2
    native = record.get("lower_bound")
    if native is None or native < degree_bound:
        record["solver_lower_bound"] = native
        record["lower_bound"] = degree_bound
    if record["lower_bound"] > value:
        raise ValueError("Reported lower bound exceeds validated witness")
    if record["status"] == "OPTIMAL" and (record["lower_bound"] != value or not record.get("optimality_proven")):
        raise ValueError("Optimality requires matching validated bounds")


def validate_solution(graph: Graph, labels: Sequence[int], reported_bandwidth: int) -> bool:
    """Check a claimed bandwidth, including zero for an edgeless graph."""
    if type(reported_bandwidth) is not int:
        return False
    try:
        validated_bandwidth(graph.n, graph.edges, labels, reported_bandwidth)
    except (ValueError, TypeError):
        return False
    return True
