---
name: at-adr
description: Create and manage Arpinine Harness ADRs in Claude Code using the shared at-adr workflow.
---

Follow `commands/at-adr.md` from the assembled Arpinine Harness plugin root.

When using this skill in Claude Code:
- execute the same ADR workflow defined in `commands/at-adr.md`
- keep `.specify/adr/ADR-INDEX.md` aligned with ADR file changes
- preserve `governs:` and `covers:` linkage exactly as the shared workflow requires

If the shared command file and this wrapper ever disagree, follow `commands/at-adr.md`.
