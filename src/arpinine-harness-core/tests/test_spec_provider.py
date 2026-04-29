from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src" / "arpinine-harness-core" / "scripts"))

from spec_provider import load_provider_config, normalize_provider_name, provider_command  # noqa: E402


class SpecProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_config(self, payload: dict) -> None:
        (self.repo / ".specify" / "specification-provider.json").write_text(
            json.dumps(payload) + "\n",
            encoding="utf-8",
        )

    def test_normalize_provider_name(self) -> None:
        self.assertEqual(normalize_provider_name("Spec_Kit"), "spec-kit")
        self.assertEqual(normalize_provider_name(" speckit "), "spec-kit")

    def test_default_provider_is_loaded_for_normalized_spec_kit_name(self) -> None:
        self.write_config({"provider": "Spec_Kit"})
        payload = load_provider_config(self.repo)
        self.assertEqual(payload["provider"], "spec-kit")
        self.assertEqual(provider_command(payload, "new_spec"), "/speckit.specify")

    def test_default_provider_is_loaded_for_speckit_alias(self) -> None:
        self.write_config({"provider": "speckit"})
        payload = load_provider_config(self.repo)
        self.assertEqual(payload["provider"], "spec-kit")
        self.assertEqual(provider_command(payload, "plan"), "/speckit.plan")

    def test_provider_command_raises_for_missing_required_action(self) -> None:
        self.write_config(
            {
                "provider": "custom-provider",
                "actions": {
                    "plan": {"kind": "assistant-command", "command": "/custom.plan"},
                },
            }
        )
        payload = load_provider_config(self.repo)
        with self.assertRaisesRegex(ValueError, "Provider custom-provider has no action 'tasks' configured"):
            provider_command(payload, "tasks")

    def test_load_provider_config_rejects_unsupported_action_kind(self) -> None:
        self.write_config(
            {
                "provider": "custom-provider",
                "actions": {
                    "new_spec": {"kind": "cli-command", "command": "custom-specify"},
                },
            }
        )
        with self.assertRaisesRegex(ValueError, "unsupported kind"):
            load_provider_config(self.repo)

    def test_load_provider_config_rejects_blank_command(self) -> None:
        self.write_config(
            {
                "provider": "custom-provider",
                "actions": {
                    "new_spec": {"kind": "assistant-command", "command": "   "},
                },
            }
        )
        with self.assertRaisesRegex(ValueError, "missing required field 'command'"):
            load_provider_config(self.repo)

    def test_load_provider_config_rejects_non_object_action(self) -> None:
        self.write_config(
            {
                "provider": "custom-provider",
                "actions": {
                    "new_spec": "custom command",
                },
            }
        )
        with self.assertRaisesRegex(ValueError, "must be a JSON object"):
            load_provider_config(self.repo)


if __name__ == "__main__":
    unittest.main()
