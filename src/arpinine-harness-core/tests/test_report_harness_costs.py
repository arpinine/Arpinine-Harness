from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "report_harness_costs.py"


class ReportHarnessCostsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        self.index = self.repo / ".specify" / "harness-usage" / "index.jsonl"
        self.index.parent.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_run(self, run_id: str, record: dict) -> None:
        with self.index.open("a", encoding="utf-8") as handle:
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

    def test_groups_by_model_command_and_host(self) -> None:
        self._write_run("r1", {"spec_slug": "001-demo", "command": "at-plan", "host": "codex", "model_name": "gpt-5", "token_count_input": 100, "token_count_output": 50, "cost_usd": 1.25})
        self._write_run("r2", {"spec_slug": "001-demo", "command": "at-implement", "host": "codex", "model_name": "gpt-5", "token_count_input": 60, "token_count_output": 20, "cost_usd": 0.75})
        self._write_run("r3", {"spec_slug": "002-demo", "command": "at-review", "host": "claude", "model_name": "claude-opus-4-8", "token_count_input": 40, "token_count_output": 10, "cost_usd": 0.50})

        report = self._run()

        self.assertEqual(report["measured_runs"], 3)
        self.assertAlmostEqual(report["total_cost_usd"], 2.50, places=4)
        self.assertEqual(report["commands"][0]["label"], "at-plan")
        labels = {item["label"] for item in report["hosts"]}
        self.assertIn("codex", labels)
        self.assertIn("claude", labels)

    def test_spec_filter_limits_scope(self) -> None:
        self._write_run("r1", {"spec_slug": "001-demo", "command": "at-plan", "host": "codex", "model_name": "gpt-5", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.10})
        self._write_run("r2", {"spec_slug": "002-demo", "command": "at-review", "host": "claude", "model_name": "claude-opus-4-8", "token_count_input": 20, "token_count_output": 10, "cost_usd": 0.20})

        report = self._run("--slug", "001-demo")

        self.assertEqual(report["scope"], ["001-demo"])
        self.assertAlmostEqual(report["total_cost_usd"], 0.10, places=4)
        self.assertEqual(report["measured_runs"], 1)

    def test_partial_runs_are_excluded(self) -> None:
        self._write_run("r1", {"spec_slug": "001-demo", "command": "at-plan", "host": "codex", "model_name": "gpt-5", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.10})
        self._write_run("r2", {"spec_slug": "001-demo", "command": "at-review", "host": "codex", "model_name": "gpt-5", "token_count_input": 999})
        self._write_run("r3", {"spec_slug": "001-demo", "command": "at-review", "host": "codex", "model_name": "gpt-5", "cost_usd": 999})

        report = self._run("--slug", "001-demo")

        self.assertEqual(report["measured_runs"], 1)
        self.assertEqual(report["incomplete_runs"], 2)
        self.assertAlmostEqual(report["total_cost_usd"], 0.10, places=4)

    def test_same_run_id_rows_in_index_are_both_counted(self) -> None:
        self._write_run("same-second-edit", {"spec_slug": "001-demo", "command": "write", "host": "codex", "model_name": "gpt-5", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.10})
        self._write_run("same-second-edit", {"spec_slug": "001-demo", "command": "write", "host": "codex", "model_name": "gpt-5", "token_count_input": 20, "token_count_output": 10, "cost_usd": 0.20})

        report = self._run("--slug", "001-demo")

        self.assertEqual(report["measured_runs"], 2)
        self.assertAlmostEqual(report["total_cost_usd"], 0.30, places=4)
        self.assertEqual(report["total_tokens"], 45)


if __name__ == "__main__":
    unittest.main()
