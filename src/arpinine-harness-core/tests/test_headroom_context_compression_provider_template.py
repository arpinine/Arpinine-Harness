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
import subprocess
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
        self.host_wiring = importlib.import_module("context_compression.host_wiring")

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

    def test_ccr_validation_allows_default_store_outside_any_git_worktree(self) -> None:
        outside_tmp = tempfile.TemporaryDirectory()
        outside = pathlib.Path(outside_tmp.name).resolve()
        prev = pathlib.Path.cwd()
        os.chdir(outside)
        self._set_fake_store_url("sqlite:///headroom.db")
        try:
            self.mod.HeadroomContextCompressionProvider()._engine_validate_configured_ccr_directory()
        finally:
            os.chdir(prev)
            outside_tmp.cleanup()

    # --- live transport seam wiring (TASK-006/TASK-012 boundary) ---

    def test_start_proxy_invokes_headroom_cli_with_loopback_port(self) -> None:
        calls = {}
        real_popen = subprocess.Popen
        mod = self.mod

        class _Proc:
            def poll(self):
                return None

            def terminate(self):
                calls["terminated"] = True

            def wait(self, timeout=None):
                calls["wait_timeout"] = timeout
                return 0

        def _fake_popen(cmd, stdout=None, stderr=None, text=None):
            calls["cmd"] = cmd
            calls["stdout"] = stdout
            calls["stderr"] = stderr
            calls["text"] = text
            return _Proc()

        subprocess.Popen = _fake_popen  # type: ignore[assignment]
        try:
            class _Provider(mod.HeadroomContextCompressionProvider):
                def _engine_pick_loopback_port(self) -> int:
                    return 8787

                def _engine_wait_for_port(self, port: int, proxy, *, timeout_s: float) -> None:
                    calls["waited_for"] = (port, timeout_s)
                    return None

            proxy, port = _Provider()._engine_start_proxy_loopback_only()
        finally:
            subprocess.Popen = real_popen  # type: ignore[assignment]

        self.assertEqual(port, 8787)
        self.assertIsNotNone(proxy)
        self.assertEqual(
            calls["cmd"],
            ["headroom", "proxy", "--host", "127.0.0.1", "--port", "8787"],
        )
        self.assertEqual(calls["waited_for"][0], 8787)

    def test_start_proxy_timeout_stops_process(self) -> None:
        calls = {"terminate": 0, "kill": 0}
        real_popen = subprocess.Popen
        mod = self.mod

        class _Proc:
            def poll(self):
                return None

            def terminate(self):
                calls["terminate"] += 1

            def kill(self):
                calls["kill"] += 1

            def wait(self, timeout=None):
                return 0

        subprocess.Popen = lambda *a, **k: _Proc()  # type: ignore[assignment]
        try:
            class _Provider(mod.HeadroomContextCompressionProvider):
                def _engine_pick_loopback_port(self) -> int:
                    return 8787

                def _engine_wait_for_port(self, port: int, proxy, *, timeout_s: float) -> None:
                    raise TimeoutError("proxy not ready")

            with self.assertRaises(TimeoutError):
                _Provider()._engine_start_proxy_loopback_only()
        finally:
            subprocess.Popen = real_popen  # type: ignore[assignment]

        self.assertEqual(calls["terminate"], 1)

    def test_deactivate_terminates_live_proxy(self) -> None:
        mod = self.mod
        calls = {"terminate": 0, "wait": 0}

        class _Proc:
            def poll(self):
                return None

            def terminate(self):
                calls["terminate"] += 1

            def wait(self, timeout=None):
                calls["wait"] += 1
                return 0

        provider = mod.HeadroomContextCompressionProvider()
        provider._proxy = _Proc()
        provider.deactivate()
        self.assertEqual(calls, {"terminate": 1, "wait": 1})
        self.assertIsNone(provider._proxy)

    def test_compression_session_uses_headroom_provider_endpoint_and_cleans_up(self) -> None:
        mod = self.mod
        events: list[str] = []

        class _Provider(mod.HeadroomContextCompressionProvider):
            def _engine_validate_configured_ccr_directory(self) -> None:
                events.append("validate")

            def _engine_start_proxy_loopback_only(self):
                events.append("start")
                return object(), 8787

            def _engine_stop_proxy(self, proxy) -> None:
                events.append("stop")

        provider = _Provider()
        with self.host_wiring.compression_session(provider, "claude") as env:
            self.assertEqual(env, {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"})
            self.assertEqual(events, ["validate", "start"])
        self.assertEqual(events, ["validate", "start", "stop"])

    # --- real readiness-loop body (_engine_wait_for_port), deterministic, no headroom ---

    def test_wait_for_port_returns_when_socket_accepts(self) -> None:
        class _AliveProc:
            def poll(self):
                return None  # still running

        calls = {"connects": 0}
        real_socket = self.mod.socket.socket

        class _FakeSocket:
            def __init__(self, *a, **k):
                pass

            def settimeout(self, timeout):
                return None

            def connect_ex(self, addr):
                calls["connects"] += 1
                return 0

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        self.mod.socket.socket = lambda *a, **k: _FakeSocket()  # type: ignore[assignment]
        try:
            self.mod.HeadroomContextCompressionProvider()._engine_wait_for_port(
                8787, _AliveProc(), timeout_s=2.0
            )
        finally:
            self.mod.socket.socket = real_socket  # type: ignore[assignment]
        self.assertEqual(calls["connects"], 1)

    def test_wait_for_port_raises_fast_if_proxy_exits_early(self) -> None:
        class _DeadProc:
            def poll(self):
                return 1  # exited before readiness

        # Unused free port; must raise on early exit WITHOUT waiting the timeout.
        with self.assertRaises(RuntimeError):
            self.mod.HeadroomContextCompressionProvider()._engine_wait_for_port(
                65535, _DeadProc(), timeout_s=5.0
            )

    def test_wait_for_port_times_out_when_nothing_listens(self) -> None:
        class _AliveProc:
            def poll(self):
                return None

        with self.assertRaises(TimeoutError):
            self.mod.HeadroomContextCompressionProvider()._engine_wait_for_port(
                65534, _AliveProc(), timeout_s=0.15
            )


if __name__ == "__main__":
    unittest.main()
