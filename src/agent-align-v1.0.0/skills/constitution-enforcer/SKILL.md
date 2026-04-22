---
name: constitution-enforcer
description: Extends spec-kit's constitution with ADR-linkage and drift-coverage enforcement rules
---

# Constitution Enforcer Skill

## Scope
Spec-kit owns base constitution: spec quality, acceptance criteria format, test-first, security section in plan.
This skill enforces ADR, drift, evaluation, and architecture-specific rules that extend the base constitution.

## Plugin-Specific Rules

| Rule | Severity | Action |
|------|----------|--------|
| CRITICAL or HIGH drift item exists without ADR whose `governs:` and `covers:` both match | CRITICAL | Block implementation |
| ADR `governs:` field is empty or `~` after Proposed status | HIGH | Warn; require field |
| ADR `covers:` is empty for a drift-resolution ADR | HIGH | Warn; require field |
| Agentic workflow has no eval plan or thresholds | HIGH | Block completion |
| Agentic workflow has failing required evaluation | CRITICAL | Block completion |
| Spec missing `## Related ADRs` section | MEDIUM | Suggest adding section |
| Plan missing `## ADRs Created During Planning` section | MEDIUM | Suggest adding section |
| Plan missing `## Evaluation Strategy` for agentic work | MEDIUM | Suggest adding section |
| Plan missing `## Module Boundaries` for non-trivial work | HIGH | Block implementation |
| Plan missing `## Dependency Rules` or `## Testability By Boundary` | HIGH | Block implementation |
| Harness-based feature missing `## Harness Strategy` | HIGH | Block implementation |
| Harness boundary, tool model, memory model, permission model, or swap strategy is undocumented | HIGH | Block implementation |
| Architecture decision with long-term impact is not documented in plan or ADR | MEDIUM | Require clarification |
| Observation artifacts contradict documented harness strategy or evaluation coverage | CRITICAL | Block completion |
| ADR status still Proposed when implementation starts | HIGH | Warn; require Accepted |
| ADR `supersedes:` missing when status = Superseded | HIGH | Block status update |

## What This Skill Does NOT Check (spec-kit's job)
- Technical details (FastAPI, PostgreSQL, etc.) in spec.md
- Measurable acceptance criteria format
- Test-before-code enforcement
- Security section presence in plan.md

## Enforcement Points
- Pre-implementation: run full rule check
- Post-drift-detection: check ADR coverage for CRITICAL/HIGH items
- Pre-completion: check evaluation plan, thresholds, and latest results for agentic work
- Pre-implementation: check architecture sections and module/test boundary clarity
- Pre-implementation: check harness strategy for harness-based application flows
- Pre-completion: check observations against harness strategy when observation artifacts exist
- On `/spec-adr status` update: check Superseded invariants
