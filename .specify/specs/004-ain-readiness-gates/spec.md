# Spec: AIN Readiness Gates

## Business Case

Arpinine Harness should not let teams implement higher-AIN product behavior without the corresponding contracts, evaluation, and observation readiness. If the product spec claims agent-callable operations, feedback loops, or runtime-dependent behavior, implementation needs explicit gates rather than informal reminders.

AIN readiness gates connect product ambition to engineering discipline. They make AI-nativeness a governed constraint instead of a descriptive label.

## User Stories

- As a product lead, I want AIN level to affect readiness requirements so that ambitious AI behavior is not under-specified.
- As an engineer, I want implementation blockers to be explicit when a spec requires eval or observation planning.
- As a reviewer, I want readiness logic to be deterministic so that Claude, Codex, and CI report the same result.

## Requirements

- FR-001: The plugin SHALL define a stable machine-readable source of truth for AIN level and related gating fields in `spec.md`.
- FR-002: The plugin SHALL determine readiness requirements from the declared AIN level.
- FR-003: For AIN >= 3, the plugin SHALL require agent-callable operations, input/output expectations, failure modes, human gates, and an evaluation plan before implementation proceeds.
- FR-004: For AIN >= 4, the plugin SHALL additionally require feedback channels, observation strategy, and harness strategy where relevant.
- FR-005: The plugin SHALL surface AIN readiness state in status reporting.
- FR-006: The plugin SHALL apply AIN gates through shared implementation-neutral checks.

## Non-Functional Requirements

- NFR-001: AIN parsing SHALL be deterministic and not depend on freeform prose interpretation alone.
- NFR-002: Gates SHALL run outside assistant-specific runtimes.
- NFR-003: AIN readiness messages SHALL explain the missing prerequisite clearly enough for a user to fix the artifact.

## Acceptance Criteria

- [ ] AC-001: Given a spec with declared AIN >= 3 but no eval plan, implementation readiness fails with a clear reason.
- [ ] AC-002: Given a spec with declared AIN >= 4 but no observation strategy, readiness fails with a clear reason.
- [ ] AC-003: Given a compliant AIN >= 3 spec, readiness checks pass when required fields and eval plan are present.
- [ ] AC-004: Given a compliant AIN >= 4 spec, readiness checks pass when feedback and observation requirements are satisfied.
- [ ] AC-005: Given any governed spec, status output shows declared AIN target and readiness state.

## Out of Scope

- Product-quality assessment beyond declared readiness contracts
- Runtime evaluation execution itself
- A universal organizational maturity framework beyond the declared AIN fields

## Operating Constraints

- AIN gating depends on the artifact-validation work providing reliable parsing.
- Body prose may remain human-readable, but machine checks need stable structured fields.
- Host-specific implementations must not fork AIN semantics.

## Open Questions

- OQ-001: Should AIN fields live in YAML frontmatter only, or also be mirrored in body sections for readability?
- OQ-002: Should AIN >= 2 carry any lightweight readiness requirements, or start only at AIN >= 3?
- OQ-003: How should non-agentic features explicitly declare “not applicable” for harness and observation expectations?

## Related ADRs

- ADR-0001
