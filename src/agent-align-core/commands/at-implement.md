---
description: Execute an approved plan with TDD and security review, while keeping implementation aligned to the spec and ADRs.
---

# /at-implement

Execute the agreed work without drifting from intent.

## Usage
`/at-implement <slug>`

- `<slug>`: feature slug matching a directory under `.specify/specs/`, e.g. `001-user-login`
- If omitted: list available specs and ask the user to choose

---

## Workflow

1. Read `.specify/specs/<slug>/spec.md`, `.specify/specs/<slug>/plan.md`, and linked ADRs before changing code.
2. Invoke the `product-owner` agent before implementation starts to identify business-case and acceptance-criteria risks.
3. Invoke the `tdd-guide` agent before implementation starts.
4. Run `/speckit.implement`.
5. Preserve the module boundaries and dependency direction defined in `plan.md`.
6. If the feature uses a harness in the product application, preserve the harness abstraction boundary, tool model, memory model, and permission model defined in `## Harness Strategy`.
7. For each task in `plan.md`:
   a. Before starting work on the task: change its checkbox from `[ ]` to `[~]` in `plan.md`.
   b. Enforce RED → GREEN → REFACTOR:
      - failing test first
      - minimal implementation
      - refactor with tests still green
   c. When the task is complete (tests green, acceptance criteria met): change its checkbox from `[~]` to `[x]` in `plan.md`.
   The `[~]` → `[x]` edit triggers the delivery matrix hook automatically.
8. Invoke the `product-owner` agent before completion to compare implementation evidence against the spec business case and acceptance criteria.
9. Invoke the `security-reviewer` agent on the plan and code changes before concluding the task.
10. Run `/agent-align:at-eval run <slug>` for any workflow whose plan declares required evaluation.
11. If evaluation fails required thresholds:
   - block completion
   - refine code, prompts, plan, or spec before retrying
12. If a CRITICAL or HIGH drift item is discovered during implementation:
   - stop and run `/agent-align:at-audit`
   - require a matching ADR before proceeding
13. If implementation breaks planned boundaries or introduces tight coupling, send the work back into planning or ADR refinement before completion.
14. If harness behavior exceeds the documented tool, memory, or permission model, send the work back into planning or ADR refinement before completion.
15. If implementation changes the original intent or weakens the business case, send the work back into refinement by updating the spec or ADRs.
16. Summarize what changed, which tests prove it, which evaluations passed, which acceptance criteria were satisfied, and which ADRs govern the implementation.
