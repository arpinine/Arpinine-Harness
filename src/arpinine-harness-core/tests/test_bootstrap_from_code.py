from __future__ import annotations

import json
import importlib.util
import pathlib
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "bootstrap_from_code.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_from_code", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BootstrapFromCodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        self.external_root: pathlib.Path | None = None
        (self.repo / ".git").mkdir()
        (self.repo / "src").mkdir()
        (self.repo / "tests").mkdir()

    def tearDown(self) -> None:
        if self.external_root and self.external_root.exists():
            shutil.rmtree(self.external_root, ignore_errors=True)
        self.tempdir.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_detects_api_signals_and_writes_assessment_artifacts(self) -> None:
        (self.repo / "src" / "app.py").write_text(
            textwrap.dedent(
                """
                from fastapi import FastAPI

                app = FastAPI()

                @app.get("/health")
                def health():
                    return {"ok": True}
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (self.repo / "tests" / "test_health.py").write_text("def test_health():\n    assert True\n", encoding="utf-8")
        (self.repo / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

        result = self.run_script("--json", "--write-artifacts")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["summary"]["endpoint_count"], 1)
        self.assertIn("api-service", payload["summary"]["system_shape"])
        self.assertTrue(payload["summary"]["tests_present"])
        self.assertEqual(payload["artifact_paths"]["json_path"], ".specify/bootstrap/latest-assessment.json")
        self.assertTrue(payload["artifact_paths"]["history_json_path"].startswith(".specify/bootstrap/history/assessment-"))
        self.assertTrue((self.repo / ".specify" / "bootstrap" / "latest-assessment.md").exists())

    def test_agentic_code_triggers_harness_and_eval_recommendations(self) -> None:
        (self.repo / "src" / "runtime.py").write_text(
            textwrap.dedent(
                """
                from openharness import AgentRuntime

                class SupportAgent:
                    def __init__(self, runtime: AgentRuntime):
                        self.runtime = runtime
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

        result = self.run_script("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertTrue(payload["artifact_recommendations"]["needs_harness_strategy"])
        self.assertTrue(payload["artifact_recommendations"]["needs_eval_plan"])
        self.assertTrue(payload["signals"]["agentic"]["present"])
        self.assertTrue(payload["signals"]["agentic"]["openharness_paths"])
        self.assertTrue(
            any("Harness boundary" in adr["title"] for adr in payload["artifact_recommendations"]["recommended_adrs"])
        )
        self.assertEqual(payload["signals"]["agentic"]["confidence"], "high")
        self.assertIn("scan", payload["signals"]["agentic"])

    def test_docs_tests_and_monorepo_signals_are_reported(self) -> None:
        (self.repo / "README.md").write_text("# Product\n", encoding="utf-8")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
        (self.repo / "docs" / "image.png").write_bytes(b"png")
        (self.repo / "services").mkdir()
        (self.repo / "services" / "billing").mkdir(parents=True)
        (self.repo / "services" / "billing" / "pyproject.toml").write_text("[project]\nname='billing'\n", encoding="utf-8")
        (self.repo / "tests" / "test_access.py").write_text(
            "def test_user_cannot_access_admin_panel():\n    assert True\n",
            encoding="utf-8",
        )
        (self.repo / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")

        result = self.run_script("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertTrue(any(item["path"] == "README.md" for item in payload["signals"]["docs"]))
        self.assertTrue(any(item["path"] == "docs/architecture.md" for item in payload["signals"]["docs"]))
        self.assertFalse(any(item["path"] == "docs/image.png" for item in payload["signals"]["docs"]))
        self.assertTrue(any(item["name"] == "test_user_cannot_access_admin_panel" for item in payload["signals"]["tests"]["descriptions"]))
        self.assertTrue(any(item["path"] == "services/billing" for item in payload["signals"]["monorepo_services"]))
        self.assertTrue(payload["summary"]["monorepo"])

    def test_single_generic_model_reference_does_not_mark_repo_as_agentic(self) -> None:
        (self.repo / "src" / "models.py").write_text(
            "class UserModel:\n    pass\n# model for persistence layer\n",
            encoding="utf-8",
        )

        result = self.run_script("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertFalse(payload["signals"]["agentic"]["present"])
        self.assertEqual(payload["signals"]["agentic"]["confidence"], "none")

    def test_agentic_exclusion_is_contextual_not_file_level(self) -> None:
        (self.repo / "src" / "llm_service.py").write_text(
            "\n".join(
                [
                    "def persistence_layer():",
                    "    note = 'sqlalchemy model mapping lives here'",
                    "    return note",
                    "",
                    "def build_agent():",
                    "    return 'agent'",
                    "",
                    "def build_llm_client():",
                    "    return 'llm'",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = self.run_script("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertTrue(payload["signals"]["agentic"]["present"])
        self.assertEqual(payload["signals"]["agentic"]["confidence"], "medium")

    def test_go_test_file_does_not_trigger_repo_agentic_state(self) -> None:
        (self.repo / "tests" / "llm_test.go").write_text(
            "package tests\n\nfunc TestPromptHarness(t *testing.T) {}\n",
            encoding="utf-8",
        )
        (self.repo / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")

        result = self.run_script("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertFalse(payload["signals"]["agentic"]["present"])

    def test_agentic_test_file_does_not_trigger_repo_agentic_state(self) -> None:
        (self.repo / "tests" / "test_prompt_flow.py").write_text(
            "def test_prompt_inference_flow():\n    assert True\n",
            encoding="utf-8",
        )
        (self.repo / "src" / "app.py").write_text("print('app')\n", encoding="utf-8")

        result = self.run_script("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertFalse(payload["signals"]["agentic"]["present"])

    def test_subdirectory_bootstrap_slug_uses_target_path(self) -> None:
        (self.repo / "services").mkdir()
        (self.repo / "services" / "billing").mkdir(parents=True)
        (self.repo / "services" / "billing" / "app.py").write_text("print('billing')\n", encoding="utf-8")

        result = self.run_script("--json", "--path", "services/billing")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["artifact_recommendations"]["spec_slug"], "001-services-billing-bootstrap")
        self.assertEqual(payload["assessed_path"], "services/billing")

    def test_symlinked_directory_is_not_followed(self) -> None:
        self.external_root = pathlib.Path(tempfile.mkdtemp())
        (self.external_root / "llm.py").write_text("from openharness import AgentRuntime\n", encoding="utf-8")
        (self.repo / "src" / "linked").symlink_to(self.external_root, target_is_directory=True)
        (self.repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")

        files = MODULE.iter_files(self.repo)
        rel_paths = sorted(path.relative_to(self.repo).as_posix() for path in files)
        self.assertEqual(rel_paths, ["src/app.py"])

    def test_invalid_path_returns_error(self) -> None:
        result = self.run_script("--json", "--path", "missing-dir")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Invalid path:", result.stderr)

    def test_empty_repo_without_code_returns_error(self) -> None:
        (self.repo / "README.md").write_text("# Demo\n", encoding="utf-8")

        result = self.run_script("--json")
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("No code files detected under:", result.stderr)


if __name__ == "__main__":
    unittest.main()
