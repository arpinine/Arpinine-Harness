"""
HeadroomContextCompressionProvider — the default ContextCompressionProvider.

Scaffolded into the product package as `context_compression/headroom_provider.py`.
Proxy-only model (ADR-0013 Option A / ADR-0015): `activate()` starts a local
`headroom proxy` and returns an opaque endpoint the host routes its provider calls
through; compression and reversible retrieval (CCR) happen transparently inside
headroom. `deactivate()` stops the proxy. The harness does NOT call a per-payload
compress()/retrieve() — that is the engine's job.

ALL headroom usage stays in this file (ADR-0014 import-boundary, enforced by
check_compression_setup.py). The interface and noop provider never import it.

Security (ADR-0014 / NFR-001):
  - the proxy binds to loopback (127.0.0.1) only — no third-party egress
  - headroom is pinned + hash-verified at install; the import name is `headroom`
    (PyPI dist `headroom-ai`, `[proxy]` extra required for the proxy transport)
  - CCR originals are owned and stored by headroom; ADR-0018's no-sync + 700/600
    invariant governs headroom's CCR directory (verified by the setup check)

Lifecycle is per-session (ADR-0019): one proxy per governed session, no state
persisted across sessions.

============================ INTEGRATION NOTE ============================
The proxy is started via the `headroom proxy` CLI as a subprocess (against
headroom 0.27.0: `headroom proxy --host 127.0.0.1 --port <p>`; host wiring is
`ANTHROPIC_BASE_URL=http://127.0.0.1:<p>`). The `_engine_*` seams implement
ephemeral loopback port selection, TCP readiness probing (with early-exit
detection + timeout), and graceful terminate→kill shutdown. They are unit-tested
in the harness via subprocess/socket mocks + a fake `headroom` module (the
deepeval/opentelemetry templates stay import-only; this one is exercised because
the transport logic is non-trivial). A LIVE run — proxy actually serving traffic —
still requires `headroom-ai[proxy]` installed in the target runtime and is not
executed in the harness CI.
=========================================================================

Governs: specs/011-context-compression-governance (TASK-002, Option A).
"""

from __future__ import annotations

import logging
import pathlib
import socket
import subprocess
import time

# headroom SDK — confined to this module (ADR-0014). Import name is `headroom`
# (PyPI dist `headroom-ai`). Used via the `_engine_*` seams below.
import headroom  # noqa: F401

from .context_compression_provider import CompressionEndpoint, CompressionError

logger = logging.getLogger(__name__)

# Loopback only — no third-party egress (NFR-001).
PROXY_HOST = "127.0.0.1"
PROXY_READY_TIMEOUT_S = 5.0
PROXY_POLL_INTERVAL_S = 0.05

# ADR-0018: headroom's CCR store must not live inside the git worktree or under a
# cloud-sync path (governed content would be committed / leave the machine).
_CLOUD_SYNC_RELATIVE_PREFIXES = (
    "Library/Mobile Documents", "Dropbox", "OneDrive", "Google Drive", "Documents", "Desktop",
)


def _sqlite_store_dir(store_url: str) -> pathlib.Path | None:
    """Resolve the filesystem directory of a sqlite store_url, else None (in-memory/non-file)."""
    if not store_url or not store_url.startswith("sqlite:///"):
        return None
    db_path = store_url[len("sqlite:///"):]
    if not db_path or db_path == ":memory:":
        return None
    return pathlib.Path(db_path).resolve().parent


def _git_worktree_root(start: pathlib.Path) -> pathlib.Path | None:
    """
    Return the enclosing git worktree root for `start`, or None when no `.git`
    ancestor is found. This enforces ADR-0018 against the actual repository
    boundary, not merely the process cwd.
    """
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


