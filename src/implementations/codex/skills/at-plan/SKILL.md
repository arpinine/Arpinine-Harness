---
name: at-plan
description: Turn an approved AgentAlign spec into a plan in Codex using the shared at-plan workflow.
---

Follow `commands/at-plan.md` from the assembled AgentAlign plugin root.

When using this skill in Codex:
- execute the same planning workflow defined in `commands/at-plan.md`
- preserve the spec intent rather than redefining it
- create or update the plan and eval artifacts in the shared locations
- call out any shared-agent or shared-skill step that still needs a Codex-native wrapper

If the shared command file and this wrapper ever disagree, follow `commands/at-plan.md`.
