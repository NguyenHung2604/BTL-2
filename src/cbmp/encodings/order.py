"""Pure threshold encoding. Positive y[v,t] means labels[v] <= t."""

from collections.abc import Sequence
from itertools import combinations
from time import perf_counter
from typing import TypedDict

from ..graph import Graph
from ..objective import cyclic_distance


class OrderMetadata(TypedDict):
    n: int
    var_map: dict[tuple[int, int], int]
    vertices: list[int]


def threshold(v: int, t: int, n: int) -> int:
    return 1 + v * (n - 1) + t


def different_from(v: int, i: int, n: int) -> list[int]:
    """Encode p[v] != i as p[v] <= i-1 OR p[v] > i, omitting false boundary terms."""
    literals: list[int] = []
    if i > 0:
        literals.append(threshold(v, i - 1, n))
    if i < n - 1:
        literals.append(-threshold(v, i, n))
    return literals


def create_metadata(graph: Graph) -> OrderMetadata:
    """Create variable index mapping for threshold variables y[v, t]."""
    n = graph.n
    vertices = list(graph.vertices)
    var_map = {(v, t): threshold(v, t, n) for v in vertices for t in range(n - 1)}
    return {"n": n, "var_map": var_map, "vertices": vertices}


def _build_diff_table(vertices: Sequence[int], n: int) -> dict[int, list[list[int]]]:
    return {v: [different_from(v, i, n) for i in range(n)] for v in vertices}


def build_fixed(
    graph: Graph,
    *,
    metadata: OrderMetadata | None = None,
    deadline: float | None = None,
) -> tuple[list[list[int]], OrderMetadata, dict[int, list[list[int]]]]:
    """Build clauses independent of k: monotone chains and collision avoidance."""
    n = graph.n
    if deadline is not None and perf_counter() >= deadline:
        raise TimeoutError("CNF build deadline reached")

    resolved_metadata = metadata if metadata is not None else create_metadata(graph)
    vertices = resolved_metadata.get("vertices") or list(graph.vertices)
    var_map = resolved_metadata["var_map"]

    clauses: list[list[int]] = [
        [-var_map[v, t], var_map[v, t + 1]]
        for v in vertices
        for t in range(n - 2)
    ]

    if n < 2 or len(vertices) < 2:
        return clauses, resolved_metadata, {}

    diff_table = _build_diff_table(vertices, n)
    for idx, (u, v) in enumerate(combinations(vertices, 2)):
        if deadline is not None and (idx & 255) == 0 and perf_counter() >= deadline:
            raise TimeoutError("CNF build deadline reached")
        diff_u = diff_table[u]
        diff_v = diff_table[v]
        for i in range(n):
            clauses.append(diff_u[i] + diff_v[i])

    return clauses, resolved_metadata, diff_table


def build_distance_clauses(
    graph: Graph,
    *,
    min_forbidden_dist: int,
    max_forbidden_dist: int | None = None,
    diff_table: dict[int, list[list[int]]] | None = None,
    deadline: float | None = None,
) -> list[list[int]]:
    """Forbid edge endpoints (u, v) whose cyclic distance falls in the target range."""
    n = graph.n
    vertices = list(graph.vertices)
    if not graph.edges or n < 2 or min_forbidden_dist >= n // 2:
        return []

    upper = (n // 2) if max_forbidden_dist is None else min(max_forbidden_dist, n // 2)
    if min_forbidden_dist > upper:
        return []

    table = diff_table if diff_table is not None else _build_diff_table(vertices, n)
    bad_pairs = [
        (i, j)
        for i in range(n)
        for j in range(n)
        if min_forbidden_dist <= cyclic_distance(i, j, n) <= upper
    ]
    if not bad_pairs:
        return []

    clauses: list[list[int]] = []
    for idx, (u, v) in enumerate(graph.edges):
        if deadline is not None and (idx & 63) == 0 and perf_counter() >= deadline:
            raise TimeoutError("CNF build deadline reached")
        diff_u = table[u]
        diff_v = table[v]
        for i, j in bad_pairs:
            clauses.append(diff_u[i] + diff_v[j])
    return clauses


def build(
    graph: Graph,
    k: int,
    *,
    deadline: float | None = None,
) -> tuple[list[list[int]], OrderMetadata]:
    """Monotone chains select one position. Forbid collisions and distant edge pairs."""
    n = graph.n
    if deadline is not None and perf_counter() >= deadline:
        raise TimeoutError("CNF build deadline reached")

    metadata = create_metadata(graph)
    if k < 0:
        return [[]], metadata

    fixed_clauses, metadata, diff_table = build_fixed(
        graph,
        metadata=metadata,
        deadline=deadline,
    )
    if k >= n // 2 or not graph.edges:
        return fixed_clauses, metadata

    distance_clauses = build_distance_clauses(
        graph,
        min_forbidden_dist=k + 1,
        max_forbidden_dist=n // 2,
        diff_table=diff_table,
        deadline=deadline,
    )
    return fixed_clauses + distance_clauses, metadata


def decode(model: Sequence[int], metadata: OrderMetadata | dict) -> list[int]:
    """Return the first true threshold in each chain, or n-1 for an all-false chain."""
    n = metadata["n"]
    vertices = metadata.get("vertices")
    if not vertices:
        vertices = list(range(n))
    positive = {lit for lit in model if lit > 0}
    var_map = metadata.get("var_map")
    if var_map is None:
        var_map = {(v, t): threshold(v, t, n) for v in vertices for t in range(n - 1)}
    return [
        next((t for t in range(n - 1) if var_map[v, t] in positive), n - 1)
        for v in vertices
    ]