class HeadroomContextCompressionProvider:
    """
    Default provider backed by a local `headroom proxy`. Lifecycle-only
    (ADR-0013 Option A): activate -> opaque endpoint, deactivate -> stop.
    """

    def __init__(self) -> None:
        self._proxy = None  # opaque subprocess/handle, set in activate()

    def activate(self) -> CompressionEndpoint:
        try:
            self._engine_validate_configured_ccr_directory()
            self._proxy, port = self._engine_start_proxy_loopback_only()
        except Exception as exc:  # never leak internals into the message
            raise CompressionError("failed to start headroom proxy") from exc
        # Provider supplies a ready-to-use loopback base_url; host wiring sets it
        # verbatim and never derives the port itself (ADR-0015). token stays opaque.
        return CompressionEndpoint(
            token=f"headroom://session/{port}",
            base_url=f"http://{PROXY_HOST}:{port}",
            metadata={"engine": "headroom"},
        )

    def deactivate(self) -> None:
        if self._proxy is not None:
            self._engine_stop_proxy(self._proxy)
            self._proxy = None

    # ===================== headroom engine seams =====================
    # The ONLY code that touches headroom / the proxy process. Wired against
    # headroom 0.27.0 and exercised by the live integration tests (TASK-010).

    def _engine_validate_configured_ccr_directory(self) -> None:
        """
        Validate headroom's configured CCR store location before activation
        (ADR-0018). headroom stores CCR originals in a sqlite `store_url`
        (default `sqlite:///headroom.db`, which resolves into the CWD — unsafe
        inside a repo). Reject a store dir that is inside the git worktree or
        under a known cloud-sync path. In-memory / non-file stores are exempt.

        Raises CompressionError on an unsafe location (callers degrade to
        passthrough rather than risk leaking governed originals).
        """
        store_dir = _sqlite_store_dir(headroom.HeadroomConfig().store_url)
        if store_dir is None:
            return None
        worktree = _git_worktree_root(pathlib.Path.cwd())
        home = pathlib.Path.home().resolve()
        if worktree is not None and (store_dir == worktree or worktree in store_dir.parents):
            raise CompressionError(f"headroom CCR store {store_dir} is inside the git worktree (ADR-0018)")
        for rel in _CLOUD_SYNC_RELATIVE_PREFIXES:
            prefix = (home / rel).resolve()
            if store_dir == prefix or prefix in store_dir.parents:
                raise CompressionError(f"headroom CCR store {store_dir} is under cloud-sync path {rel} (ADR-0018)")
        return None

    def _engine_start_proxy_loopback_only(self):
        """
        Start `headroom proxy --host 127.0.0.1 --port <p>` as a subprocess bound
        to loopback, wait for readiness, and return (handle, port). The base-URL
        the host is pointed at is http://127.0.0.1:<p> (ADR-0015 / TASK-006).
        """
        port = self._engine_pick_loopback_port()
        cmd = ["headroom", "proxy", "--host", PROXY_HOST, "--port", str(port)]
        logger.info("starting headroom proxy on %s:%s", PROXY_HOST, port)
        proxy = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            self._engine_wait_for_port(port, proxy, timeout_s=PROXY_READY_TIMEOUT_S)
        except Exception:
            self._engine_stop_proxy(proxy)
            raise
        return proxy, port

    def _engine_stop_proxy(self, proxy) -> None:
        """Gracefully terminate the proxy subprocess started in activate()."""
        if proxy is None:
            return None
        if proxy.poll() is not None:
            return None
        proxy.terminate()
        try:
            proxy.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proxy.kill()
            proxy.wait(timeout=2.0)
        return None

    def _engine_pick_loopback_port(self) -> int:
        """Reserve an ephemeral loopback port for the proxy subprocess."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((PROXY_HOST, 0))
            return int(sock.getsockname()[1])

    def _engine_wait_for_port(self, port: int, proxy, *, timeout_s: float) -> None:
        """
        Poll loopback until the proxy accepts TCP connections, or raise if the
        subprocess exits early / readiness times out.
        """
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
