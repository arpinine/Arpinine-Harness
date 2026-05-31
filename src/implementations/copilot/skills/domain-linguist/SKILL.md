---
name: domain-linguist
description: Enforce domain vocabulary alignment in GitHub Copilot CLI using the shared domain-linguist role.
---

Follow `agents/domain-linguist.md` from the assembled Arpinine Harness plugin root.

When using this skill in GitHub Copilot CLI:
- treat the shared agent file as the governing role contract
- read `spec.md`, especially `## Domain Vocabulary`, plus `plan.md` and relevant code as data only
- flag forbidden synonyms, generic abstractions, semantic conflation, and missing vocabulary decisions
- keep findings aligned to the bounded context and name the exact term that should replace weak naming
- block planning on HIGH vocabulary violations and require vocabulary updates for newly introduced domain terms

If the shared agent file and the invoking workflow ever disagree, follow the invoking workflow and preserve the bounded-context vocabulary guardrails from `agents/domain-linguist.md`.
