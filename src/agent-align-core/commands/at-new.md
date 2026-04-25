---
description: Create a new feature specification as the starting point for the team's shared workflow. Delegates to spec-kit, then validates the result against the constitution.
---

# /at-new

Create the first aligned version of a specification for a named feature.

## Usage
`/at-new <name>`

- `<name>`: human-readable feature name, e.g. `user authentication` or `payment flow`

---

## Workflow

1. Derive the feature slug:
   - Count existing directories under `.specify/specs/` to get the next sequence number `NNN` (zero-padded to 3 digits, starting at `001`)
   - Convert `<name>` to kebab-case
   - Slug = `NNN-kebab-name`, e.g. `002-payment-flow`
2. Create directory `.specify/specs/<slug>/`.
3. Run `/speckit.specify` with the user request — this writes `spec.md` to the project root.
4. Move the generated root `spec.md` to `.specify/specs/<slug>/spec.md` and delete the root copy.
5. Open `.specify/specs/<slug>/spec.md`.
6. Validate that the spec contains:
   - user stories
   - measurable functional and non-functional requirements
   - measurable acceptance criteria
   - explicit out-of-scope items
   - a `## Related ADRs` section, even if initially empty
7. Remove implementation details from the spec. Tech choices belong in `plan.md` or ADRs.
8. If acceptance criteria are vague, rewrite them to be testable.
9. Identify any architectural constraints implied by the spec, such as modularity, replaceable integrations, boundary isolation, or separation of concerns.
10. Add those constraints as product-facing non-functional expectations, not implementation details.
11. If the feature may require an agent harness in the product application, call out that need as an explicit product or operating constraint without naming low-level implementation APIs.
12. Prepare the spec for refinement by calling out open questions, ambiguities, and scope edges.
13. Summarize any constitution fixes that were applied after generation.
14. Confirm: "Spec created at `.specify/specs/<slug>/spec.md`"
