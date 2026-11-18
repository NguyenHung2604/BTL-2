"""cplex_mip solver adapter."""

from ..graph import Graph
from ..result import SolveResult


def solve(graph: Graph, time_limit_seconds: float) -> SolveResult:
    """Optimize graph under one wall-clock budget and return bounds and any incumbent.
    """
    raise NotImplementedError
