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
    literals = []
    if i > 0:
        literals.append(threshold(v, i - 1, n))
    if i < n - 1:
        literals.append(-threshold(v, i, n))
    return literals


def build(graph: Graph, k: int, *, deadline: float | None = None) -> tuple[list[list[int]], OrderMetadata]:
    """Monotone chains select one position. Forbid collisions and distant edge pairs."""
    n = graph.n
    if deadline is not None and perf_counter() >= deadline:
        raise TimeoutError("CNF build deadline reached")
    var_map = {(v, t): threshold(v, t, n) for v in graph.vertices for t in range(n - 1)}
    metadata: OrderMetadata = {"n": n, "var_map": var_map}
    if k < 0:
        return [[]], metadata
    clauses = [
        [-var_map[v, t], var_map[v, t + 1]]
        for v in graph.vertices for t in range(n - 2)
    ]
    for u, v in combinations(graph.vertices, 2):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError("CNF build deadline reached")
        for i in range(n):
            clauses.append(different_from(u, i, n) + different_from(v, i, n))
    if k < n // 2:
        for u, v in graph.edges:
            for i in range(n):
                if deadline is not None and perf_counter() >= deadline:
                    raise TimeoutError("CNF build deadline reached")
                for j in range(n):
                    if cyclic_distance(i, j, n) > k:
                        clauses.append(different_from(u, i, n) + different_from(v, j, n))
    return clauses, metadata


def decode(model: Sequence[int], metadata: OrderMetadata | dict[str, int]) -> list[int]:
    """Return the first true threshold in each chain, or n-1 for an all-false chain."""
    n = metadata["n"]
    positive = {lit for lit in model if lit > 0}
    var_map = metadata.get("var_map")
    if var_map is None:  # Earlier build() results stored only n.
        var_map = {(v, t): threshold(v, t, n) for v in range(n) for t in range(n - 1)}
    return [next((t for t in range(n - 1) if var_map[v, t] in positive), n - 1)
            for v in range(n)]
