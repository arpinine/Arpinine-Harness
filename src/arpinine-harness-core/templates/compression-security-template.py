"""
compression security helpers — headroom-free credential-scrubbing primitives.

Scaffolded into the product package as `context_compression/security.py`. Imports
NO compression engine, so it is unit-testable on its own.

SCOPE (Option A / ADR-0013): under the proxy-only model, per-payload compression
and reversible-retrieval (CCR) storage are owned by the **headroom engine**, not
the harness. The harness therefore no longer ships a CCR store, sealing, or
`store_original`/`read_original` — those were retired with the Option A decision.

What remains here are credential-scrubbing helpers for any harness-side LOGGING
path that might echo header or payload material:

  - scrub_credentials(): mask Authorization / x-api-key / cookie header values
    before they reach a log (ADR-0014).
  - scrub_bytes(): redact credential VALUES from raw text/bytes before logging.

ADR-0018's no-sync + 700/600 invariant now governs headroom's CCR directory; it
is verified by check_compression_setup.py, not implemented here.

Governs: specs/011-context-compression-governance (TASK-002, Option A).
"""

from __future__ import annotations

import re

REDACTED = "***REDACTED***"
_REDACTED_BYTES = REDACTED.encode("ascii")

# Header names whose values must never reach a log (ADR-0014).
_CREDENTIAL_HEADERS = frozenset({"authorization", "x-api-key", "cookie"})

# Byte-level credential patterns for raw payload/log content. Header-style
# (`Name: value` to end-of-line) and JSON-style (`"name": "value"`). The KEY is
# preserved; only the VALUE is redacted. Case-insensitive.
_HEADER_CRED_RE = re.compile(
    rb"(?i)(authorization|x-api-key|cookie)(\s*:\s*)([^\r\n]*)"
)
_JSON_CRED_RE = re.compile(
    rb'(?i)("(?:authorization|x-api-key|api[-_]?key|cookie)"\s*:\s*")([^"]*)(")'
)


def scrub_credentials(headers: dict) -> dict:
    """
    Return a copy of `headers` with credential header values masked. Matching is
    case-insensitive. The input mapping is not mutated.
    """
    scrubbed = dict(headers)
    for key in list(scrubbed.keys()):
        if str(key).lower() in _CREDENTIAL_HEADERS:
            scrubbed[key] = REDACTED
    return scrubbed


def scrub_bytes(data: bytes) -> bytes:
    """
    Redact credential VALUES from raw bytes before they are logged. Handles
    header-style and JSON-style credentials; keys are preserved, values replaced
    with REDACTED. Clean content is returned unchanged.
    """
    data = _HEADER_CRED_RE.sub(rb"\1\2" + _REDACTED_BYTES, data)
    data = _JSON_CRED_RE.sub(rb"\1" + _REDACTED_BYTES + rb"\3", data)
    return data
