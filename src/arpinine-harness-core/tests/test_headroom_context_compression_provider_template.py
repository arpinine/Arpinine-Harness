"""
Tests for the headroom provider template seam behavior that does not require the
real headroom runtime.

Governs: specs/011-context-compression-governance (TASK-010)
ADRs: ADR-0015 (opaque loopback endpoint), ADR-0018 (configured engine CCR dir
      validated at activation), ADR-0019 (per-session activation lifecycle).
"""

from __future__ import annotations

import importlib
import os
import pathlib
import sys
import tempfile
import types
import unittest


SCAFFOLDER_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "scaffold_compression_setup.py"
)


def _load_scaffolder():
    import importlib.util

    spec = importlib.util.spec_from_file_location("scaffold_compression_setup", SCAFFOLDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _purge_package(name: str) -> None:
    for mod in [m for m in sys.modules if m == name or m.startswith(name + ".")]:
        del sys.modules[mod]


class TestHeadroomContextCompressionProviderTemplate(unittest.TestCase):
    def setUp(self) -> None:
        self.scaffolder = _load_scaffolder()
        self._tmp = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmp.name)
        (self.target / ".git").mkdir()
        self.scaffolder.scaffold(self.target)
        self._fake_headroom = types.ModuleType("headroom")
        sys.modules["headroom"] = self._fake_headroom
        sys.path.insert(0, str(self.target))
        _purge_package("context_compression")
        self.pkg = importlib.import_module("context_compression")
        self.mod = importlib.import_module("context_compression.headroom_provider")

    def tearDown(self) -> None:
        if str(self.target) in sys.path:
            sys.path.remove(str(self.target))
        sys.modules.pop("headroom", None)
        _purge_package("context_compression")
        self._tmp.cleanup()

    def test_activate_validates_ccr_dir_before_starting_proxy(self) -> None:
        calls: list[str] = []

        class _Provider(self.mod.HeadroomContextCompressionProvider):
            def _engine_validate_configured_ccr_directory(self) -> None:
                calls.append("validate")

            def _engine_start_proxy_loopback_only(self):
                calls.append("start")
                return object(), 8787

        provider = _Provider()
        endpoint = provider.activate()
        self.assertEqual(calls, ["validate", "start"])
        self.assertEqual(endpoint.base_url, "http://127.0.0.1:8787")

    def test_validation_failure_is_wrapped_as_compression_error(self) -> None:
        Error = self.pkg.CompressionError

        class _Provider(self.mod.HeadroomContextCompressionProvider):
            def _engine_validate_configured_ccr_directory(self) -> None:
                raise RuntimeError("ccr dir unsafe")

            def _engine_start_proxy_loopback_only(self):
                raise AssertionError("proxy start must not run after failed validation")

        with self.assertRaises(Error):
            _Provider().activate()

    # --- real CCR-dir validation seam (ADR-0018) ---

    def _set_fake_store_url(self, url: str) -> None:
        import types as _t

        cfg = _t.SimpleNamespace(store_url=url)
        self._fake_headroom.HeadroomConfig = lambda: cfg

    def test_ccr_validation_rejects_store_in_worktree(self) -> None:
        # Default sqlite store resolves into CWD -> inside the worktree -> unsafe.
        self._set_fake_store_url("sqlite:///headroom.db")
        with self.assertRaises(self.pkg.CompressionError):
            self.mod.HeadroomContextCompressionProvider()._engine_validate_configured_ccr_directory()

    def test_ccr_validation_rejects_repo_root_store_from_nested_cwd(self) -> None:
        repo_root = self.target.resolve()
        nested = repo_root / "nested" / "work"
        nested.mkdir(parents=True, exist_ok=True)
        self._set_fake_store_url(f"sqlite:///{repo_root / 'headroom.db'}")
        prev = pathlib.Path.cwd()
        os.chdir(nested)
        try:
            with self.assertRaises(self.pkg.CompressionError):
                self.mod.HeadroomContextCompressionProvider()._engine_validate_configured_ccr_directory()
        finally:
            os.chdir(prev)

    def test_ccr_validation_allows_safe_external_store(self) -> None:
        safe = pathlib.Path(self._tmp.name).resolve() / "ccr" / "h.db"
        self._set_fake_store_url(f"sqlite:///{safe}")
        self.mod.HeadroomContextCompressionProvider()._engine_validate_configured_ccr_directory()

    def test_ccr_validation_exempts_in_memory_store(self) -> None:
        self._set_fake_store_url("sqlite:///:memory:")
        self.mod.HeadroomContextCompressionProvider()._engine_validate_configured_ccr_directory()


if __name__ == "__main__":
    unittest.main()
