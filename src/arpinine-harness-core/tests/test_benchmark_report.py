from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "benchmark_report.py"


class BenchmarkReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        eval_dir = self.repo / ".specify" / "evals" / "001-demo" / "history"
        eval_dir.mkdir(parents=True)
        (self.repo / ".specify" / "evals" / "001-demo" / "dataset-manifest.json").write_text("{}\n", encoding="utf-8")
        (self.repo / ".specify" / "evals" / "001-demo" / "eval-plan.md").write_text(
            "\n".join(
                [
                    "# Evaluation Plan: Demo",
                    "",
                    "## Benchmark Policy",
                    "- Benchmark required: Yes",
                    "- Minimum scenario count for aggregated reporting: 3",
                    "",
                    "## Metrics And Thresholds",
                    "| Dimension | Metric | Threshold | Failure Action |",
                    "|-----------|--------|-----------|----------------|",
                    "| Task success | pass rate | >= 0.95 | block release |",
                    "| Cost / latency | latency P95 | <= 250 | optimize execution |",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_result(self, name: str, payload: dict, session_id: str | None = None) -> None:
        base = self.repo / ".specify" / "evals" / "001-demo" / "history"
        path = (base / session_id if session_id else base) / f"{name}-results.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    def run_report(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--slug", "001-demo", *args],
            cwd=self.repo,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src" / "arpinine-harness-core" / "scripts")},
            text=True,
            capture_output=True,
            check=False,
        )

    def test_aggregate_json_contains_percentiles(self) -> None:
        base = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "demo-model",
            "model_version": "2026-04",
            "scenario_set": "core",
            "passed": True,
            "result": "PASS",
        }
        self.write_result("r1", {**base, "run_id": "r1", "latency_ms": 100, "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.01})
        self.write_result("r2", {**base, "run_id": "r2", "latency_ms": 200, "token_count_input": 20, "token_count_output": 10, "cost_usd": 0.02})
        self.write_result("r3", {**base, "run_id": "r3", "latency_ms": 300, "token_count_input": 30, "token_count_output": 15, "cost_usd": 0.03})
        result = self.run_report("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["run_count"], 3)
        self.assertEqual(payload["metrics"]["latency_p50_ms"], 200.0)
        self.assertAlmostEqual(payload["metrics"]["latency_p95_ms"], 290.0)
        self.assertEqual(payload["result"], "FAIL")
        self.assertTrue(any("latency P95" in note for note in payload["threshold_notes"]))

    def test_incompatible_baseline_yields_fail(self) -> None:
        base = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "demo-model",
            "model_version": "2026-04",
            "scenario_set": "core",
            "passed": True,
            "result": "PASS",
        }
        self.write_result("r1", {**base, "run_id": "r1", "latency_ms": 100})
        self.write_result("r2", {**base, "run_id": "r2", "latency_ms": 120})
        self.write_result("r3", {**base, "run_id": "r3", "latency_ms": 140})
        baseline_path = self.repo / ".specify" / "evals" / "001-demo" / "baseline.json"
        baseline_path.write_text(
            json.dumps(
                {
                    "dataset_version": "v1.0.0",
                    "variant_id": "variant-b",
                    "source_results_path": ".specify/evals/001-demo/history/r1-results.json",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = self.run_report("--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "FAIL")
        self.assertTrue(any("incompatible baseline dimensions" in note for note in payload["baseline_notes"]))

    def test_mixed_history_dimensions_fail_closed(self) -> None:
        base = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "demo-model",
            "model_version": "2026-04",
            "scenario_set": "core",
            "result": "PASS",
        }
        self.write_result("r1", {**base, "run_id": "r1", "latency_ms": 100})
        self.write_result("r2", {**base, "run_id": "r2", "latency_ms": 120, "variant_id": "variant-b"})
        self.write_result("r3", {**base, "run_id": "r3", "latency_ms": 140})
        result = self.run_report("--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "FAIL")
        self.assertIn("variant_id", payload["mixed_dimensions"])
        self.assertTrue(any("mixes incompatible dimensions" in note for note in payload["threshold_notes"]))

    def test_threshold_pass_yields_pass(self) -> None:
        base = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "demo-model",
            "model_version": "2026-04",
            "scenario_set": "core",
            "passed": True,
            "result": "PASS",
        }
        self.write_result("r1", {**base, "run_id": "r1", "latency_ms": 100})
        self.write_result("r2", {**base, "run_id": "r2", "latency_ms": 150})
        self.write_result("r3", {**base, "run_id": "r3", "latency_ms": 200})
        result = self.run_report("--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "PASS")
        self.assertTrue(any("all configured thresholds satisfied" in note for note in payload["threshold_notes"]))

    def test_minimum_run_count_violation_fails(self) -> None:
        base = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "demo-model",
            "model_version": "2026-04",
            "scenario_set": "core",
            "passed": True,
            "result": "PASS",
        }
        self.write_result("r1", {**base, "run_id": "r1", "latency_ms": 100})
        self.write_result("r2", {**base, "run_id": "r2", "latency_ms": 120})
        result = self.run_report("--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "FAIL")
        self.assertTrue(any("minimum benchmark scenario count" in note for note in payload["threshold_notes"]))

    def test_latest_session_isolated_from_older_history(self) -> None:
        base = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "demo-model",
            "model_version": "2026-04",
            "scenario_set": "core",
            "result": "PASS",
        }
        self.write_result("old-1", {**base, "run_id": "old-1", "latency_ms": 50}, session_id="session-old")
        self.write_result("old-2", {**base, "run_id": "old-2", "latency_ms": 60}, session_id="session-old")
        self.write_result("old-3", {**base, "run_id": "old-3", "latency_ms": 70}, session_id="session-old")
        self.write_result("new-1", {**base, "run_id": "new-1", "latency_ms": 100}, session_id="session-new")
        self.write_result("new-2", {**base, "run_id": "new-2", "latency_ms": 200}, session_id="session-new")
        self.write_result("new-3", {**base, "run_id": "new-3", "latency_ms": 300}, session_id="session-new")
        (self.repo / ".specify" / "evals" / "001-demo" / "latest-benchmark-session.json").write_text(
            json.dumps({"session_id": "session-new"}) + "\n",
            encoding="utf-8",
        )
        result = self.run_report("--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["run_count"], 3)
        self.assertEqual(payload["benchmark_session_id"], "session-new")
        self.assertEqual(payload["metrics"]["latency_p50_ms"], 200.0)

    def test_explicit_session_id_overrides_latest_session(self) -> None:
        base = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "demo-model",
            "model_version": "2026-04",
            "scenario_set": "core",
            "result": "PASS",
        }
        self.write_result("old-1", {**base, "run_id": "old-1", "latency_ms": 50}, session_id="session-old")
        self.write_result("old-2", {**base, "run_id": "old-2", "latency_ms": 60}, session_id="session-old")
        self.write_result("old-3", {**base, "run_id": "old-3", "latency_ms": 70}, session_id="session-old")
        self.write_result("new-1", {**base, "run_id": "new-1", "latency_ms": 100}, session_id="session-new")
        self.write_result("new-2", {**base, "run_id": "new-2", "latency_ms": 200}, session_id="session-new")
        self.write_result("new-3", {**base, "run_id": "new-3", "latency_ms": 300}, session_id="session-new")
        (self.repo / ".specify" / "evals" / "001-demo" / "latest-benchmark-session.json").write_text(
            json.dumps({"session_id": "session-new"}) + "\n",
            encoding="utf-8",
        )
        result = self.run_report("--json", "--session-id", "session-old")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["run_count"], 3)
        self.assertEqual(payload["benchmark_session_id"], "session-old")
        self.assertEqual(payload["metrics"]["latency_p50_ms"], 60.0)


if __name__ == "__main__":
    unittest.main()
