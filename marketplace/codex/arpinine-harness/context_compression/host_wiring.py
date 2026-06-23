"""
host wiring — consume the compression endpoint per host + drive the lifecycle.

Scaffolded into the product package as `context_compression/host_wiring.py`.
Engine-neutral: depends only on the `ContextCompressionProvider` interface
(activate/deactivate + CompressionEndpoint), never on headroom.

Responsibilities (TASK-006):
  - host_env(endpoint, host): map the provider-supplied opaque endpoint to the
    environment override a given host uses to route its provider calls through
    the compression proxy. `base_url` is used VERBATIM (ADR-0015); when it is
    None (noop/disabled) the result is empty — the host talks to the provider
    directly, no override.
  - compression_session(provider, host): per-session lifecycle (ADR-0019) —
    activate -> yield the host env mapping -> deactivate (even on error).

Per-host env mapping (headroom proxy serves Anthropic at `/` and OpenAI-compatible
at `/v1`):
  - claude  -> ANTHROPIC_BASE_URL = base_url
  - codex   -> OPENAI_BASE_URL    = base_url + "/v1"
  - copilot -> OPENAI_BASE_URL    = base_url + "/v1"   (OpenAI-compatible routing)

Governs: specs/011-context-compression-governance (TASK-006).
"""

from __future__ import annotations

import contextlib
import datetime
import json
import logging
import uuid

from .context_compression_provider import CompressionError

logger = logging.getLogger("context_compression")

# ADR-0015: when the proxy is unreachable the session degrades to uncompressed
# passthrough (no env override -> host talks direct) and emits this observable
# signal. The scaffolded product MUST route this logger to its main output stream
# (e.g. a stderr handler) so a degraded posture is visible, not buried.
PASSTHROUGH_FALLBACK_EVENT = "compression_passthrough_fallback"


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def emit_passthrough_fallback(reason: str, session_id: str, *, now=_utc_now_iso) -> dict:
    """
    Emit the structured passthrough-fallback signal at WARNING and return the
    record. `now` is injectable for deterministic tests.
    """
    record = {
        "event": PASSTHROUGH_FALLBACK_EVENT,
        "level": "WARNING",
        "timestamp": now(),
        "reason": reason,
        "session_id": session_id,
    }
    logger.warning(
        json.dumps(record, sort_keys=True),
        extra={
            "event": record["event"],
            "timestamp": record["timestamp"],
            "reason": record["reason"],
            "session_id": record["session_id"],
        },
    )
    return record


# (env var name, path suffix appended to the provider-supplied base_url)
_HOST_ENV = {
    "claude": ("ANTHROPIC_BASE_URL", ""),
    "codex": ("OPENAI_BASE_URL", "/v1"),
    "copilot": ("OPENAI_BASE_URL", "/v1"),
}


def supported_hosts() -> tuple[str, ...]:
    return tuple(_HOST_ENV)


def host_env(endpoint, host: str) -> dict:
    """
    Return the environment override for `host` given an active CompressionEndpoint.

    - Unknown host -> ValueError (callers must handle every host explicitly).
    - endpoint.base_url is None (disabled/noop) -> {} (no override; talk direct).
    - Otherwise -> {ENV_VAR: base_url[+suffix]}, base_url used verbatim per ADR-0015.
    """
    if host not in _HOST_ENV:
        raise ValueError(f"unsupported host {host!r}; known: {', '.join(_HOST_ENV)}")
    base_url = getattr(endpoint, "base_url", None)
    if not base_url:
        return {}
    env_var, suffix = _HOST_ENV[host]
    return {env_var: f"{base_url}{suffix}"}


@contextlib.contextmanager
def compression_session(provider, host: str, *, session_id: str | None = None):
    """
    Per-session lifecycle (ADR-0019) with passthrough fallback (ADR-0015).

    Activates the provider and yields the host env mapping; deactivates on exit
    (including on error). If `activate()` fails (proxy unavailable / unreachable),
    the session degrades to **uncompressed passthrough**: emit the structured
    `compression_passthrough_fallback` signal and yield `{}` (no override, the
    host talks to the provider directly) so the governed session still completes.
    """
    if host not in _HOST_ENV:
        raise ValueError(f"unsupported host {host!r}; known: {', '.join(_HOST_ENV)}")
    session_id = session_id or uuid.uuid4().hex

    try:
        endpoint = provider.activate()
    except CompressionError as exc:  # proxy unavailable -> degrade safely, do not break
        emit_passthrough_fallback(reason=str(exc) or "proxy unavailable", session_id=session_id)
        yield {}  # passthrough: no override; nothing was started, nothing to stop
        return

    try:
        yield host_env(endpoint, host)
    finally:
        provider.deactivate()
