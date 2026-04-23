---
description: Generate a technical plan and task list for an approved spec. Delegates to spec-kit, then invokes the tech-architect agent to suggest ADRs for consequential decisions.
---

# /spec-plan

Turn an approved spec into an executable engineering plan.

## Workflow

1. Run `/speckit.plan`.
2. Run `/speckit.tasks`.
3. Read the resulting `plan.md` and task list.
4. Invoke the `product-owner` agent to confirm the plan preserves the spec business case, scope, and acceptance criteria.
5. Invoke the `architecture-governor` skill to enforce modular boundaries, dependency direction, and clean separation of concerns.
6. Invoke the `harness-governor` skill for any product feature that depends on an agent harness.
7. Invoke the `tech-architect` agent on `plan.md` to identify architectural decisions that deserve ADRs.
8. For each significant decision:
   - capture a concise decision key such as `decision:001-user-login:session-storage`
   - either link an existing ADR or suggest `/spec-adr new "..."`
9. Ensure `plan.md` defines:
   - `## Module Boundaries`
   - `## Dependency Rules`
   - `## Testability By Boundary`
   - `## Harness Strategy` when the feature uses a harness in the product application
10. Invoke the `evaluation-governor` skill for agentic or AI-assisted workflows.
11. Create or update `.specify/evals/<spec-slug>/eval-plan.md` with metrics, thresholds, datasets, and the chosen framework command.
12. Update `plan.md` so the `## Technical Decisions`, `## Harness Strategy`, `## Evaluation Strategy`, and `## ADRs Created During Planning` sections reference the governing artifacts explicitly.
13. If no ADR is needed for a decision, state why.
14. Confirm that planning preserved the spec intent rather than redefining it.
