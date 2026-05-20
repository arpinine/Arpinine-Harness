from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "route_at.py"


class RouteAtTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)

        spec = importlib.util.spec_from_file_location("route_at", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        self.module = module

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, relative_path: str, body: str) -> None:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")

    def run_json(self, intent: str, repo: pathlib.Path | None = None) -> dict[str, object]:
        cmd = ["python3", str(SCRIPT), "--intent", intent, "--indent", "2"]
        if repo is not None:
            cmd.extend(["--repo", str(repo)])
        result = subprocess.run(
            cmd,
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_ungoverned_repo_routes_to_init(self) -> None:
        (self.repo / ".git").mkdir()
        payload = self.run_json("set up governance", self.repo)
        self.assertEqual(payload["route"], "/at-init")
        self.assertEqual(payload["confidence"], "high")
        self.assertEqual(payload["mode"], "execute")

    def test_existing_codebase_without_governance_offers_bootstrap_alternative(self) -> None:
        (self.repo / ".git").mkdir()
        self.write("src/app.py", "print('hello')\n")
        payload = self.run_json("we already have code here", self.repo)
        self.assertEqual(payload["route"], "/at-init")
        self.assertEqual(payload["alternative"], "/at-bootstrap-from-code")
        self.assertEqual(payload["confidence"], "medium")
        self.assertTrue(payload["requires_confirmation"])

    def test_broad_goal_routes_to_map(self) -> None:
        (self.repo / ".specify").mkdir()
        payload = self.run_json("I want to build a product for remote retrospectives", self.repo)
        self.assertEqual(payload["route"], "/at-map")
        self.assertEqual(payload["command_class"], "handoff")

    def test_feature_idea_routes_to_discover(self) -> None:
        (self.repo / ".specify").mkdir()
        payload = self.run_json("I want users to be able to add auth before I write a spec", self.repo)
        self.assertEqual(payload["route"], "/at-discover")
        self.assertEqual(payload["command_class"], "handoff")

    def test_spec_missing_plan_routes_to_plan(self) -> None:
        self.write(".specify/specs/001-auth/spec.md", "# Spec\n")
        payload = self.run_json("generate a plan for this implementation", self.repo)
        self.assertEqual(payload["route"], "/at-plan")
        self.assertEqual(payload["confidence"], "high")

    def test_vague_next_step_with_open_drift_routes_to_status(self) -> None:
        self.write(".specify/specs/001-auth/spec.md", "# Spec\n")
        self.write(".specify/specs/001-auth/plan.md", "# Plan\n")
        self.write(".specify/specs/001-auth/drift-report.md", "Remaining: 2 OPEN items\n")
        payload = self.run_json("what should I do next?", self.repo)
        self.assertEqual(payload["route"], "/at-status")
        self.assertEqual(payload["alternative"], "/at-audit")
        self.assertEqual(payload["confidence"], "medium")

    def test_implementation_without_specs_redirects_earlier(self) -> None:
        (self.repo / ".specify").mkdir()
        payload = self.run_json("implement it now", self.repo)
        self.assertEqual(payload["route"], "/at-discover")
        self.assertEqual(payload["confidence"], "medium")

    def test_explicit_init_is_honored_when_no_hard_gate_blocks_it(self) -> None:
        self.write(".specify/specs/001-auth/spec.md", "# Spec\n")
        payload = self.run_json("run at-init", self.repo)
        self.assertEqual(payload["route"], "/at-init")
        self.assertEqual(payload["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
