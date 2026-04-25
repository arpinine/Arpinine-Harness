---
description: Refine a spec before or after implementation. Validate it against the constitution, improve measurability, and realign it when learning has changed the work.
---

# /at-review

Refine and realign the specification.

## Usage
`/at-review <slug>`

- `<slug>`: feature slug matching a directory under `.specify/specs/`, e.g. `001-user-login`
- If omitted: list available specs and ask the user to choose

---

## Workflow

1. Open `.specify/specs/<slug>/spec.md`.
2. Invoke the `product-owner` agent to verify business case, user value, scope, and acceptance criteria.
3. Check that the spec stays product-facing:
   - no frameworks, databases, protocols, or deployment choices
4. Check that each requirement and acceptance criterion is measurable.
5. Check that `## Related ADRs` exists.
6. Check whether the spec is ready for planning or needs another refinement pass.
7. Check whether the spec includes architectural quality expectations when the feature implies modular boundaries, integration seams, or long-lived domain logic.
8. If the product feature implies a harness-based agent workflow, ensure the spec makes that operational need explicit enough to drive a later harness strategy.
9. If the spec describes agentic behavior, ensure the evaluation expectations are measurable enough to support an eval plan.
10. If the spec references a decision already implemented in code, ensure the relevant ADR is linked.
11. For any CRITICAL or HIGH issue that can be resolved by clarification, ask the user the minimum focused questions needed to resolve it, then update `spec.md` directly instead of asking the user to edit the document.
12. Report unresolved issues as:
   - `CRITICAL`: contradicts implementation or missing governing ADR for a known drift item
   - `HIGH`: ambiguous or untestable requirement
   - `MEDIUM`: missing structure section or weak wording
