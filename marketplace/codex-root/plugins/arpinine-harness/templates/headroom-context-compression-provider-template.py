"""
HeadroomContextCompressionProvider — the default ContextCompressionProvider.

Scaffolded into the product package as `context_compression/headroom_provider.py`.
Proxy-only + zero-config (ADR-0013 Option A / ADR-0015 / ADR-0021): `activate()`
self-provisions a managed venv with the pinned headroom, sets+creates a safe CCR
store, starts a loopback `headroom proxy` SUBPROCESS, and returns an opaque
endpoint the host routes its provider calls through. `deactivate()` stops it.

This module imports headroom **nowhere** — the proxy is purely a subprocess from a
managed venv, so the host's own Python never needs headroom installed (ADR-0021).
The benchmark's `headroom-simulate` engine imports headroom in its own module.

Security (ADR-0014 / ADR-0018 / NFR-001):
  - proxy binds to loopback (127.0.0.1) only — no third-party egress
  - headroom is pinned and isolated in `~/.arpinine/compression-venv`
  - the CCR store is provider-owned at `~/.arpinine/ccr-store` (700), created and
    validated (no worktree / no cloud-sync) before the proxy starts

Lifecycle is per-session (ADR-0019). Bootstrap seams (`_engine_*`) are injectable
so they are unit-tested without running real pip or starting a real proxy; a true
live run still needs network on first provision (documented live-smoke).

Governs: specs/011-context-compression-governance (TASK-002/019/020).
"""

from __future__ import annotations

import logging
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import hashlib

from .context_compression_provider import CompressionEndpoint, CompressionError

logger = logging.getLogger(__name__)

PROXY_HOST = "127.0.0.1"
# Cold start loads tokenizers/ML, so first boot can take well over a few seconds
# (live-smoke: 5s spuriously fell back to passthrough on a fresh venv; warm starts
# are sub-second). Generous timeout avoids a false first-run passthrough.
PROXY_READY_TIMEOUT_S = 30.0
PROXY_POLL_INTERVAL_S = 0.05

# ADR-0021: provider-managed, zero-config locations under the user home.
MANAGED_VENV = pathlib.Path.home() / ".arpinine" / "compression-venv"
MANAGED_CCR_STORE = pathlib.Path.home() / ".arpinine" / "ccr-store"
HEADROOM_PIN = "headroom-ai[proxy]==0.27.0"
# Per-platform wheel SHA256s, sourced from PyPI's published digests for the pin
# (same trust model as `pip --require-hashes`). headroom ships posix wheels only.
# To support a new platform, add its wheel filename + PyPI sha256 here.
HEADROOM_VERIFIED_ARTIFACTS = {
    "headroom_ai-0.27.0-cp310-abi3-macosx_11_0_arm64.whl":
        "00b54b70533c841f4702fffaf215eff84bafed7612c07a56d675ef8a1ffab543",
    "headroom_ai-0.27.0-cp310-abi3-manylinux_2_28_aarch64.whl":
        "f8fa150061db2513e8584d2e4b50af930131bcfe301080f297464b351a03f577",
    "headroom_ai-0.27.0-cp310-abi3-manylinux_2_28_x86_64.whl":
        "640e67a41743265376582a92691a192a8c2448ef0b2167a0e14a2a458adbe2dd",
}
# Env var the proxy subprocess reads for its CCR/store location.
STORE_ENV = "HEADROOM_DATABASE_URL"

# ADR-0018: the CCR store must not live inside the git worktree or under a
# cloud-sync path (governed content would be committed / leave the machine).
_CLOUD_SYNC_RELATIVE_PREFIXES = (
    "Library/Mobile Documents", "Dropbox", "OneDrive", "Google Drive", "Documents", "Desktop",
)


