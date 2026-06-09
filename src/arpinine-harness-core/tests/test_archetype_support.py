from __future__ import annotations

import json
import importlib.util
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
ARCHETYPES_ROOT = ROOT / "src" / "arpinine-harness-core" / "archetypes"
SCRIPTS_DIR = ROOT / "src" / "arpinine-harness-core" / "scripts"
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "archetype_support.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location("archetype_support", SCRIPT)
archetype_support = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(archetype_support)


class ArchetypeSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_list_archetypes_returns_known_archetypes(self) -> None:
        available = archetype_support.list_archetypes(ARCHETYPES_ROOT)
        self.assertIn("agent-app", available)
        self.assertIn("ml-pipeline", available)
        self.assertIn("fullstack-app", available)
        self.assertIn("fullstack-react-fastapi", available)

    def test_load_manifest_reads_fullstack_app_fields(self) -> None:
        manifest = archetype_support.load_manifest(ARCHETYPES_ROOT, "fullstack-app")
        self.assertEqual(manifest["name"], "fullstack-app")
        self.assertIn("infra", manifest["directories"])
        rule_ids = {rule["rule_id"] for rule in manifest["starter_rules"]}
        self.assertIn("archetype-fullstack-app-infra-boundary", rule_ids)

    def test_load_manifest_reads_fullstack_react_fastapi_fields(self) -> None:
        manifest = archetype_support.load_manifest(ARCHETYPES_ROOT, "fullstack-react-fastapi")
        self.assertEqual(manifest["name"], "fullstack-react-fastapi")
        self.assertIn("backend/api", manifest["directories"])
        self.assertIn("iac/cdk", manifest["directories"])
        rule_ids = {rule["rule_id"] for rule in manifest["starter_rules"]}
        self.assertIn("archetype-fullstack-react-fastapi-route-handler-boundary", rule_ids)

    def test_load_manifest_reads_structured_fields(self) -> None:
        manifest = archetype_support.load_manifest(ARCHETYPES_ROOT, "agent-app")
        self.assertEqual(manifest["name"], "agent-app")
        self.assertIn("constitution_principles", manifest)
        self.assertIn("starter_rules", manifest)

    def test_write_and_load_metadata_round_trip(self) -> None:
        path = archetype_support.write_metadata(self.repo, "agent-app")
        self.assertEqual(path, self.repo / ".specify" / "archetype.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["archetype"], "agent-app")
        self.assertEqual(archetype_support.load_selected_archetype(self.repo), "agent-app")

    def test_find_constitution_path_prefers_known_candidate(self) -> None:
        constitution = self.repo / "CONSTITUTION.md"
        constitution.write_text("# Project Constitution\n", encoding="utf-8")
        found = archetype_support.find_constitution_path(self.repo)
        self.assertEqual(found, constitution)

    def test_find_constitution_path_falls_back_to_markdown_scan(self) -> None:
        nested = self.repo / "docs" / "team-constitution.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("# Project Constitution\n\n## Principles\n", encoding="utf-8")
        found = archetype_support.find_constitution_path(self.repo)
        self.assertEqual(found, nested)

    def test_load_selected_archetype_returns_empty_on_invalid_json(self) -> None:
        metadata = self.repo / ".specify" / "archetype.json"
        metadata.parent.mkdir(parents=True)
        metadata.write_text("{not-json}\n", encoding="utf-8")
        self.assertEqual(archetype_support.load_selected_archetype(self.repo), "")


if __name__ == "__main__":
    unittest.main()
