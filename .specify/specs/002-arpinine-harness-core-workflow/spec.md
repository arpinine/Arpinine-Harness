# Spec: Arpinine Harness Core Workflow

## Business Case

AI-assisted development moves fast but drifts from intent. Teams accumulate vibe-coded work that nobody can audit, decisions that nobody documented, and tests that measure the wrong things. Arpinine Harness gives a team a shared operating model: a governed loop from product intent to implementation to evidence, with compounding rules so lessons are not lost after each sprint.

The core workflow is the primary product. It must be coherent, automatable at each stage, and usable by both product and engineering roles without requiring manual coordination between them.

## User Stories

- As a product manager, I want to capture feature intent in a structured spec, so that engineering cannot diverge from it without an explicit decision record.
- As an engineer, I want a planning step that defines module boundaries and dependency rules before I write code, so that I am not refactoring at the end.
- As a tech lead, I want architectural decisions captured in ADRs and linked to the specs they govern, so that I can audit why things are built the way they are.
- As an engineer, I want automated drift detection that tells me when implementation diverges from the spec, so that I learn about it before it reaches production.
- As a team, I want evaluation defined up front for agentic behavior, so that "it works" has a measurable meaning before we ship.
- As a team, I want lessons from retros captured as compounding rules, so that past mistakes do not recur silently on the next sprint.
- As a new team member, I want a single governance overview command, so that I can understand the current state of work without reading ten files.

## Requirements

- FR-001: The workflow SHALL provide a command to initialize the governance structure in a project.
- FR-002: The workflow SHALL provide a command to create a product specification as the starting point for each feature.
- FR-003: The workflow SHALL provide a command to refine a specification for clarity, measurability, and scope.
- FR-004: The workflow SHALL provide a command to generate an implementation plan from an approved spec, including module boundaries, dependency rules, and harness strategy when applicable.
- FR-005: The workflow SHALL provide a command to create and manage Architecture Decision Records linked to specs.
- FR-006: The workflow SHALL provide a command to define and run evaluation for agentic behavior, including metrics, thresholds, datasets, and pass/fail policy.
- FR-007: The workflow SHALL provide a command to record and review runtime observations against planned behavior.
- FR-008: The workflow SHALL provide a command to execute the plan with TDD enforcement and security review.
- FR-009: The workflow SHALL provide a command to detect drift between spec, plan, ADRs, and code, and route findings to refinement or ADR creation.
- FR-010: The workflow SHALL provide a command to run a retrospective that captures lessons as machine-readable rules for future enforcement.
- FR-011: The workflow SHALL provide a command to display the governance state of all specs in a single summary.
- FR-012: The workflow SHALL enforce, via hooks, that implementation cannot begin without completed architecture and constitution requirements.
- FR-013: The workflow SHALL invoke specialized agents (product-owner, tdd-guide, security-reviewer, tech-architect) at appropriate stages automatically.

## Non-Functional Requirements

- NFR-001: Each command SHALL be independently invocable. No command SHALL require another command to have run in the same session.
- NFR-002: All governance artifacts (specs, plans, ADRs, eval plans, observations, rules) SHALL be stored as plain text files under `.specify/` so they are version-controlled with the codebase.
- NFR-003: The drift detection step SHALL produce structured, severity-classified findings that map to specific files and locations.
- NFR-004: Rules produced by the retro step SHALL be machine-readable and enforceable in future audit and implementation cycles.
- NFR-005: The governance structure SHALL be self-describing: a new team member running the status command SHALL receive enough context to contribute safely without reading source files.
- NFR-006: The workflow SHALL be additive: each step builds on prior artifacts without requiring prior steps to have used the same session or tooling.

## Acceptance Criteria

- [ ] AC-001: Given a project with no `.specify/` directory, `/arpinine-harness:at-init` creates the full directory structure and constitution file.
- [ ] AC-002: Given a feature request, `/arpinine-harness:at-new <name>` produces a spec.md containing user stories, measurable requirements, testable acceptance criteria, explicit out-of-scope items, and a Related ADRs section.
- [ ] AC-003: Given a spec.md with vague acceptance criteria, `/arpinine-harness:at-review` rewrites them to be testable and documents open questions.
- [ ] AC-004: Given an approved spec.md, `/arpinine-harness:at-plan` produces a plan.md with module boundaries, dependency rules, and testability-by-boundary sections before any implementation begins.
- [ ] AC-005: Given a consequential architectural decision, `/arpinine-harness:at-adr new "<title>"` creates a numbered ADR file and links it in ADR-INDEX.md.
- [ ] AC-006: Given an agentic spec, `/arpinine-harness:at-eval plan` produces an eval-plan.md with metrics, thresholds, datasets, and execution command before implementation is approved.
- [ ] AC-007: Given a plan.md that lacks module boundaries, the pre-implementation hook blocks file edits and explains the missing requirement.
- [ ] AC-008: Given implementation in progress, `/arpinine-harness:at-implement` enforces RED → GREEN → REFACTOR for each task, and the tdd-guide agent interrupts if production code is written before a failing test.
- [ ] AC-009: Given code that diverges from the spec, `/arpinine-harness:at-audit` produces a severity-classified drift report with CRITICAL, HIGH, and MEDIUM findings.
- [ ] AC-010: Given a drift finding, `/arpinine-harness:at-audit` routes it to either spec refinement (precondition failure) or ADR creation (postcondition failure), not both.
- [ ] AC-011: Given a completed delivery, `/arpinine-harness:at-retro` produces at least one machine-readable rule in `.specify/rules/` that captures a non-obvious lesson.
- [ ] AC-012: Given any project state, `/arpinine-harness:at-status` displays AC coverage, drift state, ADR coverage, eval state, architecture sections, harness strategy, and observation state per spec.

## Out of Scope

- The plugin does not execute code, run tests, or deploy software
- The plugin does not enforce source control policies (branch protection, PR requirements)
- The plugin does not manage team permissions or role access
- Eval framework selection (DeepEval, pytest, etc.) — the workflow is framework-agnostic
- Real-time monitoring or alerting after deployment
- Automatic spec generation from existing codebases without human review

## Operating Constraints

- The workflow has no agent harness dependency. Harness governance skills exist to govern harness use in the product application being built, not in the plugin itself.
- The workflow depends on a configured specification provider for automated spec generation and planning. The default provider is spec-kit (`specify` CLI), but commands must resolve provider actions through the shared adapter layer so other providers can be used without changing the command surface.
- All governance artifacts must remain in `.specify/` and committed with the codebase. External stores or databases are out of scope.
- Pre-implementation hooks enforce architecture and constitution requirements. Teams cannot opt out of these gates by skipping the hook.

## Open Questions

- OQ-001: Should `/arpinine-harness:at-review` be a mandatory step (enforced by hooks before `/arpinine-harness:at-plan` is allowed) or remain advisory?
- OQ-002: What is the minimum viable spec for a non-agentic feature — should eval be required, optional, or gated differently?
- OQ-003: Should `/arpinine-harness:at-status` expose a machine-readable JSON output for CI integration alongside the human-readable summary?
- OQ-004: Should compounding rules from `/arpinine-harness:at-retro` be automatically applied as hook-level blockers, or remain advisory until explicitly promoted?

## Related ADRs

_None yet._
