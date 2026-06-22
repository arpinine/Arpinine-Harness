"""
compression security helpers — headroom-free, security-critical primitives for
the context-compression provider layer.

Scaffolded into the product package as `context_compression/security.py`. Imports
NO compression engine (no headroom), so it is unit-testable on its own and is the
single home for the controls that must hold regardless of engine:

  - scrub_credentials(): mask Authorization / x-api-key / cookie before any log
    or other non-reversible storage/log paths (ADR-0014).
  - ensure_ccr_store() / store_original() / read_original(): the reversible-
    retrieval (CCR) store — directory 700, files 600, byte-equal recovery
    (ADR-0018). Originals are sealed at rest with a store-local key to avoid
    PLAINTEXT secrets in the store.

SECURITY SCOPE OF THE SEAL (read this before trusting it):
  The seal key (`.ccr-store.key`) is co-located in the store directory for
  portability. The seal is therefore PLAINTEXT-AVOIDANCE / defense-in-depth only
  — it is NOT confidential against anyone who can read the store directory, since
  they read the key too. Any threat that leaks the store (cloud-sync, backup,
  world-readable copy) leaks the key with it. The PRIMARY protection of CCR
  originals is the no-sync + 700/600 invariant enforced by ADR-0018 and
  check_compression_setup.py; the seal does NOT relax that invariant. For real
  at-rest confidentiality, derive the key from outside the store (OS keychain /
  env) — see ADR-0018.

Governs: specs/011-context-compression-governance (TASK-002).
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import re
import secrets

REDACTED = "***REDACTED***"
_REDACTED_BYTES = REDACTED.encode("ascii")

# Header names whose values must never reach a log or the CCR store (ADR-0014).
_CREDENTIAL_HEADERS = frozenset({"authorization", "x-api-key", "cookie"})

# Byte-level credential patterns for raw payload/segment content. Header-style
# (`Name: value` to end-of-line) and JSON-style (`"name": "value"`). The KEY is
# preserved; only the VALUE is redacted. Case-insensitive.
_HEADER_CRED_RE = re.compile(
    rb"(?i)(authorization|x-api-key|cookie)(\s*:\s*)([^\r\n]*)"
)
_JSON_CRED_RE = re.compile(
    rb'(?i)("(?:authorization|x-api-key|api[-_]?key|cookie)"\s*:\s*")([^"]*)(")'
)
_SEALED_MAGIC = b"CCR1"
_NONCE_BYTES = 16
_KEY_FILE = ".ccr-store.key"


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
    Redact credential VALUES from raw payload/segment bytes before they are
    logged or written to the CCR store (ADR-0014). Handles header-style and
    JSON-style credentials; keys are preserved, values replaced with REDACTED.
    Clean content is returned unchanged.
    """
    data = _HEADER_CRED_RE.sub(rb"\1\2" + _REDACTED_BYTES, data)
    data = _JSON_CRED_RE.sub(rb"\1" + _REDACTED_BYTES + rb"\3", data)
    return data


def ensure_ccr_store(store: pathlib.Path | str) -> pathlib.Path:
    """
    Create the CCR store directory (and parents) with mode 700. Returns the path.
    Idempotent; tightens the mode on an existing directory.
    """
    path = pathlib.Path(store)
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def _key_file(store: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(store) / _KEY_FILE


def _load_or_create_key(store: pathlib.Path) -> bytes:
    path = _key_file(store)
    if path.exists():
        return path.read_bytes()
    key = secrets.token_bytes(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, key)
    finally:
        os.close(fd)
    os.chmod(path, 0o600)
    return key


def _segment_file(store: pathlib.Path, segment_key: str) -> pathlib.Path:
    # Hash the key so arbitrary keys map to a safe, fixed-shape filename.
    digest = hashlib.sha256(segment_key.encode("utf-8")).hexdigest()
    return pathlib.Path(store) / f"{digest}.orig"


def _keystream(key: bytes, nonce: bytes, size: int) -> bytes:
    blocks: list[bytes] = []
    counter = 0
    while sum(len(b) for b in blocks) < size:
        block = hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest()
        blocks.append(block)
        counter += 1
    return b"".join(blocks)[:size]


def _seal_bytes(store: pathlib.Path, data: bytes) -> bytes:
    key = _load_or_create_key(store)
    nonce = secrets.token_bytes(_NONCE_BYTES)
    stream = _keystream(key, nonce, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, stream))
    return _SEALED_MAGIC + nonce + ciphertext


def _open_bytes(store: pathlib.Path, payload: bytes) -> bytes:
    if not payload.startswith(_SEALED_MAGIC):
        raise ValueError("CCR payload missing seal header")
    key = _load_or_create_key(store)
    nonce = payload[len(_SEALED_MAGIC):len(_SEALED_MAGIC) + _NONCE_BYTES]
    ciphertext = payload[len(_SEALED_MAGIC) + _NONCE_BYTES:]
    stream = _keystream(key, nonce, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, stream))


def store_original(store: pathlib.Path | str, segment_key: str, data: bytes) -> pathlib.Path:
    """
    Persist the exact original bytes for a segment, file mode 600. Returns the
    file path. Data is sealed with a store-local key so the store holds no
    PLAINTEXT secrets (defense-in-depth, NOT confidential against a reader of the
    store — see module docstring); read_original() recovers byte-identical content.
    """
    store = pathlib.Path(store)
    path = _segment_file(store, segment_key)
    sealed = _seal_bytes(store, data)
    # Create with 600 from the start (avoid a readable window).
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, sealed)
    finally:
        os.close(fd)
    os.chmod(path, 0o600)
    return path


def read_original(store: pathlib.Path | str, segment_key: str) -> bytes:
    """Return the exact stored bytes for a segment. Raises KeyError if absent."""
    store = pathlib.Path(store)
    path = _segment_file(store, segment_key)
    if not path.exists():
        raise KeyError(segment_key)
    return _open_bytes(store, path.read_bytes())
