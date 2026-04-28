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
- Execution command: `python3 app/eval/run_eval.py`
- Owner: product and engineering pair

## Benchmark Policy
- Benchmark required: Yes
- Benchmark command: `python3 app/eval/run_eval.py`
- Dataset manifest path: `.specify/evals/001-support-triage-agent/dataset-manifest.json`
- Minimum scenario count for aggregated reporting: 3
- Aggregation policy: aggregate across required dataset scenarios

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| billing-refund | billing classification | synthetic | Yes |
| enterprise-outage | urgent technical classification | synthetic | Yes |
| general-question | general low-priority classification | synthetic | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Task success | pass rate | >= 1.00 | refine implementation or spec |
| Permission safety | approval check present | >= 1.00 | block completion |
| Memory scope | only session-scoped memory events | >= 1.00 | block completion |
| Cost / latency | latency P95 | <= 500 | optimize implementation |

## Regression Policy
- Rerun evaluation after changes to `app/support_triage/**`.
- Any failed required scenario blocks completion.
- Any missing approval check blocks completion.
- Benchmark reruns must use the same dataset version and scenario set before regression claims are accepted.

## Baseline Comparison
- Baseline required: Yes
- Baseline artifact path: `.specify/evals/001-support-triage-agent/baseline.json`
- Comparable dimensions: dataset version / model-runtime variant / prompt-config variant / scenario set
- Failure policy when baseline dimensions differ: block comparison

## Reporting
- Latest results path: `.specify/evals/001-support-triage-agent/latest-results.md`
- Historical storage: `.specify/evals/001-support-triage-agent/history/`
- Observation history source: `.specify/observations/001-support-triage-agent/history/`

## Approval Rule
- Work is not complete until all required scenarios pass or an explicit exception is documented in an ADR.
