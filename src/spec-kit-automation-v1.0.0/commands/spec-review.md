---
description: Refine a spec before or after implementation. Validate it against the constitution, improve measurability, and realign it when learning has changed the work.
---

# /spec-review

Refine and realign the specification.

## Workflow

1. Open the target `spec.md`.
2. Check that the spec stays product-facing:
   - no frameworks, databases, protocols, or deployment choices
3. Check that each requirement and acceptance criterion is measurable.
4. Check that `## Related ADRs` exists.
5. Check whether the spec is ready for planning or needs another refinement pass.
6. Check whether the spec includes architectural quality expectations when the feature implies modular boundaries, integration seams, or long-lived domain logic.
7. If the spec describes agentic behavior, ensure the evaluation expectations are measurable enough to support an eval plan.
8. If the spec references a decision already implemented in code, ensure the relevant ADR is linked.
9. Report issues as:
   - `CRITICAL`: contradicts implementation or missing governing ADR for a known drift item
   - `HIGH`: ambiguous or untestable requirement
   - `MEDIUM`: missing structure section or weak wording
