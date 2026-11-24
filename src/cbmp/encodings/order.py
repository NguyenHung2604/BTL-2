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

    vertices = metadata["vertices"]
    var_map = metadata["var_map"]

    clauses: list[list[int]] = [
        [-var_map[v, t], var_map[v, t + 1]]
        for v in vertices
        for t in range(n - 2)
    ]

    if n < 2 or len(vertices) < 2:
        return clauses, metadata

    diff_table = {v: [different_from(v, i, n) for i in range(n)] for v in vertices}

    for idx, (u, v) in enumerate(combinations(vertices, 2)):
        if deadline is not None and (idx & 255) == 0 and perf_counter() >= deadline:
            raise TimeoutError("CNF build deadline reached")
        diff_u = diff_table[u]
        diff_v = diff_table[v]
        for i in range(n):
            clauses.append(diff_u[i] + diff_v[i])

    if k >= n // 2 or not graph.edges:
        return clauses, metadata

    bad_pairs = [
        (i, j)
        for i in range(n)
        for j in range(n)
        if cyclic_distance(i, j, n) > k
    ]
    if not bad_pairs:
        return clauses, metadata

    for idx, (u, v) in enumerate(graph.edges):
        if deadline is not None and (idx & 63) == 0 and perf_counter() >= deadline:
            raise TimeoutError("CNF build deadline reached")
        diff_u = diff_table[u]
        diff_v = diff_table[v]
        for i, j in bad_pairs:
            clauses.append(diff_u[i] + diff_v[j])

    return clauses, metadata


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