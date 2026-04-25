# Plan: Governance Health Report

## Governing Spec
`.specify/specs/006-governance-health-report/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Extend `spec_status.py` rather than creating a second status entrypoint | Keeps one canonical health surface | Consequence of existing workflow design |
| Compute EP with a documented deterministic formula | Avoids aspirational or inconsistent maturity labels | No separate ADR |
| Read validation, AIN, rule, eval, and observation state from shared artifacts/scripts | Keeps the report coherent across implementations | Consequence of ADR-0001 |

## Architecture

```
scripts/spec_status.py              ← canonical health report entrypoint
validation output / artifact checks ← validity inputs
AIN readiness data                  ← AI-nativeness inputs
rule output                         ← enforcement inputs
eval / observation artifacts        ← evidence inputs
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| `spec_status.py` | Aggregate governance health per spec | Shared artifacts and script outputs | Recompute incompatible semantics in host overlays |
| Validation/AIN/rule scripts | Produce structured readiness signals | Shared artifact store | Depend on status formatting |
| Host overlays | Expose the same status command surface | Shared core | Fork health dimensions |

## Dependency Rules

- Status MUST consume shared structured outputs where available.
- EP scoring MUST use one documented formula for all implementations.
- Missing dimensions MUST be shown clearly, not silently omitted.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Validation state aggregation | Unit | Feed mocked validation results and assert table columns |
| AIN state aggregation | Unit | Feed mocked AIN readiness and assert rendering |
| Rule/eval/observation aggregation | Unit | Feed sample inputs and assert output |
| Human readability | Integration | Run status on mixed repo state and confirm blockers are understandable |

## Harness Strategy

Not applicable. This is status aggregation for governance artifacts, not harness orchestration.

## Tasks

- [ ] TASK-001: Document the deterministic EP scoring formula in shared docs/code comments
- [ ] TASK-002: Extend `src/agent-align-core/scripts/spec_status.py` to include validation state
- [ ] TASK-003: Add AIN target and readiness columns
- [ ] TASK-004: Add rule count and recent rule violation summary
- [ ] TASK-005: Add observation and eval freshness/coverage signals
- [ ] TASK-006: Add tests for mixed repository states and partial adoption
- [ ] TASK-007: Decide whether to add JSON output in this phase or defer it explicitly
- [ ] TASK-008: Audit README and command docs so status claims match implemented fields

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Correct aggregation | AC-001 through AC-005 | Unit tests with mocked inputs |
| Operator usefulness | AC-006 | Manual integration review on mixed spec states |

## Security

- Status reads local artifacts only
- Aggregation must not execute repository content
- Missing or malformed inputs should degrade clearly rather than crash silently

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Status table becomes too noisy | Medium | Keep the first version focused on high-signal dimensions |
| Upstream validation/AIN/rule work slips | High | Treat this spec as dependent and surface blocked tasks clearly |
| Different implementations drift on displayed columns | Low | Keep status logic in shared core only |

## ADRs Created During Planning

No new ADR required at planning time.
