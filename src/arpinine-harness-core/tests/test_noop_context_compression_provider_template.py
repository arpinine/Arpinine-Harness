"""
Tests for the noop ContextCompressionProvider implementation template.

Governs: specs/011-context-compression-governance (TASK-003)
ADRs: ADR-0013 (noop satisfies the interface, starts no process),
      ADR-0016 (the disabled path uses noop — zero overhead, no proxy).

The noop provider is the disabled-compression path: it must satisfy the
interface, pass payloads through byte-for-byte, start no process, and open
no socket.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

TEMPLATES = pathlib.Path(__file__).resolve().parents[1] / "templates"
INTERFACE_PATH = TEMPLATES / "context-compression-provider-template.py"
NOOP_PATH = TEMPLATES / "noop-context-compression-provider-template.py"


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestNoopContextCompressionProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(NOOP_PATH.exists(), f"noop template missing at {NOOP_PATH}")
        self.iface = _load(INTERFACE_PATH, "context_compression_provider_template")
        self.mod = _load(NOOP_PATH, "noop_context_compression_provider_template")
        self.provider = self.mod.NoopContextCompressionProvider()

    def test_satisfies_protocol(self) -> None:
        self.assertIsInstance(
            self.provider, self.iface.ContextCompressionProvider
        )

    def test_compress_is_byte_identical_passthrough(self) -> None:
        payload = b'{"role":"user","content":"hello"}'
        result = self.provider.compress(payload)
        self.assertEqual(result.payload, payload)
        self.assertEqual(result.original_bytes, len(payload))

    def test_compress_yields_no_segments(self) -> None:
        result = self.provider.compress(b"anything")
        self.assertEqual(result.segment_keys, [])

    def test_activate_returns_opaque_endpoint_without_starting_anything(self) -> None:
        endpoint = self.provider.activate()
        self.assertIsInstance(endpoint, self.iface.CompressionEndpoint)
        self.assertTrue(endpoint.token)
        # No raw network coordinates leaked through metadata.
        for leaked in ("port", "host", "address"):
            self.assertNotIn(leaked, endpoint.metadata)

    def test_deactivate_is_idempotent(self) -> None:
        self.assertIsNone(self.provider.deactivate())
        self.assertIsNone(self.provider.deactivate())

    def test_retrieve_raises_keyerror_since_nothing_is_stored(self) -> None:
        with self.assertRaises(KeyError):
            self.provider.retrieve("any-key")

    def test_starts_no_subprocess_and_opens_no_socket(self) -> None:
        """ADR-0016: disabled path must impose zero overhead — no proxy/socket."""
        import socket
        import subprocess

        real_popen = subprocess.Popen
        real_socket = socket.socket
        calls = {"popen": 0, "socket": 0}

        def _spy_popen(*a, **k):
            calls["popen"] += 1
            return real_popen(*a, **k)

        def _spy_socket(*a, **k):
            calls["socket"] += 1
            return real_socket(*a, **k)

        subprocess.Popen = _spy_popen  # type: ignore[assignment]
        socket.socket = _spy_socket  # type: ignore[assignment]
        try:
            ep = self.provider.activate()
            self.provider.compress(b"payload")
            self.provider.deactivate()
            _ = ep
        finally:
            subprocess.Popen = real_popen  # type: ignore[assignment]
            socket.socket = real_socket  # type: ignore[assignment]

        self.assertEqual(calls["popen"], 0, "noop must not start a subprocess")
        self.assertEqual(calls["socket"], 0, "noop must not open a socket")


if __name__ == "__main__":
    unittest.main()
