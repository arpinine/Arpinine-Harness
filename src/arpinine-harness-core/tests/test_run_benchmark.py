from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "run_benchmark.py"


class RunBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        eval_dir = self.repo / ".specify" / "evals" / "001-demo"
        eval_dir.mkdir(parents=True)
        (self.repo / ".specify" / "observations" / "001-demo").mkdir(parents=True)
        (eval_dir / "eval-plan.md").write_text(
            textwrap.dedent(
                """
                # Evaluation Plan: Demo

                ## Benchmark Policy
                - Benchmark required: Yes
                - Benchmark command: `python3 bench_fixture.py`
                - Dataset manifest path: `.specify/evals/001-demo/dataset-manifest.json`
                - Minimum scenario count for aggregated reporting: 3

                ## Metrics And Thresholds
                | Dimension | Metric | Threshold | Failure Action |
                |-----------|--------|-----------|----------------|
                | Task success | pass rate | >= 0.95 | block release |
                | Cost / latency | latency P95 | <= 250 | optimize execution |
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (eval_dir / "dataset-manifest.json").write_text(
            json.dumps(
                {
                    "dataset_name": "core-suite",
                    "dataset_version": "v1.0.0",
                    "scenarios": [
                        {"scenario_id": "s1", "required": True},
                        {"scenario_id": "s2", "required": True},
                        {"scenario_id": "s3", "required": True},
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (self.repo / "bench_fixture.py").write_text(
            textwrap.dedent(
                """
                import json
                import os
                import pathlib

                scenario_id = os.environ["ARPININE_HARNESS_SCENARIO_ID"]
                result_path = pathlib.Path(os.environ["ARPININE_HARNESS_RESULT_PATH"])
                observation_path = pathlib.Path(os.environ["ARPININE_HARNESS_OBSERVATION_PATH"])
                latencies = {"s1": 100, "s2": 200, "s3": 240}
                costs = {"s1": 0.01, "s2": 0.02, "s3": 0.03}
                payload = {
                    "run_id": f"{scenario_id}-run",
                    "result": "PASS",
                    "variant_id": "variant-a",
                    "model_name": "demo-model",
                    "model_version": "2026-04",
                    "latency_ms": latencies[scenario_id],
                    "token_count_input": 10,
                    "token_count_output": 5,
                    "cost_usd": costs[scenario_id],
                }
                result_path.write_text(json.dumps(payload) + "\\n", encoding="utf-8")
                observation = {
                    "run_id": f"{scenario_id}-obs",
                    "runtime_class": "fixture-runtime",
                    "latency_ms": latencies[scenario_id],
                    "token_count_input": 10,
                    "token_count_output": 5,
                    "cost_usd": costs[scenario_id],
                    "final_outcome": "PASS",
                }
                observation_path.write_text(json.dumps(observation) + "\\n", encoding="utf-8")
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_benchmark(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--slug", "001-demo", *args],
            cwd=self.repo,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src" / "arpinine-harness-core" / "scripts")},
            text=True,
            capture_output=True,
            check=False,
        )

    def test_runner_executes_required_scenarios_and_writes_aggregate(self) -> None:
        result = self.run_benchmark("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["run_count"], 3)
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["dataset_version"], "v1.0.0")
        self.assertEqual(payload["variant_id"], "variant-a")
        self.assertAlmostEqual(payload["metrics"]["latency_p95_ms"], 236.0)

        eval_root = self.repo / ".specify" / "evals" / "001-demo"
        observation_root = self.repo / ".specify" / "observations" / "001-demo"
        self.assertTrue((eval_root / "latest-results.md").exists())
        self.assertEqual(len(list((eval_root / "history").glob("*-results.json"))), 3)
        self.assertTrue((observation_root / "latest-observation.md").exists())
        self.assertEqual(len(list((observation_root / "history").glob("*.json"))), 3)

    def test_runner_rejects_non_benchmark_eval_plan(self) -> None:
        eval_plan = self.repo / ".specify" / "evals" / "001-demo" / "eval-plan.md"
        eval_plan.write_text(
            eval_plan.read_text(encoding="utf-8").replace("Benchmark required: Yes", "Benchmark required: No"),
            encoding="utf-8",
        )
        result = self.run_benchmark()
        self.assertEqual(result.returncode, 2)
        self.assertIn("benchmark mode is not enabled", result.stderr)

    def test_runner_reports_non_zero_benchmark_command_failure(self) -> None:
        fixture = self.repo / "bench_fixture.py"
        fixture.write_text("raise SystemExit(7)\n", encoding="utf-8")
        result = self.run_benchmark()
        self.assertEqual(result.returncode, 2)
        self.assertIn("benchmark command failed for scenario s1", result.stderr)

    def test_runner_reports_missing_result_json(self) -> None:
        fixture = self.repo / "bench_fixture.py"
        fixture.write_text(
            textwrap.dedent(
                """
                import os
                import pathlib

                observation_path = pathlib.Path(os.environ["ARPININE_HARNESS_OBSERVATION_PATH"])
                observation_path.write_text("{}", encoding="utf-8")
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        result = self.run_benchmark()
        self.assertEqual(result.returncode, 2)
        self.assertIn("did not produce result JSON for scenario s1", result.stderr)


if __name__ == "__main__":
    unittest.main()
