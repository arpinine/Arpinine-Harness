---
name: at
description: Use the single Arpinine Harness facade in Claude Code to inspect repo state, choose the correct workflow command, explain the route, and delegate.
---

Follow `commands/at.md` from the assembled Arpinine Harness plugin root.

When using this skill in Claude Code:
- execute the facade workflow defined in `commands/at.md`
- call the shared `scripts/route_at.py` implementation to inspect state and compute the route
- treat router output as authoritative rather than inventing local routing logic
- expose the selected underlying `/at-*` command before delegating
- stop speaking as the facade after delegating a handoff command

If the shared command file and this wrapper ever disagree, follow `commands/at.md`.
