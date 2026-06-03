# Drift Report: 005-deterministic-rule-engine

## Inputs Reviewed
- `.specify/specs/005-deterministic-rule-engine/spec.md`
- `.specify/specs/005-deterministic-rule-engine/plan.md`
- `.specify/evals/005-deterministic-rule-engine/` (missing)
- `scripts/quick_drift_check.py` output via shared `/at-audit` workflow

## Findings
HIGH `.specify/evals/005-deterministic-rule-engine/eval-plan.md` is missing, so the governed workflow has no persisted evaluation contract for this implemented feature.

## Attribution
FINDING: missing eval plan for governed feature
Attribution: PRECONDITION FAILURE
Reason: the feature is planned and implemented, but the audit/status workflow cannot verify ongoing quality because the required eval artifact is absent.
Action: add `.specify/evals/005-deterministic-rule-engine/eval-plan.md` and record results, or refine the governing artifacts to make the exemption explicit.
Rule candidate: NO

## ADR Coverage
- No ADR required for the current finding.
- The issue is missing governance support data, not a ratified implementation deviation.
- No active rule under `.specify/rules/` currently covers missing eval artifacts.

## Summary
Summary: 1 drift item found, 0 ADRs created.
Attributions: 0 postcondition failures, 1 precondition failure.
Rule violations: 0.
Remaining: 1 HIGH unresolved item until eval governance is recorded or the spec/plan is refined to remove the requirement.
