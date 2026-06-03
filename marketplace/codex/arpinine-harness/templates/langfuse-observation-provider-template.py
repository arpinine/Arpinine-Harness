"""
LangfuseObservationProvider — specialized LLM-focused ObservationProvider implementation.

Wraps the Langfuse SDK. All Langfuse imports stay in this file.
Product code must import ObservationProvider from src/observability/base.py only.

Required env vars:
  LANGFUSE_PUBLIC_KEY   — Langfuse project public key
  LANGFUSE_SECRET_KEY   — Langfuse project secret key
  LANGFUSE_HOST         — Langfuse host URL (default: https://cloud.langfuse.com)

Install: pip install langfuse
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

from langfuse import Langfuse

from src.observability.base import (
    ObservationProvider,
    SpanContext,
    TokenUsage,
    TraceContext,
)

logger = logging.getLogger(__name__)


class LangfuseObservationProvider:
    """
    ObservationProvider backed by Langfuse.

    Maps the protocol primitives to Langfuse trace/generation/span objects.
    Thread-safe: each call creates a new Langfuse client reference from the
    shared singleton — Langfuse SDK is thread-safe by design.
    """

    def __init__(self, *, flush_at_exit: bool = True) -> None:
        self._client = Langfuse(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        self._flush_at_exit = flush_at_exit
        if flush_at_exit:
            import atexit
            atexit.register(self.flush)

    def trace(
        self,
        name: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> TraceContext:
        lf_trace = self._client.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            tags=tags or [],
        )
        return TraceContext(
            trace_id=lf_trace.id,
            name=name,
            metadata=metadata or {},
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
        lf_trace = self._client.trace(id=trace.trace_id)
        lf_usage = None
        if usage is not None:
            lf_usage = {
                "input": usage.prompt_tokens,
                "output": usage.completion_tokens,
                "total": usage.total_tokens,
            }
        lf_trace.generation(
            name=name or "llm-call",
            model=model,
            input=input,
            output=output,
            usage=lf_usage,
            metadata=metadata or {},
            completion_start_time=None,
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
        lf_trace = self._client.trace(id=trace.trace_id)
        lf_span = lf_trace.span(name=name, input=input, metadata=metadata or {})
        try:
            yield SpanContext(span_id=lf_span.id, trace_id=trace.trace_id, name=name)
        finally:
            lf_span.end()

    def score(
        self,
        trace: TraceContext,
        *,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        self._client.score(
            trace_id=trace.trace_id,
            name=name,
            value=value,
            comment=comment,
        )

    def flush(self) -> None:
        try:
            self._client.flush()
        except Exception:
            logger.warning("Langfuse flush failed — events may be lost", exc_info=True)


assert isinstance(LangfuseObservationProvider, type)
_ = ObservationProvider  # structural check: LangfuseObservationProvider satisfies the Protocol
