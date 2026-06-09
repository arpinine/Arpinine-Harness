from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "scaffold_archetype.py"
SCRIPTS_DIR = ROOT / "src" / "arpinine-harness-core" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location("scaffold_archetype", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
project_looks_nonempty = MODULE.project_looks_nonempty


class ScaffoldArchetypeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_list_archetypes(self) -> None:
        result = self.run_script("--list")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("agent-app", result.stdout)
        self.assertIn("ml-pipeline", result.stdout)
        self.assertIn("fullstack-app", result.stdout)

    def test_scaffold_fullstack_app_into_empty_repo(self) -> None:
        result = self.run_script("fullstack-app")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for layer in ("backend", "frontend", "domain", "db"):
            self.assertTrue((self.repo / "src" / layer / ".gitkeep").exists(), layer)
        self.assertTrue((self.repo / "infra" / ".gitkeep").exists())
        self.assertTrue((self.repo / "PROJECT_CONVENTIONS.md").exists())
        self.assertTrue((self.repo / ".specify" / "archetype.json").exists())

    def test_scaffold_agent_app_into_empty_repo(self) -> None:
        result = self.run_script("agent-app")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / "src" / "agents" / ".gitkeep").exists())
        self.assertTrue((self.repo / "src" / "tools" / ".gitkeep").exists())
        self.assertTrue((self.repo / "PROJECT_CONVENTIONS.md").exists())
        self.assertTrue((self.repo / ".specify" / "archetype.json").exists())

    def test_skip_if_nonempty_leaves_existing_repo_untouched(self) -> None:
        (self.repo / "backend").mkdir()

        result = self.run_script("agent-app", "--skip-if-nonempty")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Skipping scaffold", result.stdout)
        self.assertFalse((self.repo / "PROJECT_CONVENTIONS.md").exists())

    def test_nonempty_repo_requires_force(self) -> None:
        (self.repo / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")

        result = self.run_script("agent-app")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Refusing to scaffold", result.stderr)

    def test_force_allows_scaffold_in_nonempty_repo(self) -> None:
        (self.repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (self.repo / "backend").mkdir()

        result = self.run_script("ml-pipeline", "--force")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / "src" / "pipelines" / ".gitkeep").exists())
        self.assertTrue((self.repo / "PROJECT_CONVENTIONS.md").exists())

    def test_project_looks_nonempty_allows_docs_only_repo(self) -> None:
        (self.repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "architecture.md").write_text("# Architecture\n", encoding="utf-8")

        nonempty, reason = project_looks_nonempty(self.repo)
        self.assertFalse(nonempty, reason)

    def test_project_looks_nonempty_flags_unallowlisted_dotfile(self) -> None:
        (self.repo / ".env").write_text("SECRET=1\n", encoding="utf-8")

        nonempty, reason = project_looks_nonempty(self.repo)
        self.assertTrue(nonempty)
        self.assertIn(".env", reason)

    def test_project_looks_nonempty_allows_standard_root_files(self) -> None:
        (self.repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (self.repo / ".gitignore").write_text(".venv/\n", encoding="utf-8")
        (self.repo / ".python-version").write_text("3.12\n", encoding="utf-8")

        nonempty, reason = project_looks_nonempty(self.repo)
        self.assertFalse(nonempty, reason)

    def test_project_looks_nonempty_flags_nested_source_file(self) -> None:
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "notes.py").write_text("print('x')\n", encoding="utf-8")

        nonempty, reason = project_looks_nonempty(self.repo)
        self.assertTrue(nonempty)
        self.assertIn("docs/notes.py", reason)


if __name__ == "__main__":
    unittest.main()
