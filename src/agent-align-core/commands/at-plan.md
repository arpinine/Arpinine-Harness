---
description: Generate a technical plan and task list for an approved spec. Delegates to spec-kit, then invokes the tech-architect agent to suggest ADRs for consequential decisions.
---

# /at-plan

Turn an approved spec into an executable engineering plan.

## Usage
`/at-plan <slug>`

- `<slug>`: feature slug matching a directory under `.specify/specs/`, e.g. `001-user-login`
- If omitted: list available specs and ask the user to choose

---

## Workflow

1. Resolve the spec path: `.specify/specs/<slug>/spec.md`. Error if not found — list available slugs.
2. Temporarily copy `.specify/specs/<slug>/spec.md` to the project root as `spec.md` so spec-kit can read it.
3. Run `/speckit.plan` and `/speckit.tasks` — these write `plan.md` to the project root.
4. Move the root `plan.md` to `.specify/specs/<slug>/plan.md` and delete the root copy.
5. Delete the temporary root `spec.md` copy.
6. Read `.specify/specs/<slug>/plan.md` and the task list.
7. Invoke the `product-owner` agent to confirm the plan preserves the spec business case, scope, and acceptance criteria.
8. Invoke the `architecture-governor` skill to enforce modular boundaries, dependency direction, and clean separation of concerns.
9. Invoke the `harness-governor` skill for any product feature that depends on an agent harness.
10. Invoke the `tech-architect` agent on `plan.md` to identify architectural decisions that deserve ADRs.
11. For each significant decision:
    - capture a concise decision key such as `decision:001-user-login:session-storage`
    - either link an existing ADR or suggest `/agent-align:at-adr new "..."`
12. Ensure `plan.md` defines:
    - `## Module Boundaries`
    - `## Dependency Rules`
    - `## Testability By Boundary`
    - `## Harness Strategy` when the feature uses a harness in the product application
13. Invoke the `evaluation-governor` skill for agentic or AI-assisted workflows.
14. Create or update `.specify/evals/<slug>/eval-plan.md` with metrics, thresholds, datasets, and the chosen framework command.
15. Update `plan.md` so the `## Technical Decisions`, `## Harness Strategy`, `## Evaluation Strategy`, and `## ADRs Created During Planning` sections reference the governing artifacts explicitly.
16. If no ADR is needed for a decision, state why.
17. Confirm that planning preserved the spec intent rather than redefining it.
18. Confirm: "Plan created at `.specify/specs/<slug>/plan.md`"
