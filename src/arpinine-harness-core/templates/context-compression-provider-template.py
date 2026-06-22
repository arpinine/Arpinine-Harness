"""
ContextCompressionProvider — abstract interface for governed context compression.

Product/harness code depends on this Protocol only. Engine-specific implementations
(e.g. the headroom default provider) live in their own module and are injected at
the composition root; a noop implementation satisfies this interface with no proxy.

Swap the implementation by changing the composition root — no dependent code changes.

Governs: specs/011-context-compression-governance
ADRs:
  - ADR-0013 (amended, Option A): the interface is **lifecycle-only**. Under the
    proxy-only model, compression happens transparently inside the headroom proxy
    at the HTTP layer and reversible retrieval (CCR) is owned by the engine — the
    harness never calls a per-payload compress()/retrieve(). The interface has
    ZERO dependencies and uses vendor/transport-neutral names so the noop impl
    satisfies it without inheriting a proxy metaphor.
  - ADR-0015: host integrations receive only an opaque endpoint token via
    CompressionEndpoint — never the proxy's raw local port or address.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class CompressionEndpoint:
    """
    Handle a host integration uses to route its outbound provider calls through
    the active compression implementation.

    ADR-0015: `token` is an opaque endpoint identifier. `base_url` is a
    ready-to-use base URL **supplied by the provider** for host wiring to set
    verbatim (e.g. as `ANTHROPIC_BASE_URL`). Host wiring MUST treat `base_url` as
    opaque — use it as given, never parse or derive a port/host from it, and
    never construct network coordinates itself. `base_url is None` means "no
    override" (the noop/disabled path → the host talks to the provider directly).
    This dataclass exposes no separate `port`/`host`/`address` field.
    """
    token: str
    base_url: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class CompressionError(Exception):
    """Raised when the compression implementation cannot be activated."""


@runtime_checkable
class ContextCompressionProvider(Protocol):
    """
    Lifecycle-only abstraction over context-compression engines (ADR-0013,
    Option A). `activate` brings the implementation online for a governed session
    and returns an opaque CompressionEndpoint the host routes its provider calls
    through; `deactivate` tears it down (ADR-0019: per-session lifecycle).

    Per-payload compression and reversible retrieval are owned by the engine
    (e.g. the headroom proxy), NOT by this interface. A noop implementation
    satisfies both methods as no-ops and starts no process.
    """

    def activate(self) -> CompressionEndpoint:
        """
        Bring the implementation online for a session and return its opaque
        endpoint. The noop implementation returns a trivial endpoint and starts
        nothing. Must not expose raw network coordinates to callers.

        CONTRACT: on any failure to come online — including the proxy being
        unreachable — implementations MUST raise CompressionError (wrapping the
        underlying cause). The host-wiring passthrough fallback (ADR-0015)
        degrades to uncompressed ONLY on CompressionError; any other exception
        propagates as a bug rather than being silently converted to passthrough.
        """
        ...

    def deactivate(self) -> None:
        """
        Tear down anything `activate` started and release resources. Idempotent;
        safe to call when nothing was started.
        """
        ...
