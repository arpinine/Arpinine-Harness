# Plan: AIN Readiness Gates

## Governing Spec
`.specify/specs/004-ain-readiness-gates/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Use machine-readable AIN fields in `spec.md` as the source of truth | Gating cannot rely on brittle prose-only parsing | ADR-0010 |
| Implement AIN checks in shared core scripts, not host overlays | Keeps Claude and Codex behavior coherent | Consequence of ADR-0001 |
| Reuse status reporting as the user-facing surface for readiness state | Avoids a separate fragmented reporting path | No separate ADR |

## Architecture

```
spec.md frontmatter / structured sections   ← AIN source of truth
scripts/validate_artifacts.py               ← enforces field presence and format
scripts/check-architecture-readiness.sh     ← extended to include AIN-derived readiness where appropriate
scripts/spec_status.py                      ← reports AIN target and readiness
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| Spec format | Declare AIN target and related readiness fields | Template conventions | Drift by implementation |
| Shared scripts | Compute readiness from AIN level | Parsed spec + related artifacts | Depend on host-native CLIs |
| Status reporting | Surface AIN target and readiness | Shared validation output | Recompute incompatible semantics |

## Dependency Rules

- AIN readiness MUST depend on structured spec data.
- Readiness checks MUST reuse shared validation/parsing rather than invent a second parser.
- Host overlays MUST present the same readiness semantics.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| AIN field parsing | Unit | Parse valid and invalid specs with declared AIN fields |
| AIN >= 3 gates | Unit | Assert missing eval/operation fields block readiness |
| AIN >= 4 gates | Unit | Assert missing observation/feedback fields block readiness |
| Status surface | Integration | Confirm status output shows AIN target and readiness |

## Harness Strategy

Not applicable to the plugin itself. Harness requirements are checked only when a governed product spec declares them.

## Tasks

- [ ] TASK-001: Decide and document the machine-readable AIN source of truth in `spec.md`
- [ ] TASK-002: Update templates and examples to use the chosen AIN format
- [ ] TASK-003: Extend shared validation to parse and validate AIN fields
- [ ] TASK-004: Implement AIN >= 3 readiness checks
- [ ] TASK-005: Implement AIN >= 4 readiness checks
- [ ] TASK-006: Extend status output to show declared AIN target and readiness
- [ ] TASK-007: Add fixtures and tests for compliant and non-compliant AIN specs
- [ ] TASK-008: Audit docs so AIN claims are clearly marked as implemented or planned

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Gate correctness | AC-001 through AC-004 | Unit tests with spec fixtures |
| Reporting clarity | AC-005 | Integration check of status output |

## Security

- Readiness checks rely on repository artifacts only
- Missing fields must block or warn deterministically, not by model interpretation

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| AIN format decision is deferred too long | High | Make TASK-001 the first blocker before gate implementation |
| Requirements overfit one product style | Medium | Keep the source of truth minimal and the body human-readable |
| Status output diverges from gate logic | Medium | Reuse shared parsed readiness state in status reporting |

## ADRs Created During Planning

- ADR-0010: Machine-readable AIN fields in spec.md as the gating source of truth — governs TASK-001, TASK-003 through TASK-006
