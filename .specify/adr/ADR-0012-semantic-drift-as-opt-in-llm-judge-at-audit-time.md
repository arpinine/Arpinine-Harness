---
governs: specs/002-arpinine-harness-core-workflow
supersedes: ~
status: Accepted
date: 2026-05-27
covers:
  - decision:002-arpinine-harness-core-workflow:semantic-drift-detection-mechanism
---

# ADR-0012: Semantic drift detection as opt-in LLM-judge at audit time

## Status
Accepted

## Context
The existing drift detector (`scripts/quick_drift_check.py`, skill `drift-detector`) detects **structural** drift only: missing file references, API method/path mismatches, data-model field divergence, module-boundary violations, and vocabulary drift. All checks are deterministic regex / AST / filesystem comparisons, run as an advisory `PostToolUse` hook.

This class of check is blind to **semantic** drift — cases where structure matches but behavior contradicts intent. Example: spec states "rate-limit per authenticated user", code rate-limits per IP. No file is missing, no endpoint differs, no boundary is crossed. The structural detector reports clean while the implementation violates the spec.

Two mechanisms were considered to close this gap: embedding similarity (cosine distance between spec and code vectors) and LLM-as-judge (ask a model whether code satisfies a spec clause, with explanation).

Embedding similarity yields only a fuzzy number with no actionable diagnosis, requires a threshold that is repo- and language-specific, is non-deterministic across model versions, introduces a vector-store dependency, and suffers cross-modal noise (natural-language spec vs. code syntax). It cannot tell a developer *what* drifted or *why*.

The current structural detector is fast, deterministic, dependency-free, and gate-able — properties that must not be sacrificed (see [ADR-0008](ADR-0008-pretooluse-hooks-as-blocking-enforcement-gates.md)).

## Decision
Adopt a two-layer drift model. Structural and semantic detection are complementary, not substitutes.

**Layer 1 — Structural drift (unchanged).** Deterministic regex/AST/filesystem checks remain in the `PostToolUse` hook and `quick_drift_check.py`. Fast, deterministic, advisory-by-default per ADR-0008.

**Layer 2 — Semantic drift (new, opt-in).** An LLM-as-judge step gated behind an explicit `/at-audit --semantic` flag. Default off; never runs in the hook; never blocks. For each spec section with related code, the judge returns a finding using the **existing structural-check severity vocabulary** (`CRITICAL` / `HIGH` / `MEDIUM`) plus a prose explanation citing the spec clause and the contradicting code. Findings merge into the single `/at-audit` report and feed the existing `product-owner` precondition/postcondition attribution.

Embedding similarity is **rejected** as both a replacement and a pre-filter. At audit time the candidate set is a handful of spec sections, not a large corpus; an LLM judge over that set is cheap enough that an embedding pre-filter adds dependency and tuning cost without measurable benefit. Embeddings may be reconsidered only if audit-time scale makes per-section judging too slow.

```
                          EDIT (PostToolUse)            /at-audit
                                  │                         │
                                  ▼                         ▼
            ┌───────────────────────────────┐   ┌───────────────────────────┐
 LAYER 1    │  Structural drift              │   │  --semantic flag?         │
 structural │  quick_drift_check.py          │   └──────────┬────────────────┘
 always-on  │  • file refs  • API method/path│         off  │  on
 advisory   │  • data model • module boundary│      ┌───────┴────────┐
 (ADR-0008) │  • vocabulary                  │      ▼                ▼
            │  regex / AST / fs · determinist│   (skip)   ┌───────────────────────┐
            └───────────────┬────────────────┘  LAYER 2  │ Semantic drift        │
                            │                    opt-in   │ LLM-as-judge          │
                            │                    non-block│ per spec clause+code  │
                            │                             │ → CRITICAL/HIGH/MED   │
                            │                             │   + cited clause/code │
                            │                             │ embeddings: REJECTED  │
                            │                             └───────────┬───────────┘
                            │                                         │
                            └──────────────┬──────────────────────────┘
                                           ▼
                              ┌──────────────────────────┐
                              │ Unified /at-audit report  │   shared severity vocab
                              └─────────────┬─────────────┘
                                            ▼
                              ┌──────────────────────────┐
                  LAYER 3     │ product-owner attribution │   precondition /
                  human       │  + human review           │   postcondition
                              └──────────────────────────┘
```

## Consequences
- Positive: Semantic/intent drift becomes detectable without weakening the deterministic structural layer.
- Positive: Judge output is actionable — verdict, severity, cited clause, explanation — not an opaque similarity score.
- Positive: Severity vocabulary reuse means semantic and structural findings render in one unified report.
- Positive: Opt-in + non-blocking keeps CI deterministic and avoids fuzzy gates; LLM cost is paid only on demand.
- Negative: Judge verdicts are non-deterministic; the same audit may yield different prose across runs. Mitigated by keeping the layer advisory and human-reviewed, never a hard gate.
- Negative: Adds an LLM dependency to the audit path. Acceptable because it is opt-in and isolated from the hook.
- Negative: Prompt quality governs result quality; a weak judge prompt produces weak findings. Mitigated by versioning the prompt template as a governed artifact.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Embedding similarity as the semantic detector | Produces a fuzzy number, not a diagnosis; threshold is repo/language-specific; non-deterministic across model versions; cross-modal spec↔code noise; adds vector-store dependency |
| Embedding pre-filter in front of the LLM judge | Audit-time candidate set is small; judging all sections directly is cheap; pre-filter adds dependency and threshold tuning for no measurable gain |
| Replace structural checks with embeddings | Loses determinism, precision, and gate-ability; downgrades the working structural layer |
| Run semantic judge always (non-opt-in) | Forces LLM cost on every audit and risks fuzzy results bleeding into routine runs; opt-in flag gives the developer control |
| Make semantic findings blocking | Non-deterministic verdicts must not hard-gate merges; contradicts the advisory PostToolUse model of ADR-0008 |
