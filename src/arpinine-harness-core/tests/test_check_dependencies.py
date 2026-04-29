from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "check_dependencies.py"


class CheckDependenciesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_json(self) -> dict[str, object]:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--json"],
            cwd=self.repo,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src" / "arpinine-harness-core" / "scripts")},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_defaults_to_spec_kit_provider_when_config_is_missing(self) -> None:
        payload = self.run_json()
        self.assertEqual(payload["provider"]["name"], "spec-kit")
        self.assertEqual(payload["provider"]["source"], "default")
        self.assertIn("new_spec", payload["provider"]["actions"])

    def test_uses_custom_provider_dependencies_when_configured(self) -> None:
        config = self.repo / ".specify" / "specification-provider.json"
        config.write_text(
            json.dumps(
                {
                    "provider": "custom-provider",
                    "description": "Custom planning backend",
                    "dependencies": [
                        {
                            "label": "Custom provider binary",
                            "command": "definitely-missing-provider-binary",
                            "required": True,
                        }
                    ],
                    "actions": {
                        "new_spec": {"kind": "assistant-command", "command": "/custom.specify"},
                        "plan": {"kind": "assistant-command", "command": "/custom.plan"},
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        payload = self.run_json()
        self.assertEqual(payload["provider"]["name"], "custom-provider")
        self.assertEqual(payload["provider"]["source"], ".specify/specification-provider.json")
        self.assertIn("Custom provider binary", payload["summary"]["blocking"])
        self.assertIn("new_spec", payload["provider"]["actions"])


if __name__ == "__main__":
    unittest.main()
