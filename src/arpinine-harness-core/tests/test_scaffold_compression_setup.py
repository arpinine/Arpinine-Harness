"""
Tests for scaffold_compression_setup.py — idempotent provider scaffolder.

Governs: specs/011-context-compression-governance (TASK-005)
ADRs: ADR-0013 (interface + noop always scaffolded; headroom default only when
      its template exists; single interface identity via package imports).

The scaffolded output is a Python PACKAGE (`context_compression/` with
`__init__.py`) — deliberately NOT `compression`, which would shadow the Python
3.14+ stdlib `compression` package.
Consumers import through the import system, which caches by name — so the
ContextCompressionProvider interface is a single identity regardless of import
order. (Two independent file-path loads of the same file cannot guarantee that.)
"""

from __future__ import annotations

import importlib
import importlib.util
import pathlib
import sys
import tempfile
import unittest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "scaffold_compression_setup.py"
)


def _load_scaffolder():
    spec = importlib.util.spec_from_file_location("scaffold_compression_setup", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_checker():
    path = MODULE_PATH.parent / "check_compression_setup.py"
    spec = importlib.util.spec_from_file_location("check_compression_setup", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _purge_package(name: str) -> None:
    for mod in [m for m in sys.modules if m == name or m.startswith(name + ".")]:
        del sys.modules[mod]


class TestScaffoldCompressionSetup(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.exists(), f"missing module at {MODULE_PATH}")
        self.m = _load_scaffolder()
        self._tmp = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmp.name)
        self._added_path = False

    def tearDown(self) -> None:
        if self._added_path and str(self.target) in sys.path:
            sys.path.remove(str(self.target))
        _purge_package("context_compression")
        self._tmp.cleanup()

    def _import_package(self):
        """Add target to sys.path and return the scaffolded `context_compression` package fresh."""
        _purge_package("context_compression")
        if str(self.target) not in sys.path:
            sys.path.insert(0, str(self.target))
            self._added_path = True
        return importlib.import_module("context_compression")

    # --- scaffolding mechanics ---

    def test_scaffolds_interface_noop_and_package_init(self) -> None:
        report = self.m.scaffold(self.target)
        self.assertEqual(report["status"], "ok")
        comp = self.target / "context_compression"
        self.assertTrue((comp / "context_compression_provider.py").exists())
        self.assertTrue((comp / "noop_provider.py").exists())
        self.assertTrue((comp / "__init__.py").exists())

    def test_scaffolded_noop_uses_package_import_not_path_loader(self) -> None:
        self.m.scaffold(self.target)
        noop_src = (self.target / "context_compression" / "noop_provider.py").read_text()
        self.assertIn(
            "from .context_compression_provider import CompressionEndpoint",
            noop_src,
        )
        self.assertNotIn("scaffold-replace-start", noop_src)
        self.assertNotIn("spec_from_file_location", noop_src)

    def test_scaffolds_security_headroom_and_host_wiring(self) -> None:
        self.m.scaffold(self.target)
        comp = self.target / "context_compression"
        self.assertTrue((comp / "security.py").exists())
        self.assertTrue((comp / "headroom_provider.py").exists())
        self.assertTrue((comp / "host_wiring.py").exists())

    def test_package_exposes_host_wiring(self) -> None:
        self.m.scaffold(self.target)
        pkg = self._import_package()
        self.assertTrue(hasattr(pkg, "compression_session"))
        self.assertTrue(hasattr(pkg, "host_env"))
        # disabled endpoint -> no override
        ep = pkg.CompressionEndpoint(token="noop")
        self.assertEqual(pkg.host_env(ep, "claude"), {})

    def test_scaffolded_host_wiring_uses_package_import_not_path_loader(self) -> None:
        self.m.scaffold(self.target)
        wiring_src = (self.target / "context_compression" / "host_wiring.py").read_text()
        self.assertIn(
            "from .context_compression_provider import CompressionError",
            wiring_src,
        )
        self.assertNotIn("host-wiring-replace-start", wiring_src)
        self.assertNotIn("spec_from_file_location", wiring_src)

    def test_headroom_import_confined_to_headroom_provider(self) -> None:
        """ADR-0021: the package imports headroom NOWHERE (proxy is subprocess-only)."""
        self.m.scaffold(self.target)
        comp = self.target / "context_compression"
        # Boundary check must be clean even with NO module importing headroom.
        checker = _load_checker()
        findings = checker.check_headroom_import_boundary(
            comp, comp / "headroom_provider.py"
        )
        self.assertEqual(findings, [])
        # And no module (including headroom_provider) imports headroom in-process.
        for f in comp.glob("*.py"):
            text = f.read_text()
            self.assertNotIn("import headroom", text)
            self.assertNotIn("from headroom", text)

    def test_security_module_has_no_headroom_import_statement(self) -> None:
        self.m.scaffold(self.target)
        sec = (self.target / "context_compression" / "security.py").read_text()
        self.assertNotIn("import headroom", sec)
        self.assertNotIn("from headroom", sec)

    def test_package_import_stays_safe_without_headroom_installed(self) -> None:
        """__init__/noop must import even though headroom is not a dev dependency."""
        self.m.scaffold(self.target)
        pkg = self._import_package()  # must not raise (no headroom import on this path)
        self.assertTrue(hasattr(pkg, "NoopContextCompressionProvider"))

    def test_idempotent_second_run_skips(self) -> None:
        self.m.scaffold(self.target)
        report = self.m.scaffold(self.target)
        self.assertEqual(report["scaffolded"], [])
        self.assertTrue(report["skipped"])

    def test_does_not_overwrite_existing_file(self) -> None:
        comp = self.target / "context_compression"
        comp.mkdir()
        sentinel = comp / "noop_provider.py"
        sentinel.write_text("# user-edited, keep me\n")
        self.m.scaffold(self.target)
        self.assertEqual(sentinel.read_text(), "# user-edited, keep me\n")

    # --- single interface identity, via the import system, both orders ---

    def test_package_import_interface_first_shares_identity(self) -> None:
        self.m.scaffold(self.target)
        self._import_package()
        iface = importlib.import_module("context_compression.context_compression_provider")
        noop = importlib.import_module("context_compression.noop_provider")
        self.assertIs(noop.CompressionEndpoint, iface.CompressionEndpoint)
        provider = noop.NoopContextCompressionProvider()
        self.assertIsInstance(provider.activate(), iface.CompressionEndpoint)

    def test_package_import_noop_first_shares_identity(self) -> None:
        self.m.scaffold(self.target)
        self._import_package()
        noop = importlib.import_module("context_compression.noop_provider")
        iface = importlib.import_module("context_compression.context_compression_provider")
        self.assertIs(noop.CompressionEndpoint, iface.CompressionEndpoint)

    def test_package_root_exports_providers(self) -> None:
        self.m.scaffold(self.target)
        pkg = self._import_package()
        self.assertTrue(hasattr(pkg, "ContextCompressionProvider"))
        provider = pkg.NoopContextCompressionProvider()
        self.assertIsInstance(provider.activate(), pkg.CompressionEndpoint)

    def test_package_name_does_not_shadow_stdlib_compression(self) -> None:
        """HIGH regression: scaffolded package must not be named `compression`."""
        self.m.scaffold(self.target)
        # The scaffolder must not emit a top-level `compression/` dir.
        self.assertFalse((self.target / "compression").exists())
        self.assertTrue((self.target / "context_compression").exists())
        pkg = self._import_package()
        self.assertEqual(pkg.__name__, "context_compression")
        self.assertTrue(pkg.__file__.startswith(str(self.target)))
        # The Python 3.14+ stdlib `compression` package, if present, must still
        # resolve to the stdlib — never to anything under our scaffold target.
        try:
            import compression as _stdlib
        except ImportError:
            return
        self.assertFalse(str(self.target) in (_stdlib.__file__ or ""))


if __name__ == "__main__":
    unittest.main()
