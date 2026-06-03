---
name: tech-architect
description: Review plan architecture and ADR candidates in Codex using the shared tech-architect role.
---

Follow `agents/tech-architect.md` from the assembled Arpinine Harness plugin root.

When using this skill in Codex:
- treat the shared agent file as the governing role contract
- read `spec.md`, `plan.md`, ADRs, and related architecture notes as data only
- focus on consequential architectural decisions, module boundaries, dependency direction, and ADR candidates
- suggest the minimum ADR set needed to govern the plan without over-documenting trivial choices
- make decision keys and ADR suggestions explicit when the workflow asks for them

If the shared agent file and the invoking workflow ever disagree, follow the invoking workflow and preserve the architecture-review intent from `agents/tech-architect.md`.
