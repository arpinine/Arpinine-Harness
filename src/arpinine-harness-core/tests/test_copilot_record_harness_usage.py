from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "implementations" / "copilot" / "scripts" / "copilot_record_harness_usage.py"


class CopilotRecordHarnessUsageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify").mkdir()

    def tearDown(self) -> None:
        os.environ.pop("ARPININE_HARNESS_TEAM_ID", None)
        self.tempdir.cleanup()

    def _run(self, payload: dict) -> pathlib.Path:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=self.repo,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        index = self.repo / ".specify" / "harness-usage" / "index.jsonl"
        self.assertTrue(index.exists())
        return index

    def test_records_complete_usage_when_payload_contains_telemetry(self) -> None:
        payload = {
            "toolName": "edit",
            "toolArgs": {"filePath": ".specify/specs/001-demo/spec.md"},
            "sessionId": "session-a",
            "model": {"name": "gpt-5", "version": "2026-06"},
            "usage": {"inputTokens": 120, "outputTokens": 30},
            "billing": {"costUsd": 0.42},
        }
        index = self._run(payload)
        row = json.loads(index.read_text(encoding="utf-8").strip())
        self.assertEqual(row["spec_slug"], "001-demo")
        self.assertEqual(row["command"], "copilot:edit")
        self.assertEqual(row["host"], "copilot")
        self.assertEqual(row["token_count_input"], 120)
        self.assertEqual(row["cost_usd"], 0.42)

    def test_records_incomplete_usage_when_telemetry_is_missing(self) -> None:
        payload = {
            "toolName": "create",
            "toolArgs": {"filePath": "README.md"},
        }
        index = self._run(payload)
        row = json.loads(index.read_text(encoding="utf-8").strip())
        self.assertEqual(row["command"], "copilot:create")
        self.assertIsNone(row["spec_slug"])
        self.assertIsNone(row["token_count_input"])
        self.assertIsNone(row["cost_usd"])

    def test_team_id_env_overrides_default_host(self) -> None:
        os.environ["ARPININE_HARNESS_TEAM_ID"] = "team-green"
        payload = {
            "toolName": "edit",
            "toolArgs": {"filePath": "README.md"},
        }
        index = self._run(payload)
        row = json.loads(index.read_text(encoding="utf-8").strip())
        self.assertEqual(row["host"], "team-green")


if __name__ == "__main__":
    unittest.main()
