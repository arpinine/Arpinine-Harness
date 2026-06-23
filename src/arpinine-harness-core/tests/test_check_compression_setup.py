"""
Tests for check_compression_setup.py — enforced compression security controls.

Governs: specs/011-context-compression-governance (TASK-005)
ADRs: ADR-0014 (headroom pin+hash, import confinement), ADR-0016 (toggle-gated:
      disabled => nothing to check), ADR-0018 (configured engine CCR dir path
      safety + 700/600).

Checks are pure functions so they can be unit-tested without an installed
headroom or a live proxy. The top-level run is gated by the constitution toggle.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import stat
import tempfile
import unittest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "check_compression_setup.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("check_compression_setup", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCcrPathSafety(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.exists(), f"missing module at {MODULE_PATH}")
        self.m = _load()

    def test_default_arpinine_store_is_safe(self) -> None:
        home = pathlib.Path("/home/dev")
        finding = self.m.check_ccr_store_path(
            store=home / ".arpinine" / "ccr-store",
            repo_root=pathlib.Path("/home/dev/project"),
            home=home,
        )
        self.assertIsNone(finding)

    def test_path_inside_worktree_is_high(self) -> None:
        repo = pathlib.Path("/home/dev/project")
        finding = self.m.check_ccr_store_path(
            store=repo / ".specify" / "ccr",
            repo_root=repo,
            home=pathlib.Path("/home/dev"),
        )
        self.assertIsNotNone(finding)
        self.assertEqual(finding["severity"], "HIGH")

    def test_cloud_sync_prefixes_are_high(self) -> None:
        home = pathlib.Path("/home/dev")
        repo = home / "project"
        for sub in (
            "Library/Mobile Documents/store",
            "Dropbox/store",
            "OneDrive/store",
            "Google Drive/store",
            "Documents/store",
            "Desktop/store",
        ):
            finding = self.m.check_ccr_store_path(
                store=home / sub, repo_root=repo, home=home
            )
            self.assertIsNotNone(finding, f"{sub} should be flagged")
            self.assertEqual(finding["severity"], "HIGH")


class TestStorePermissions(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()
        self._tmp = tempfile.TemporaryDirectory()
        self.store = pathlib.Path(self._tmp.name) / "ccr-store"
        self.store.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_mode_700_dir_passes(self) -> None:
        os.chmod(self.store, 0o700)
        self.assertIsNone(self.m.check_store_permissions(self.store))

    def test_world_readable_dir_is_high(self) -> None:
        os.chmod(self.store, 0o755)
        finding = self.m.check_store_permissions(self.store)
        self.assertIsNotNone(finding)
        self.assertEqual(finding["severity"], "HIGH")

    def test_group_readable_stored_file_is_high(self) -> None:
        """ADR-0018: stored-original files must be 600, not just the 700 dir."""
        os.chmod(self.store, 0o700)
        f = self.store / "seg-001.orig"
        f.write_bytes(b"governed original")
        os.chmod(f, 0o644)
        finding = self.m.check_store_permissions(self.store)
        self.assertIsNotNone(finding, "world/group-readable original must be flagged")
        self.assertEqual(finding["severity"], "HIGH")
        self.assertIn("seg-001.orig", finding.get("path", ""))


class TestHeadroomImportBoundary(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.allowed = self.root / "headroom_provider.py"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_import_only_in_allowed_module_passes(self) -> None:
        self.allowed.write_text("import headroom\n")
        findings = self.m.check_headroom_import_boundary(self.root, self.allowed)
        self.assertEqual(findings, [])

    def test_import_outside_allowed_module_is_high(self) -> None:
        self.allowed.write_text("import headroom\n")
        (self.root / "rogue.py").write_text("from headroom import proxy\n")
        findings = self.m.check_headroom_import_boundary(self.root, self.allowed)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "HIGH")
        self.assertIn("rogue.py", findings[0]["file"])


class TestHeadroomPin(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()

    def test_matching_version_and_hash_passes(self) -> None:
        self.assertIsNone(
            self.m.check_headroom_pin(
                installed_version="0.27.0",
                installed_hash="abc",
                pinned_version="0.27.0",
                pinned_hash="abc",
            )
        )

    def test_version_mismatch_is_high(self) -> None:
        f = self.m.check_headroom_pin(
            installed_version="0.28.0",
            installed_hash="abc",
            pinned_version="0.27.0",
            pinned_hash="abc",
        )
        self.assertEqual(f["severity"], "HIGH")

    def test_not_installed_when_enabled_is_high(self) -> None:
        f = self.m.check_headroom_pin(
            installed_version=None,
            installed_hash=None,
            pinned_version="0.27.0",
            pinned_hash="abc",
        )
        self.assertEqual(f["severity"], "HIGH")


class TestLoggingConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()

    def test_full_payload_logging_flag_is_high(self) -> None:
        f = self.m.check_no_full_payload_logging({"log_full_payload": True})
        self.assertEqual(f["severity"], "HIGH")

    def test_debug_payload_logging_flag_is_high(self) -> None:
        f = self.m.check_no_full_payload_logging({"debug_log_bodies": True})
        self.assertEqual(f["severity"], "HIGH")

    def test_clean_logging_config_passes(self) -> None:
        self.assertIsNone(self.m.check_no_full_payload_logging({"log_level": "WARN"}))


class TestToggleGate(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        (self.repo / ".specify").mkdir()
        (self.repo / ".specify" / "CONSTITUTION.md").write_text("# C\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_disabled_toggle_reports_ok_with_no_findings(self) -> None:
        report = self.m.run_checks(self.repo)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["findings"], [])
        self.assertFalse(report["compression_enabled"])

    def _enable(self) -> None:
        sys_path = str(pathlib.Path(self.m.__file__).resolve().parent)
        import importlib.util as iu

        spec = iu.spec_from_file_location(
            "compression_config", pathlib.Path(sys_path) / "compression_config.py"
        )
        cc = iu.module_from_spec(spec)
        spec.loader.exec_module(cc)
        cc.set_compression_enabled(self.repo, True)

    def test_enabled_runs_real_ccr_path_check(self) -> None:
        """run_checks must actually invoke the configured-engine-CCR-path helper."""
        self._enable()
        unsafe = self.repo / ".specify" / "ccr"  # inside the worktree
        report = self.m.run_checks(
            self.repo, store_path=unsafe, headroom={"version": "0.27.0", "hash": "x", "pinned_version": "0.27.0", "pinned_hash": "x"}
        )
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("ccr-store-in-worktree", codes)
        self.assertEqual(report["status"], "high")

    def test_enabled_runs_real_import_boundary_check(self) -> None:
        self._enable()
        provider_root = self.repo / "compression"
        provider_root.mkdir()
        (provider_root / "headroom_provider.py").write_text("import headroom\n")
        (provider_root / "rogue.py").write_text("from headroom import proxy\n")
        report = self.m.run_checks(
            self.repo,
            provider_root=provider_root,
            headroom={"version": "0.27.0", "hash": "x", "pinned_version": "0.27.0", "pinned_hash": "x", "ccr_dir": str(pathlib.Path.home() / ".arpinine" / "ccr-store")},
        )
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("headroom-import-boundary", codes)

    def test_enabled_runs_real_logging_check(self) -> None:
        self._enable()
        report = self.m.run_checks(
            self.repo,
            logging_config={"log_full_payload": True},
            headroom={"version": "0.27.0", "hash": "x", "pinned_version": "0.27.0", "pinned_hash": "x", "ccr_dir": str(pathlib.Path.home() / ".arpinine" / "ccr-store")},
        )
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("full-payload-logging", codes)

    def test_enabled_clean_setup_passes(self) -> None:
        self._enable()
        report = self.m.run_checks(
            self.repo,
            logging_config={"log_level": "WARN"},
            headroom={"version": "0.27.0", "hash": "x", "pinned_version": "0.27.0", "pinned_hash": "x", "ccr_dir": str(pathlib.Path.home() / ".arpinine" / "ccr-store")},
        )
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["status"], "ok")

    def test_enabled_without_host_headroom_metadata_still_passes(self) -> None:
        self._enable()
        report = self.m.run_checks(
            self.repo,
            logging_config={"log_level": "WARN"},
        )
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["status"], "ok")

    def test_enabled_uses_configured_headroom_ccr_dir_when_store_path_omitted(self) -> None:
        self._enable()
        unsafe = self.repo / ".specify" / "ccr"
        report = self.m.run_checks(
            self.repo,
            headroom={
                "version": "0.27.0",
                "hash": "x",
                "pinned_version": "0.27.0",
                "pinned_hash": "x",
                "ccr_dir": str(unsafe),
            },
        )
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("ccr-store-in-worktree", codes)


if __name__ == "__main__":
    unittest.main()
