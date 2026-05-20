from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "inspect_state.py"


class InspectStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)

        spec = importlib.util.spec_from_file_location("inspect_state", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        self.module = module

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_json(self, repo: pathlib.Path | None = None) -> dict[str, object]:
        cmd = ["python3", str(SCRIPT), "--indent", "2"]
        if repo is not None:
            cmd.extend(["--repo", str(repo)])
        result = subprocess.run(
            cmd,
            cwd=self.repo,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def write(self, relative_path: str, body: str) -> None:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")

    def test_ungoverned_empty_repo(self) -> None:
        payload = self.run_json(self.repo)
        self.assertEqual(pathlib.Path(payload["repo_root"]).resolve(), self.repo.resolve())
        self.assertFalse(payload["governed"])
        self.assertFalse(payload["has_specs"])
        self.assertEqual(payload["spec_count"], 0)
        self.assertFalse(payload["has_existing_codebase"])
        self.assertFalse(payload["bootstrap_candidate"])

    def test_ungoverned_repo_with_existing_codebase_is_bootstrap_candidate(self) -> None:
        self.write("src/app.py", "print('hello')\n")
        payload = self.run_json(self.repo)
        self.assertFalse(payload["governed"])
        self.assertTrue(payload["has_existing_codebase"])
        self.assertTrue(payload["bootstrap_candidate"])

    def test_active_and_completed_sessions_are_reported_separately(self) -> None:
        self.write(
            ".specify/map/initiative-a/map.md",
            """
            ---
            state: needs-clarification
            ---
            """,
        )
        self.write(
            ".specify/map/initiative-b/map.md",
            """
            ---
            state: completed
            ---
            """,
        )
        self.write(
            ".specify/discovery/feature-a/discovery.md",
            """
            ---
            state: spec-ready-awaiting-confirmation
            ---
            """,
        )
        self.write(
            ".specify/discovery/feature-b/discovery.md",
            """
            ---
            state: promoted-to-spec
            ---
            """,
        )

        payload = self.run_json(self.repo)
        self.assertEqual(payload["active_map_sessions"], ["initiative-a"])
        self.assertEqual(payload["completed_map_sessions"], ["initiative-b"])
        self.assertEqual(payload["active_discovery_sessions"], ["feature-a"])
        self.assertEqual(payload["completed_discovery_sessions"], ["feature-b"])

    def test_spec_eval_and_observation_gaps_follow_governed_layout(self) -> None:
        self.write(".specify/specs/001-alpha/spec.md", "# Spec\n")
        self.write(".specify/specs/001-alpha/plan.md", "# Plan\n")

        self.write(".specify/specs/002-beta/spec.md", "# Spec\n")
        self.write(".specify/specs/002-beta/plan.md", "# Plan\n")
        self.write(".specify/evals/002-beta/eval-plan.md", "# Eval Plan\n")

        self.write(".specify/specs/003-gamma/spec.md", "# Spec\n")
        self.write(".specify/specs/003-gamma/plan.md", "# Plan\n")
        self.write(".specify/evals/003-gamma/eval-plan.md", "# Eval Plan\n")
        self.write(".specify/observations/003-gamma/latest-observation.md", "# Observation\n")

        payload = self.run_json(self.repo)
        self.assertEqual(payload["spec_count"], 3)
        self.assertEqual(payload["specs_without_plan"], [])
        self.assertEqual(payload["specs_with_plan"], ["001-alpha", "002-beta", "003-gamma"])
        self.assertEqual(payload["eval_gaps"], ["001-alpha"])
        self.assertEqual(payload["observation_gaps"], ["002-beta"])

    def test_drift_detection_uses_unresolved_markers_only(self) -> None:
        self.write(".specify/specs/001-open/spec.md", "# Spec\n")
        self.write(".specify/specs/001-open/drift-report.md", "Remaining: 2 CRITICAL unresolved\n")
        self.write(".specify/specs/002-closed/spec.md", "# Spec\n")
        self.write(".specify/specs/002-closed/drift-report.md", "Drift was reviewed and resolved.\n")

        payload = self.run_json(self.repo)
        self.assertEqual(payload["specs_with_open_drift"], ["001-open"])

    def test_incomplete_state_flips_true_when_scan_emits_warning(self) -> None:
        (self.repo / ".specify").mkdir()

        original_scan_sessions = self.module.scan_sessions

        def warning_scan_sessions(*args, **kwargs):
            warnings = args[4]
            warnings.append("Injected session scan warning")
            return original_scan_sessions(*args, **kwargs)

        with mock.patch.object(self.module, "scan_sessions", side_effect=warning_scan_sessions):
            payload = self.module.inspect(self.repo)

        self.assertTrue(payload["incomplete_state"])
        self.assertIn("Injected session scan warning", payload["warnings"])


if __name__ == "__main__":
    unittest.main()
