# Evaluation Plan: Support Triage Agent

## Governing Spec
`.specify/specs/001-support-triage-agent/spec.md`

## Scope
- Evaluate the local demo implementation of support ticket triage.
- Applies to the fake harness adapter implementation in `app/support_triage/adapters/fake_harness.py`.

## Evaluation Objective
- Prove that the demo classifies representative tickets, assigns priority, requests approval, and avoids persistent memory.

## Evaluation Framework
- Framework: custom Python script
- Execution command: `PYTHONPATH=app python3 app/eval/run_eval.py`
- Owner: product and engineering pair

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| billing-refund | billing classification | synthetic | Yes |
| enterprise-outage | urgent technical classification | synthetic | Yes |
| general-question | general low-priority classification | synthetic | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Task success | scenario pass rate | >= 1.00 | refine implementation or spec |
| Permission safety | approval check present | 100% scenarios | block completion |
| Memory scope | only session-scoped memory events | 100% observations | block completion |

## Regression Policy
- Rerun evaluation after changes to `app/support_triage/**`.
- Any failed required scenario blocks completion.
- Any missing approval check blocks completion.

## Reporting
- Latest results path: `.specify/evals/001-support-triage-agent/latest-results.md`
- Historical storage: not used in this demo

## Approval Rule
- Work is not complete until all required scenarios pass or an explicit exception is documented in an ADR.
