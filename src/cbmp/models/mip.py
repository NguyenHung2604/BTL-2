"""Assignment ILP shared by MIP backends.

Minimize integer B in [0, floor(n/2)]. Binary x[v,i] has row and column
sums one. For an edge u,v placed at i,j the corresponding row enforces
B >= d(i,j) * (x[u,i] + x[v,j] - 1). Other placements relax that row.
"""

from collections.abc import Iterator

from ..graph import Graph
from ..objective import cyclic_distance


def build(graph: Graph) -> Iterator[tuple[int, int, int, int, int]]:
    """Yield (u,i,v,j,d) for each nontrivial edge row of the assignment ILP."""
    for u, v in graph.edges:
        for i in graph.vertices:
            for j in graph.vertices:
                if i != j:
                    yield u, i, v, j, cyclic_distance(i, j, graph.n)
