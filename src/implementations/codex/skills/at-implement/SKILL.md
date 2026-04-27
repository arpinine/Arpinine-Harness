---
name: at-implement
description: Execute an Arpinine Harness plan in Codex using the shared at-implement workflow.
---

Follow `commands/at-implement.md` from the assembled Arpinine Harness plugin root.

When using this skill in Codex:
- execute the same implementation workflow defined in `commands/at-implement.md`
- treat `codex` as the team identity for task claims; override `ARPININE_HARNESS_TEAM_ID` only if the host runtime cannot expose its plugin identity
- update `plan.md` task checkboxes as work starts and completes
- preserve boundary, harness, evaluation, and security requirements from the shared workflow

If the shared command file and this wrapper ever disagree, follow `commands/at-implement.md`.
