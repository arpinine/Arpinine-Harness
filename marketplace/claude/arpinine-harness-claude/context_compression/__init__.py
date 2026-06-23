"""Context-compression provider package (scaffolded).

Consume providers through this package (e.g. `from context_compression.noop_provider
import NoopContextCompressionProvider`). Do not load the modules by file path;
package imports keep a single ContextCompressionProvider interface identity.

Package name is `context_compression` (NOT `compression`) to avoid shadowing
the Python 3.14+ stdlib `compression` package.
"""
from .context_compression_provider import (
    CompressionEndpoint,
    CompressionError,
    ContextCompressionProvider,
)
from .noop_provider import NoopContextCompressionProvider
from .host_wiring import (
    PASSTHROUGH_FALLBACK_EVENT,
    compression_session,
    emit_passthrough_fallback,
    host_env,
    supported_hosts,
)

__all__ = [
    "CompressionEndpoint",
    "CompressionError",
    "ContextCompressionProvider",
    "NoopContextCompressionProvider",
    "PASSTHROUGH_FALLBACK_EVENT",
    "compression_session",
    "emit_passthrough_fallback",
    "host_env",
    "supported_hosts",
]
