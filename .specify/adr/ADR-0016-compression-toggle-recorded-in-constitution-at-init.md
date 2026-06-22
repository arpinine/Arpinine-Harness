---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-22
covers:
  - decision:011-context-compression-governance:constitution-toggle
---

# ADR-0016: Record the compression enable/disable toggle in the constitution at /at-init

## Status
Accepted

## Context

Compression is lossy and can change the AI assistant's output (spec business case, AC-003/FR-004). Spec 011 therefore requires compression to be optional, with the choice made at constitution creation (`/at-init`) and recorded in the constitution. Teams that cannot accept any result variance keep it off; teams prioritizing token savings turn it on and rely on the fidelity gate.

A toggle needs a single, auditable, governed home. ADR-0009 establishes the plain-text artifact store under `.specify/`, and the constitution is the existing top-level governance configuration artifact.

## Decision

Store the compression toggle as a single key in `.specify/CONSTITUTION.md`, set once at `/at-init`.

Invariants:

1. Absent key defaults to disabled. Existing installs without the key behave exactly as a pre-feature install (FR-005, RD-003) — no proxy, no overhead.
2. The toggle records only the enabled/disabled flag, not a provider class; provider selection remains behind the `ContextCompressionProvider` interface (ADR-0013).
3. When ADR-0014's network restriction cannot be guaranteed, `/at-init` surfaces the residual-risk acknowledgment alongside the enable choice.

## Consequences

- Positive: One auditable location for the decision; consistent with how governance configuration already lives in the constitution.
- Positive: Default-to-disabled-on-absent-key gives clean backward compatibility for all existing repositories.
- Positive: Establishes a reusable governance precedent for toggling optional harness-level features.
- Negative: No mid-session or per-command override path; testing compression both ways requires re-running `/at-init` or editing the constitution.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Environment variable only | Not governed or auditable; invisible to `/at-status` and review |
| Per-command flag | Spec scopes the decision to constitution-creation time; per-command toggling is explicitly out of scope |
| Default to enabled | Compression can alter results; safe default must be off (business case) |
| Fold into ADR-0013 | Buries a distinct cross-cutting governance pattern inside the abstraction ADR |
