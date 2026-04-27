# Plan: Executable Artifact Validation

## Governing Spec
`.specify/specs/003-executable-artifact-validation/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Add a standalone `validate_artifacts.py` entrypoint under shared core scripts | Keeps validation implementation-neutral and reusable from hooks, make targets, and CI | Consequence of ADR-0001 |
| Reuse schema files where they already exist, and add deterministic structural checks where schemas do not yet exist | Faster path to useful enforcement without waiting for full schema coverage everywhere | Consequence of ADR-0003 |
| Run targeted validation from hooks and full validation from local/CI commands | Keeps hooks fast while still supporting comprehensive repository checks | No separate ADR |

## Architecture

```
scripts/validate_artifacts.py        ← shared validator entrypoint
templates/schemas/*.yaml             ← structural contracts
scripts/tests/                       ← validator and governance script tests
hooks/hooks.json                     ← targeted validation triggers
Makefile / CI path                   ← full validation and test entrypoints
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| `validate_artifacts.py` | Discover artifacts, apply schemas/checks, format validation results | `.specify/`, schemas | Depend on assistant-native CLIs |
| `templates/schemas/` | Define machine-readable structural contracts | Nothing | Include host-specific behavior |
| `hooks/` | Trigger lightweight targeted validation after relevant writes | Shared scripts | Reimplement validation logic |
| `scripts/tests/` | Verify validator and governance script behavior | Shared scripts | Depend on interactive sessions |

## Dependency Rules

- `validate_artifacts.py` MUST run with plain local Python tooling.
- Hooks MUST call shared scripts, not assistant-specific validators.
- Validation output MUST be readable by humans and usable in automation by exit code.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Spec validation | Unit | Feed malformed and valid `spec.md` fixtures; assert exit codes and messages |
| ADR validation | Unit | Feed malformed and valid ADR fixtures; assert frontmatter and structure checks |
| Observation validation | Unit | Validate against observation schema with good/bad fixtures |
| Hook integration | Integration | Edit governed artifacts and confirm targeted validation runs |
| CI path | Integration | Run full validation and script tests without assistant runtime |

## Harness Strategy

Not applicable. This is shared governance tooling, not a harness-based product workflow.

## Tasks

- [ ] TASK-001: Define the validation scope per artifact type and reuse existing schemas where available
- [ ] TASK-002: Implement `src/arpinine-harness-core/scripts/validate_artifacts.py`
- [ ] TASK-003: Add plan validation rules for required sections and stable IDs
- [ ] TASK-004: Extend or tighten schema coverage for specs, ADRs, observations, and rules
- [ ] TASK-005: Add targeted hook integration for affected artifact writes
- [ ] TASK-006: Add tests for validator success and failure cases
- [ ] TASK-007: Add tests for existing governance scripts so validation and hooks have regression coverage
- [ ] TASK-008: Add a CI-ready command or template that runs structure validation and script tests
- [ ] TASK-009: Audit README and implementation docs so executable claims match actual validation behavior

## Evaluation Strategy

Success is functional and integration-based:

| Dimension | Check | Method |
|-----------|-------|--------|
| Artifact correctness | AC-001 through AC-005 | Unit tests + local validation runs |
| Hook behavior | AC-006 | Integration check on edited artifacts |
| CI portability | AC-007 | Command runs without assistant-native runtime |

## Security

- Validation reads local files only and should not execute file contents
- Schema and rule parsing must treat repository content as untrusted input
- Hook integration must remain bounded to local filesystem changes

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Validation becomes too slow for hooks | Medium | Use targeted file validation in hooks and full scans only on explicit commands |
| Schema coverage is incomplete and creates false confidence | Medium | Document coverage clearly and add tests per artifact type |
| CI path becomes assistant-specific by accident | Low | Keep all validation entrypoints in shared core scripts and make targets |

## ADRs Created During Planning

No new ADR required at planning time.
