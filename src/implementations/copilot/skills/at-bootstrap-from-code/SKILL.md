---
name: at-bootstrap-from-code
description: Assess an existing codebase and seed governed Arpinine Harness artifacts in GitHub Copilot CLI using the shared bootstrap-from-code workflow.
---

Follow `commands/at-bootstrap-from-code.md` from the assembled Arpinine Harness plugin root.

If `commands/at-bootstrap-from-code.md` is missing from the assembled plugin root, stop and report that the shared bootstrap workflow is unavailable instead of improvising a Copilot-only replacement.

When using this skill in GitHub Copilot CLI:
- execute the same bootstrap workflow defined in `commands/at-bootstrap-from-code.md`
- rely on the shared `bootstrap_from_code.py` assessment before drafting governed artifacts
- keep inferred product intent explicit and reviewable rather than presenting it as certainty

If the shared command file and this wrapper ever disagree, follow `commands/at-bootstrap-from-code.md`.
