"""Tests for the JSON-configured benchmark runner."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts import benchmark
from cbmp.result import read_jsonl


class TestBenchmarkRunner(unittest.TestCase):

    def test_loads_compressed_harwell_boeing_matrix(self):
        instance = benchmark._load_instance(
            {"graph_id": "jgl009", "path": "data/benchmarks/harwell_boeing/raw/jgl009.pua.gz"},
            REPO_ROOT,
        )
        self.assertEqual((instance["n"], instance["num_edges"]), (9, 32))
        self.assertEqual(instance["matrix_type"], "PUA")
        self.assertEqual(len(instance["raw_sha256"]), 64)

    def test_loads_compressed_matrix_market_file(self):
        instance = benchmark._load_instance(
            {"graph_id": "bcsstk01", "path": "data/benchmarks/harwell_boeing/raw/bcsstk01.mtx.gz"},
            REPO_ROOT,
        )
        self.assertEqual((instance["n"], instance["num_edges"]), (48, 176))
        self.assertEqual(instance["matrix_type"], "MatrixMarket")

    def test_inline_instance_is_normalized(self):
        instance = benchmark._load_instance(
            {
                "graph_id": "path3",
                "n": 3,
                "edges": [[1, 0], [2, 1], [0, 1]],
            },
            REPO_ROOT,
        )
        self.assertEqual(instance["graph_id"], "path3")
        self.assertEqual(instance["n"], 3)
        self.assertEqual(instance["edges"], ((0, 1), (1, 2)))
        self.assertEqual(instance["num_edges"], 2)
        self.assertEqual(len(instance["graph_checksum"]), 64)

    def test_dry_run_does_not_create_output(self):
        config = {
            "instances": [{"graph_id": "path3", "n": 3, "edges": [[0, 1], [1, 2]]}],
            "methods": ["fake"],
            "time_limit": 5,
            "threads": 1,
            "output": "unused.jsonl",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dry.jsonl"
            with patch.dict(benchmark.SOLVER_REGISTRY, {"fake": lambda *a, **k: {}}, clear=False):
                benchmark.run_benchmark(
                    config,
                    REPO_ROOT / "configs" / "smoke.json",
                    output_override=output,
                    dry_run=True,
                )
            self.assertFalse(output.exists())

    def test_runner_writes_result_and_resume_skips_duplicate(self):
        config = {
            "instances": [{"graph_id": "path3", "n": 3, "edges": [[0, 1], [1, 2]]}],
            "methods": ["fake"],
            "time_limit": 5,
            "threads": 1,
            "seed": 4,
            "max_constraints": 100,
            "resume": True,
        }

        def fake_solver(formulation, **kwargs):
            return {
                "method": "fake",
                "status": "OPTIMAL",
                "termination_reason": "completed",
                "incumbent": 1,
                "lower_bound": 1,
                "optimality_proven": True,
                "labeling": [0, 1, 2],
                "build_time": 0.01,
                "solve_time": 0.02,
                "total_time": 0.03,
                "num_variables": 10,
                "num_constraints": 24,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "runs.jsonl"
            with patch.dict(benchmark.SOLVER_REGISTRY, {"fake": fake_solver}, clear=False):
                benchmark.run_benchmark(
                    config,
                    REPO_ROOT / "configs" / "smoke.json",
                    output_override=output,
                )
                first = read_jsonl(output)
                self.assertEqual(len(first), 1)
                self.assertEqual(first[0]["graph_id"], "path3")
                self.assertEqual(first[0]["seed"], 4)
                self.assertGreaterEqual(first[0]["total_time"], 0.03)
                self.assertGreaterEqual(first[0]["validation_time"], 0.0)
                benchmark.run_benchmark(
                    config,
                    REPO_ROOT / "configs" / "smoke.json",
                    output_override=output,
                )
                second = read_jsonl(output)
                self.assertEqual(len(second), 1)

    def test_preflight_limit_records_error_without_calling_solver(self):
        config = {
            "instances": [{"graph_id": "large", "n": 10, "edges": [[i, j] for i in range(10) for j in range(i + 1, 10)]}],
            "methods": ["gurobi_mip"],
            "time_limit": 5,
            "threads": 1,
            "max_constraints": 10,
        }
        def should_not_run(*args, **kwargs):
            raise AssertionError("solver must not be called after preflight guard")

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "guard.jsonl"
            with patch.dict(benchmark.SOLVER_REGISTRY, {"gurobi_mip": should_not_run}, clear=False):
                benchmark.run_benchmark(
                    config,
                    REPO_ROOT / "configs" / "smoke.json",
                    output_override=output,
                )
            records = read_jsonl(output)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["termination_reason"], "error")
            self.assertEqual(records[0]["error_type"], "preflight_model_size_limit")


    def test_sat_preflight_guard_records_upper_bound_without_importing_solver(self):
        config = {
            "instances": [{"graph_id": "dense", "n": 6,
                           "edges": [[i, j] for i in range(6) for j in range(i + 1, 6)]}],
            "methods": ["sat_pairwise"], "time_limit": 5, "threads": 1,
            "max_sat_variables": 100, "max_sat_clauses": 10, "resume": False,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "sat-guard.jsonl"
            benchmark.run_benchmark(
                config, REPO_ROOT / "configs" / "smoke.json", output_override=output,
            )
            record = read_jsonl(output)[0]
        self.assertEqual(record["error_type"], "preflight_model_size_limit")
        self.assertEqual(record["termination_reason"], "error")
        self.assertGreater(record["estimated_num_clauses"], 10)

    def test_runner_rejects_invalid_solver_incumbent(self):
        config = {
            "instances": [{"graph_id": "path3", "n": 3, "edges": [[0, 1], [1, 2]]}],
            "methods": ["fake"], "time_limit": 5, "threads": 1, "resume": False,
        }

        def invalid_solver(formulation, **kwargs):
            return {
                "status": "OPTIMAL", "termination_reason": "completed",
                "incumbent": 0, "lower_bound": 0, "optimality_proven": True,
                "labeling": [0, 1, 2], "build_time": 0.01, "solve_time": 0.01,
                "total_time": 0.02,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "invalid.jsonl"
            with patch.dict(benchmark.SOLVER_REGISTRY, {"fake": invalid_solver}, clear=False):
                benchmark.run_benchmark(config, REPO_ROOT / "configs" / "smoke.json", output_override=output)
            record = read_jsonl(output)[0]
            self.assertEqual(record["status"], "NO_SOLUTION")
            self.assertEqual(record["termination_reason"], "error")
            self.assertEqual(record["error_type"], "ValueError")
            self.assertIn("validator computed", record["error_message"])


if __name__ == "__main__":
    unittest.main()
