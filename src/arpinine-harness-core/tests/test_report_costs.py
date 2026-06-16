from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "report_costs.py"


class ReportCostsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        self.history = self.repo / ".specify" / "observations" / "009-demo" / "history" / "session-a"
        self.history.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_run(self, run_id: str, record: dict) -> None:
        (self.history / f"{run_id}.json").write_text(json.dumps(record), encoding="utf-8")

    def _run(self, *args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--json", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_groups_by_model_and_totals_cost(self) -> None:
        self._write_run("r1", {"model_name": "claude-opus-4-8", "token_count_input": 100, "token_count_output": 40, "cost_usd": 1.50})
        self._write_run("r2", {"model_name": "claude-opus-4-8", "token_count_input": 60, "token_count_output": 20, "cost_usd": 0.50})
        self._write_run("r3", {"model_name": "claude-haiku-4-5", "token_count_input": 30, "token_count_output": 10, "cost_usd": 0.10})

        report = self._run()

        self.assertEqual(report["measured_runs"], 3)
        self.assertEqual(report["incomplete_runs"], 0)
        self.assertAlmostEqual(report["total_cost_usd"], 2.10, places=4)
        self.assertEqual(report["total_token_input"], 190)
        self.assertEqual(report["total_token_output"], 70)

        models = {item["model_name"]: item for item in report["models"]}
        self.assertEqual(models["claude-opus-4-8"]["runs"], 2)
        self.assertAlmostEqual(models["claude-opus-4-8"]["cost_usd"], 2.00, places=4)
        # Highest-cost model is reported first.
        self.assertEqual(report["models"][0]["model_name"], "claude-opus-4-8")

    def test_runs_without_telemetry_are_excluded_not_synthesized(self) -> None:
        self._write_run("r1", {"model_name": "claude-opus-4-8", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.25})
        self._write_run("r2", {"model_name": "claude-opus-4-8", "final_outcome": "PASS"})  # no telemetry

        report = self._run()

        self.assertEqual(report["measured_runs"], 1)
        self.assertEqual(report["incomplete_runs"], 1)
        self.assertAlmostEqual(report["total_cost_usd"], 0.25, places=4)

    def test_tokens_without_cost_are_excluded_not_undercounted(self) -> None:
        self._write_run("r1", {"model_name": "claude-opus-4-8", "token_count_input": 100, "token_count_output": 40, "cost_usd": 1.50})
        # Partial: tokens present but no cost_usd. Must be excluded, not rolled in with 0.0 cost.
        self._write_run("r2", {"model_name": "claude-opus-4-8", "token_count_input": 9999, "token_count_output": 9999})

        report = self._run()

        self.assertEqual(report["measured_runs"], 1)
        self.assertEqual(report["incomplete_runs"], 1)
        self.assertAlmostEqual(report["total_cost_usd"], 1.50, places=4)
        # Partial run's tokens must NOT inflate totals.
        self.assertEqual(report["total_token_input"], 100)
        self.assertEqual(report["total_token_output"], 40)

    def test_cost_without_tokens_is_excluded(self) -> None:
        self._write_run("r1", {"model_name": "m", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.25})
        self._write_run("r2", {"model_name": "m", "cost_usd": 9.99})  # cost but no tokens

        report = self._run()

        self.assertEqual(report["measured_runs"], 1)
        self.assertEqual(report["incomplete_runs"], 1)
        self.assertAlmostEqual(report["total_cost_usd"], 0.25, places=4)

    def test_unknown_model_label_when_missing(self) -> None:
        self._write_run("r1", {"token_count_input": 10, "token_count_output": 5, "cost_usd": 0.25})

        report = self._run()

        self.assertEqual(report["models"][0]["model_name"], "unknown-model")

    def test_empty_scope_reports_zero(self) -> None:
        # No runs written in this test → totals are zero, not synthesized.
        report = self._run("--slug", "009-demo")
        self.assertEqual(report["measured_runs"], 0)
        self.assertEqual(report["total_cost_usd"], 0.0)
        self.assertEqual(report["models"], [])


if __name__ == "__main__":
    unittest.main()