def _git_worktree_root(start: pathlib.Path) -> pathlib.Path | None:
    """Enclosing git worktree root for `start`, or None when no `.git` ancestor."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


class HeadroomContextCompressionProvider:
    """
    Default provider backed by a local `headroom proxy` subprocess. Lifecycle-only
    (ADR-0013): activate -> opaque endpoint, deactivate -> stop. Self-provisioning
    (ADR-0021): managed venv + owned CCR store, no operator setup.
    """

    def __init__(
        self,
        *,
        repo_root: pathlib.Path | str | None = None,
        ccr_store: pathlib.Path | str | None = None,
        installer=None,
    ) -> None:
        self._repo_root = pathlib.Path(repo_root).resolve() if repo_root else None
        self._ccr_store = pathlib.Path(ccr_store) if ccr_store else MANAGED_CCR_STORE
        self._installer = installer  # injectable: ensure venv + pinned headroom
        self._proxy = None

    # --- lifecycle ---

    def activate(self) -> CompressionEndpoint:
        try:
            store_db = self._engine_prepare_ccr_store()       # #2: own + create + validate
            headroom_bin = self._engine_ensure_headroom()     # #1: managed venv + pinned install
            self._proxy, port = self._engine_start_proxy_loopback_only(headroom_bin, store_db)
        except CompressionError:
            raise
        except Exception as exc:  # never leak internals into the message
            raise CompressionError("failed to start headroom proxy") from exc
        return CompressionEndpoint(
            token=f"headroom://session/{port}",
            base_url=f"http://{PROXY_HOST}:{port}",
            metadata={"engine": "headroom"},
        )

    def deactivate(self) -> None:
        if self._proxy is not None:
            self._engine_stop_proxy(self._proxy)
            self._proxy = None

    # ============ engine seams (the only OS / headroom touch points) ============

    def _engine_prepare_ccr_store(self) -> pathlib.Path:
        """
        #2 (ADR-0021/0018): own a safe CCR store. Reject an unsafe location (inside
        the git worktree or under a cloud-sync path), create the store dir 700, and
        return the sqlite db path. No operator config; an explicit `ccr_store`
        override is validated the same way.
        """
        store_dir = self._ccr_store.resolve()
        worktree = _git_worktree_root(self._repo_root or pathlib.Path.cwd())
        if worktree is not None and (store_dir == worktree or worktree in store_dir.parents):
            raise CompressionError(f"CCR store {store_dir} is inside the git worktree (ADR-0018)")
        home = pathlib.Path.home().resolve()
        for rel in _CLOUD_SYNC_RELATIVE_PREFIXES:
            prefix = (home / rel).resolve()
            if store_dir == prefix or prefix in store_dir.parents:
                raise CompressionError(f"CCR store {store_dir} is under cloud-sync path {rel} (ADR-0018)")
        store_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(store_dir, 0o700)
        db_path = store_dir / "headroom.db"
        db_path.touch(exist_ok=True)
        os.chmod(db_path, 0o600)
        return db_path

    def _engine_ensure_headroom(self) -> pathlib.Path:
        """
        #1 (ADR-0021): ensure the managed venv has the pinned headroom and return
        its `headroom` executable. Idempotent — skipped if present. The create+install
        is delegated to an injectable installer (default: `python -m venv` + pinned
        `pip install`) so tests don't hit network.
        """
        bin_path = MANAGED_VENV / "bin" / "headroom"
        if bin_path.exists():
            return bin_path
        installer = self._installer or _default_installer
        installer(MANAGED_VENV, HEADROOM_PIN)
        if not bin_path.exists():
            raise CompressionError(f"managed headroom venv missing executable at {bin_path}")
        return bin_path

    def _engine_start_proxy_loopback_only(self, headroom_bin, store_db):
        """Start `<venv>/headroom proxy --host 127.0.0.1 --port <p>` bound to loopback."""
        port = self._engine_pick_loopback_port()
        env = dict(os.environ)
        env[STORE_ENV] = f"sqlite:///{store_db}"
        proxy = subprocess.Popen(
            [str(headroom_bin), "proxy", "--host", PROXY_HOST, "--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            text=True,
            preexec_fn=lambda: os.umask(0o077),
        )
        try:
            self._engine_wait_for_port(port, proxy, timeout_s=PROXY_READY_TIMEOUT_S)
        except Exception:
            self._engine_stop_proxy(proxy)
            raise
        return proxy, port

    def _engine_stop_proxy(self, proxy) -> None:
        if proxy is None or proxy.poll() is not None:
            return None
        proxy.terminate()
        try:
            proxy.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proxy.kill()
            proxy.wait(timeout=2.0)
        return None

    def _engine_pick_loopback_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((PROXY_HOST, 0))
            return int(sock.getsockname()[1])

    def _engine_wait_for_port(self, port: int, proxy, *, timeout_s: float) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if proxy.poll() is not None:
                raise RuntimeError(f"headroom proxy exited before readiness on port {port}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(PROXY_POLL_INTERVAL_S)
                if sock.connect_ex((PROXY_HOST, port)) == 0:
                    return None
            time.sleep(PROXY_POLL_INTERVAL_S)
        raise TimeoutError(f"headroom proxy readiness timed out on port {port}")


def _default_installer(venv_dir: pathlib.Path, pin: str) -> None:
    """Create the managed venv (if absent) and install a hash-verified headroom wheel."""
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    if not (venv_dir / "bin" / "python").exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    python_bin = venv_dir / "bin" / "python"
    with tempfile.TemporaryDirectory(prefix="arpinine-headroom-") as tmp:
        download_dir = pathlib.Path(tmp)
        subprocess.run(
            [
                str(python_bin),
                "-m",
                "pip",
                "download",
                "--quiet",
                "--only-binary=:all:",
                "--no-deps",
                "--dest",
                str(download_dir),
                pin,
            ],
            check=True,
        )
        artifacts = sorted(download_dir.iterdir())
        if len(artifacts) != 1:
            raise CompressionError(
                f"expected exactly one headroom artifact, found {len(artifacts)}"
            )
        artifact = artifacts[0]
        expected_hash = HEADROOM_VERIFIED_ARTIFACTS.get(artifact.name)
        if expected_hash is None:
            raise CompressionError(
                f"unverified headroom artifact {artifact.name}; add its SHA256 to the allowlist"
            )
        actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise CompressionError(
                f"headroom artifact hash mismatch for {artifact.name}"
            )
        # Install the hash-verified headroom wheel itself with --no-deps (the
        # security-critical, full-traffic-visibility package is pinned + verified)...
        subprocess.run(
            [str(python_bin), "-m", "pip", "install", "--quiet", "--no-deps", str(artifact)],
            check=True,
        )
        # ...then pull the `[proxy]` extra's runtime deps. headroom==0.27.0 is
        # already satisfied by the verified wheel above, so pip only adds the
        # missing deps (httpx, etc.) without re-fetching headroom. Without this
        # the proxy cannot run (missing transitive deps).
        subprocess.run(
            [str(python_bin), "-m", "pip", "install", "--quiet", pin],
            check=True,
        )
