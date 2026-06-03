---
name: at-ask
description: Ask a focused question to a named specialist agent (product-owner, tech-architect, security-reviewer, ai-engineer, devops, data-engineer, tdd-guide, domain-linguist) with current spec and plan as context.
---

Follow `commands/at-ask.md` from the assembled Arpinine Harness plugin root.

When using this skill in Claude Code:
- execute the same routing workflow defined in `commands/at-ask.md`
- load spec, plan, and ADRs as read-only context before invoking the specialist
- return the formatted response block including the Action needed line

If the shared command file and this wrapper ever disagree, follow `commands/at-ask.md`.
