---
governs: specs/002-arpinine-harness-core-workflow
supersedes: ~
status: Accepted
date: 2026-05-04
covers:
  - decision:002-arpinine-harness-core-workflow:plain-text-artifact-store
---

# ADR-0009: Plain-text version-controlled artifact store under .specify/

## Status
Accepted

## Context
The governance workflow produces structured artifacts throughout a delivery cycle: specs, plans, ADRs, eval plans, observations, drift reports, and compounding rules. These artifacts must be readable by enforcement scripts, diffable in pull request review, trustworthy (no hidden mutable state), and accessible across independent Claude Code sessions with no shared in-memory state.

Two broad storage models were considered: version-controlled plain text in the repository, and an external state backend (database, cloud store, or external service).

## Decision
All governance artifacts are stored as plain-text Markdown and JSON files under `.specify/` in the repository root. The directory structure is:

```
.specify/
  specs/<slug>/       ← spec.md, plan.md
  adr/                ← ADR-NNNN-*.md, ADR-INDEX.md
  evals/<slug>/       ← eval-plan.md, latest-results.md
  observations/<slug>/← latest-observation.md, trace.json
  rules/              ← machine-readable compounding rule files
```

Governance state is fully derivable from the repository checkout. Scripts read from `.specify/` directly. No database connection, credentials, or network access is required at runtime.

## Consequences
- Positive: Artifacts are reviewable and diffable in standard code review tooling — governance decisions are visible to the whole team.
- Positive: Session independence (NFR-006) is satisfied: any session can reconstruct full governance state from a repo checkout with no warm-up.
- Positive: No infrastructure dependency — governance works in any environment where the repository is checked out.
- Positive: Compounding rules accumulate in version history, providing an auditable governance trail.
- Negative: Artifact store grows without automatic pruning; stale observations and drift reports accumulate over time.
- Negative: Concurrent writes from multiple sessions can produce merge conflicts in artifact files. File-based locking (ADR-0005) mitigates this for task coordination but not for all artifact types.
- Negative: Large binary or structured data (e.g., eval traces) stored as JSON under `.specify/` will grow repository size over time.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| External database (SQLite, Postgres, etc.) | Requires infrastructure; breaks session independence; adds setup burden for new team members |
| External service (cloud store, Linear, Notion) | Network dependency; credentials required; not diffable in PR review |
| In-memory state per session | Lost on session end; incompatible with multi-session and multi-team workflows |
