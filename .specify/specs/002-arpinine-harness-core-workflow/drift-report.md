# Drift Report: 002-arpinine-harness-core-workflow

## Inputs Reviewed
- `.specify/specs/002-arpinine-harness-core-workflow/spec.md`
- `.specify/specs/002-arpinine-harness-core-workflow/plan.md`
- `.specify/evals/002-arpinine-harness-core-workflow/` (missing)
- `scripts/quick_drift_check.py` output via shared `/at-audit` workflow

## Findings
HIGH `.specify/evals/002-arpinine-harness-core-workflow/eval-plan.md` is missing, so the governed workflow has no persisted evaluation contract for this implemented feature.

## Attribution
FINDING: missing eval plan for governed feature
Attribution: PRECONDITION FAILURE
Reason: the workflow feature is specified and planned, but the repository lacks the evaluation artifact expected by the audit/status pipeline to validate quality and regression posture.
Action: add `.specify/evals/002-arpinine-harness-core-workflow/eval-plan.md` and record results, or refine the spec/plan so the feature is explicitly outside eval governance.
Rule candidate: NO

## ADR Coverage
- No ADR required for the current finding.
- This is a missing governance precondition, not an implementation deviation.
- No active rule under `.specify/rules/` currently covers missing eval artifacts.

## Summary
Summary: 1 drift item found, 0 ADRs created.
Attributions: 0 postcondition failures, 1 precondition failure.
Rule violations: 0.
Remaining: 1 HIGH unresolved item until eval governance is recorded or the spec/plan is refined to remove the requirement.
