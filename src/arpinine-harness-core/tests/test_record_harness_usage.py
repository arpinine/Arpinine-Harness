from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "record_harness_usage.py"


class RecordHarnessUsageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _record(self, payload: dict, env: dict[str, str]) -> dict:
        input_path = self.repo / "usage.json"
        input_path.write_text(json.dumps(payload), encoding="utf-8")
        run_env = {**os.environ, **env}
        # Ensure heuristics do not leak in from the caller's environment.
        run_env.pop("CLAUDE_PLUGIN_ROOT", None)
        if "ARPININE_HARNESS_TEAM_ID" not in env:
            run_env.pop("ARPININE_HARNESS_TEAM_ID", None)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(input_path)],
            cwd=self.repo,
            capture_output=True,
            text=True,
            env=run_env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        index = self.repo / ".specify" / "harness-usage" / "index.jsonl"
        lines = index.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        return json.loads(lines[0])

    def test_missing_host_defaults_to_team_id(self) -> None:
        record = self._record(
            {"command": "at-plan", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.1},
            env={"ARPININE_HARNESS_TEAM_ID": "team-green"},
        )
        self.assertEqual(record["host"], "team-green")

    def test_missing_host_without_env_is_unknown(self) -> None:
        record = self._record(
            {"command": "at-plan", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.1},
            env={},
        )
        self.assertEqual(record["host"], "unknown-host")

    def test_explicit_host_is_preserved(self) -> None:
        record = self._record(
            {"command": "at-plan", "host": "codex", "token_count_input": 10, "token_count_output": 5, "cost_usd": 0.1},
            env={"ARPININE_HARNESS_TEAM_ID": "team-green"},
        )
        self.assertEqual(record["host"], "codex")


if __name__ == "__main__":
    unittest.main()
