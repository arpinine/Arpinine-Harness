"""
Tests for the compression-security helper template — the headroom-free,
security-critical logic the headroom provider depends on.

Governs: specs/011-context-compression-governance (TASK-002)
ADRs: ADR-0014 (credential scrubbing before any log path), ADR-0018 (engine-owned
      CCR directory policy; harness store retired under Option A).

These helpers contain NO headroom import so they are unit-testable without the
SDK installed and are reused by both the headroom provider and the check script.
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
    / "templates"
    / "compression-security-template.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("compression_security", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestScrubCredentials(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.exists(), f"missing template at {MODULE_PATH}")
        self.m = _load()

    def test_masks_known_credential_headers_case_insensitively(self) -> None:
        headers = {
            "Authorization": "Bearer sk-secret",
            "X-Api-Key": "abc123",
            "Cookie": "session=xyz",
            "Content-Type": "application/json",
        }
        scrubbed = self.m.scrub_credentials(headers)
        self.assertEqual(scrubbed["Authorization"], self.m.REDACTED)
        self.assertEqual(scrubbed["X-Api-Key"], self.m.REDACTED)
        self.assertEqual(scrubbed["Cookie"], self.m.REDACTED)
        self.assertEqual(scrubbed["Content-Type"], "application/json")

    def test_lowercase_header_variants_masked(self) -> None:
        scrubbed = self.m.scrub_credentials({"authorization": "x", "x-api-key": "y"})
        self.assertEqual(scrubbed["authorization"], self.m.REDACTED)
        self.assertEqual(scrubbed["x-api-key"], self.m.REDACTED)

    def test_does_not_mutate_input(self) -> None:
        original = {"Authorization": "Bearer s"}
        self.m.scrub_credentials(original)
        self.assertEqual(original["Authorization"], "Bearer s")

    def test_no_credential_string_survives(self) -> None:
        scrubbed = self.m.scrub_credentials({"Authorization": "Bearer sk-LEAK"})
        self.assertNotIn("sk-LEAK", "".join(map(str, scrubbed.values())))


class TestScrubBytes(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()

    def test_redacts_authorization_header_in_bytes(self) -> None:
        out = self.m.scrub_bytes(b"GET /\r\nAuthorization: Bearer sk-LEAK\r\n\r\n")
        self.assertNotIn(b"sk-LEAK", out)
        self.assertIn(b"Authorization:", out)

    def test_redacts_x_api_key_and_cookie_headers(self) -> None:
        out = self.m.scrub_bytes(b"x-api-key: abc-SECRET\nCookie: session=TOPSECRET\n")
        self.assertNotIn(b"abc-SECRET", out)
        self.assertNotIn(b"TOPSECRET", out)

    def test_redacts_json_credential_values(self) -> None:
        out = self.m.scrub_bytes(b'{"api_key": "sk-JSONLEAK", "authorization": "Bearer X"}')
        self.assertNotIn(b"sk-JSONLEAK", out)
        self.assertNotIn(b"Bearer X", out)

    def test_clean_bytes_unchanged(self) -> None:
        data = b'{"role":"user","content":"hello world"}'
        self.assertEqual(self.m.scrub_bytes(data), data)

    def test_returns_bytes(self) -> None:
        self.assertIsInstance(self.m.scrub_bytes(b"Authorization: x"), bytes)


class TestCcrRetired(unittest.TestCase):
    """Option A: the harness no longer ships a CCR store — headroom owns it."""

    def setUp(self) -> None:
        self.m = _load()

    def test_store_helpers_are_gone(self) -> None:
        for removed in ("store_original", "read_original", "ensure_ccr_store"):
            self.assertFalse(hasattr(self.m, removed), f"{removed} should be retired")


if __name__ == "__main__":
    unittest.main()
