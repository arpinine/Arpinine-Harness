"""
CompositeObservationProvider — fan-out ObservationProvider for dual backends.

Use this provider when a workflow requires both generic runtime telemetry and
LLM-focused trace inspection. It delegates to OpenTelemetry and Langfuse while
keeping product code bound only to the ObservationProvider Protocol.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

from src.observability.base import ObservationProvider, SpanContext, TokenUsage, TraceContext
from src.observability.langfuse import LangfuseObservationProvider
from src.observability.opentelemetry import OpenTelemetryObservationProvider


class CompositeObservationProvider:
    """
    Dual-backend observation provider.

    OpenTelemetry acts as the primary runtime telemetry backend. Langfuse adds
    AI-native trace inspection for prompts, generations, and scores.
    """

    def __init__(
        self,
        *,
        primary: ObservationProvider | None = None,
        secondary: ObservationProvider | None = None,
    ) -> None:
        self._primary = primary or OpenTelemetryObservationProvider(flush_at_exit=False)
        self._secondary = secondary or LangfuseObservationProvider(flush_at_exit=False)

    def trace(
        self,
        name: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> TraceContext:
        primary_trace = self._primary.trace(
            name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            tags=tags,
        )
        secondary_trace = self._secondary.trace(
            name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            tags=tags,
        )
        combined_metadata = dict(metadata or {})
        combined_metadata["_provider_contexts"] = {
            "primary": primary_trace,
            "secondary": secondary_trace,
        }
        combined_metadata["langfuse_trace_id"] = secondary_trace.trace_id
        combined_metadata["opentelemetry_trace_id"] = primary_trace.trace_id
        return TraceContext(
            trace_id=primary_trace.trace_id,
            name=name,
            metadata=combined_metadata,
        )

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
        primary_trace, secondary_trace = self._child_traces(trace)
        for provider, child_trace in ((self._primary, primary_trace), (self._secondary, secondary_trace)):
            provider.generation(
                child_trace,
                model=model,
                input=input,
                output=output,
                usage=usage,
                name=name,
                metadata=metadata,
                latency_ms=latency_ms,
            )

    @contextmanager
    def span(
        self,
        trace: TraceContext,
        name: str,
        *,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[SpanContext, None, None]:
        primary_trace, secondary_trace = self._child_traces(trace)
        with self._primary.span(primary_trace, name, input=input, metadata=metadata) as primary_span:
            with self._secondary.span(secondary_trace, name, input=input, metadata=metadata):
                yield primary_span

    def score(
        self,
        trace: TraceContext,
        *,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        primary_trace, secondary_trace = self._child_traces(trace)
        self._primary.score(primary_trace, name=name, value=value, comment=comment)
        self._secondary.score(secondary_trace, name=name, value=value, comment=comment)

    def flush(self) -> None:
        self._primary.flush()
        self._secondary.flush()

    def _child_traces(self, trace: TraceContext) -> tuple[TraceContext, TraceContext]:
        providers = trace.metadata.get("_provider_contexts")
        if not isinstance(providers, dict):
            raise KeyError("CompositeObservationProvider requires provider contexts in TraceContext.metadata")
        primary = providers.get("primary")
        secondary = providers.get("secondary")
        if not isinstance(primary, TraceContext) or not isinstance(secondary, TraceContext):
            raise KeyError("CompositeObservationProvider received invalid provider trace contexts")
        return primary, secondary


assert isinstance(CompositeObservationProvider, type)
_ = ObservationProvider
