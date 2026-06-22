"""
Tests for the host-wiring template — per-host consumption of the opaque
compression endpoint + the activate/deactivate lifecycle.

Governs: specs/011-context-compression-governance (TASK-006)
ADRs: ADR-0013 (lifecycle-only), ADR-0015 (base_url used verbatim; no override
      when disabled), ADR-0019 (per-session activate/deactivate).

The wiring is engine-neutral: it depends only on the interface's
CompressionEndpoint and the provider lifecycle, never on headroom.
"""

from __future__ import annotations

import importlib.util
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


class TestHostWiring(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(WIRING.exists(), f"missing host-wiring template at {WIRING}")
        self.iface = _load(IFACE, "context_compression_provider_template")
        # host_wiring imports the interface as a sibling; preload it under the
        # name the template resolves (file-path dev loader, like noop).
        self.m = _load(WIRING, "host_wiring")
        self.Endpoint = self.iface.CompressionEndpoint

    def test_known_hosts_map_to_expected_env_vars(self) -> None:
        ep = self.Endpoint(token="t", base_url="http://127.0.0.1:8787")
        self.assertEqual(self.m.host_env(ep, "claude"), {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"})
        self.assertEqual(self.m.host_env(ep, "codex"), {"OPENAI_BASE_URL": "http://127.0.0.1:8787/v1"})
        self.assertEqual(self.m.host_env(ep, "copilot"), {"OPENAI_BASE_URL": "http://127.0.0.1:8787/v1"})

    def test_disabled_endpoint_yields_no_override(self) -> None:
        """base_url is None (noop/disabled) -> empty env -> host talks direct."""
        ep = self.Endpoint(token="noop")  # base_url defaults None
        for host in ("claude", "codex", "copilot"):
            self.assertEqual(self.m.host_env(ep, host), {})

    def test_unknown_host_raises(self) -> None:
        ep = self.Endpoint(token="t", base_url="http://127.0.0.1:8787")
        with self.assertRaises(ValueError):
            self.m.host_env(ep, "emacs")

    def test_base_url_used_verbatim_not_parsed(self) -> None:
        # An odd but provider-supplied base_url must be set as-is for claude.
        ep = self.Endpoint(token="t", base_url="http://127.0.0.1:9999")
        self.assertEqual(self.m.host_env(ep, "claude")["ANTHROPIC_BASE_URL"], "http://127.0.0.1:9999")

    def test_compression_session_activates_and_deactivates(self) -> None:
        events = []
        Endpoint = self.Endpoint

        class _Provider:
            def activate(self):
                events.append("activate")
                return Endpoint(token="t", base_url="http://127.0.0.1:8787")

            def deactivate(self):
                events.append("deactivate")

        with self.m.compression_session(_Provider(), "claude") as env:
            self.assertEqual(env, {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"})
            self.assertEqual(events, ["activate"])
        self.assertEqual(events, ["activate", "deactivate"])

    def test_compression_session_deactivates_on_exception(self) -> None:
        events = []
        Endpoint = self.Endpoint

        class _Provider:
            def activate(self):
                events.append("activate")
                return Endpoint(token="t", base_url="http://127.0.0.1:8787")

            def deactivate(self):
                events.append("deactivate")

        with self.assertRaises(RuntimeError):
            with self.m.compression_session(_Provider(), "claude"):
                raise RuntimeError("boom")
        self.assertEqual(events, ["activate", "deactivate"])  # cleaned up


if __name__ == "__main__":
    unittest.main()
