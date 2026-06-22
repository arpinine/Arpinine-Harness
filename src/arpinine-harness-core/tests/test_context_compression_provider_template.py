"""
Contract tests for the ContextCompressionProvider interface template.

Governs: specs/011-context-compression-governance (TASK-001, Option A)
ADRs: ADR-0013 (amended — lifecycle-only: activate/deactivate; no harness-driven
      compress/retrieve), ADR-0015 (opaque endpoint, no raw port).
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

TEMPLATE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "templates"
    / "context-compression-provider-template.py"
)


def _load_template():
    spec = importlib.util.spec_from_file_location(
        "context_compression_provider_template", TEMPLATE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestContextCompressionProviderTemplate(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(TEMPLATE_PATH.exists(), f"interface template missing at {TEMPLATE_PATH}")
        self.mod = _load_template()

    def test_exports_protocol_and_types(self) -> None:
        for name in ("ContextCompressionProvider", "CompressionEndpoint", "CompressionError"):
            self.assertTrue(hasattr(self.mod, name), f"missing {name}")

    def test_interface_is_lifecycle_only(self) -> None:
        provider = self.mod.ContextCompressionProvider
        for required in ("activate", "deactivate"):
            self.assertTrue(hasattr(provider, required), f"interface missing {required}()")
        # Option A: per-payload compress/retrieve are NOT on the harness interface.
        for removed in ("compress", "retrieve"):
            self.assertFalse(
                hasattr(provider, removed),
                f"interface must not expose harness-driven {removed}() under Option A",
            )

    def test_no_transport_detail_leaks_in_method_names(self) -> None:
        provider = self.mod.ContextCompressionProvider
        for forbidden in ("start_proxy", "stop_proxy", "get_port"):
            self.assertFalse(hasattr(provider, forbidden), f"leaks transport: {forbidden}")

    def test_endpoint_is_opaque_no_raw_network_coordinates(self) -> None:
        import dataclasses

        fields = {f.name for f in dataclasses.fields(self.mod.CompressionEndpoint)}
        self.assertIn("token", fields)
        for leaked in ("port", "host", "address"):
            self.assertNotIn(leaked, fields)

    def test_lifecycle_only_impl_satisfies_protocol(self) -> None:
        mod = self.mod

        class _Lifecycle:
            def activate(self) -> "mod.CompressionEndpoint":
                return mod.CompressionEndpoint(token="x")

            def deactivate(self) -> None:
                return None

        self.assertIsInstance(_Lifecycle(), mod.ContextCompressionProvider)


if __name__ == "__main__":
    unittest.main()
