"""
Tests for passthrough fallback + the compression_passthrough_fallback signal.

Governs: specs/011-context-compression-governance (TASK-007)
ADRs: ADR-0015 (proxy unreachable => uncompressed passthrough, never a broken or
      silently-altered session; observable WARN signal in the main output stream).
"""

from __future__ import annotations

import importlib.util
import json
import logging
import pathlib
import sys
import unittest

TEMPLATES = pathlib.Path(__file__).resolve().parents[1] / "templates"
IFACE = TEMPLATES / "context-compression-provider-template.py"
WIRING = TEMPLATES / "host-wiring-template.py"


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestEmitSignal(unittest.TestCase):
    def setUp(self) -> None:
        self.iface = _load(IFACE, "context_compression_provider_template")
        self.m = _load(WIRING, "host_wiring")

    def test_event_constant(self) -> None:
        self.assertEqual(self.m.PASSTHROUGH_FALLBACK_EVENT, "compression_passthrough_fallback")

    def test_record_has_required_fields(self) -> None:
        rec = self.m.emit_passthrough_fallback(
            reason="proxy refused connection", session_id="sess-1", now=lambda: "2026-06-22T00:00:00Z"
        )
        self.assertEqual(rec["event"], "compression_passthrough_fallback")
        self.assertEqual(rec["level"], "WARNING")
        self.assertEqual(rec["reason"], "proxy refused connection")
        self.assertEqual(rec["session_id"], "sess-1")
        self.assertEqual(rec["timestamp"], "2026-06-22T00:00:00Z")

    def test_emits_at_warning_level(self) -> None:
        with self.assertLogs("context_compression", level="WARNING") as cm:
            self.m.emit_passthrough_fallback(reason="down", session_id="s")
        self.assertTrue(any("compression_passthrough_fallback" in line for line in cm.output))

    def test_log_payload_is_json(self) -> None:
        with self.assertLogs("context_compression", level="WARNING") as cm:
            self.m.emit_passthrough_fallback(
                reason="proxy refused connection",
                session_id="sess-2",
                now=lambda: "2026-06-22T00:00:00Z",
            )
        payload = cm.output[0].split(":", 2)[-1].strip()
        record = json.loads(payload)
        self.assertEqual(record["event"], "compression_passthrough_fallback")
        self.assertEqual(record["reason"], "proxy refused connection")
        self.assertEqual(record["session_id"], "sess-2")


class TestSessionFallback(unittest.TestCase):
    def setUp(self) -> None:
        self.iface = _load(IFACE, "context_compression_provider_template")
        self.m = _load(WIRING, "host_wiring")
        self.Endpoint = self.iface.CompressionEndpoint
        self.Error = self.iface.CompressionError

    def test_activate_failure_falls_back_to_passthrough(self) -> None:
        events = []
        Error = self.Error

        class _DownProvider:
            def activate(self):
                raise Error("proxy unreachable")

            def deactivate(self):
                events.append("deactivate")

        with self.assertLogs("context_compression", level="WARNING") as cm:
            with self.m.compression_session(_DownProvider(), "claude", session_id="s1") as env:
                # passthrough: no override -> host talks direct, session continues
                self.assertEqual(env, {})
        self.assertTrue(any("compression_passthrough_fallback" in l for l in cm.output))
        # nothing was started, so deactivate must NOT be called
        self.assertEqual(events, [])

    def test_session_continues_and_body_runs_on_fallback(self) -> None:
        Error = self.Error

        class _DownProvider:
            def activate(self):
                raise Error("boom")

            def deactivate(self):
                pass

        ran = []
        with self.m.compression_session(_DownProvider(), "claude", session_id="s") as env:
            ran.append(env)
        self.assertEqual(ran, [{}])  # body executed despite proxy failure

    def test_successful_activate_does_not_emit_fallback(self) -> None:
        Endpoint = self.Endpoint
        events = []

        class _Up:
            def activate(self):
                events.append("activate")
                return Endpoint(token="t", base_url="http://127.0.0.1:8787")

            def deactivate(self):
                events.append("deactivate")

        logger = logging.getLogger("context_compression")
        with self.assertNoLogs(logger, level="WARNING") if hasattr(self, "assertNoLogs") else _noop_cm():
            with self.m.compression_session(_Up(), "claude") as env:
                self.assertEqual(env, {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"})
        self.assertEqual(events, ["activate", "deactivate"])

    def test_non_transport_activate_error_is_not_downgraded_to_fallback(self) -> None:
        class _BuggyProvider:
            def activate(self):
                raise RuntimeError("bad provider state")

            def deactivate(self):
                raise AssertionError("deactivate must not run when activate failed")

        with self.assertRaises(RuntimeError):
            with self.m.compression_session(_BuggyProvider(), "claude", session_id="s-bug"):
                pass


class _noop_cm:
    def __enter__(self): return self
    def __exit__(self, *a): return False


if __name__ == "__main__":
    unittest.main()
