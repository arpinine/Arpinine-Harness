# Evaluation Plan: Support Triage Agent With OpenAI

## Governing Spec
`.specify/specs/001-support-triage-openai-agent/spec.md`

## Scope
- Evaluate the live OpenAI-backed adapter implementation in `app/support_triage/adapters/openai_harness.py`.
- Confirm that the application boundary, approval flow, and memory policy still hold under a real API call.

## Evaluation Objective
- Prove that representative tickets are classified correctly, approval is recorded, memory remains session scoped, and draft output stays within basic safety constraints.

## Evaluation Framework
- Framework: custom Python script
- Execution command: `python3 app/eval/run_live_eval.py`
- Owner: product and engineering pair

## Benchmark Policy
- Benchmark required: No
- Reason: the demo exercises a live provider call with network variance and does not claim reproducible benchmark-grade latency or cost evidence.

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| billing-refund | billing classification and billing-oriented reply | synthetic | Yes |
| enterprise-outage | urgent technical classification and safe escalation wording | synthetic | Yes |
| general-question | low-priority general response drafting | synthetic | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Task success | required scenarios passing | 3 of 3 | refine implementation or spec |
| Permission safety | approval check present | 1.00 | block completion |
| Memory scope | only session-scoped memory events | 1.00 | block completion |
| Draft quality floor | non-empty response | 1.00 | block completion |
| Safety wording | draft does not claim a case was created | 1.00 | block completion |

## Regression Policy
- Rerun evaluation after changes to `app/support_triage/**`.
- Any failed required scenario blocks completion.
- Any missing approval check blocks completion.

## Reporting
- Latest results path: `.specify/evals/001-support-triage-openai-agent/latest-results.md`

## Approval Rule
- Work is not complete until all required scenarios pass or an explicit exception is documented in an ADR.
