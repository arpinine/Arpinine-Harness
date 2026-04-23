---
description: Create a new feature specification as the starting point for the team's shared workflow. Delegates to spec-kit, then validates the result against the constitution.
---

# /at-new

Create the first aligned version of a specification.

## Workflow

1. Run `/speckit.specify` with the user request.
2. Open the generated `spec.md`.
3. Validate that the spec contains:
   - user stories
   - measurable functional and non-functional requirements
   - measurable acceptance criteria
   - explicit out-of-scope items
   - a `## Related ADRs` section, even if initially empty
4. Remove implementation details from `spec.md`. Tech choices belong in `plan.md` or ADRs.
5. If acceptance criteria are vague, rewrite them to be testable.
6. Identify any architectural constraints implied by the spec, such as modularity, replaceable integrations, boundary isolation, or separation of concerns.
7. Add those constraints as product-facing non-functional expectations, not implementation details.
8. If the feature may require an agent harness in the product application, call out that need as an explicit product or operating constraint without naming low-level implementation APIs.
9. Prepare the spec for refinement by calling out open questions, ambiguities, and scope edges.
10. Summarize any constitution fixes that were applied after generation.
