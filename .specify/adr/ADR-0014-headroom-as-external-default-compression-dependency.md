---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-22
covers:
  - decision:011-context-compression-governance:headroom-dependency
---

# ADR-0014: Consume headroom as the external default compression dependency

## Status
Accepted

## Context

Spec 011 requires a default `ContextCompressionProvider` implementation. The user decision (recorded in discovery and spec FR-002/RD-008) is that the default is headroom (https://github.com/chopratejas/headroom), a local-first context-compression engine, consumed rather than re-implemented.

headroom is a third-party package. The compression proxy sees the entire outbound payload — prompts, governed artifacts, and authentication headers — so this dependency operates at a high-trust position. Consuming it without supply-chain controls would put that whole surface at the mercy of an unpinned external package and its transitive dependencies.

## Decision

Consume headroom as the sole default compression engine, as a versioned external dependency confined behind the `ContextCompressionProvider` interface (ADR-0013).

Mandatory controls, which gate completion of this ADR and of TASK-002:

1. headroom is the PyPI package `headroom-ai` (Python 3.10+), installed with the `[proxy]` extra. It is version-pinned to an exact version + hash (pin: `headroom-ai==0.27.0`), not a semver range, and verified by SHA256 at install. The package ships as compiled per-platform wheels, so the SHA256 is per-wheel and MUST live in a lockfile (e.g. `requirements.txt` with `--hash`), not a single global value. Verified reference wheel: `headroom_ai-0.27.0-cp310-abi3-macosx_11_0_arm64.whl` → `sha256:00b54b70533c841f4702fffaf215eff84bafed7612c07a56d675ef8a1ffab543`. The npm/Docker distributions are out of scope; the harness consumes the Python package.
2. `check_compression_setup.py` asserts the installed headroom version and hash match the pinned values.
3. All headroom imports are confined to the headroom default-provider module; the boundary check fails if any headroom import appears elsewhere. NOTE: the PyPI distribution is `headroom-ai` but the **import name is `headroom`** (verified against 0.27.0); the boundary check matches both. The proxy transport requires the `[proxy]` extra. Production transport uses the `headroom proxy` CLI (`--host 127.0.0.1` loopback default = no egress); the harness starts/stops it as a subprocess (ADR-0015).
4. This ADR documents headroom's actual runtime network behavior (verified, not assumed). headroom runs with outbound network restricted to loopback so governed content cannot leave the machine (NFR-001). If headroom cannot be run network-restricted, that is a residual risk requiring explicit operator acknowledgment at `/at-init`.

## Consequences

- Positive: The harness gets a working, maintained compression engine (content routing, structure/code/prose compressors, reversible retrieval) without re-implementing it.
- Positive: The supply-chain surface is bounded by pinning, hash verification, an import boundary, and network restriction.
- Negative: Swapping the default later requires re-running the fidelity benchmark, because teams will have calibrated reduction expectations against headroom.
- Negative: Tracking headroom's runtime network behavior across upgrades is ongoing work; each version bump must re-verify it.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Re-implement compression internally following headroom's design | Large effort; loses upstream maintenance; the user explicitly chose headroom |
| Depend on headroom with a semver range | Unpinned third-party code at a full-payload-visibility position is an unacceptable supply-chain risk |
| Skip runtime network verification and assume local-first | "Local-first by design" is an assertion; NFR-001 requires enforcement and documented verification |
