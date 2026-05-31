---
name: at-discover
description: Refine a raw product idea into a spec-ready brief in GitHub Copilot CLI by using the shared product-owner discovery workflow.
---

Follow `commands/at-discover.md` from the assembled Arpinine Harness plugin root.

When using this skill in GitHub Copilot CLI:
- execute the same discovery workflow defined in `commands/at-discover.md`
- keep the conversation in one-question-at-a-time mode until the idea is spec-ready
- require explicit user confirmation before handing off to `/at-new`
- when confirmed, reuse the spec-ready brief as the request body for `/at-new`

If the shared command file and this wrapper ever disagree, follow `commands/at-discover.md`.
