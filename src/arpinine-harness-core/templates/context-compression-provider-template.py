"""
ContextCompressionProvider — abstract interface for governed context compression.

Product/harness code depends on this Protocol only. Engine-specific implementations
(e.g. the headroom default provider) live in their own module and are injected at
the composition root; a noop implementation satisfies this interface with no proxy.

Swap the implementation by changing the composition root — no dependent code changes.

Governs: specs/011-context-compression-governance
ADRs:
  - ADR-0013: this abstraction, the retrieve() segment-key contract, and
    vendor/transport-neutral lifecycle naming (activate/deactivate, never
    start_proxy). The interface has ZERO dependencies — it must not reference
    headroom, any proxy/port concept, any host API, or the constitution.
  - ADR-0015: host integrations receive only an opaque endpoint token via
    CompressionEndpoint — never the proxy's raw local port or address.
  - ADR-0017: compressed output of governed artifacts MUST preserve the same
    DATA delimiter/role boundary as the uncompressed artifact, so the model
    cannot read compressed content as new instructions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class CompressionEndpoint:
    """
    Opaque handle a host integration uses to route its outbound provider calls
    through the active compression implementation.

    ADR-0015: `token` is an opaque endpoint identifier. This dataclass MUST NOT
    expose raw network coordinates (port, host, address); host wiring resolves
    the token through host-specific plumbing without coupling to those details.
    """
    token: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class CompressionResult:
    """
    Outcome of compressing an outbound payload.

    `payload`        — the compressed bytes to forward to the model provider.
    `segment_keys`   — stable keys for reversibly-stored segments (see retrieve()).
    `original_bytes` — size of the input prior to compression (for measurement).

    The data boundary (ADR-0017) is a property of `payload`: governed artifact
    content within it must remain delimited as DATA, never promoted to instructions.
    """
    payload: bytes
    segment_keys: list[str] = field(default_factory=list)
    original_bytes: int = 0


class CompressionError(Exception):
    """Raised when compression cannot proceed and passthrough is not acceptable."""


@runtime_checkable
class ContextCompressionProvider(Protocol):
    """
    Thin abstraction over context-compression engines.

    Lifecycle is vendor/transport-neutral: `activate` brings the implementation
    online for a governed session and returns an opaque CompressionEndpoint;
    `deactivate` tears it down (ADR-0019: per-session lifecycle). A noop
    implementation satisfies both as no-ops and starts no process.

    Implementations must be deterministic given the same input and configuration,
    and must preserve the DATA role boundary of governed artifacts (ADR-0017).
    """

    def activate(self) -> CompressionEndpoint:
        """
        Bring the implementation online for a session and return its opaque
        endpoint. The noop implementation returns a trivial endpoint and starts
        nothing. Must not expose raw network coordinates to callers.
        """
        ...

    def deactivate(self) -> None:
        """
        Tear down anything `activate` started and release resources. Idempotent;
        safe to call when nothing was started.
        """
        ...

    def compress(self, payload: bytes) -> CompressionResult:
        """
        Compress one outbound payload. Must preserve the DATA role boundary of
        any governed-artifact content (ADR-0017). The noop implementation returns
        the payload unchanged with no segment keys.
        """
        ...

    def retrieve(self, segment_key: str) -> bytes:
        """
        Return the exact original bytes for a previously compressed segment
        (reversible retrieval / CCR). The result MUST be byte-equal to the
        pre-compression input for that segment. Raises KeyError for unknown keys.
        `segment_key` values are produced in CompressionResult.segment_keys.
        """
        ...
