# Spec: Executable Artifact Validation

## Business Case

Arpinine Harness relies on text artifacts such as `spec.md`, `plan.md`, ADRs, eval plans, observations, and rules. Today those artifacts are well structured by convention, but not fully enforced by executable validation. That leaves room for drift, malformed documents, and aspirational claims that the plugin cannot verify.

Executable artifact validation turns the governance model into a machine-checkable contract. It is the foundation for stronger hooks, safer automation, CI verification, and implementation-neutral behavior across Claude, Codex, and future hosts.

## User Stories

- As a plugin author, I want artifact validation to run outside any specific assistant so that governance checks work across implementations and in CI.
- As an engineer, I want malformed specs, plans, ADRs, and rules reported clearly so that I can fix them before implementation drifts.
- As a tech lead, I want artifact contracts enforced consistently so that status and audit views can trust the underlying data.

## Requirements

- FR-001: The plugin SHALL provide an executable validator for governed artifacts under `.specify/`.
- FR-002: The validator SHALL validate at least specs, plans, ADRs, eval plans, observations, and rule files.
- FR-003: The validator SHALL use schema and deterministic structural checks rather than prompt-only interpretation.
- FR-004: The validator SHALL report violations with file-scoped, human-readable output suitable for local use.
- FR-005: The validator SHALL be invocable outside Claude and Codex sessions.
- FR-006: The plugin SHALL support lightweight hook integration for validation of affected artifact types during editing.
- FR-007: The plugin SHALL provide automated tests for the validator and existing governance scripts.
- FR-008: The plugin SHALL provide a CI-ready validation path that can run plugin structure checks and governance script tests.

## Non-Functional Requirements

- NFR-001: Validation SHALL be deterministic for the same repository contents.
- NFR-002: Validation SHALL fail clearly without requiring network access.
- NFR-003: Validation SHALL remain implementation-neutral and not depend on a Claude-only or Codex-only runtime contract.
- NFR-004: Validation SHALL complete quickly enough for local hook use on targeted artifact changes.

## Acceptance Criteria

- [ ] AC-001: Given a malformed `spec.md`, the validator reports the file and the missing or invalid section.
- [ ] AC-002: Given a malformed ADR, the validator reports frontmatter or structural violations without requiring an assistant session.
- [ ] AC-003: Given a malformed observation artifact, the validator checks it against the observation schema and reports the failure.
- [ ] AC-004: Given a malformed rule file, the validator reports invalid executable fields.
- [ ] AC-005: Given valid governed artifacts, the validator exits successfully.
- [ ] AC-006: Given a direct ADR write during plugin use, the configured validation path runs automatically and surfaces violations before work proceeds.
- [ ] AC-007: Given the repo in CI, the validation path runs without relying on Claude-native commands.

## Out of Scope

- Semantic evaluation of business quality beyond deterministic artifact checks
- Full policy-engine execution for rule files
- AIN readiness gating
- Rich EP/AIN status scoring

## Operating Constraints

- Existing schema files under `templates/schemas/` remain the starting point for validation contracts.
- The validator must tolerate host differences and run as plain local tooling.
- Hook integration should stay lightweight and avoid broad repository rescans on every file write when a targeted validation is possible.

## Open Questions

- OQ-001: Should `plan.md` receive a dedicated schema file or continue with section-based deterministic validation?
- OQ-002: Should malformed rules fail closed in hooks or warn first until the rule engine is implemented?
- OQ-003: Should CI configuration live as a real workflow file in this repo or as a documented template only?

## Related ADRs

- ADR-0001
- ADR-0003
