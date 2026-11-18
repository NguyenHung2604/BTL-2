"""Read simple undirected graphs with vertices numbered from zero."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Graph:
    name: str
    n: int
    edges: tuple[tuple[int, int], ...]

    @property
    def vertices(self) -> range:
        return range(self.n)


def load_graph(path: str | Path) -> Graph:
    """Read name, n and edges, retaining isolated vertices via n."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not {"name", "n", "edges"} <= data.keys():
        raise ValueError("Expected name, n and edges")
    name, n, edges = data["name"], data["n"], data["edges"]
    if not isinstance(name, str) or type(n) is not int or n < 0 or not isinstance(edges, list):
        raise ValueError("Invalid graph name, size or edge list")
    normalized = set()
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise ValueError(f"Expected two endpoints: {edge!r}")
        if any(type(v) is not int or not 0 <= v < n for v in edge):
            raise ValueError(f"Endpoint outside vertex domain: {edge!r}")
        u, v = edge
        if u == v:
            raise ValueError(f"Self-loop in simple graph: {edge!r}")
        normalized.add((min(u, v), max(u, v)))
    return Graph(name, n, tuple(sorted(normalized)))
