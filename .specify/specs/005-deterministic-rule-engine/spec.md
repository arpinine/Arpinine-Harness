# Spec: Deterministic Rule Engine

## Business Case

Retrospectives and audits only compound value if their lessons become enforceable. Today AgentAlign can describe rules in markdown, but recurring failures can still reappear unless there is a deterministic execution path that turns those rules into repeatable checks.

A first deterministic rule engine lets the plugin prevent or report known classes of failure without depending purely on assistant interpretation.

## User Stories

- As a team, I want recurring lessons captured as executable rules so that the same avoidable mistake is not repeated silently.
- As an engineer, I want rule violations reported with file-level evidence so that I can fix them quickly.
- As a maintainer, I want rule execution to be implementation-neutral and reusable from hooks, drift checks, audit, and status.

## Requirements

- FR-001: The plugin SHALL define a structured executable field schema for rule files.
- FR-002: The plugin SHALL provide a deterministic rule-checking script in shared core tooling.
- FR-003: The rule checker SHALL support structured JSON output for downstream consumers.
- FR-004: The rule checker SHALL support matching against file patterns, required conditions, forbidden patterns, and allowed paths.
- FR-005: Hook, drift, audit, and status workflows SHALL be able to consume the same rule-violation output contract.
- FR-006: The plugin SHALL provide tests for rule parsing, matching, and output formatting.

## Non-Functional Requirements

- NFR-001: Rule execution SHALL be deterministic for the same repository contents.
- NFR-002: Rule output SHALL be stable enough for other shared scripts to consume.
- NFR-003: Rule execution SHALL not require a specific assistant implementation.

## Acceptance Criteria

- [ ] AC-001: Given a rule with structured executable fields, the checker parses it successfully.
- [ ] AC-002: Given a matching code violation, the checker reports a structured violation with rule id, category, severity, file, and match evidence.
- [ ] AC-003: Given a non-matching file, the checker does not report a false violation.
- [ ] AC-004: Given `--json`, the checker emits the shared stable JSON contract.
- [ ] AC-005: Given an active ruleset, status reporting shows rule counts or recent violations using the shared rule output.

## Out of Scope

- A full general-purpose policy language
- Automatic promotion of every retro observation into a blocking rule
- Runtime observation analysis beyond repository artifact checks

## Operating Constraints

- Rule files must remain plain text artifacts under `.specify/rules/`.
- The first implementation should prefer a small useful subset over a complex DSL.
- Existing natural-language rule context can remain for humans, but executable fields must be structured.

## Open Questions

- OQ-001: Which violations should block writes immediately versus remain audit/status-only at first?
- OQ-002: Should malformed rule files fail open or fail closed before the validator is mature?
- OQ-003: How should rule severity map to hook behavior versus reporting-only behavior?

## Related ADRs

- ADR-0001
