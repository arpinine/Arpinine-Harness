#!/usr/bin/env python3
"""
run_compressed_session.py — the out-of-host compression launcher (ADR-0020,
AC-008). The harness-provided entry point that makes context compression LIVE.

A plugin running inside a host cannot repoint its own session, so this runs
*around* the host: start the local headroom proxy, launch the host pointed at it
via the host base-URL env, then tear the proxy down on exit.

    run_compressed_session.py --repo <root> --host claude -- claude [args...]

Behavior (ADR-0015/0016/0019/0020):
  - compression disabled (constitution toggle) -> exec the host directly, no proxy,
    behavior identical to launching the host yourself.
  - enabled -> validate CCR dir + activate proxy -> set the host base-URL env ->
    spawn host (inherit stdio/tty) -> deactivate on exit.
  - provider unavailable (e.g. headroom not installed) or proxy unreachable ->
    uncompressed passthrough + a `compression_passthrough_fallback` signal. The
    host ALWAYS runs.

Returns the host's exit code.

Governs: specs/011-context-compression-governance (TASK-014).
"""

from __future__ import annotations

import argparse
import os
import pathlib
import signal
import subprocess
import sys
import uuid

_CORE_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCRIPTS = _CORE_ROOT / "scripts"
for _p in (str(_CORE_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from compression_config import read_compression_enabled  # noqa: E402


def _load_pkg():
    """Import the live context_compression package (host_wiring + interface)."""
    import importlib

    host_wiring = importlib.import_module("context_compression.host_wiring")
    iface = importlib.import_module("context_compression.context_compression_provider")
    return host_wiring, iface


def _default_provider_factory(repo):
    """
    Build the default (headroom) provider from the live package. Importing it
    pulls in `headroom`; if that is missing, raise CompressionError so the caller
    degrades to passthrough rather than crashing.
    """
    import importlib

    _, iface = _load_pkg()
    try:
        hp = importlib.import_module("context_compression.headroom_provider")
    except Exception as exc:  # headroom not installed / import error
        raise iface.CompressionError("headroom provider unavailable") from exc
    return hp.HeadroomContextCompressionProvider(repo_root=repo)


def _default_spawn(argv: list[str], env: dict, *, cwd: pathlib.Path) -> int:
    """
    Spawn the host, inheriting stdio/tty for an interactive session and
    forwarding termination signals to the child process group.
    """
    proc = subprocess.Popen(argv, env=env, cwd=str(cwd), start_new_session=True)
    previous_handlers: dict[int, object] = {}

    def _forward(signum, _frame) -> None:
        if proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, signum)
        except ProcessLookupError:
            return

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, _forward)
        return proc.wait()
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)


def _exec_host_direct(argv: list[str], env: dict, *, cwd: pathlib.Path) -> None:
    """Replace the launcher with the host process for the disabled direct path."""
    os.chdir(cwd)
    os.execvpe(argv[0], argv, env)


def run_compressed_session(
    repo,
    host: str,
    host_argv: list[str],
    *,
    provider_factory=_default_provider_factory,
    spawn=_default_spawn,
) -> int:
    """Orchestrate one compressed (or passthrough/direct) host session. Returns exit code."""
    repo = pathlib.Path(repo)
    base_env = dict(os.environ)

    if not read_compression_enabled(repo):
        return spawn(host_argv, base_env, cwd=repo)  # disabled: direct, no proxy

    host_wiring, _iface = _load_pkg()
    # Provider construction can fail (e.g. headroom missing) -> passthrough.
    try:
        provider = provider_factory(repo)
    except Exception as exc:
        host_wiring.emit_passthrough_fallback(
            reason=f"provider unavailable: {exc}", session_id=uuid.uuid4().hex
        )
        return spawn(host_argv, base_env, cwd=repo)

    # compression_session handles activate-failure internally (yields {} env +
    # emits the fallback signal), so passthrough is covered there too.
    with host_wiring.compression_session(provider, host) as comp_env:
        return spawn(host_argv, {**base_env, **comp_env}, cwd=repo)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Launch a host session through the compression proxy (or direct when disabled).",
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--host", required=True, choices=("claude", "codex", "copilot"))
    parser.add_argument("host_argv", nargs=argparse.REMAINDER,
                        help="-- <host command and args> (the host to launch)")
    args = parser.parse_args(argv)

    host_argv = args.host_argv
    if host_argv and host_argv[0] == "--":
        host_argv = host_argv[1:]
    if not host_argv:
        parser.error("provide the host command after `--`, e.g. --host claude -- claude")

    repo = pathlib.Path(args.repo).resolve()
    if not read_compression_enabled(repo):
        _exec_host_direct(host_argv, dict(os.environ), cwd=repo)
    return run_compressed_session(repo, args.host, host_argv)


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
