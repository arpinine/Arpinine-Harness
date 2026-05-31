---
name: at-init
description: Initialize the Arpinine Harness workflow in GitHub Copilot CLI by following the shared at-init workflow and creating the required governance structure.
---

Follow `commands/at-init.md` from the assembled Arpinine Harness plugin root.

When using this skill in GitHub Copilot CLI:
- execute the same workflow and file creation steps defined in `commands/at-init.md`
- treat the shared command file as the source of truth
- report which paths were created or verified
- report dependency readiness clearly before claiming setup is complete

If the shared command file and this wrapper ever disagree, follow `commands/at-init.md`.
