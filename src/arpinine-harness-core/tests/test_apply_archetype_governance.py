from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCAFFOLD_SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "scaffold_archetype.py"
APPLY_SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "apply_archetype_governance.py"


class ApplyArchetypeGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".git").mkdir()
        (self.repo / ".specify" / "rules").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_script(self, script: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(script), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_apply_writes_constitution_addendum_and_rules(self) -> None:
        scaffold = self.run_script(SCAFFOLD_SCRIPT, "agent-app")
        self.assertEqual(scaffold.returncode, 0, scaffold.stdout + scaffold.stderr)
        (self.repo / "CONSTITUTION.md").write_text("# Project Constitution\n\n## Principles\n1. Base rule\n", encoding="utf-8")

        result = self.run_script(APPLY_SCRIPT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        constitution = (self.repo / "CONSTITUTION.md").read_text(encoding="utf-8")
        self.assertIn("## Archetype Addendum", constitution)
        self.assertIn("`agent-app`", constitution)
        rule_path = self.repo / ".specify" / "rules" / "archetype" / "archetype-agent-app-domain-boundary.md"
        self.assertTrue(rule_path.exists())

    def test_apply_is_idempotent(self) -> None:
        self.run_script(SCAFFOLD_SCRIPT, "ml-pipeline")
        (self.repo / "CONSTITUTION.md").write_text("# Project Constitution\n\n## Principles\n1. Base rule\n", encoding="utf-8")

        first = self.run_script(APPLY_SCRIPT)
        second = self.run_script(APPLY_SCRIPT)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)

        constitution = (self.repo / "CONSTITUTION.md").read_text(encoding="utf-8")
        self.assertEqual(constitution.count("## Archetype Addendum"), 1)

    def test_explicit_archetype_updates_metadata(self) -> None:
        (self.repo / "CONSTITUTION.md").write_text("# Project Constitution\n\n## Principles\n1. Base rule\n", encoding="utf-8")
        result = self.run_script(APPLY_SCRIPT, "--archetype", "agent-app")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads((self.repo / ".specify" / "archetype.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["archetype"], "agent-app")


if __name__ == "__main__":
    unittest.main()
