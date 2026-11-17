
import unittest

from src.cbmp.objective import cyclic_distance, compute_bandwidth


class TestCyclicDistance(unittest.TestCase):
    def test_adjacent_positions(self):
        self.assertEqual(cyclic_distance(6, 0, 1), 1)

    def test_wrap_around_distance(self):
        self.assertEqual(cyclic_distance(6, 0, 5), 1)

    def test_opposite_positions_even_cycle(self):
        self.assertEqual(cyclic_distance(6, 0, 3), 3)

    def test_max_distance_odd_cycle(self):
        self.assertEqual(cyclic_distance(5, 0, 2), 2)

    def test_same_position(self):
        self.assertEqual(cyclic_distance(5, 2, 2), 0)

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            cyclic_distance(0, 0, 0)

    def test_invalid_position(self):
        with self.assertRaises(ValueError):
            cyclic_distance(5, 0, 5)


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


if __name__ == "__main__":
    unittest.main()
