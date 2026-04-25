---
name: at-init
description: Initialize the AgentAlign workflow in Codex by following the shared at-init workflow and creating the required governance structure.
---

Follow `commands/at-init.md` from the assembled AgentAlign plugin root.

When using this skill in Codex:
- execute the same workflow and file creation steps defined in `commands/at-init.md`
- treat the shared command file as the source of truth
- report which paths were created or verified
- report dependency readiness clearly before claiming setup is complete

If the shared command file and this wrapper ever disagree, follow `commands/at-init.md`.
