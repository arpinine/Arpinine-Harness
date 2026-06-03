# Drift Report: 006-governance-health-report

## Inputs Reviewed
- `.specify/specs/006-governance-health-report/spec.md`
- `.specify/specs/006-governance-health-report/plan.md`
- `.specify/evals/006-governance-health-report/` (missing)
- `scripts/quick_drift_check.py` output via shared `/at-audit` workflow

## Findings
HIGH `.specify/evals/006-governance-health-report/eval-plan.md` is missing, so the governed workflow has no persisted evaluation contract for this implemented feature.

## Attribution
FINDING: missing eval plan for governed feature
Attribution: PRECONDITION FAILURE
Reason: the repository has the governing spec and plan, but it does not include the eval artifact expected by the shared governance health checks.
Action: add `.specify/evals/006-governance-health-report/eval-plan.md` and record results, or refine the spec/plan so the feature is explicitly outside eval tracking.
Rule candidate: NO

## ADR Coverage
- No ADR required for the current finding.
- The finding reflects incomplete governance artifacts rather than implementation drift.
- No active rule under `.specify/rules/` currently covers missing eval artifacts.

## Summary
Summary: 1 drift item found, 0 ADRs created.
Attributions: 0 postcondition failures, 1 precondition failure.
Rule violations: 0.
Remaining: 1 HIGH unresolved item until eval governance is recorded or the spec/plan is refined to remove the requirement.
