# Drift Report: 008-cross-language-code-style-governance

## Inputs Reviewed
- `.specify/specs/008-cross-language-code-style-governance/spec.md`
- `.specify/specs/008-cross-language-code-style-governance/plan.md`
- `.specify/evals/008-cross-language-code-style-governance/` (missing)
- `scripts/quick_drift_check.py` output via shared `/at-audit` workflow

## Findings
HIGH `.specify/evals/008-cross-language-code-style-governance/eval-plan.md` is missing, so the governed workflow has no persisted evaluation contract for this implemented feature.

## Attribution
FINDING: missing eval plan for governed feature
Attribution: PRECONDITION FAILURE
Reason: the feature is implemented and complete at the plan level, but the shared audit/status workflow still has no eval artifact to reference for regression tracking.
Action: add `.specify/evals/008-cross-language-code-style-governance/eval-plan.md` and record results, or refine the governing artifacts and/or audit policy so this AIN-2 workflow feature is explicitly exempt.
Rule candidate: NO

## ADR Coverage
- No ADR required for the current finding.
- The finding is about missing governance evidence, not a code deviation that needs ratification.
- No active rule under `.specify/rules/` currently covers missing eval artifacts.

## Summary
Summary: 1 drift item found, 0 ADRs created.
Attributions: 0 postcondition failures, 1 precondition failure.
Rule violations: 0.
Remaining: 1 HIGH unresolved item until eval governance is recorded or the spec/plan is refined to remove the requirement.
