"""
Tests for the headroom provider — zero-config provisioning + proxy lifecycle
(ADR-0018/0019/0020/0021). No real headroom, venv, or proxy: the engine seams
and installer are injected / monkeypatched.

Governs: specs/011-context-compression-governance (TASK-019/020)
"""

from __future__ import annotations

import importlib
import pathlib
import socket
import stat
import subprocess
import sys
import tempfile
import unittest

CORE = pathlib.Path(__file__).resolve().parents[1]


def _load():
    if str(CORE) not in sys.path:
        sys.path.insert(0, str(CORE))
    for m in [x for x in sys.modules if x.startswith("context_compression")]:
        del sys.modules[m]
    pkg = importlib.import_module("context_compression")
    mod = importlib.import_module("context_compression.headroom_provider")
    return pkg, mod


class TestZeroConfigProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.pkg, self.mod = _load()
        self.Provider = self.mod.HeadroomContextCompressionProvider
        self.Error = self.pkg.CompressionError
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_activate_orders_store_then_headroom_then_proxy(self) -> None:
        order = []

        class _P(self.Provider):
            def _engine_prepare_ccr_store(self):
                order.append("store"); return pathlib.Path("/x/headroom.db")
            def _engine_ensure_headroom(self):
                order.append("headroom"); return pathlib.Path("/x/bin/headroom")
            def _engine_start_proxy_loopback_only(self, hb, db):
                order.append("proxy"); return object(), 8787

        ep = _P().activate()
        self.assertEqual(order, ["store", "headroom", "proxy"])
        self.assertEqual(ep.base_url, "http://127.0.0.1:8787")

    # #2 provider-owned CCR store
    def test_prepare_ccr_store_creates_700_and_returns_db(self) -> None:
        store = self.tmp / "ccr-store"
        db = self.Provider(ccr_store=store)._engine_prepare_ccr_store()
        self.assertEqual(db, store.resolve() / "headroom.db")
        self.assertTrue(store.exists())
        self.assertEqual(stat.S_IMODE(store.stat().st_mode), 0o700)

    def test_prepare_ccr_store_rejects_store_in_worktree(self) -> None:
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        with self.assertRaises(self.Error):
            self.Provider(repo_root=repo, ccr_store=repo / "ccr")._engine_prepare_ccr_store()

    # #1 managed venv bootstrap
    def test_ensure_headroom_returns_existing_without_installing(self) -> None:
        venv = self.tmp / "venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "headroom").write_text("#!/bin/sh\n")
        self.mod.MANAGED_VENV = venv
        called = {"n": 0}
        p = self.Provider(installer=lambda *a: called.__setitem__("n", called["n"] + 1))
        self.assertEqual(p._engine_ensure_headroom(), venv / "bin" / "headroom")
        self.assertEqual(called["n"], 0)

    def test_ensure_headroom_invokes_installer_when_absent(self) -> None:
        venv = self.tmp / "venv2"
        self.mod.MANAGED_VENV = venv
        seen = {}

        def installer(vdir, pin):
            seen["vdir"], seen["pin"] = vdir, pin
            (vdir / "bin").mkdir(parents=True)
            (vdir / "bin" / "headroom").write_text("#!/bin/sh\n")

        self.assertEqual(self.Provider(installer=installer)._engine_ensure_headroom(), venv / "bin" / "headroom")
        self.assertEqual(seen["vdir"], venv)
        self.assertIn("headroom-ai[proxy]==0.27.0", seen["pin"])

    def test_ensure_headroom_raises_if_installer_produces_no_binary(self) -> None:
        self.mod.MANAGED_VENV = self.tmp / "venv3"
        with self.assertRaises(self.Error):
            self.Provider(installer=lambda *a: None)._engine_ensure_headroom()

    # proxy start: CLI + store env
    def test_start_proxy_uses_venv_bin_and_sets_store_env(self) -> None:
        captured = {}
        real_popen = subprocess.Popen

        class _Proc:
            def poll(self): return None

        def fake_popen(cmd, stdout=None, stderr=None, env=None, text=None):
            captured["cmd"] = cmd; captured["env"] = env; return _Proc()

        subprocess.Popen = fake_popen  # type: ignore[assignment]
        try:
            class _P(self.Provider):
                def _engine_pick_loopback_port(self): return 8787
                def _engine_wait_for_port(self, port, proxy, *, timeout_s): return None
            _P()._engine_start_proxy_loopback_only(pathlib.Path("/v/bin/headroom"), pathlib.Path("/s/h.db"))
        finally:
            subprocess.Popen = real_popen  # type: ignore[assignment]

        self.assertEqual(captured["cmd"], ["/v/bin/headroom", "proxy", "--host", "127.0.0.1", "--port", "8787"])
        self.assertEqual(captured["env"][self.mod.STORE_ENV], "sqlite:////s/h.db")

    # readiness loop body
    def test_wait_for_port_returns_when_socket_accepts(self) -> None:
        class _Alive:
            def poll(self): return None
        lis = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lis.bind(("127.0.0.1", 0)); lis.listen(1); port = lis.getsockname()[1]
        try:
            self.Provider()._engine_wait_for_port(port, _Alive(), timeout_s=2.0)
        finally:
            lis.close()

    def test_wait_for_port_raises_fast_on_early_exit(self) -> None:
        class _Dead:
            def poll(self): return 1
        with self.assertRaises(RuntimeError):
            self.Provider()._engine_wait_for_port(65535, _Dead(), timeout_s=5.0)

    def test_wait_for_port_times_out(self) -> None:
        class _Alive:
            def poll(self): return None
        with self.assertRaises(TimeoutError):
            self.Provider()._engine_wait_for_port(65534, _Alive(), timeout_s=0.1)

    def test_deactivate_terminates_proxy(self) -> None:
        calls = {"t": 0, "w": 0}
        class _Proc:
            def poll(self): return None
            def terminate(self): calls["t"] += 1
            def wait(self, timeout=None): calls["w"] += 1; return 0
        p = self.Provider(); p._proxy = _Proc(); p.deactivate()
        self.assertEqual(calls, {"t": 1, "w": 1})
        self.assertIsNone(p._proxy)

    def test_compression_session_e2e(self) -> None:
        hw = importlib.import_module("context_compression.host_wiring")
        Endpoint = importlib.import_module(
            "context_compression.context_compression_provider"
        ).CompressionEndpoint
        events = []

        class _P:
            def activate(self):
                events.append("a"); return Endpoint(token="t", base_url="http://127.0.0.1:8787")
            def deactivate(self):
                events.append("d")

        with hw.compression_session(_P(), "claude") as env:
            self.assertEqual(env, {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"})
        self.assertEqual(events, ["a", "d"])


if __name__ == "__main__":
    unittest.main()
