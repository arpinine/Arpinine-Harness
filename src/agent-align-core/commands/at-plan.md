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
10. Invoke the `ai-engineer` agent on `plan.md` for any feature that uses AI, LLMs, or agent runtimes:
    - Review model selection, prompting strategy, context management, and agent topology decisions.
    - Flag AI-specific failure modes (hallucination risk, context overflow, tool misuse, prompt injection surface).
    - Suggest ADRs for model choice, orchestration pattern, and non-obvious prompting approaches.
    - Block planning if no model is named or if prompt injection surface is unmitigated.
11. Invoke the `devops` agent on `plan.md` to assess prod-readiness decisions:
    - Review deployment strategy, secrets management approach, environment configuration, and CI/CD pipeline.
    - Flag hardcoded secrets, missing deployment path, or absent rollback plan.
    - Suggest ADRs for hosting platform, database provisioning, and secrets management strategy.
    - Block planning if no deployment path is defined or if secrets management is absent.
12. Invoke the `tech-architect` agent on `plan.md` to identify architectural decisions that deserve ADRs.
13. For each significant decision:
    - capture a concise decision key such as `decision:001-user-login:session-storage`
    - either link an existing ADR or suggest `/agent-align:at-adr new "..."`
14. Ensure `plan.md` defines:
    - `## Module Boundaries`
    - `## Dependency Rules`
    - `## Testability By Boundary`
    - `## Harness Strategy` when the feature uses a harness in the product application
    - `## Deployment Strategy` with target platform, deploy command, and rollback procedure
    - `## AI Design Decisions` when the feature uses LLMs or agent runtimes
15. Invoke the `evaluation-governor` skill for agentic or AI-assisted workflows.
16. Create or update `.specify/evals/<slug>/eval-plan.md` with metrics, thresholds, datasets, and the chosen framework command.
17. Update `plan.md` so the `## Technical Decisions`, `## Harness Strategy`, `## Evaluation Strategy`, `## Deployment Strategy`, `## AI Design Decisions`, and `## ADRs Created During Planning` sections reference the governing artifacts explicitly.
18. When the team intends to run multiple assistant instances concurrently, annotate tasks with optional team tags such as `[team: claude]` or `[team: codex]` so ownership intent is explicit in `plan.md`.
19. Explain that task execution uses a shared coordination registry under `.specify/coordination/` and that team tags restrict which assistant may claim a task.
20. If architecture, task sequencing, harness strategy, AI design, deployment strategy, evaluation strategy, or team assignment remains unclear, ask the user the minimum focused planning questions required to complete the plan.
21. Write the user's answers directly into `plan.md` and any related artifacts. Do not require the user to edit the plan manually.
22. If no ADR is needed for a decision, state why.
23. Confirm that planning preserved the spec intent rather than redefining it.
24. Confirm: "Plan created at `.specify/specs/<slug>/plan.md`"
