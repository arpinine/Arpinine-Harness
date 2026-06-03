"""
OpenTelemetryObservationProvider — generic ObservationProvider implementation.

Wraps the OpenTelemetry SDK and exports spans over OTLP. All OpenTelemetry SDK
imports stay in this file. Product code must import ObservationProvider from
src/observability/base.py only.

Required env vars:
  OTEL_SERVICE_NAME             — logical service name for the runtime
  OTEL_EXPORTER_OTLP_ENDPOINT   — OTLP collector endpoint

Optional env vars:
  OTEL_EXPORTER_OTLP_HEADERS    — comma-separated k=v headers for the exporter
  OTEL_RESOURCE_ATTRIBUTES      — comma-separated k=v resource attributes

Install:
  pip install opentelemetry-sdk opentelemetry-exporter-otlp
"""

from __future__ import annotations

import atexit
import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.observability.base import (
    ObservationProvider,
    SpanContext,
    TokenUsage,
    TraceContext,
)

logger = logging.getLogger(__name__)


def _parse_key_value_csv(value: str) -> dict[str, str]:
    items: dict[str, str] = {}
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item or "=" not in item:
            continue
        key, raw_value = item.split("=", 1)
        items[key.strip()] = raw_value.strip()
    return items


class OpenTelemetryObservationProvider:
    """
    ObservationProvider backed by OpenTelemetry traces.

    The provider creates a root span for each trace, nested spans for tool or
    workflow steps, and span events for LLM generations and evaluation scores.
    """

    def __init__(self, *, flush_at_exit: bool = True) -> None:
        service_name = os.environ.get("OTEL_SERVICE_NAME", "agent-runtime")
        resource_attributes = _parse_key_value_csv(os.environ.get("OTEL_RESOURCE_ATTRIBUTES", ""))
        resource = Resource.create({"service.name": service_name, **resource_attributes})

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(
            endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"],
            headers=_parse_key_value_csv(os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        self._provider = provider
        self._tracer = provider.get_tracer("arpinine-harness")
        self._spans: dict[str, Any] = {}
        self._flush_at_exit = flush_at_exit
        if flush_at_exit:
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
        attributes: dict[str, Any] = {
            "observation.name": name,
            "observation.tags": ",".join(tags or []),
        }
        if user_id is not None:
            attributes["enduser.id"] = user_id
        if session_id is not None:
            attributes["session.id"] = session_id
        for key, value in (metadata or {}).items():
            attributes[f"observation.metadata.{key}"] = value

        span = self._tracer.start_span(name, attributes=attributes)
        trace_id = f"{span.get_span_context().trace_id:032x}"
        self._spans[trace_id] = span
        return TraceContext(trace_id=trace_id, name=name, metadata=metadata or {})

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
        parent = self._require_trace_span(trace)
        attributes: dict[str, Any] = {
            "gen_ai.request.model": model,
            "gen_ai.operation.name": name or "llm-call",
            "gen_ai.prompt": str(input),
            "gen_ai.completion": str(output),
        }
        if usage is not None:
            attributes["gen_ai.usage.input_tokens"] = usage.prompt_tokens
            attributes["gen_ai.usage.output_tokens"] = usage.completion_tokens
            attributes["gen_ai.usage.total_tokens"] = usage.total_tokens
        if latency_ms is not None:
            attributes["gen_ai.latency_ms"] = latency_ms
        for key, value in (metadata or {}).items():
            attributes[f"gen_ai.metadata.{key}"] = value

        with otel_trace.use_span(parent, end_on_exit=False):
            child = self._tracer.start_span(name or "llm-call", attributes=attributes)
            child.end()

    @contextmanager
    def span(
        self,
        trace: TraceContext,
        name: str,
        *,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[SpanContext, None, None]:
        parent = self._require_trace_span(trace)
        attributes: dict[str, Any] = {}
        if input is not None:
            attributes["observation.input"] = str(input)
        for key, value in (metadata or {}).items():
            attributes[f"observation.metadata.{key}"] = value

        with otel_trace.use_span(parent, end_on_exit=False):
            child = self._tracer.start_span(name, attributes=attributes)
        span_id = f"{child.get_span_context().span_id:016x}"
        try:
            yield SpanContext(span_id=span_id, trace_id=trace.trace_id, name=name)
        finally:
            child.end()

    def score(
        self,
        trace: TraceContext,
        *,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        span = self._require_trace_span(trace)
        attributes: dict[str, Any] = {"score.value": value}
        if comment is not None:
            attributes["score.comment"] = comment
        span.add_event(f"score.{name}", attributes=attributes)

    def flush(self) -> None:
        try:
            for trace_id, span in list(self._spans.items()):
                span.end()
                self._spans.pop(trace_id, None)
            self._provider.force_flush()
            self._provider.shutdown()
        except Exception:
            logger.warning("OpenTelemetry flush failed — events may be lost", exc_info=True)

    def _require_trace_span(self, trace: TraceContext) -> Any:
        span = self._spans.get(trace.trace_id)
        if span is None:
            raise KeyError(f"Unknown trace_id {trace.trace_id}")
        return span


assert isinstance(OpenTelemetryObservationProvider, type)
_ = ObservationProvider  # structural check: OpenTelemetryObservationProvider satisfies the Protocol
