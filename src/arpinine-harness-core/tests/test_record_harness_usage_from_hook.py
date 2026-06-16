from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "record_harness_usage_from_hook.py"


class RecordHarnessUsageFromHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify").mkdir()

        spec = importlib.util.spec_from_file_location("record_harness_usage_from_hook", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        self.module = module

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_builds_record_from_generic_hook_payload(self) -> None:
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": ".specify/specs/001-demo/spec.md"},
            "session_id": "session-a",
            "model": {"name": "gpt-5", "version": "2026-06"},
            "usage": {"inputTokens": 50, "outputTokens": 20},
            "billing": {"costUsd": 0.15},
        }
        os.environ["CLAUDE_PLUGIN_ROOT"] = "/tmp/plugin"
        record, session_id = self.module.build_usage_record(payload)
        self.assertEqual(session_id, "session-a")
        self.assertEqual(record["spec_slug"], "001-demo")
        self.assertEqual(record["command"], "edit")
        self.assertEqual(record["host"], "claude")
        self.assertEqual(record["token_count_input"], 50.0)
        self.assertEqual(record["cost_usd"], 0.15)

    def test_unknown_host_without_env(self) -> None:
        payload = {"tool_name": "Write", "tool_input": {"file_path": "README.md"}}
        os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
        os.environ.pop("ARPININE_HARNESS_TEAM_ID", None)
        record, _ = self.module.build_usage_record(payload)
        self.assertEqual(record["command"], "write")
        self.assertEqual(record["host"], "unknown-host")
        self.assertIsNone(record["spec_slug"])

    def test_team_id_env_overrides_host_inference(self) -> None:
        payload = {"tool_name": "Edit", "tool_input": {"file_path": "README.md"}}
        os.environ["CLAUDE_PLUGIN_ROOT"] = "/tmp/plugin"
        os.environ["ARPININE_HARNESS_TEAM_ID"] = "team-blue"
        record, _ = self.module.build_usage_record(payload)
        self.assertEqual(record["host"], "team-blue")


if __name__ == "__main__":
    unittest.main()
