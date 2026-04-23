---
description: Initialize the shared product-engineering workflow, including spec-kit conventions and ADR structure. Run once per project.
---

# /at-init

Initialize the shared team workflow.

## Workflow

1. Run `check-dependencies.sh` from the plugin scripts directory, or perform equivalent environment validation and share the output.
2. If `spec-kit` is missing, stop and install it before relying on automated `/at-*` generation flows.
3. Run `/speckit.constitution`.
4. Ensure these paths exist:
   - `.specify/adr/`
   - `.specify/adr/ADR-INDEX.md`
   - `.specify/evals/`
   - `.specify/observations/`
   - `.specify/rules/`
5. If `ADR-INDEX.md` does not exist, create it with:

```md
# ADR Index

| Number | Title | Status | Governs | Covers |
|--------|-------|--------|---------|--------|
```

6. Confirm the plugin conventions in the repo:
   - `spec.md` captures product intent only
   - `plan.md` captures implementation details
   - `plan.md` must define module boundaries and dependency rules before implementation
   - harness-based product features must document harness strategy before implementation
   - ADRs capture architectural decisions and drift resolutions
   - eval plans define metrics, thresholds, scenarios, and execution commands
   - observations capture actual runtime behavior for later drift analysis
   - rules compound across projects — lessons from retros live in `.specify/rules/`
   - refinement happens before implementation and after drift is found
7. Tell the user which files were created or verified.
8. Report dependency status clearly:
   - `spec-kit` required for automated generation and planning
   - harness runtime required only when selected in `## Harness Strategy`
   - eval tool required only when selected in `eval-plan.md`
