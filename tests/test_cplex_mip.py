
"""Tests for the CPLEX MIP adapter."""

import importlib.util
import unittest

from src.cbmp.models.mip import MIPFormulation
from src.cbmp.solvers.cplex_mip import solve_cplex
from src.cbmp.validator import validate_solution


HAS_CPLEX = importlib.util.find_spec("cplex") is not None


@unittest.skipUnless(HAS_CPLEX, "cplex is not installed")
class TestCplexMIP(unittest.TestCase):

    def solve_and_check(self, n, edges, expected_optimum):
        formulation = MIPFormulation(n, tuple(edges))

        result = solve_cplex(
            formulation,
            time_limit=30,
            threads=1,
            output_flag=False,
        )

        if result["termination_reason"] == "license_error":
            self.skipTest(
                "CPLEX license or Community Edition limit prevents this test"
            )

        self.assertEqual(
            result["status"],
            "OPTIMAL",
            msg=str(result),
        )

        self.assertEqual(result["incumbent"], expected_optimum)
        self.assertTrue(result["optimality_proven"])
        self.assertIsNotNone(result["labeling"])

        self.assertAlmostEqual(
            result["lower_bound"],
            expected_optimum,
            places=5,
        )

        actual_bandwidth = validate_solution(
            n,
            edges,
            result["labeling"],
            claimed_bandwidth=expected_optimum,
        )

        self.assertEqual(actual_bandwidth, expected_optimum)

        return result

    def test_path_5(self):
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 4)
        ]

        result = self.solve_and_check(5, edges, 1)

        self.assertEqual(result["num_variables"], 26)
        self.assertEqual(result["num_constraints"], 110)

    def test_cycle_6(self):
        edges = [
            (0, 1), (1, 2), (2, 3),
            (3, 4), (4, 5), (5, 0),
        ]

        self.solve_and_check(6, edges, 1)

    def test_complete_graph_5(self):
        edges = [
            (i, j)
            for i in range(5)
            for j in range(i + 1, 5)
        ]

        self.solve_and_check(5, edges, 2)

    def test_empty_graph(self):
        self.solve_and_check(5, [], 0)


if __name__ == "__main__":
    unittest.main()
