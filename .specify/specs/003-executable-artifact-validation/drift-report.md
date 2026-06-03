# Drift Report: 003-executable-artifact-validation

## Inputs Reviewed
- `.specify/specs/003-executable-artifact-validation/spec.md`
- `.specify/specs/003-executable-artifact-validation/plan.md`
- `.specify/evals/003-executable-artifact-validation/` (missing)
- `scripts/quick_drift_check.py` output via shared `/at-audit` workflow

## Findings
HIGH `.specify/evals/003-executable-artifact-validation/eval-plan.md` is missing, so the governed workflow has no persisted evaluation contract for this implemented feature.

## Attribution
FINDING: missing eval plan for governed feature
Attribution: PRECONDITION FAILURE
Reason: the feature has governing artifacts and implementation evidence, but the repository does not yet capture the evaluation plan required by the current governance checks.
Action: add `.specify/evals/003-executable-artifact-validation/eval-plan.md` and record results, or refine the governing artifacts to state why eval tracking is not required.
Rule candidate: NO

## ADR Coverage
- No ADR required for the current finding.
- The gap is in governance completeness rather than an accepted implementation choice.
- No active rule under `.specify/rules/` currently covers missing eval artifacts.

## Summary
Summary: 1 drift item found, 0 ADRs created.
Attributions: 0 postcondition failures, 1 precondition failure.
Rule violations: 0.
Remaining: 1 HIGH unresolved item until eval governance is recorded or the spec/plan is refined to remove the requirement.
