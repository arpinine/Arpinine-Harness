"""
Tests for compression_config.py — the governed compression toggle reader/writer.

Governs: specs/011-context-compression-governance (TASK-004)
ADRs: ADR-0016 (toggle recorded in the constitution; absent key defaults to
      disabled; records only the enabled/disabled flag, not a provider class;
      surfaces the network-restriction residual-risk acknowledgment).
"""

from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "compression_config.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("compression_config", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCompressionConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.exists(), f"missing module at {MODULE_PATH}")
        self.cc = _load()
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        (self.repo / ".specify").mkdir()
        self.constitution = self.repo / ".specify" / "CONSTITUTION.md"
        self.constitution.write_text("# Project Constitution\n\n## Principles\n1. x\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ADR-0016: absent key defaults to disabled.
    def test_absent_block_defaults_to_disabled(self) -> None:
        self.assertFalse(self.cc.read_compression_enabled(self.repo))

    def test_missing_constitution_defaults_to_disabled(self) -> None:
        self.constitution.unlink()
        self.assertFalse(self.cc.read_compression_enabled(self.repo))

    def test_set_enabled_then_read_true(self) -> None:
        self.cc.set_compression_enabled(self.repo, True)
        self.assertTrue(self.cc.read_compression_enabled(self.repo))

    def test_set_disabled_then_read_false(self) -> None:
        self.cc.set_compression_enabled(self.repo, True)
        self.cc.set_compression_enabled(self.repo, False)
        self.assertFalse(self.cc.read_compression_enabled(self.repo))

    def test_set_is_idempotent_single_block(self) -> None:
        self.cc.set_compression_enabled(self.repo, True)
        self.cc.set_compression_enabled(self.repo, True)
        text = self.constitution.read_text()
        self.assertEqual(text.count("arpinine:compression"), 2)  # open + close marker

    def test_preserves_existing_constitution_content(self) -> None:
        self.cc.set_compression_enabled(self.repo, True)
        text = self.constitution.read_text()
        self.assertIn("# Project Constitution", text)
        self.assertIn("## Principles", text)

    # ADR-0016: residual-risk acknowledgment is recorded with the toggle.
    def test_residual_risk_ack_recorded_and_read(self) -> None:
        self.cc.set_compression_enabled(
            self.repo, True, network_restriction_ack=True
        )
        self.assertTrue(self.cc.read_network_restriction_ack(self.repo))

    def test_residual_risk_ack_defaults_false(self) -> None:
        self.cc.set_compression_enabled(self.repo, True)
        self.assertFalse(self.cc.read_network_restriction_ack(self.repo))

    # ADR-0016: stores only the flag, not a provider class.
    def test_block_does_not_record_a_provider_class(self) -> None:
        self.cc.set_compression_enabled(self.repo, True)
        text = self.constitution.read_text().lower()
        self.assertNotIn("provider", text.split("arpinine:compression")[1])


if __name__ == "__main__":
    unittest.main()
