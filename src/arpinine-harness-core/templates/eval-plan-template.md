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

## Benchmark Policy
- Benchmark required: [Yes / No]
- Benchmark command: `[command to run benchmark suite]`
- Dataset manifest path: `.specify/evals/[SPEC-NUMBER]-[name]/dataset-manifest.json`
- Minimum scenario count for aggregated reporting: [e.g. 3]
- Aggregation policy: [single run only / aggregate across scenarios / aggregate across repeated runs]

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

## Runtime Contract Assertions
- Allowed tools: [`tool_name_1`, `tool_name_2`]
- Protected actions requiring approval: [`create_case`, `issue_refund`]
- Memory scope invariant: [session-only / persistent / none]
- Session reset evidence: [`session_reset`] or [`session_ended` + new `session_started`]
- Required event types: [`model_turn_started`, `tool_requested`, `tool_executed`, `permission_check`, `memory_write`, `session_reset`]
- Required policy assertions: [approval before protected write / no persistent memory write / only allowed tools used]

## Deterministic Replay
- Replay required: [Yes / No]
- Replay command: `[command to rerun the same scenario with mocked tools or fixed fixtures]`
- Mock / fixture strategy: [fake tool registry / recorded tool outputs / stubbed runtime / seeded test data]
- Replay fixture path: `[tests/replay/... or .specify/evals/.../fixtures]`

## Regression Policy
- What counts as a regression?
- Which metrics are release-blocking?
- When must evaluation be rerun?

## Baseline Comparison
- Baseline required: [Yes / No]
- Baseline artifact path: `.specify/evals/[SPEC-NUMBER]-[name]/baseline.json`
- Comparable dimensions: [dataset version / model-runtime variant / prompt-config variant / scenario set]
- Failure policy when baseline dimensions differ: [block comparison / warn only]

## Reporting
- Latest results path: `.specify/evals/[SPEC-NUMBER]-[name]/latest-results.md`
- Historical storage: `.specify/evals/[SPEC-NUMBER]-[name]/history/<session-id>/`
- Observation history source: `.specify/observations/[SPEC-NUMBER]-[name]/history/<session-id>/`

## Approval Rule
- Work is not complete until required thresholds pass or an explicit exception is documented.
