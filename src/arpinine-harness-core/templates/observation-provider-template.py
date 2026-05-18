"""
ObservationProvider — abstract interface for runtime observability and telemetry.

Product code depends on this Protocol only. SDK-specific implementations
(e.g. OpenTelemetryObservationProvider or LangfuseObservationProvider)
live in src/observability/<provider>.py
and are injected at the composition root.

Swap the provider by changing the composition root import — no product code changes.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator, Protocol, runtime_checkable


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class TraceContext:
    trace_id: str
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanContext:
    span_id: str
    trace_id: str
    name: str


@runtime_checkable
class ObservationProvider(Protocol):
    """
    Thin abstraction over runtime observability backends.

    Implementations must be thread-safe and must not raise on flush failure
    (log the error and continue). Product code must never import from
    concrete implementation modules.
    """

    def trace(
        self,
        name: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> TraceContext:
        """Open a new trace. Returns a context object for subsequent calls."""
        ...

    def generation(
        self,
        trace: TraceContext,
        *,
        model: str,
        input: Any,
        output: Any,
        usage: TokenUsage | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """Record an LLM generation event within an open trace."""
        ...

    @contextmanager
    def span(
        self,
        trace: TraceContext,
        name: str,
        *,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[SpanContext, None, None]:
        """Context manager for a named span within a trace."""
        ...

    def score(
        self,
        trace: TraceContext,
        *,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        """Attach a numeric score (e.g. eval metric) to a trace."""
        ...

    def flush(self) -> None:
        """Flush buffered events. Must be called before process exit."""
        ...
