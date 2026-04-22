# Evaluation Plan: [FEATURE NAME]

## Governing Spec
`.specify/specs/[SPEC-NUMBER]-[name]/spec.md`

## Scope
- What system or agent behavior is being evaluated?
- Which release or implementation variant does this apply to?

## Evaluation Objective
- [What must be proven before the work is accepted?]

## Evaluation Framework
- Framework: [DeepEval / pytest / custom harness / benchmark / other]
- Execution command: `[command to run evaluation]`
- Owner: [team or role]

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| [name] | [what it tests] | [path / synthetic / curated / benchmark] | Yes / No |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Task success | [metric name] | >= [value] | refine implementation |
| Safety / compliance | [metric name] | >= [value] | block release |
| Hallucination / grounding | [metric name] | <= or >= [value] | refine prompts or retrieval |
| Cost / latency | [metric name] | <= [value] | optimize execution |

## Regression Policy
- What counts as a regression?
- Which metrics are release-blocking?
- When must evaluation be rerun?

## Reporting
- Latest results path: `.specify/evals/[SPEC-NUMBER]-[name]/latest-results.md`
- Historical storage: [optional path or system]

## Approval Rule
- Work is not complete until required thresholds pass or an explicit exception is documented.
