"""Tiny-instance reference oracle for future solver checks."""

from cbmp.graph import Graph


def optimum(graph: Graph) -> int:
    """Return the exact minimum bandwidth by enumerating vertex labelings."""
    raise NotImplementedError
