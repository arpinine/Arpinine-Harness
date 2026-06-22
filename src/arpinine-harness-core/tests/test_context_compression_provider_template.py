"""
Contract tests for the ContextCompressionProvider interface template.

Governs: specs/011-context-compression-governance (TASK-001)
ADRs: ADR-0013 (abstraction + segment-key + neutral lifecycle naming),
      ADR-0015 (opaque endpoint, no raw port), ADR-0017 (data-boundary preservation).

The template is loaded by file path because templates/ is not an importable
package; this mirrors how the templates are consumed (scaffolded, not imported).
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
    # Register before exec so dataclass / runtime_checkable Protocol introspection
    # (get_type_hints) can resolve the module by name.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestContextCompressionProviderTemplate(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            TEMPLATE_PATH.exists(),
            f"interface template missing at {TEMPLATE_PATH}",
        )
        self.mod = _load_template()

    def test_exports_runtime_checkable_protocol(self) -> None:
        provider = getattr(self.mod, "ContextCompressionProvider", None)
        self.assertIsNotNone(provider, "ContextCompressionProvider not exported")

    def test_required_dataclasses_exist(self) -> None:
        for name in ("CompressionResult", "CompressionEndpoint"):
            self.assertTrue(hasattr(self.mod, name), f"missing dataclass {name}")

    def test_neutral_lifecycle_method_names(self) -> None:
        """ADR-0013: vendor/transport-neutral names; no proxy/port/start_proxy."""
        provider = self.mod.ContextCompressionProvider
        for required in ("compress", "retrieve", "activate", "deactivate"):
            self.assertTrue(
                hasattr(provider, required), f"interface missing {required}()"
            )
        for forbidden in ("start_proxy", "stop_proxy", "get_port"):
            self.assertFalse(
                hasattr(provider, forbidden),
                f"interface leaks transport detail: {forbidden}()",
            )

    def test_endpoint_is_opaque_no_raw_network_coordinates(self) -> None:
        """ADR-0015: host wiring gets an opaque token, never raw port/address."""
        import dataclasses

        fields = {f.name for f in dataclasses.fields(self.mod.CompressionEndpoint)}
        self.assertIn("token", fields)
        self.assertNotIn("port", fields)
        self.assertNotIn("host", fields)
        self.assertNotIn("address", fields)

    def test_noop_implementation_satisfies_protocol(self) -> None:
        """ADR-0013: a no-op impl must satisfy the interface without a proxy."""
        mod = self.mod

        class _Noop:
            def activate(self) -> "mod.CompressionEndpoint":
                return mod.CompressionEndpoint(token="noop")

            def deactivate(self) -> None:
                return None

            def compress(self, payload: bytes) -> "mod.CompressionResult":
                return mod.CompressionResult(
                    payload=payload, segment_keys=[], original_bytes=len(payload)
                )

            def retrieve(self, segment_key: str) -> bytes:
                raise KeyError(segment_key)

        self.assertIsInstance(_Noop(), mod.ContextCompressionProvider)


if __name__ == "__main__":
    unittest.main()
