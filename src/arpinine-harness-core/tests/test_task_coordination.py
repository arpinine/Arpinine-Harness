from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "src" / "arpinine-harness-core" / "scripts"
CLAIM = SCRIPTS / "claim_task.py"
RELEASE = SCRIPTS / "release_task.py"
HOOK = SCRIPTS / "check-task-claim.sh"


class TaskCoordinationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "coordination").mkdir(parents=True)
        (self.repo / "src").mkdir()
        (self.repo / "src" / "demo.py").write_text("print('demo')\n", encoding="utf-8")
        (self.repo / ".specify" / "specs" / "001-demo" / "spec.md").write_text(
            "# Spec\n\nImplementation path: src/demo.py\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_plan(self, task_lines: list[str]) -> None:
        plan = ["# Plan: Demo", "", "## Tasks", *task_lines, ""]
        (self.repo / ".specify" / "specs" / "001-demo" / "plan.md").write_text(
            "\n".join(plan),
            encoding="utf-8",
        )

    def run_script(self, script: pathlib.Path, *args: str, env: dict[str, str] | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["python3" if script.suffix == ".py" else "bash", str(script), *args],
            cwd=self.repo,
            env=merged_env,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_team_tag_blocks_other_team_claim(self) -> None:
        self.write_plan(
            [
                "- [ ] TASK-001: Codex-only work [team: codex]",
                "- [ ] TASK-002: Claude-only work [team: claude]",
            ]
        )

        codex = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        claude = self.run_script(
            CLAIM,
            "--slug",
            "001-demo",
            "--team-id",
            "claude",
            "--instance-id",
            "claude-1",
            "--task-id",
            "TASK-001",
        )

        self.assertEqual(codex.returncode, 0, codex.stdout + codex.stderr)
        self.assertEqual(claude.returncode, 2, claude.stdout + claude.stderr)
        self.assertIn("no eligible task available", claude.stdout)

    def test_active_lease_blocks_other_team_from_shared_task(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        codex = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        claude = self.run_script(
            CLAIM,
            "--slug",
            "001-demo",
            "--team-id",
            "claude",
            "--instance-id",
            "claude-1",
            "--task-id",
            "TASK-001",
        )

        self.assertEqual(codex.returncode, 0, codex.stdout + codex.stderr)
        self.assertEqual(claude.returncode, 2, claude.stdout + claude.stderr)
        self.assertIn("no eligible task available", claude.stdout)

    def test_expired_lease_becomes_claimable(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        first = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

        registry = self.repo / ".specify" / "coordination" / "001-demo.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        payload["tasks"]["TASK-001"]["lease_until"] = "2000-01-01T00:00:00Z"
        registry.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        second = self.run_script(
            CLAIM,
            "--slug",
            "001-demo",
            "--team-id",
            "claude",
            "--instance-id",
            "claude-1",
            "--task-id",
            "TASK-001",
        )

        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        claimed = json.loads(second.stdout)
        self.assertEqual(claimed["claimed_by"], "claude:claude-1")

    def test_pre_edit_hook_requires_active_claim(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])
        payload = json.dumps({"tool_input": {"file_path": "src/demo.py"}})
        env = {"ARPININE_HARNESS_TEAM_ID": "codex", "ARPININE_HARNESS_INSTANCE_ID": "codex-1"}

        blocked = self.run_script(HOOK, env=env, input_text=payload)
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        self.assertIn("without an active task claim", blocked.stdout)

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        allowed = self.run_script(HOOK, env=env, input_text=payload)
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)

    def test_runtime_identity_auto_resolves_from_host_env(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])
        payload = json.dumps({"tool_input": {"file_path": "src/demo.py"}})
        env = {"CODEX_PLUGIN_ROOT": "/tmp/fake-codex-plugin"}

        blocked = self.run_script(HOOK, env=env, input_text=payload)
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        self.assertIn("Resolved identity: codex:", blocked.stdout)

        claim = self.run_script(CLAIM, "--slug", "001-demo", env=env)
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)
        claimed = json.loads(claim.stdout)
        self.assertTrue(claimed["claimed_by"].startswith("codex:codex-"))

        allowed = self.run_script(HOOK, env=env, input_text=payload)
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)

    def test_completed_task_preserves_claimer_history(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        release = self.run_script(
            RELEASE,
            "--slug",
            "001-demo",
            "--task-id",
            "TASK-001",
            "--team-id",
            "codex",
            "--instance-id",
            "codex-1",
            "--state",
            "completed",
        )
        self.assertEqual(release.returncode, 0, release.stdout + release.stderr)

        registry = self.repo / ".specify" / "coordination" / "001-demo.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        record = payload["tasks"]["TASK-001"]
        self.assertEqual(record["state"], "completed")
        self.assertEqual(record["team_id"], "codex")
        self.assertEqual(record["instance_id"], "codex-1")
        self.assertEqual(record["claimed_by"], "codex:codex-1")
        self.assertEqual(record["completed_by"], "codex:codex-1")
        self.assertIsNotNone(record["claimed_at"])
        self.assertIsNotNone(record["completed_at"])
        self.assertIsNone(record["lease_until"])

    def test_plan_sync_does_not_clear_completed_claim_metadata(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        release = self.run_script(
            RELEASE,
            "--slug",
            "001-demo",
            "--task-id",
            "TASK-001",
            "--team-id",
            "codex",
            "--instance-id",
            "codex-1",
            "--state",
            "completed",
        )
        self.assertEqual(release.returncode, 0, release.stdout + release.stderr)

        self.write_plan(["- [x] TASK-001: Shared work"])

        blocked = self.run_script(
            HOOK,
            env={"ARPININE_HARNESS_TEAM_ID": "claude", "ARPININE_HARNESS_INSTANCE_ID": "claude-1"},
            input_text=json.dumps({"tool_input": {"file_path": "src/demo.py"}}),
        )
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)

        registry = self.repo / ".specify" / "coordination" / "001-demo.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        record = payload["tasks"]["TASK-001"]
        self.assertEqual(record["state"], "completed")
        self.assertEqual(record["team_id"], "codex")
        self.assertEqual(record["instance_id"], "codex-1")
        self.assertEqual(record["claimed_by"], "codex:codex-1")
        self.assertEqual(record["completed_by"], "codex:codex-1")


    def test_task_removed_from_plan_while_claimed_reports_task_name(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        # Remove the task from the plan entirely.
        self.write_plan([])

        env = {"ARPININE_HARNESS_TEAM_ID": "codex", "ARPININE_HARNESS_INSTANCE_ID": "codex-1"}
        blocked = self.run_script(HOOK, env=env, input_text=json.dumps({"tool_input": {"file_path": "src/demo.py"}}))

        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        self.assertIn("TASK-001", blocked.stdout)
        self.assertIn("removed from plan.md", blocked.stdout)

    def test_team_tag_change_revokes_ineligible_claim(self) -> None:
        # Claim with no team restriction.
        self.write_plan(["- [ ] TASK-001: Shared work"])

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        # Restrict task to claude — codex claim should be revoked on next sync.
        self.write_plan(["- [ ] TASK-001: Shared work [team: claude]"])

        env = {"ARPININE_HARNESS_TEAM_ID": "codex", "ARPININE_HARNESS_INSTANCE_ID": "codex-1"}
        blocked = self.run_script(HOOK, env=env, input_text=json.dumps({"tool_input": {"file_path": "src/demo.py"}}))

        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        self.assertIn("without an active task claim", blocked.stdout)

        # claude can now claim it.
        new_claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "claude", "--instance-id", "claude-1")
        self.assertEqual(new_claim.returncode, 0, new_claim.stdout + new_claim.stderr)

        registry = self.repo / ".specify" / "coordination" / "001-demo.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        record = payload["tasks"]["TASK-001"]
        self.assertEqual(record["team_id"], "claude")
        self.assertEqual(record["claimed_by"], "claude:claude-1")

    def test_reassigned_task_cannot_be_completed_by_revoked_claimer(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        self.write_plan(["- [ ] TASK-001: Shared work [team: claude]"])

        release = self.run_script(
            RELEASE,
            "--slug",
            "001-demo",
            "--task-id",
            "TASK-001",
            "--team-id",
            "codex",
            "--instance-id",
            "codex-1",
            "--state",
            "completed",
        )
        self.assertEqual(release.returncode, 2, release.stdout + release.stderr)
        self.assertIn("assigned to claude", release.stdout)

    def test_manual_checkbox_completion_infers_completed_by(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        # Manually mark task complete in plan without using release_task.
        self.write_plan(["- [x] TASK-001: Shared work"])

        # Trigger sync via claim attempt on any other task (there is none, so it returns 2,
        # but sync runs and persists the registry).
        self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")

        registry = self.repo / ".specify" / "coordination" / "001-demo.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        record = payload["tasks"]["TASK-001"]
        self.assertEqual(record["state"], "completed")
        self.assertEqual(record["completed_by"], "codex:codex-1")
        self.assertIsNotNone(record["completed_at"])

    def test_hook_persists_manual_completion_metadata(self) -> None:
        self.write_plan(["- [ ] TASK-001: Shared work"])

        claim = self.run_script(CLAIM, "--slug", "001-demo", "--team-id", "codex", "--instance-id", "codex-1")
        self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)

        self.write_plan(["- [x] TASK-001: Shared work"])
        env = {"ARPININE_HARNESS_TEAM_ID": "claude", "ARPININE_HARNESS_INSTANCE_ID": "claude-1"}
        blocked = self.run_script(HOOK, env=env, input_text=json.dumps({"tool_input": {"file_path": "src/demo.py"}}))
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)

        registry = self.repo / ".specify" / "coordination" / "001-demo.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        record = payload["tasks"]["TASK-001"]
        self.assertEqual(record["state"], "completed")
        self.assertEqual(record["completed_by"], "codex:codex-1")
        self.assertIsNotNone(record["completed_at"])


if __name__ == "__main__":
    unittest.main()
