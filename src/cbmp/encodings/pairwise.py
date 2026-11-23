"""Direct encoding: variable 1 + v*n + i means vertex v occupies position i."""

from collections.abc import Sequence
from itertools import combinations
from time import perf_counter

from ..graph import Graph
from ..objective import cyclic_distance


def build(graph: Graph, k: int, *, deadline: float | None = None) -> tuple[list[list[int]], dict[str, int]]:
    """Encode a bijection and forbid edge placements whose cyclic distance exceeds k."""
    n = graph.n
    if deadline is not None and perf_counter() >= deadline:
        raise TimeoutError("CNF build deadline reached")
    positions = [[1 + v * n + i for i in range(n)] for v in graph.vertices]
    clauses = [row.copy() for row in positions]
    for group in (*positions, *zip(*positions)):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError("CNF build deadline reached")
        clauses.extend([-a, -b] for a, b in combinations(group, 2))
    for u, v in graph.edges:
        for i in range(n):
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("CNF build deadline reached")
            for j in range(n):
                if cyclic_distance(i, j, n) > k:
                    clauses.append([-positions[u][i], -positions[v][j]])
    if k < 0:
        clauses.append([])
    return clauses, {"n": n}


def decode(model: Sequence[int], metadata: dict[str, int]) -> list[int]:
    """Recover the unique true position in each vertex row of a satisfying model."""
    n = metadata["n"]
    positive = {lit for lit in model if lit > 0}
    return [next(i for i in range(n) if 1 + v * n + i in positive) for v in range(n)]
