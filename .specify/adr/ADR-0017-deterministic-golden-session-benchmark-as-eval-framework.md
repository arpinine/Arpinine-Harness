---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-22
covers:
  - decision:011-context-compression-governance:eval-framework
---

# ADR-0017: Deterministic golden-session replay benchmark as the evaluation framework

## Status
Accepted

## Context

Spec 011 requires evaluation (Evaluation Required: YES) because compression can change results. The success gate is: replay a fixed golden harness session with compression ON vs OFF and require identical governance outcomes plus 60–95% token reduction (AC-001, AC-002, RD-005, RD-009, RD-010).

The harness default evaluation framework is DeepEval (LLM-judged quality scoring). That is the wrong tool here: the gate is an exact structural comparison of governance outcomes, not a subjective quality score. An LLM judge would introduce nondeterminism into a gate whose entire purpose is to prove determinism was preserved.

## Decision

Gate compression-enabled releases with a deterministic golden-session replay benchmark instead of DeepEval.

Components and constraints:

1. Runner: `run_golden_session_benchmark.py` replays each recorded `/at-*` run with compression ON and OFF and measures session-total outbound prompt tokens.
2. Gate: `FidelityGate` (`fidelity_gate.py`) performs a zero-divergence diff over the governance outcome set — routing-decision fields (`route`, `confidence`, `command_class`, `requires_confirmation`), drift-finding records (file, line, severity, id), and AC checkbox states. Any single differing field is a FAIL. No materiality tolerance.
3. Token measurement occurs at the proxy boundary (the single point seeing both payloads), never estimated from provider billing — a hard constraint because billing-derived counts drift across model versions and pricing.
4. A reduction above 95% is a FAIL, not a bonus: it signals over-aggressive compression risking dropped governance content. PASS requires both empty diff and reduction within 60–95%.
5. The golden session includes at least one adversarial directive-shaped artifact case to prove the DATA boundary survives compression.

## Consequences

- Positive: The gate is fully reproducible and exact — correct for a governance harness where outcome correctness is non-negotiable.
- Positive: Token measurement at the proxy is reliable and provider-agnostic.
- Negative: The golden session must be representative and maintained as the harness evolves; a stale session gives false confidence.
- Negative: This deviates from the DeepEval default and sets a precedent feature teams may cite to bypass LLM-judged evaluation — acceptable here because the gate is genuinely structural.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| DeepEval LLM-judged scoring | Nondeterministic; cannot prove exact governance-outcome preservation |
| Compare only token reduction | Ignores the central risk: silently changed governance decisions |
| Estimate tokens from provider billing | Unreliable across model versions and pricing; not measurable at the boundary |
| Allow a materiality tolerance on the diff | A governance harness cannot accept silent decision drift; zero divergence is the point |
