---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-22
covers:
  - decision:011-context-compression-governance:proxy-lifecycle-model
---

# ADR-0019: Compression proxy lifecycle — per-session activate/deactivate

## Status
Accepted

## Context

Spec 011 OQ-003 asks how the local compression proxy's lifecycle binds to a harness session: a per-session start/stop, or a long-running local service shared across sessions. The choice affects the `ContextCompressionProvider` lifecycle API (ADR-0013), the per-host wiring (ADR-0015), and the benchmark runner.

A long-running service has cheaper per-session startup but risks carrying state (KV-cache alignment data, CCR mappings, content-router caches) across governed sessions, which could let one session's content influence another's compression — a fidelity and isolation hazard for a governance harness. A per-session model pays a startup cost each session but guarantees a clean slate.

## Decision

Use a per-session lifecycle: the provider's `activate` starts the proxy at the beginning of a governed session and `deactivate` stops it at the end, with no proxy state persisting across sessions.

1. Each governed session gets a freshly activated proxy; `deactivate` tears it down and releases resources.
2. CCR originals persist in the store (ADR-0018) keyed by segment, independent of proxy lifetime; the proxy process itself holds no cross-session state.
3. The benchmark replays each golden-session run under the same per-session activate/deactivate model so ON/OFF measurement matches real operation.

## Consequences

- Positive: Clean isolation between governed sessions — no cross-session compression state, which protects the fidelity guarantee.
- Positive: Simpler reasoning for the benchmark, since each run mirrors a real session lifecycle.
- Negative: Per-session startup cost (proxy spin-up, model load in headroom) is paid each session; mitigated because activation is local and the cost is amortized over a multi-turn session.
- Negative: Rapid sequential sessions re-pay startup; a future optimization could add an opt-in warm pool, but only if it provably preserves cross-session isolation.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Long-running shared local service | Risks cross-session state bleeding into compression; isolation hazard for a governance harness |
| No explicit lifecycle (lazy/implicit start) | Makes teardown and resource release ambiguous; harder to guarantee a clean slate and clean stop |
| Warm pool now | Premature optimization; only justified if it provably preserves isolation, which needs its own evidence |
