# AgentAlign Next Implementation Steps

## Purpose

AgentAlign is intended to be a governance system for vibe-coded products, not only a prompt bundle.

The current plugin already defines a strong operating model:
- product-facing specifications
- engineering plans
- architecture and harness governance
- ADRs
- evaluation plans
- observations
- retrospectives and rules
- status reporting
- lightweight hooks and script-backed checks

The next milestone should make more of that governance executable. The goal is to reduce the gap between "the workflow says this should happen" and "the plugin can verify or block this automatically."

## Current Gap

The codebase and the two-axis framework are directionally aligned, but some framework claims are still aspirational:
- schemas exist, but are not yet used by an executable validator
- rules exist as markdown, but are not yet evaluated by a deterministic rule engine
- AIN fields exist in the spec template, but AIN level does not yet gate implementation readiness
- `/spec-status` reports useful governance state, but not the full EP/AIN maturity view
- the governance scripts are useful, but do not yet have a test suite or CI guard

These are the right gaps to close next because they turn AgentAlign from structured guidance into enforceable governance.

## Design Decisions To Make First

The next work should start by defining contracts, not by adding more regex.

### AIN Format

AIN gating depends on reliable parsing. The current body format is readable but brittle:

```md
**AIN Target Level**: 3
```

For v1.5, choose a stable representation and use it consistently before implementing v1.6 gates.

Recommended decision: use YAML frontmatter in `spec.md`.

```yaml
---
ain_level: 3
evaluation_required: true
---
```

Why:
- consistent with ADR and rule frontmatter already used by the plugin
- parseable without markdown-specific heuristics
- easy for future Codex or non-Claude adapters to consume
- safer foundation for validation, AIN gates, and status reporting

The existing `## AI-Nativeness Assessment` body section can remain as human-readable explanation, but frontmatter should become the source of truth for machine checks.

Define the split explicitly:
- Frontmatter: `ain_level`, `evaluation_required`
- Body `## AI-Nativeness Assessment`: agent-callable operations, human-in-the-loop gates, feedback channels

The body section should no longer be treated as free prose. It should use structured subsection conventions that `validate_artifacts.py` can check deterministically.

### Executable Rule Field Schema

Rule files should keep natural-language `triggers` for human explanation, but executable fields must be structured.

Avoid prose in machine-executed fields:

```yaml
required_when:
  - "content contains OpenHarness"
```

Use structured fields:

```yaml
required_when:
  - field: content
    matches: "openharness"
    case_insensitive: true

forbidden_patterns:
  - pattern: "^\\s*(from|import)\\s+fastapi"
    regex: true
    case_insensitive: true

file_patterns:
  - "src/**/*.py"

allowed_paths:
  - "src/adapters/**"
```

This schema should be defined before `check_rules.py` is implemented.

### Rule Violation Output Contract

`check_rules.py` should emit structured JSON so hooks, drift checks, audit, and status can consume the same output.

Required JSON format:

```json
[
  {
    "rule_id": "harness-001",
    "category": "harness",
    "severity": "HIGH",
    "prevents": "Product code coupling directly to a harness SDK",
    "file": "src/api/handler.py",
    "match": "from openharness import AgentRuntime"
  }
]
```

`check_rules.py --json` should always return this shape. Text output can be a formatted view of the same data.

### EP Scoring Formula

The richer status dashboard should not invent Engineering Process maturity labels without a deterministic formula.

Initial EP scoring:

| EP Level | Criteria |
|----------|----------|
| 1 | `spec.md` exists |
| 2 | `plan.md` exists with Module Boundaries, Dependency Rules, and Testability By Boundary |
| 3 | at least one `/spec-audit` has been run and all CRITICAL/HIGH findings are covered by ADRs or marked resolved |
| 4 | active rules exist under `.specify/rules/` |
| 5 | eval coverage exists, observation is recorded, and `/spec-status --onboard` can be generated |

This formula is intentionally pragmatic. It should be treated as a project-governance readiness score, not as a universal organisational maturity score.

## Recommended Order

1. Define artifact and rule contracts
2. Add executable schema validation
3. Add AIN readiness gates
4. Add deterministic rule execution
5. Add richer status metrics

This order matters because each layer depends on the previous one. AIN gating needs reliable spec parsing. Rule execution needs structured fields. Status reporting becomes more useful once validators and gates produce machine-readable results.

## v1.5: Executable Artifact Validation

### Why

Schema validation makes AgentAlign artifacts machine-checkable. Without it, `spec.md`, ADRs, eval plans, observations, and rules can drift into well-written but non-compliant markdown.

This is the foundation for governed vibe coding: AI agents and humans need shared, verifiable contracts.

### Deliverables

- Decide and document the machine-readable AIN format, preferably `spec.md` frontmatter.
- Add `scripts/validate_artifacts.py`.
- Validate specs, plans, ADRs, eval plans, observations, and rules.
- Add ADR write-time validation through a lightweight `PreToolUse` hook.
- Add `scripts/tests/` with tests for existing and new governance scripts.
- Add a CI job or CI template that runs script tests and plugin validation.
- Update `spec-schema.yaml` to validate the agreed AIN frontmatter fields and the structured body representation for AIN details.

### Validation Scope

