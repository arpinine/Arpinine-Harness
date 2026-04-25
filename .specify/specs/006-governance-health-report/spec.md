# Spec: Governance Health Report

## Business Case

AgentAlign needs a single view of governance health that product, engineering, and onboarding teammates can trust. The current status output is useful, but it does not yet fully reflect artifact validity, AIN readiness, rules, observations, and evaluation freshness in one coherent surface.

A stronger governance health report turns the workflow into an inspectable operating system for delivery rather than a collection of isolated commands.

## User Stories

- As a new engineer, I want one command to show the current delivery and governance state so that I can contribute safely.
- As a product lead, I want to see whether AI-nativeness expectations and evaluation readiness are protected.
- As a tech lead, I want a status view driven by structured checks rather than narrative summaries.

## Requirements

- FR-001: The plugin SHALL extend status reporting to include validation state per governed spec.
- FR-002: The plugin SHALL report declared AIN target and AIN readiness when available.
- FR-003: The plugin SHALL report rule counts and recent rule violations when rule execution data exists.
- FR-004: The plugin SHALL report observation coverage and evaluation recency where those artifacts exist.
- FR-005: The plugin SHALL compute and report an Engineering Process score using a documented deterministic formula.
- FR-006: The status view SHALL remain available through shared implementation-neutral tooling.

## Non-Functional Requirements

- NFR-001: Status output SHALL be derived from structured artifacts and checks rather than assistant-only interpretation.
- NFR-002: The report SHALL remain readable to humans while being stable enough to extend later for machine consumption.
- NFR-003: Status generation SHALL tolerate partial repository adoption and show missing dimensions clearly.

## Acceptance Criteria

- [ ] AC-001: Given governed specs with validation output, status shows validation state per spec.
- [ ] AC-002: Given AIN-declared specs, status shows target AIN and readiness.
- [ ] AC-003: Given rule execution data, status shows rule count or recent violations.
- [ ] AC-004: Given observation and eval artifacts, status surfaces their presence or recency.
- [ ] AC-005: Given the documented EP scoring formula, status computes and displays EP per spec.
- [ ] AC-006: Given a new engineer onboarding to the repo, the status view provides enough governance context to identify blockers and next actions without reading every artifact manually.

## Out of Scope

- Real-time production monitoring
- Organization-wide portfolio dashboards outside the repository
- Replacing detailed audit or eval artifacts with a summary-only view

## Operating Constraints

- This work depends on validation, AIN, and rule outputs being structured and trustworthy.
- Status must remain meaningful even when some specs have partial governance adoption.
- Host overlays must expose the same health dimensions.

## Open Questions

- OQ-001: Should status add a JSON output mode now or only after the richer table stabilizes?
- OQ-002: How much recency detail should be shown for evals and observations before the table becomes too noisy?
- OQ-003: Should EP scoring be shown as a number only or number plus named level?

## Related ADRs

- ADR-0001
