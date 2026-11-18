"""Shared MIP formulation for CBMP."""

from ..graph import Graph


def build(graph: Graph) -> object:
    """Build the MIP formulation for graph and return it for the MIP adapters."""
    raise NotImplementedError
