"""
NoopContextCompressionProvider — the disabled-compression implementation.

This is the implementation selected when compression is disabled (the default;
ADR-0016). It satisfies the ContextCompressionProvider interface while doing
nothing: payloads pass through byte-for-byte, no proxy is started, no socket is
opened, and no originals are stored. Choosing it must impose zero overhead and
leave harness behavior identical to a pre-feature install.

Governs: specs/011-context-compression-governance
ADRs:
  - ADR-0013: satisfies the interface; starts no process.
  - ADR-0016: the disabled path is this provider — zero overhead, no proxy.

Consumption contract: in the scaffolded product these files form a Python
package (`compression/` with `__init__.py`). The interface MUST be consumed
through the import system (`from .context_compression_provider import ...`),
NOT by ad-hoc file-path loading. Importing by name is cached by the interpreter,
so the dataclass/Protocol types are a single identity regardless of import order.
scaffold_compression_setup.py rewrites the dev-only loader block below into that
package-relative import when it emits `noop_provider.py`.

Two independent file-path loads of the same interface file always produce
distinct module objects (a Python invariant); that is why the product must use
package imports, not path loading. See plan `## Module Boundaries`.
"""

from __future__ import annotations

from .context_compression_provider import CompressionEndpoint


class NoopContextCompressionProvider:
    """
    Lifecycle-only passthrough provider (ADR-0013, Option A). Implements
    ContextCompressionProvider structurally (the interface is a runtime_checkable
    Protocol, so no inheritance needed). Starts no process and opens no socket.
    """

    def activate(self) -> CompressionEndpoint:
        # Opaque, inert endpoint. No process, no socket, no network coordinates.
        return CompressionEndpoint(token="noop")

    def deactivate(self) -> None:
        # Nothing was started; idempotent no-op.
        return None
