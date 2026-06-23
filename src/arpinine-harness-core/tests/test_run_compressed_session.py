"""
Tests for run_compressed_session.py — the out-of-host compression launcher
(ADR-0020, AC-008). Verifies the orchestration without a real host or headroom:
spawn + provider are injected.

Governs: specs/011-context-compression-governance (TASK-014/016)
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import unittest

MODULE = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_compressed_session.py"
)
CORE = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("run_compressed_session", MODULE)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _load_pkg_symbols():
    # CompressionError + a real CompressionEndpoint from the live package.
    import importlib

    if str(CORE) not in sys.path:
        sys.path.insert(0, str(CORE))
    iface = importlib.import_module("context_compression.context_compression_provider")
    return iface.CompressionEndpoint, iface.CompressionError


class TestRunCompressedSession(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE.exists(), f"missing {MODULE}")
        self.m = _load()
        self.Endpoint, self.Error = _load_pkg_symbols()
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        (self.repo / ".specify").mkdir()
        (self.repo / ".specify" / "CONSTITUTION.md").write_text("# C\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _enable(self, enabled: bool) -> None:
        import importlib

        if str(CORE / "scripts") not in sys.path:
            sys.path.insert(0, str(CORE / "scripts"))
        cc = importlib.import_module("compression_config")
        cc.set_compression_enabled(self.repo, enabled)

    def _spawn_recorder(self):
        captured = {}

        def spawn(argv, env, *, cwd):
            captured["argv"] = argv
            captured["env"] = env
            captured["cwd"] = pathlib.Path(cwd)
            return 0

        return spawn, captured

    def test_disabled_execs_host_directly_no_proxy(self) -> None:
        self._enable(False)
        spawn, captured = self._spawn_recorder()

        def factory():
            raise AssertionError("provider must not be built when disabled")

        rc = self.m.run_compressed_session(
            self.repo, "claude", ["claude", "--foo"], provider_factory=factory, spawn=spawn
        )
        self.assertEqual(rc, 0)
        self.assertEqual(captured["argv"], ["claude", "--foo"])
        self.assertEqual(captured["cwd"], self.repo)
        self.assertNotIn("ANTHROPIC_BASE_URL", captured["env"])

    def test_enabled_routes_host_through_proxy_and_tears_down(self) -> None:
        self._enable(True)
        spawn, captured = self._spawn_recorder()
        events = []
        Endpoint = self.Endpoint

        class _Provider:
            def activate(self):
                events.append("activate")
                return Endpoint(token="t", base_url="http://127.0.0.1:8787")

            def deactivate(self):
                events.append("deactivate")

        rc = self.m.run_compressed_session(
            self.repo, "claude", ["claude"], provider_factory=lambda repo: _Provider(), spawn=spawn
        )
        self.assertEqual(rc, 0)
        self.assertEqual(captured["cwd"], self.repo)
        self.assertEqual(captured["env"]["ANTHROPIC_BASE_URL"], "http://127.0.0.1:8787")
        self.assertEqual(events, ["activate", "deactivate"])

    def test_provider_build_failure_falls_back_to_passthrough(self) -> None:
        self._enable(True)
        spawn, captured = self._spawn_recorder()
        Error = self.Error

        def factory(repo):
            raise Error("headroom not installed")

        rc = self.m.run_compressed_session(
            self.repo, "claude", ["claude"], provider_factory=factory, spawn=spawn
        )
        self.assertEqual(rc, 0)  # host still runs
        self.assertEqual(captured["cwd"], self.repo)
        self.assertNotIn("ANTHROPIC_BASE_URL", captured["env"])  # uncompressed

    def test_activate_failure_falls_back_to_passthrough(self) -> None:
        self._enable(True)
        spawn, captured = self._spawn_recorder()
        Error = self.Error

        class _DownProvider:
            def activate(self):
                raise Error("proxy unreachable")

            def deactivate(self):
                raise AssertionError("nothing started")

        rc = self.m.run_compressed_session(
            self.repo, "claude", ["claude"], provider_factory=lambda repo: _DownProvider(), spawn=spawn
        )
        self.assertEqual(rc, 0)
        self.assertEqual(captured["cwd"], self.repo)
        self.assertNotIn("ANTHROPIC_BASE_URL", captured["env"])

    def test_returns_host_exit_code(self) -> None:
        self._enable(False)

        def spawn(argv, env, *, cwd):
            return 42

        rc = self.m.run_compressed_session(
            self.repo, "claude", ["claude"], provider_factory=lambda repo: None, spawn=spawn
        )
        self.assertEqual(rc, 42)

    def test_provider_factory_receives_repo_root(self) -> None:
        self._enable(True)
        spawn, _captured = self._spawn_recorder()
        seen = {}
        Endpoint = self.Endpoint

        class _Provider:
            def activate(self):
                return Endpoint(token="t", base_url="http://127.0.0.1:8787")

            def deactivate(self):
                return None

        def factory(repo):
            seen["repo"] = pathlib.Path(repo)
            return _Provider()

        self.m.run_compressed_session(
            self.repo, "claude", ["claude"], provider_factory=factory, spawn=spawn
        )
        self.assertEqual(seen["repo"], self.repo)

    def test_main_execs_host_directly_when_disabled(self) -> None:
        self._enable(False)
        calls = {}
        real_execvpe = os.execvpe
        real_chdir = os.chdir

        def fake_execvpe(file, argv, env):
            calls["file"] = file
            calls["argv"] = argv
            calls["env"] = env
            raise SystemExit(0)

        def fake_chdir(path):
            calls["cwd"] = pathlib.Path(path)

        os.execvpe = fake_execvpe  # type: ignore[assignment]
        os.chdir = fake_chdir  # type: ignore[assignment]
        try:
            with self.assertRaises(SystemExit):
                self.m._main(["--repo", str(self.repo), "--host", "claude", "--", "claude", "--print"])
        finally:
            os.execvpe = real_execvpe  # type: ignore[assignment]
            os.chdir = real_chdir  # type: ignore[assignment]

        self.assertEqual(calls["file"], "claude")
        self.assertEqual(calls["argv"], ["claude", "--print"])
        self.assertEqual(calls["cwd"], self.repo.resolve())


if __name__ == "__main__":
    unittest.main()
