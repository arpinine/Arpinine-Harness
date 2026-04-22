---
description: Execute an approved plan with TDD and security review, while keeping implementation aligned to the spec and ADRs.
---

# /spec-implement

Execute the agreed work without drifting from intent.

## Workflow

1. Read the governing `spec.md`, `plan.md`, and linked ADRs before changing code.
2. Invoke the `tdd-guide` agent before implementation starts.
3. Run `/speckit.implement`.
4. Preserve the module boundaries and dependency direction defined in `plan.md`.
5. If the feature uses a harness in the product application, preserve the harness abstraction boundary, tool model, memory model, and permission model defined in `## Harness Strategy`.
6. Enforce RED → GREEN → REFACTOR for each task:
   - failing test first
   - minimal implementation
   - refactor with tests still green
7. Invoke the `security-reviewer` agent on the plan and code changes before concluding the task.
8. Run `/spec-eval run <spec-path>` for any workflow whose plan declares required evaluation.
9. If evaluation fails required thresholds:
   - block completion
   - refine code, prompts, plan, or spec before retrying
10. If a CRITICAL or HIGH drift item is discovered during implementation:
   - stop and run `/spec-audit`
   - require a matching ADR before proceeding
11. If implementation breaks planned boundaries or introduces tight coupling, send the work back into planning or ADR refinement before completion.
12. If harness behavior exceeds the documented tool, memory, or permission model, send the work back into planning or ADR refinement before completion.
13. If implementation changes the original intent, send the work back into refinement by updating the spec or ADRs.
14. Summarize what changed, which tests prove it, which evaluations passed, and which ADRs govern the implementation.
