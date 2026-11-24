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


def _build_diff_table(n: int) -> list[list[list[int]]]:
    return [[different_from(v, i, n) for i in range(n)] for v in range(n)]


def _forbidden_pairs(n: int, k: int) -> list[tuple[int, int]]:
    return [
        (i, j)
        for i in range(n)
        for j in range(n)
        if cyclic_distance(i, j, n) > k
    ]


def build(graph: Graph, k: int, *, deadline: float | None = None) -> tuple[list[list[int]], OrderMetadata]:
    """Monotone chains select one position. Forbid collisions and distant edge pairs."""
    n = graph.n
    if deadline is not None and perf_counter() >= deadline:
        raise TimeoutError("CNF build deadline reached")

    var_map = {(v, t): threshold(v, t, n) for v in graph.vertices for t in range(n - 1)}
    metadata: OrderMetadata = {"n": n, "var_map": var_map}
    if k < 0:
        return [[]], metadata

    clauses: list[list[int]] = [
        [-var_map[v, t], var_map[v, t + 1]]
        for v in graph.vertices
        for t in range(n - 2)
    ]

    if n < 2:
        return clauses, metadata

    diff_table = _build_diff_table(n)

    # Forbid two vertices occupying the same position i.
    collision_clauses: list[list[int]] = []
    append_collision = collision_clauses.append
    for idx, (u, v) in enumerate(combinations(graph.vertices, 2)):
        if deadline is not None and (idx & 255) == 0 and perf_counter() >= deadline:
            raise TimeoutError("CNF build deadline reached")
        diff_u = diff_table[u]
        diff_v = diff_table[v]
        for i in range(n):
            append_collision(diff_u[i] + diff_v[i])
    clauses.extend(collision_clauses)
    del collision_clauses

    # Forbid edge endpoints placed at positions exceeding cyclic distance k.
    if k < n // 2 and graph.edges:
        bad_pairs = _forbidden_pairs(n, k)
        if bad_pairs:
            edge_clauses: list[list[int]] = []
            append_edge = edge_clauses.append
            for idx, (u, v) in enumerate(graph.edges):
                if deadline is not None and (idx & 63) == 0 and perf_counter() >= deadline:
                    raise TimeoutError("CNF build deadline reached")
                diff_u = diff_table[u]
                diff_v = diff_table[v]
                for i, j in bad_pairs:
                    append_edge(diff_u[i] + diff_v[j])
            clauses.extend(edge_clauses)

    return clauses, metadata


def decode(model: Sequence[int], metadata: OrderMetadata | dict[str, int]) -> list[int]:
    """Return the first true threshold in each chain, or n-1 for an all-false chain."""
    n = metadata["n"]
    positive = {lit for lit in model if lit > 0}
    var_map = metadata.get("var_map")
    if var_map is None:
        var_map = {(v, t): threshold(v, t, n) for v in range(n) for t in range(n - 1)}
    return [
        next((t for t in range(n - 1) if var_map[v, t] in positive), n - 1)
        for v in range(n)
    ]