---
name: at-audit
description: Detect and realign Arpinine Harness drift in Claude Code using the shared at-audit workflow.
---

Follow `commands/at-audit.md` from the assembled Arpinine Harness plugin root.

When using this skill in Claude Code:
- execute the same audit workflow defined in `commands/at-audit.md`
- use the shared drift detection scripts when available
- classify findings and route them through spec refinement, ADR creation, or implementation fixes exactly as the shared workflow requires

If the shared command file and this wrapper ever disagree, follow `commands/at-audit.md`.
