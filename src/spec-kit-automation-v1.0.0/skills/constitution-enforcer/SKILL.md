---
name: constitution-enforcer
description: Extends spec-kit's constitution with ADR-linkage and drift-coverage enforcement rules
---

# Constitution Enforcer Skill

## Scope
Spec-kit owns base constitution: spec quality, acceptance criteria format, test-first, security section in plan.
This skill enforces **ADR and drift-specific rules only** — it extends, not replaces, spec-kit.

## Plugin-Specific Rules

| Rule | Severity | Action |
|------|----------|--------|
| CRITICAL or HIGH drift item exists without governing ADR | CRITICAL | Block implementation |
| ADR `governs:` field is empty or `~` after Proposed status | HIGH | Warn; require field |
| Spec missing `## Related ADRs` section | MEDIUM | Suggest adding section |
| Plan missing `## ADRs Created During Planning` section | MEDIUM | Suggest adding section |
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
- On `/spec-adr status` update: check Superseded invariants