Initial checks should be deterministic and lightweight:
- required sections exist
- required IDs match expected patterns, such as `FR-001`, `AC-001`, `ADR-0001`
- required frontmatter fields exist
- placeholders are not left in required sections
- observation traces match `observation-schema.yaml`
- acceptance criteria use measurable `AC-NNN:` format
- ADRs include non-empty `governs:` and meaningful `covers:` entries where required
- rule files include required frontmatter and valid executable field structure

### Success Criteria

- malformed specs, ADRs, observations, and rules are reported clearly
- direct writes to malformed ADRs are blocked or warned before completion
- `/spec-status` can display validation state per spec
- validation can run locally or in CI without Claude
- regression tests cover the validator and existing governance scripts

## v1.6: AIN Readiness Gates

### Why

AgentAlign should connect product AI-nativeness to delivery control. If a product spec declares agent-callable operations or feedback-driven behavior, implementation should not start until the required contracts are explicit.

This bridges product strategy and engineering execution.

### Prerequisite

AIN format must be finalized in v1.5. Do not implement AIN gates against freeform markdown variants.

### Deliverables

- Parse the agreed AIN source of truth.
- Gate implementation for AIN >= 3.
- Gate implementation for AIN >= 4.
- Add AIN readiness state to status output.
- Add eval and observation requirements derived from AIN level.

### Gate Rules

For AIN >= 3, require:
- agent-callable operations
- input schema
- output shape
- failure modes
- human-in-the-loop gates
- evaluation plan

For AIN >= 4, additionally require:
- feedback channels
- observation plan or trace format
- evaluation coverage for feedback-loop behavior
- harness strategy when the product depends on an agent runtime

### Success Criteria

- AIN >= 3 specs cannot proceed without agent-callable operations and eval plan.
- AIN >= 4 specs cannot proceed without feedback channel and observation strategy.
- `/spec-status` shows AIN target and readiness state.

## v1.7: Deterministic Rule Engine

### Why

Rules are what make AgentAlign compound. If lessons from retros and audits are only markdown, they help humans but do not reliably prevent repeat failures.

The goal is not to build a complex policy engine immediately. The goal is to make the first useful subset deterministic.

### Prerequisite

Executable rule field schema and JSON output contract must be finalized before implementation.

### Deliverables

- Add executable rule fields to examples and templates.
- Add `scripts/check_rules.py`.
- Support `check_rules.py --json` using the shared violation output contract.
- Add tests for file pattern matching, required conditions, forbidden patterns, allowed paths, and output format.
- Integrate rule violations into pre-write checks, drift checks, audit, and status.

### Success Criteria

- at least one example rule blocks or reports a real code violation
- known recurring failures are detected without relying only on Claude prompt interpretation
- `/spec-status` reports active rule count and recent rule violations
- hooks and scripts consume the same rule violation JSON

## v1.8: Governance Health Report

### Why

AgentAlign needs a single health view that product, engineering, and new team members can trust.

The current status report is useful, but it should better reflect the two-axis framework:
- Engineering Process maturity
- Product AI-Nativeness

### Prerequisites

- validation produces structured results
- AIN readiness is computable
- rule violations use a stable output contract
- EP scoring formula is documented and implemented

### Deliverables

- Extend `spec_status.py` to report validation state.
- Add EP score using the documented formula.
- Add AIN target and AIN readiness.
- Add agent-callable operation count.
- Add feedback channel state.
- Add rule count by category and recent rule violations.
- Add attribution counts from latest drift report when available.
- Add observation coverage and eval recency.
- Add a CI job template for status, validation, tests, and plugin validation.

Suggested table:

```text
Spec                 ACs  Valid  EP  AIN  Drift  ADRs  Eval  Arch  Harness  Obs
001-user-login       4/4  PASS   3   2    CLEAN  2     PASS  OK    n/a      none
002-agent-support    3/5  WARN   4   4    HIGH   3     FAIL  OK    OK       recorded
```

### Success Criteria

- a new engineer can understand project governance state from one command
- product can see whether business intent and AIN expectations are protected
- engineering can see what blocks implementation or completion
- status output is driven by structured validation, rule, AIN, eval, observation, and drift data

## Cleanup Before Or During v1.5

- Remove the superseded `reverse-diff-audit` skill from the distributable package, or move it to archived documentation.
- Keep README claims aligned with what is executable today.
- Keep the two-axis framework clear about implementation status: "implemented", "supported", and "planned" should not be mixed.

## Implementation Task Files

This roadmap describes what changes and why. Detailed wiring should be tracked in version-specific task files when implementation begins.

Suggested task files:
- `docs/tasks/v1.5_artifact_validation.md`
- `docs/tasks/v1.6_ain_gating.md`
- `docs/tasks/v1.7_rule_engine.md`
- `docs/tasks/v1.8_status_metrics.md`

Each task file should include:
- scripts to add or modify
- hooks to wire
- command prompts to update
- examples to update
- tests to add
- acceptance criteria
- explicit list of README and skill claims that must be audited for aspirational wording before release

## Guiding Principle

Keep AgentAlign framework-agnostic.

The plugin should enforce contracts and evidence, not lock teams into one evaluation framework, one harness runtime, or one AI coding platform.

The right architecture is:
- AgentAlign owns governance contracts
- adapters and scripts execute checks
- teams choose their implementation frameworks behind explicit boundaries
