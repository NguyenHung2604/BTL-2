"""sat solver adapter."""

from typing import Literal

from ..graph import Graph
from ..result import SolveResult


def solve(graph: Graph, encoding: Literal["pairwise", "order"], time_limit_seconds: float) -> SolveResult:
    """Optimize graph under one wall-clock budget and return bounds and any incumbent.

    Select the requested encoding. All builds and decision calls share this budget.
    """
    raise NotImplementedError
