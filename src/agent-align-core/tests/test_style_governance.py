from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
HOOK = ROOT / "src" / "agent-align-core" / "scripts" / "check-style-governance.sh"


class StyleGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify").mkdir()
        (self.repo / "src").mkdir()
        (self.repo / "tools" / "style" / "python").mkdir(parents=True)
        (self.repo / "tools" / "style" / "frontend").mkdir(parents=True)
        (self.repo / "tools" / "style" / "java").mkdir(parents=True)
        (self.repo / "tools" / "style" / "rust").mkdir(parents=True)
        (self.repo / "tools" / "style" / "shared").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_hook(self, file_path: str) -> subprocess.CompletedProcess[str]:
        payload = json.dumps({"tool_input": {"file_path": file_path}})
        return subprocess.run(
            ["bash", str(HOOK)],
            cwd=self.repo,
            env=os.environ.copy(),
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_python_edit_is_blocked_without_style_config(self) -> None:
        result = self.run_hook("src/demo.py")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("no repository-defined style standard found for Python", result.stdout)

    def test_python_edit_is_allowed_with_pyproject(self) -> None:
        (self.repo / "tools" / "style" / "python" / "pyproject.toml").write_text(
            "[tool.ruff]\nline-length = 100\n",
            encoding="utf-8",
        )
        result = self.run_hook("src/demo.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_javascript_edit_is_blocked_without_frontend_style_config(self) -> None:
        result = self.run_hook("src/demo.ts")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("no repository-defined style standard found for JavaScript/TypeScript", result.stdout)

    def test_javascript_edit_is_allowed_with_prettier_config(self) -> None:
        (self.repo / "tools" / "style" / "frontend" / ".prettierrc.json").write_text(
            "{\"semi\": true}\n",
            encoding="utf-8",
        )
        result = self.run_hook("src/demo.ts")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_javascript_edit_is_allowed_with_eslint_config(self) -> None:
        (self.repo / "tools" / "style" / "frontend" / "eslint.config.cjs").write_text(
            "module.exports = [];\n",
            encoding="utf-8",
        )
        result = self.run_hook("src/demo.tsx")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_java_edit_is_allowed_with_checkstyle(self) -> None:
        (self.repo / "tools" / "style" / "java" / "checkstyle.xml").write_text(
            "<module name=\"Checker\"/>\n",
            encoding="utf-8",
        )
        result = self.run_hook("src/Demo.java")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rust_edit_is_allowed_with_rustfmt(self) -> None:
        (self.repo / "tools" / "style" / "rust" / "rustfmt.toml").write_text(
            "max_width = 100\n",
            encoding="utf-8",
        )
        result = self.run_hook("src/demo.rs")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_constitution_edit_is_allowed_without_style_config(self) -> None:
        result = self.run_hook(".specify/CONSTITUTION.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
