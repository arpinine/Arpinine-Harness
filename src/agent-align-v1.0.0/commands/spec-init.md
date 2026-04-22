---
description: Initialize the shared product-engineering workflow, including spec-kit conventions and ADR structure. Run once per project.
---

# /spec-init

Initialize the shared team workflow.

## Workflow

1. Run `/speckit.constitution`.
2. Ensure these paths exist:
   - `.specify/adr/`
   - `.specify/adr/ADR-INDEX.md`
   - `.specify/evals/`
3. If `ADR-INDEX.md` does not exist, create it with:

```md
# ADR Index

| Number | Title | Status | Governs | Covers |
|--------|-------|--------|---------|--------|
```

4. Confirm the plugin conventions in the repo:
   - `spec.md` captures product intent only
   - `plan.md` captures implementation details
   - `plan.md` must define module boundaries and dependency rules before implementation
   - ADRs capture architectural decisions and drift resolutions
   - eval plans define metrics, thresholds, scenarios, and execution commands
   - refinement happens before implementation and after drift is found
5. Tell the user which files were created or verified.
