"""Assignment ILP shared by MIP backends.

Minimize integer B in [0, floor(n/2)]. Binary x[v,i] has row and column
sums one. For an edge u,v placed at i,j the corresponding row enforces
B >= d(i,j) * (x[u,i] + x[v,j] - 1). Other placements relax that row.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Iterable, Iterator as TypingIterator, Tuple

from ..graph import Graph
from ..objective import cyclic_distance


def build(graph: Graph) -> Iterator[tuple[int, int, int, int, int]]:
    """Yield (u,i,v,j,d) for each nontrivial edge row of the assignment ILP."""
    for u, v in graph.edges:
        for i in graph.vertices:
            for j in graph.vertices:
                if i != j:
                    yield u, i, v, j, cyclic_distance(i, j, graph.n)


DistanceConstraint = Tuple[int, int, int, int, int]


@dataclass(frozen=True)
class MIPFormulation:
    """Compatibility view for the branch's existing MIP adapters.

    New code should use Graph and models.mip.build(). The adapter compatibility
    layer keeps solve_cplex and solve_gurobi source-compatible during the merge.
    """

    n: int
    edges: Tuple[Tuple[int, int], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.n, int) or isinstance(self.n, bool) or self.n <= 0:
            raise ValueError("A graph must have at least one vertex")
        normalized = set()
        for edge in self.edges:
            if len(edge) != 2:
                raise ValueError("Each edge must contain two vertices")
            u, v = edge
            if not (0 <= u < self.n and 0 <= v < self.n) or u == v:
                raise ValueError(f"Invalid edge: {edge}")
            normalized.add((min(u, v), max(u, v)))
        object.__setattr__(self, "edges", tuple(sorted(normalized)))

    @property
    def num_binary_variables(self) -> int:
        return self.n * self.n

    @property
    def max_bandwidth(self) -> int:
        return self.n // 2

    @property
    def num_assignment_constraints(self) -> int:
        return 2 * self.n

    @property
    def num_distance_constraints(self) -> int:
        return len(self.edges) * self.n * self.n

    def iter_distance_constraints(self) -> TypingIterator[DistanceConstraint]:
        for u, v in self.edges:
            for i in range(self.n):
                for j in range(self.n):
                    yield u, v, i, j, cyclic_distance(i, j, self.n)
