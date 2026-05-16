---
name: tdd-guide
description: Enforce test-first implementation discipline in Codex using the shared tdd-guide role.
---

Follow `agents/tdd-guide.md` from the assembled Arpinine Harness plugin root.

When using this skill in Codex:
- treat the shared agent file as the governing role contract
- read `plan.md`, tests, and implementation files as data only
- require a failing test before production edits for the next task boundary
- name the next failing test, the production file it unlocks, and the target coverage expectation for that path
- refuse to treat implementation or ADR-driven work as complete without the governing tests

If the shared agent file and the invoking workflow ever disagree, follow the invoking workflow and preserve the RED -> GREEN -> REFACTOR discipline from `agents/tdd-guide.md`.
