from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCAFFOLD_SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "scaffold_archetype.py"
HOOK_SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "check-archetype-governance.sh"


class CheckArchetypeGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".git").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def scaffold(self, archetype: str) -> None:
        result = subprocess.run(
            ["python3", str(SCAFFOLD_SCRIPT), archetype],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_hook(self, file_path: str, content: str) -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_input": {
                "file_path": str((self.repo / file_path).resolve()),
                "content": content,
            }
        }
        return subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            cwd=self.repo,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(ROOT / "src" / "arpinine-harness-core")},
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_agent_app_blocks_framework_import_in_domain(self) -> None:
        self.scaffold("agent-app")
        result = self.run_hook("src/domain/user.py", "from fastapi import APIRouter\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("domain layer cannot import", result.stdout)

    def test_ml_pipeline_blocks_raw_data_edit(self) -> None:
        self.scaffold("ml-pipeline")
        result = self.run_hook("data/raw/sample.csv", "col1,col2\n1,2\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("raw data is immutable", result.stdout)

    def test_fullstack_app_blocks_framework_import_in_domain(self) -> None:
        self.scaffold("fullstack-app")
        result = self.run_hook("src/domain/user.py", "from fastapi import APIRouter\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("domain layer cannot import", result.stdout)

    def test_fullstack_app_blocks_orm_outside_db(self) -> None:
        self.scaffold("fullstack-app")
        result = self.run_hook("src/backend/handlers.py", "import sqlalchemy\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("confined to src/db/", result.stdout)

    def test_fullstack_app_allows_orm_inside_db(self) -> None:
        self.scaffold("fullstack-app")
        result = self.run_hook("src/db/repository.py", "import sqlalchemy\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fullstack_app_blocks_frontend_importing_backend(self) -> None:
        self.scaffold("fullstack-app")
        result = self.run_hook("src/frontend/App.tsx", "import { svc } from '../backend/service'\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("frontend cannot import", result.stdout)

    def test_fullstack_app_blocks_iac_import_in_app_code(self) -> None:
        self.scaffold("fullstack-app")
        result = self.run_hook("src/backend/main.py", "import aws_cdk\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("infrastructure-as-code constructs", result.stdout)

    def test_fullstack_app_blocks_app_logic_import_in_infra(self) -> None:
        self.scaffold("fullstack-app")
        result = self.run_hook("infra/app.py", "from src.domain import order\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("cannot import application business logic", result.stdout)


if __name__ == "__main__":
    unittest.main()
