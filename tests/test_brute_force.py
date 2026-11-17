
import unittest

from brute_force import brute_force_optimum, is_feasible_at_threshold


class TestBruteForce(unittest.TestCase):
    def test_path_5(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 4)]

        optimum, labeling = brute_force_optimum(5, edges)

        self.assertEqual(optimum, 1)
        self.assertEqual(sorted(labeling), list(range(5)))

    def test_cycle_6(self):
        edges = [
            (0, 1), (1, 2), (2, 3),
            (3, 4), (4, 5), (5, 0),
        ]

        optimum, labeling = brute_force_optimum(6, edges)

        self.assertEqual(optimum, 1)
        self.assertEqual(sorted(labeling), list(range(6)))

    def test_complete_graph_5(self):
        edges = [
            (i, j)
            for i in range(5)
            for j in range(i + 1, 5)
        ]

        optimum, _ = brute_force_optimum(5, edges)

        self.assertEqual(optimum, 2)

    def test_empty_graph(self):
        optimum, _ = brute_force_optimum(5, [])

        self.assertEqual(optimum, 0)

    def test_path_threshold_zero_is_infeasible(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 4)]

        self.assertFalse(is_feasible_at_threshold(5, edges, 0))

    def test_path_threshold_one_is_feasible(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 4)]

        self.assertTrue(is_feasible_at_threshold(5, edges, 1))

    def test_threshold_at_maximum_is_always_feasible(self):
        edges = [(0, 1), (1, 2), (2, 3)]

        self.assertTrue(is_feasible_at_threshold(4, edges, 2))

    def test_reject_graph_larger_than_eight(self):
        with self.assertRaises(ValueError):
            brute_force_optimum(9, [])

    def test_reject_negative_threshold(self):
        with self.assertRaises(ValueError):
            is_feasible_at_threshold(5, [], -1)


if __name__ == "__main__":
    unittest.main()
