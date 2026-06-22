---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-22
covers:
  - decision:011-context-compression-governance:provider-abstraction
---

# ADR-0013: One shared ContextCompressionProvider abstraction with swappable implementations

## Status
Accepted

## Context

Spec 011 introduces context compression across all three host implementations (Claude, Codex, Copilot). The repository already establishes a consistent pattern for cross-cutting integrations: one shared core abstraction with a swappable default implementation and a noop fallback (ADR-0001 core/impl separation; the observation and evaluation provider templates follow the same shape).

Context compression must follow that pattern rather than embedding headroom-specific or host-specific logic across the codebase. If host integrations or the fidelity benchmark depended directly on headroom, swapping the compression engine would require touching every host and the benchmark, and the abstraction boundary the spec mandates (FR-001, FR-010, RD-001) would erode.

The interface is also the load-bearing surface for two subtle requirements: reversible retrieval (FR-009, AC-007) needs a stable segment-key contract, and the lifecycle must be expressible by a noop implementation that starts no process.

## Decision

Define a single `ContextCompressionProvider` interface as the sole harness-facing surface for governed context compression, with `compress`, `retrieve`, `activate`, and `deactivate` operations.

**Amended (Option A, proxy-only).** Live integration against `headroom-ai==0.27.0`
showed compression in the chosen model (ADR-0015) happens **transparently inside
the proxy at the HTTP layer** — the host points its provider base-URL at a local
`headroom proxy` and the harness never calls a per-payload `compress()`/`retrieve()`
in-process (it cannot — that was the reason for proxy mode). headroom's library
`compress(messages)` exists but is library-mode, not the transport path. Therefore
the harness-facing interface is **lifecycle-only**; per-payload compression and
reversible retrieval (CCR) are owned by headroom, not re-implemented in the harness.

Constraints that make the abstraction durable:

1. The interface has zero dependencies. It MUST NOT reference headroom, any proxy/port concept, any host API, or the constitution.
2. The interface is lifecycle-only: `activate() -> CompressionEndpoint` and `deactivate()`. Names are vendor/transport-neutral so the noop implementation satisfies them as no-ops.
3. `activate()` returns only an **opaque endpoint token** to host integrations — never the proxy's raw port/address — so host wirings cannot couple to network coordinates.
4. Per-payload `compress()`/`retrieve()` are NOT on the harness interface. Compression is transparent in the proxy; reversible retrieval (CCR) is owned by the headroom engine. (Superseded the earlier compress/retrieve + segment-key design.)
5. The data boundary (governed artifacts stay DATA) is preserved by the proxy transform and asserted by the fidelity benchmark; it is not a per-call harness responsibility.

The default (headroom) and noop implementations are both selected through this interface.

## Consequences

- Positive: Host integrations and the fidelity benchmark depend only on the interface; the compression engine is swappable without touching them.
- Positive: The noop path is a first-class implementation, making "compression disabled" a clean substitution rather than scattered conditionals.
- Positive: The opaque-endpoint rule prevents latent coupling between the three host wirings and the proxy's network details.
- Negative: Getting the lifecycle contract wrong is expensive to reverse once all three hosts are wired against it, so the interface must be settled before host wiring (TASK-006) begins.
- Positive (Option A): a lifecycle-only interface shrinks the harness's security surface — no harness-side payload handling or CCR storage to get wrong; headroom owns compression and CCR.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Call headroom directly from each host | Couples every host + the benchmark to a vendor; defeats the swap requirement (FR-010) |
| Expose the proxy port/address through the lifecycle API | Couples host wirings to network coordinates; brittle across lifecycle models |
| Fold the retrieve segment-key contract into implementation detail | Byte-equality (AC-007) cannot be asserted stably without a governed key scheme |
