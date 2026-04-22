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
5. Enforce RED → GREEN → REFACTOR for each task:
   - failing test first
   - minimal implementation
   - refactor with tests still green
6. Invoke the `security-reviewer` agent on the plan and code changes before concluding the task.
7. Run `/spec-eval run <spec-path>` for any workflow whose plan declares required evaluation.
8. If evaluation fails required thresholds:
   - block completion
   - refine code, prompts, plan, or spec before retrying
9. If a CRITICAL or HIGH drift item is discovered during implementation:
   - stop and run `/spec-audit`
   - require a matching ADR before proceeding
10. If implementation breaks planned boundaries or introduces tight coupling, send the work back into planning or ADR refinement before completion.
11. If implementation changes the original intent, send the work back into refinement by updating the spec or ADRs.
12. Summarize what changed, which tests prove it, which evaluations passed, and which ADRs govern the implementation.
