from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "check_harness_observation.py"


class CheckHarnessObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "evals" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "observations" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "specs" / "001-demo" / "plan.md").write_text(
            textwrap.dedent(
                """
                # Plan: Demo

                ## Harness Strategy
                | Concern | Decision |
                |---------|----------|
                | Why harness is needed | multi-turn tool loop |
                | Runtime selected | OpenHarness |
                | Product abstraction boundary | `SupportAgentRuntime` |
                | Tool access model | `draft_support_reply` only |
                | Memory / state model | session-only; reset after each run |
                | Permission and safety model | `create_case` requires approval |
                | Swap strategy | adapter only |
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (self.repo / ".specify" / "evals" / "001-demo" / "eval-plan.md").write_text(
            textwrap.dedent(
                """
                # Evaluation Plan: Demo

                ## Runtime Contract Assertions
                - Allowed tools: [`draft_support_reply`]
                - Protected actions requiring approval: [`create_case`]
                - Memory scope invariant: session-only
                - Session reset evidence: [`session_reset`]
                - Required event types: [`model_turn_started`, `tool_requested`, `tool_executed`, `permission_check`, `memory_write`, `session_reset`]
                - Required policy assertions: approval before protected write; only allowed tools used; no persistent memory write

                ## Deterministic Replay
                - Replay required: Yes
                - Replay command: `pytest tests/replay.py`
                - Mock / fixture strategy: fake tool registry and recorded tool outputs
                - Replay fixture path: `tests/fixtures/replay`
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--slug", "001-demo", "--json"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_trace(self, events: list[dict[str, object]]) -> None:
        payload = {
            "spec": "001-demo",
            "runtime_class": "OpenHarnessAdapter",
            "scenario_id": "golden-path",
            "timestamp": "2026-05-04T12:00:00Z",
            "events": events,
        }
        (self.repo / ".specify" / "observations" / "001-demo" / "trace.json").write_text(
            json.dumps(payload) + "\n",
            encoding="utf-8",
        )

    def test_checker_passes_when_trace_matches_contract(self) -> None:
        self.write_trace(
            [
                {"type": "model_turn_started"},
                {"type": "tool_requested", "tool": "draft_support_reply"},
                {"type": "tool_executed", "tool": "draft_support_reply"},
                {"type": "permission_check", "action": "create_case", "approved": True},
                {"type": "memory_write", "scope": "session"},
                {"type": "session_reset"},
                {"type": "write_action", "action": "create_case"},
            ]
        )
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "PASS")

    def test_checker_fails_on_unexpected_tool(self) -> None:
        self.write_trace(
            [
                {"type": "model_turn_started"},
                {"type": "tool_requested", "tool": "delete_ticket"},
                {"type": "tool_executed", "tool": "delete_ticket"},
                {"type": "permission_check", "action": "create_case", "approved": True},
                {"type": "memory_write", "scope": "session"},
                {"type": "session_reset"},
                {"type": "write_action", "action": "create_case"},
            ]
        )
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertIn("unexpected tools", json.dumps(payload))

    def test_checker_fails_on_missing_session_reset_and_bad_memory_scope(self) -> None:
        self.write_trace(
            [
                {"type": "model_turn_started"},
                {"type": "tool_requested", "tool": "draft_support_reply"},
                {"type": "tool_executed", "tool": "draft_support_reply"},
                {"type": "permission_check", "action": "create_case", "approved": True},
                {"type": "memory_write", "scope": "persistent"},
                {"type": "write_action", "action": "create_case"},
            ]
        )
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        failed_names = {check["name"] for check in payload["checks"] if check["status"] == "FAIL"}
        self.assertIn("memory_scope_invariant", failed_names)
        self.assertIn("session_reset_evidence", failed_names)


if __name__ == "__main__":
    unittest.main()
