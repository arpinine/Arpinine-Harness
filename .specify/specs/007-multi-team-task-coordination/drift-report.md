# Drift Report: 007-multi-team-task-coordination

## Inputs Reviewed
- `.specify/specs/007-multi-team-task-coordination/spec.md`
- `.specify/specs/007-multi-team-task-coordination/plan.md`
- `.specify/evals/007-multi-team-task-coordination/` (missing)
- `scripts/quick_drift_check.py` output via shared `/at-audit` workflow

## Findings
HIGH `.specify/evals/007-multi-team-task-coordination/eval-plan.md` is missing, so the governed workflow has no persisted evaluation contract for this implemented feature.

## Attribution
FINDING: missing eval plan for governed feature
Attribution: PRECONDITION FAILURE
Reason: the feature is fully planned and its acceptance criteria are marked complete, but the current audit pipeline still expects a persisted eval artifact to prove the verified state over time.
Action: add `.specify/evals/007-multi-team-task-coordination/eval-plan.md` and record results, or refine the governing artifacts and/or audit policy so this AIN-2 workflow feature is explicitly exempt.
Rule candidate: NO

## ADR Coverage
- No ADR required for the current finding.
- This is a governance contract gap, not an intentional code-path deviation.
- No active rule under `.specify/rules/` currently covers missing eval artifacts.

## Summary
Summary: 1 drift item found, 0 ADRs created.
Attributions: 0 postcondition failures, 1 precondition failure.
Rule violations: 0.
Remaining: 1 HIGH unresolved item until eval governance is recorded or the spec/plan is refined to remove the requirement.
