
import unittest

from src.cbmp.validator import validate_solution


class TestValidateSolution(unittest.TestCase):
    def test_valid_path_solution(self):
        edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
        labeling = [0, 1, 2, 3, 4]

        self.assertEqual(
            validate_solution(5, edges, labeling, claimed_bandwidth=1),
            1,
        )

    def test_valid_empty_graph(self):
        self.assertEqual(
            validate_solution(4, [], [0, 1, 2, 3], claimed_bandwidth=0),
            0,
        )

    def test_reject_duplicate_positions(self):
        with self.assertRaises(ValueError):
            validate_solution(4, [], [0, 1, 1, 3])

    def test_reject_missing_position(self):
        with self.assertRaises(ValueError):
            validate_solution(4, [], [0, 1, 2, 4])

    def test_reject_wrong_labeling_length(self):
        with self.assertRaises(ValueError):
            validate_solution(4, [], [0, 1, 2])

    def test_reject_incorrect_claimed_bandwidth(self):
        edges = [(0, 1)]
        labeling = [0, 1, 2, 3]

        with self.assertRaises(ValueError):
            validate_solution(
                4,
                edges,
                labeling,
                claimed_bandwidth=2,
            )

    def test_reject_negative_claimed_bandwidth(self):
        with self.assertRaises(ValueError):
            validate_solution(
                3,
                [],
                [0, 1, 2],
                claimed_bandwidth=-1,
            )

    def test_reject_invalid_edge(self):
        with self.assertRaises(ValueError):
            validate_solution(3, [(0, 3)], [0, 1, 2])

    def test_reject_self_loop(self):
        with self.assertRaises(ValueError):
            validate_solution(3, [(0, 0)], [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
