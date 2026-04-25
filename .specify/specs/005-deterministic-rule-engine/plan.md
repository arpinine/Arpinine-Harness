# Plan: Deterministic Rule Engine

## Governing Spec
`.specify/specs/005-deterministic-rule-engine/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Add `check_rules.py` under shared core scripts | Keeps rule execution reusable across hooks, audit, status, and implementations | Consequence of ADR-0001 |
| Define a shared JSON violation contract first | Downstream consumers need one stable output format | No separate ADR |
| Start with a constrained executable schema rather than a broad policy DSL | Faster path to reliable enforcement and lower false-positive risk | No separate ADR |

## Architecture

```
.specify/rules/*.md                 ← human-readable rule docs + structured executable fields
scripts/check_rules.py              ← deterministic parser and matcher
hooks / drift / audit / status      ← consume shared rule output
tests/fixtures/rules/               ← sample rules and matching files
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| Rule files | Store human explanation and structured executable fields | Nothing | Depend on host-specific syntax |
| `check_rules.py` | Parse rules, scan files, emit shared violations | `.specify/rules/`, repo files | Reimplement unrelated drift logic |
| Hooks/audit/status | Consume rule violations | Shared JSON/text output | Fork output formats |

## Dependency Rules

- Rule execution MUST consume structured fields, not ambiguous prose.
- JSON output MUST be the contract shared by hooks, audit, and status.
- Host implementations MUST not define divergent rule semantics.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Rule parsing | Unit | Parse valid and invalid rule fixtures |
| File matching | Unit | Assert required conditions, forbidden patterns, and allowed paths behave correctly |
| JSON output | Unit | Compare `--json` output to expected contract |
| Status integration | Integration | Confirm rule counts or violations surface in status |

## Harness Strategy

Not applicable. Rule execution governs repository artifacts and code layout, not harness runtime behavior inside the plugin.

## Tasks

- [ ] TASK-001: Define the executable rule field schema
- [ ] TASK-002: Update templates or examples to use the executable schema
- [ ] TASK-003: Implement `src/agent-align-core/scripts/check_rules.py`
- [ ] TASK-004: Implement stable `--json` output contract
- [ ] TASK-005: Add file-matching and rule-fixture tests
- [ ] TASK-006: Integrate rule checks into shared audit/status paths
- [ ] TASK-007: Decide initial hook behavior for rule severities
- [ ] TASK-008: Audit docs to distinguish implemented rule execution from planned enforcement

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Parsing and matching | AC-001 through AC-003 | Unit tests with fixtures |
| Output contract | AC-004 | Snapshot-style JSON assertions |
| Shared integration | AC-005 | Integration check through status output |

## Security

- Pattern matching must not execute arbitrary rule content
- File scanning must remain inside repository scope
- False positives should be controlled through constrained schema design and tests

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Rule DSL grows too quickly | Medium | Start with constrained fields and postpone advanced logic |
| Hook integration becomes noisy | Medium | Introduce severity-based behavior deliberately after rule accuracy is tested |
| Consumers diverge on output parsing | Low | Freeze the JSON contract early and test it |

## ADRs Created During Planning

No new ADR required at planning time.
