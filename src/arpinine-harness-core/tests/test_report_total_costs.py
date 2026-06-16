from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "report_total_costs.py"


class ReportTotalCostsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        self.obs_history = self.repo / ".specify" / "observations" / "001-demo" / "history" / "session-a"
        self.harness_index = self.repo / ".specify" / "harness-usage" / "index.jsonl"
        self.obs_history.mkdir(parents=True)
        self.harness_index.parent.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_runtime(self, run_id: str, record: dict) -> None:
        (self.obs_history / f"{run_id}.json").write_text(json.dumps(record), encoding="utf-8")

    def _write_harness(self, run_id: str, record: dict) -> None:
        with self.harness_index.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"run_id": run_id, **record}) + "\n")

    def _run(self, *args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--json", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_combines_runtime_and_harness_subtotals(self) -> None:
        self._write_runtime("runtime-1", {"model_name": "claude-opus-4-8", "token_count_input": 100, "token_count_output": 40, "cost_usd": 1.50})
        self._write_harness("harness-1", {"spec_slug": "001-demo", "command": "at-plan", "host": "codex", "model_name": "gpt-5", "token_count_input": 50, "token_count_output": 10, "cost_usd": 0.50})

        report = self._run("--slug", "001-demo")

        self.assertAlmostEqual(report["product_runtime"]["total_cost_usd"], 1.50, places=4)
        self.assertAlmostEqual(report["harness_delivery"]["total_cost_usd"], 0.50, places=4)
        self.assertAlmostEqual(report["combined_total_cost_usd"], 2.00, places=4)
        self.assertEqual(report["combined_total_tokens"], 200)


if __name__ == "__main__":
    unittest.main()
