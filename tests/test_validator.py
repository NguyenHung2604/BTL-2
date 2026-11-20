from cbmp.graph import Graph
from cbmp.result import SolveResult
from cbmp.validator import validate_solution


def test_reject_duplicate_labels():
    assert not validate_solution(Graph("edge", 2, ((0, 1),)), [0, 0], 0)


def test_vertex_to_position_convention():
    graph = Graph("edge", 5, ((0, 1),))
    labels = [1, 3, 4, 0, 2]
    assert validate_solution(graph, labels, 2)
    assert not validate_solution(graph, labels, 1)


def test_result_without_incumbent():
    result = SolveResult("path5", "sat_order", "NO_SOLUTION", "timeout", 10)
    assert result.labels is None and result.bandwidth is None
