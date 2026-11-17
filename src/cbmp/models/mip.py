
"""Solver-independent ILP formulation for the Cyclic Bandwidth Problem."""

from dataclasses import dataclass
from typing import Iterable, Iterator, Tuple


DistanceConstraint = Tuple[int, int, int, int, int]


def cyclic_distance(n: int, i: int, j: int) -> int:
    """Return the shortest distance between positions i and j on C_n."""
    if n <= 0:
        raise ValueError("n must be positive")

    if not (0 <= i < n and 0 <= j < n):
        raise ValueError("Positions must belong to range(0, n)")

    return min(abs(i - j), n - abs(i - j))


@dataclass(frozen=True)
class MIPFormulation:
    """Mathematical specification shared by Gurobi and CPLEX."""

    n: int
    edges: Tuple[Tuple[int, int], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.n, int) or isinstance(self.n, bool):
            raise TypeError("n must be an integer")

        if self.n <= 0:
            raise ValueError("A graph must have at least one vertex")

        normalized_edges = set()

        for edge in self.edges:
            if len(edge) != 2:
                raise ValueError("Each edge must contain two vertices")

            u, v = edge

            if not isinstance(u, int) or isinstance(u, bool):
                raise TypeError("Vertex IDs must be integers")

            if not isinstance(v, int) or isinstance(v, bool):
                raise TypeError("Vertex IDs must be integers")

            if not (0 <= u < self.n and 0 <= v < self.n):
                raise ValueError(f"Invalid edge: {edge}")

            if u == v:
                raise ValueError("Self-loops are not supported")

            normalized_edges.add((min(u, v), max(u, v)))

        object.__setattr__(
            self,
            "edges",
            tuple(sorted(normalized_edges)),
        )

    @property
    def num_binary_variables(self) -> int:
        """Number of assignment variables x[v, i]."""
        return self.n * self.n

    @property
    def max_bandwidth(self) -> int:
        """Maximum possible cyclic distance."""
        return self.n // 2

    @property
    def num_assignment_constraints(self) -> int:
        """One constraint per vertex and one per position."""
        return 2 * self.n

    @property
    def num_distance_constraints(self) -> int:
        """Number of edge-position-pair constraints."""
        return len(self.edges) * self.n * self.n

    def iter_distance_constraints(
        self,
    ) -> Iterator[DistanceConstraint]:
        """
        Yield (u, v, i, j, distance) for every distance constraint.

        The corresponding ILP inequality is:

            K >= distance * (x[u, i] + x[v, j] - 1)
        """
        for u, v in self.edges:
            for i in range(self.n):
                for j in range(self.n):
                    distance = cyclic_distance(self.n, i, j)
                    yield (u, v, i, j, distance)
