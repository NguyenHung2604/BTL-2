import random

from src.cbmp.objective import compute_bandwidth

import unittest

try:
    from .brute_force import brute_force_optimum, is_feasible_at_threshold
except ImportError:
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



class TestBruteForceGraphFamilies(unittest.TestCase):
    def test_disconnected_graph_with_isolated_vertex(self):
        # A path on vertices 0, 1, 2; an edge on 3, 4;
        # and vertex 5 is isolated.
        edges = [(0, 1), (1, 2), (3, 4)]

        optimum, labeling = brute_force_optimum(6, edges)

        self.assertEqual(optimum, 1)
        self.assertEqual(sorted(labeling), list(range(6)))
        self.assertEqual(compute_bandwidth(6, edges, labeling), optimum)

    def test_star_graph(self):
        # K1,4: vertex 0 is the center.
        edges = [(0, 1), (0, 2), (0, 3), (0, 4)]

        optimum, labeling = brute_force_optimum(5, edges)

        self.assertEqual(optimum, 2)
        self.assertEqual(sorted(labeling), list(range(5)))
        self.assertEqual(compute_bandwidth(5, edges, labeling), optimum)

    def test_random_graphs_are_consistent(self):
        rng = random.Random(2026)

        graph_cases = []
        for n in (5, 6):
            for probability in (0.2, 0.5, 0.8):
                edges = [
                    (u, v)
                    for u in range(n)
                    for v in range(u + 1, n)
                    if rng.random() < probability
                ]
                graph_cases.append((n, edges))

        for n, edges in graph_cases:
            with self.subTest(n=n, edges=edges):
                optimum, labeling = brute_force_optimum(n, edges)

                # The returned labeling must achieve the reported optimum.
                self.assertEqual(
                    compute_bandwidth(n, edges, labeling),
                    optimum,
                )

                # Decision results must agree with the exact optimum.
                for threshold in range(n // 2 + 1):
                    self.assertEqual(
                        is_feasible_at_threshold(n, edges, threshold),
                        threshold >= optimum,
                    )

    def test_reject_invalid_edges_even_at_maximum_threshold(self):
        # The maximum threshold must not bypass input validation.
        with self.assertRaises(ValueError):
            is_feasible_at_threshold(4, [(0, 4)], 2)



if __name__ == "__main__":
    unittest.main()
