"""
HeadroomContextCompressionProvider — the default ContextCompressionProvider.

Scaffolded into the product package as `context_compression/headroom_provider.py`.
Wraps the headroom engine (PyPI `headroom-ai[proxy]`, pinned per ADR-0014). ALL
headroom imports stay in this file (ADR-0014 import-boundary; enforced by
check_compression_setup.py). The interface and the noop provider never import it.

Security controls (concrete, via the headroom-free `security` helpers which are
unit-tested):
  - credentials scrubbed before any log or CCR write (ADR-0014)
  - reversible-retrieval (CCR) originals stored at ~/.arpinine/ccr-store, 700/600
    (ADR-0018)
  - headroom proxy run network-restricted to loopback; no third-party egress
    (ADR-0014 / NFR-001)
  - no full-payload/debug logging (logger stays at WARN; payloads never logged)

Lifecycle is per-session (ADR-0019): activate() starts the proxy, deactivate()
stops it, no state persists across sessions.

============================ INTEGRATION NOTE ============================
The headroom 0.27.0 Python API surface (proxy start/stop entry points, the
compress() signature, and how segment originals are exposed for reversible
retrieval) MUST be confirmed against the installed SDK during the golden-session
integration (TASK-008/009) and wired into the clearly-marked `_engine_*` seams
below. Those seams are the ONLY places that touch headroom; everything else
(security, CCR store, lifecycle, the interface contract) is concrete and tested.
This file is a scaffold template and is intentionally NOT import-tested here
(headroom is not a dev dependency of the harness itself), mirroring the
deepeval / opentelemetry provider templates.
=========================================================================

Governs: specs/011-context-compression-governance (TASK-002).
"""

from __future__ import annotations

import logging
import pathlib

# headroom SDK — confined to this module (ADR-0014). Pinned/hash-verified at
# install (ADR-0014); run network-restricted (NFR-001).
import headroom_ai  # noqa: F401  (used via the _engine_* seams below)

from .context_compression_provider import (
    CompressionEndpoint,
    CompressionError,
    CompressionResult,
)
from .security import (
    ensure_ccr_store,
    read_original,
    store_original,
)

logger = logging.getLogger(__name__)

# ADR-0018: fixed, non-synced store. Never under the repo or a cloud-sync path;
# check_compression_setup.py enforces this at setup and at activation.
DEFAULT_CCR_STORE = pathlib.Path.home() / ".arpinine" / "ccr-store"


class HeadroomContextCompressionProvider:
    """
    Default provider backed by the headroom engine. Implements
    ContextCompressionProvider structurally (runtime_checkable Protocol).
    """

    def __init__(self, ccr_store: pathlib.Path | None = None) -> None:
        self._ccr_store = pathlib.Path(ccr_store) if ccr_store else DEFAULT_CCR_STORE
        self._proxy = None  # opaque engine handle; set in activate()

    # --- lifecycle (ADR-0019: per-session) ---

    def activate(self) -> CompressionEndpoint:
        ensure_ccr_store(self._ccr_store)  # 700; tested in security helpers
        self._proxy = self._engine_start_proxy_loopback_only()
        token = self._engine_endpoint_token(self._proxy)
        # Opaque endpoint only — never expose the raw port/address (ADR-0015).
        return CompressionEndpoint(token=token)

    def deactivate(self) -> None:
        if self._proxy is not None:
            self._engine_stop_proxy(self._proxy)
            self._proxy = None

    # --- compression ---

    def compress(self, payload: bytes) -> CompressionResult:
        try:
            compressed, segments = self._engine_compress(payload)
        except Exception as exc:  # never leak payloads into the message
            raise CompressionError("headroom compression failed") from exc
        # Persist exact originals for reversible retrieval; security helper
        # seals them at rest so retrieve() stays byte-equal while credentials
        # are not persisted in plaintext.
        for key, original in segments:
            store_original(self._ccr_store, key, original)
        return CompressionResult(
            payload=compressed,
            segment_keys=[k for k, _ in segments],
            original_bytes=len(payload),
        )

    def retrieve(self, segment_key: str) -> bytes:
        # Byte-equal recovery from the CCR store (ADR-0018). KeyError if absent.
        return read_original(self._ccr_store, segment_key)

    # ===================== headroom engine seams =====================
    # The ONLY code that touches headroom. Wire to the confirmed 0.27.0 API at
    # golden-session integration (see INTEGRATION NOTE). Keep payload scrubbing
    # (scrub_credentials) on any headers before they are logged or stored.

    def _engine_start_proxy_loopback_only(self):
        """Start the headroom proxy bound to loopback only (no egress)."""
        raise NotImplementedError(
            "wire headroom 0.27.0 proxy start (loopback-only) at integration"
        )

    def _engine_stop_proxy(self, proxy) -> None:
        raise NotImplementedError("wire headroom 0.27.0 proxy stop at integration")

    def _engine_endpoint_token(self, proxy) -> str:
        """Return an opaque endpoint token for host wiring (never a raw port)."""
        raise NotImplementedError("wire headroom 0.27.0 endpoint token at integration")

    def _engine_compress(self, payload: bytes):
        """
        Return (compressed_bytes, [(segment_key, original_bytes), ...]) using
        headroom. Apply scrub_credentials()/scrub_bytes() to any header material
        before it is logged. Stored originals are sealed by store_original().
        """
        raise NotImplementedError("wire headroom 0.27.0 compress() at integration")
