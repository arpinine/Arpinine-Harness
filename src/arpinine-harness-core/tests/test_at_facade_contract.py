from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
ROUTING_POLICY = ROOT / "src" / "arpinine-harness-core" / "routing-policy.md"
AT_COMMAND = ROOT / "src" / "arpinine-harness-core" / "commands" / "at.md"


class AtFacadeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.routing_policy = ROUTING_POLICY.read_text(encoding="utf-8")
        cls.at_command = AT_COMMAND.read_text(encoding="utf-8")

    def assertContains(self, haystack: str, needle: str) -> None:
        self.assertIn(needle, haystack, f"Expected to find {needle!r}")

    def test_at_uses_inspector_and_policy_as_dependencies(self) -> None:
        self.assertContains(self.at_command, 'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/route_at.py"')
        self.assertContains(self.at_command, "inspector contract and implementation")
        self.assertContains(self.at_command, "routing-policy.md")
        self.assertContains(self.at_command, "state-inspector.md")
        self.assertContains(
            self.at_command,
            "all hard routing gates (gates 1-4) in `routing-policy.md` always take precedence",
        )

    def test_handoff_and_return_constraints_are_stated(self) -> None:
        self.assertContains(self.at_command, "#### 4a. Handoff commands")
        self.assertContains(self.at_command, "- stop speaking as the facade for that session")
        self.assertContains(self.at_command, "#### 4b. Return commands")
        self.assertContains(
            self.at_command,
            "recommend the next step unless the return command already produced its own recommendation",
        )
        self.assertContains(
            self.at_command,
            "the read-only return commands are `/at-status` and `/at-ask`",
        )

    def test_command_classes_cover_primary_handoff_commands(self) -> None:
        for command in ("/at-map", "/at-discover", "/at-bootstrap-from-code", "/at-implement"):
            self.assertContains(self.routing_policy, f"| `{command}` |")

    def test_decision_table_covers_front_door_smoke_scenarios(self) -> None:
        expected_rows = (
            "| 3 | `governed == false` | `/at-init` | High |",
            "| 8 | Broad-goal intent, no active sessions | `/at-map` | High/Medium |",
            "| 9 | Single-feature intent, no active sessions | `/at-discover` | High/Medium |",
            "| 11 | Planning intent + `specs_without_plan` non-empty | `/at-plan` | High |",
            "| 23 | Status/next-step intent OR no strong intent match | `/at-status` | Medium/Low |",
        )
        for row in expected_rows:
            self.assertContains(self.routing_policy, row)

    def test_drift_and_eval_fallbacks_are_documented(self) -> None:
        self.assertContains(
            self.routing_policy,
            "| 17 | `specs_with_open_drift` non-empty AND intent is vague or status-oriented | `/at-status` with drift surfaced as a recommended next action | Medium |",
        )
        self.assertContains(
            self.routing_policy,
            "| 19 | Eval intent AND `spec_count > 0` AND `eval_gaps` empty | `/at-status` with explanation that all current specs already have eval plans | Medium |",
        )

    def test_no_spec_redirects_cover_late_stage_commands(self) -> None:
        expected_redirects = (
            "| 13b | Spec refinement intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |",
            "| 15b | Implementation intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |",
            "| 16b | Explicit drift/audit intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |",
            "| 18b | Eval intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |",
            "| 20b | Retrospective intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |",
            "| 22b | Observation intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |",
        )
        for row in expected_redirects:
            self.assertContains(self.routing_policy, row)


if __name__ == "__main__":
    unittest.main()
