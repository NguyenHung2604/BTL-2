"""Pure threshold encoding. Positive y[v,t] means labels[v] <= t."""

from collections.abc import Sequence
from itertools import combinations

from ..graph import Graph
from ..objective import cyclic_distance


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


def build(graph: Graph, k: int) -> tuple[list[list[int]], dict[str, int]]:
    """Monotone chains select one position. Forbid collisions and distant edge pairs."""
    n = graph.n
    clauses = [
        [-threshold(v, t, n), threshold(v, t + 1, n)]
        for v in graph.vertices for t in range(n - 2)
    ]
    for u, v in combinations(graph.vertices, 2):
        for i in range(n):
            clauses.append(different_from(u, i, n) + different_from(v, i, n))
    for u, v in graph.edges:
        for i in range(n):
            for j in range(n):
                if cyclic_distance(i, j, n) > k:
                    clauses.append(different_from(u, i, n) + different_from(v, j, n))
    if k < 0:
        clauses.append([])
    return clauses, {"n": n}


def decode(model: Sequence[int], metadata: dict[str, int]) -> list[int]:
    """Return the first true threshold in each chain, or n-1 for an all-false chain."""
    n = metadata["n"]
    positive = {lit for lit in model if lit > 0}
    return [next((t for t in range(n - 1) if threshold(v, t, n) in positive), n - 1)
            for v in range(n)]
