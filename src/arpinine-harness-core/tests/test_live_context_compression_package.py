"""
The live `context_compression` package — materialized in the plugin so the
launcher (run_compressed_session.py) can import it at runtime, not just scaffold
it into a product.

Governs: specs/011-context-compression-governance (TASK-013, ADR-0020)

It is GENERATED from the tested templates via scaffold_compression_setup.py, so a
drift guard asserts the committed package stays byte-identical to scaffolder output
(no hand-edited divergence).
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

CORE = pathlib.Path(__file__).resolve().parents[1]
LIVE_PKG = CORE / "context_compression"
SCAFFOLDER = CORE / "scripts" / "scaffold_compression_setup.py"


def _load_scaffolder():
    spec = importlib.util.spec_from_file_location("scaffold_compression_setup", SCAFFOLDER)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


class TestLiveContextCompressionPackage(unittest.TestCase):
    def test_live_package_exists_with_expected_modules(self) -> None:
        self.assertTrue((LIVE_PKG / "__init__.py").exists(), f"missing live package at {LIVE_PKG}")
        for f in (
            "context_compression_provider.py",
            "noop_provider.py",
            "host_wiring.py",
            "security.py",
            "headroom_provider.py",
        ):
            self.assertTrue((LIVE_PKG / f).exists(), f"missing {f}")

    def test_live_package_imports_and_exposes_api(self) -> None:
        # Subprocess with CORE on the path -> clean import, no headroom needed
        # (headroom_provider is not imported by __init__).
        code = (
            "import context_compression as c; "
            "assert hasattr(c, 'ContextCompressionProvider'); "
            "assert hasattr(c, 'NoopContextCompressionProvider'); "
            "assert hasattr(c, 'host_env'); "
            "assert hasattr(c, 'compression_session'); "
            "p=c.NoopContextCompressionProvider(); "
            "assert p.activate().token; "
            "print('ok')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=str(CORE), capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)

    def test_live_package_matches_scaffolder_output(self) -> None:
        """Drift guard: committed live package == freshly scaffolded output."""
        m = _load_scaffolder()
        with tempfile.TemporaryDirectory() as tmp:
            m.scaffold(pathlib.Path(tmp))
            generated = pathlib.Path(tmp) / "context_compression"
            gen_files = {p.name for p in generated.glob("*.py")}
            live_files = {p.name for p in LIVE_PKG.glob("*.py")}
            self.assertEqual(gen_files, live_files, "live package file set drifted from scaffolder")
            for name in gen_files:
                self.assertEqual(
                    (LIVE_PKG / name).read_text(),
                    (generated / name).read_text(),
                    f"{name} drifted from scaffolder output — regenerate the live package",
                )


if __name__ == "__main__":
    unittest.main()
