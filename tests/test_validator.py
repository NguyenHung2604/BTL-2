import unittest

from cbmp.validator import validated_bandwidth


class TestValidateSolution(unittest.TestCase):
    def test_valid_path_solution(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
        labeling = [0, 1, 2, 3, 4]

        self.assertEqual(
            validated_bandwidth(5, edges, labeling, claimed_bandwidth=1),
            1,
        )

    def test_valid_empty_graph(self):
        self.assertEqual(
            validated_bandwidth(4, [], [0, 1, 2, 3], claimed_bandwidth=0),
            0,
        )

    def test_reject_duplicate_positions(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(4, [], [0, 1, 1, 3])

    def test_reject_missing_position(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(4, [], [0, 1, 2, 4])

    def test_reject_wrong_labeling_length(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(4, [], [0, 1, 2])

    def test_reject_incorrect_claimed_bandwidth(self):
        edges = [(0, 1)]
        labeling = [0, 1, 2, 3]

        with self.assertRaises(ValueError):
            validated_bandwidth(
                4,
                edges,
                labeling,
                claimed_bandwidth=2,
            )

    def test_reject_negative_claimed_bandwidth(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(
                3,
                [],
                [0, 1, 2],
                claimed_bandwidth=-1,
            )

    def test_reject_invalid_edge(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(3, [(0, 3)], [0, 1, 2])

    def test_reject_self_loop(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(3, [(0, 0)], [0, 1, 2])



class TestValidatorEdgeCases(unittest.TestCase):
    def test_reject_non_integer_n(self):
        for n in (3.0, "3", True):
            with self.subTest(n=n):
                with self.assertRaises(TypeError):
                    validated_bandwidth(n, [], [0, 1, 2])

    def test_reject_non_integer_labeling_position(self):
        for labeling in ([0, 1.0, 2], [0, True, 2]):
            with self.subTest(labeling=labeling):
                with self.assertRaises(TypeError):
                    validated_bandwidth(3, [], labeling)

    def test_reject_negative_position(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(3, [], [-1, 1, 2])

    def test_reject_position_out_of_range(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(3, [], [0, 1, 3])

    def test_reject_non_integer_claimed_bandwidth(self):
        for claimed in (1.5, "1", True):
            with self.subTest(claimed=claimed):
                with self.assertRaises(TypeError):
                    validated_bandwidth(
                        3, [(0, 1)], [0, 1, 2],
                        claimed_bandwidth=claimed,
                    )

    def test_accept_edge_generator(self):
        edges = ((u, v) for u, v in [(0, 1), (1, 2)])

        self.assertEqual(
            validated_bandwidth(3, edges, [0, 1, 2], 1),
            1,
        )

    def test_reject_negative_vertex_id(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(3, [(-1, 1)], [0, 1, 2])

    def test_reject_non_integer_vertex_id(self):
        with self.assertRaises(TypeError):
            validated_bandwidth(3, [(0.5, 1)], [0, 1, 2])

    def test_reject_malformed_edge(self):
        with self.assertRaises(ValueError):
            validated_bandwidth(3, [(0,)], [0, 1, 2])


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
