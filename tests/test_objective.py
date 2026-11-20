import unittest

from cbmp.objective import cyclic_distance, compute_bandwidth


class TestCyclicDistance(unittest.TestCase):
    def test_adjacent_positions(self):
        self.assertEqual(cyclic_distance(0, 1, 6), 1)

    def test_wrap_around_distance(self):
        self.assertEqual(cyclic_distance(0, 5, 6), 1)

    def test_opposite_positions_even_cycle(self):
        self.assertEqual(cyclic_distance(0, 3, 6), 3)

    def test_max_distance_odd_cycle(self):
        self.assertEqual(cyclic_distance(0, 2, 5), 2)

    def test_same_position(self):
        self.assertEqual(cyclic_distance(2, 2, 5), 0)

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            cyclic_distance(0, 0, 0)

    def test_invalid_position(self):
        with self.assertRaises(ValueError):
            cyclic_distance(0, 5, 5)


class TestComputeBandwidth(unittest.TestCase):
    def test_path_graph(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
        labeling = [0, 1, 2, 3, 4]

        self.assertEqual(compute_bandwidth(5, edges, labeling), 1)

    def test_cycle_graph(self):
        edges = [
            (0, 1), (1, 2), (2, 3),
            (3, 4), (4, 5), (5, 0),
        ]
        labeling = [0, 1, 2, 3, 4, 5]

        self.assertEqual(compute_bandwidth(6, edges, labeling), 1)

    def test_empty_graph(self):
        self.assertEqual(compute_bandwidth(5, [], [0, 1, 2, 3, 4]), 0)

    def test_wrap_around_edge(self):
        edges = [(0, 1)]
        labeling = [0, 5, 1, 2, 3, 4]

        self.assertEqual(compute_bandwidth(6, edges, labeling), 1)

    def test_invalid_labeling_length(self):
        with self.assertRaises(ValueError):
            compute_bandwidth(3, [], [0, 1])

    def test_invalid_edge(self):
        with self.assertRaises(ValueError):
            compute_bandwidth(3, [(0, 3)], [0, 1, 2])


class TestObjectiveEdgeCases(unittest.TestCase):
    def test_reject_non_integer_n(self):
        for n in (3.0, "3", True):
            with self.subTest(n=n):
                with self.assertRaises(TypeError):
                    cyclic_distance(0, 1, n)

    def test_reject_negative_n(self):
        with self.assertRaises(ValueError):
            cyclic_distance(0, 1, -3)

    def test_reject_non_integer_positions(self):
        for i, j in ((0.5, 1), (0, 1.5), (False, 1)):
            with self.subTest(i=i, j=j):
                with self.assertRaises(TypeError):
                    cyclic_distance(i, j, 5)

    def test_reject_non_integer_labeling_position(self):
        for labeling in ([0, 1.0, 2], [0, True, 2]):
            with self.subTest(labeling=labeling):
                with self.assertRaises(TypeError):
                    compute_bandwidth(3, [], labeling)

    def test_reject_out_of_range_labeling_position(self):
        with self.assertRaises(ValueError):
            compute_bandwidth(3, [], [0, 1, 3])

    def test_reject_negative_vertex_id(self):
        with self.assertRaises(ValueError):
            compute_bandwidth(3, [(-1, 1)], [0, 1, 2])

    def test_reject_non_integer_vertex_id(self):
        with self.assertRaises(TypeError):
            compute_bandwidth(3, [(0.5, 1)], [0, 1, 2])

    def test_reject_boolean_vertex_id(self):
        with self.assertRaises(TypeError):
            compute_bandwidth(3, [(False, 1)], [0, 1, 2])

    def test_reject_malformed_edge(self):
        with self.assertRaises(ValueError):
            compute_bandwidth(3, [(0,)], [0, 1, 2])

        with self.assertRaises(ValueError):
            compute_bandwidth(3, [(0, 1, 2)], [0, 1, 2])

    def test_duplicate_edges_do_not_change_bandwidth(self):
        edges = [(0, 1), (0, 1), (1, 2)]
        labeling = [0, 1, 2]

        self.assertEqual(compute_bandwidth(3, edges, labeling), 1)

    def test_accept_edge_generator(self):
        edges = ((u, v) for u, v in [(0, 1), (1, 2)])

        self.assertEqual(
            compute_bandwidth(3, edges, [0, 1, 2]),
            1,
        )


from pathlib import Path

from cbmp.graph import Graph, load_graph
from cbmp.objective import bandwidth, cyclic_distance


def test_wraparound_distance():
    assert cyclic_distance(0, 5, 6) == 1


def test_cycle6_natural_labels():
    graph = load_graph(Path(__file__).resolve().parents[1] / "data/toy/cycle6.json")
    assert graph.n == 6 and len(graph.edges) == 6 and (0, 5) in graph.edges
    assert bandwidth(graph, range(6)) == 1


def test_edgeless_bandwidth():
    assert bandwidth(Graph("empty", 3, ()), range(3)) == 0
