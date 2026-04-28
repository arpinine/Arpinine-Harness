# Arpinine Harness Operational Measurement Design Proposal

## Purpose

This proposal extends Arpinine Harness so it can govern agent products that need measurable runtime performance, regression detection, and multi-scenario evaluation without specializing the plugin to any single business domain.

The main goal of Arpinine Harness stays the same:
- governed AI-assisted delivery
- explicit specs, plans, ADRs, evals, and observations
- reusable governance across assistants, runtimes, and products

This proposal adds the missing operational measurement layer.

## Problem Statement

Today Arpinine Harness can require metrics such as latency P50/P95 and token cost during `/arpinine-harness:at-eval plan`, but it cannot reliably compute or compare them because:

1. observation traces do not store performance telemetry
2. observations only keep latest artifacts, not run history
3. evaluation results only keep latest artifacts, not result history
4. evaluation has single-run semantics, not benchmark aggregation
5. baselines are not first-class artifacts
6. dataset versions are not governed as measurement inputs

These are generic operational gaps for any agent product, including conversational systems, support agents, workflow agents, and memoryful multi-step agents.

## Goals

- make latency, token, cost, and turn metrics computable from governed artifacts
- support history across observations and eval runs
- support benchmark mode across many scenarios
- support regression detection against approved baselines
- support reproducible evaluation through dataset versioning
- keep the design framework-agnostic

## Non-Goals

- do not hardcode a specific evaluation vendor
- do not specialize artifacts for business-opportunity products only
- do not replace existing `latest-*` convenience artifacts
- do not require a specific harness runtime

## Design Summary

The proposal adds six capabilities:

1. richer observation schema with performance telemetry and provenance
2. append-only observation history
3. append-only evaluation result history
4. benchmark mode under `/arpinine-harness:at-eval`
5. first-class baseline artifact
6. first-class dataset manifest for versioned, reproducible measurement

## Proposed Artifact Model

### Observations

Keep current convenience artifacts:
- `.specify/observations/<slug>/latest-observation.md`
- `.specify/observations/<slug>/trace.json`

Add history artifacts:
- `.specify/observations/<slug>/history/<run-id>.json`
- `.specify/observations/<slug>/history/<run-id>.md`
- `.specify/observations/<slug>/index.jsonl`

`<run-id>` format:
- `YYYYMMDDTHHMMSSZ-<scenario-id>-<variant-id>`

Purpose:
- `latest-*` remains human-friendly
- `history/*` is immutable evidence
- `index.jsonl` supports fast aggregation

### Evaluations

Keep current convenience artifact:
- `.specify/evals/<slug>/latest-results.md`

Add:
- `.specify/evals/<slug>/history/<run-id>-results.json`
- `.specify/evals/<slug>/history/<run-id>-results.md`
- `.specify/evals/<slug>/baseline.json`
- `.specify/evals/<slug>/dataset-manifest.json`

Purpose:
- preserve latest summary for operators
- preserve immutable benchmark results for comparison
- explicitly define baseline and dataset version

## Observation Schema Changes

Current `observation-schema.yaml` is too small for measurement.

### New top-level fields

```yaml
run_id: string
variant_id: string
model_name: string
model_version: string
started_at: string
completed_at: string
latency_ms: integer
turn_count: integer
tool_call_count: integer
token_count_input: integer
token_count_output: integer
cost_usd: number
error_count: integer
dataset_version: string
baseline_comparable: boolean
```

### New provenance fields

```yaml
conversation_ids:
  type: array
  items: { type: string }
evidence_refs:
  type: array
  items: { type: string }
decision_records:
  type: array
  items:
    type: object
    properties:
      decision_type: { type: string }
      decision_id: { type: string }
      confidence: { type: number }
      rationale: { type: string }
      evidence_refs:
        type: array
        items: { type: string }
      review_required: { type: boolean }
      review_outcome: { type: string }
```

### Event schema additions

Add optional per-event fields:

```yaml
timestamp: string
duration_ms: integer
token_count_input: integer
token_count_output: integer
cost_usd: number
attempt: integer
correlation_id: string
```

### Why this matters

This change makes the following metrics computable:
- latency P50/P95
- tokens per run or per turn
- cost per run or per scenario
- tool-call frequency
- error/retry rate
- confidence distribution

## Evaluation Model Changes

### New eval subcommand

Add:

```text
/arpinine-harness:at-eval benchmark <slug>
```

This remains part of `/at-eval`, not a separate top-level command.

### Benchmark workflow

1. Read:
   - `eval-plan.md`
   - `dataset-manifest.json`
   - optional `baseline.json`
2. Validate dataset version and scenario list.
3. Execute all required scenarios or a filtered subset.
4. For each scenario:
   - capture observation trace
   - capture quality result
   - capture telemetry
5. Aggregate:
   - quality metrics
   - latency percentiles
   - token/cost metrics
   - failure and retry rates
6. Compare:
   - thresholds from `eval-plan.md`
   - baseline from `baseline.json`
7. Emit:
   - `latest-results.md`
   - `history/<run-id>-results.json`
   - PASS/WARN/FAIL verdict

## Baseline Artifact

Add:

```json
{
  "baseline_run_id": "20260428T120000Z-core-suite-v1",
  "approved_at": "2026-04-28T12:00:00Z",
  "approved_by": "team-or-person",
  "dataset_version": "v1.2.0",
  "model_name": "example-model",
  "model_version": "2026-04",
  "variant_id": "prompt-a_adapter-b",
  "source_results_path": ".specify/evals/001-example/history/20260428T120000Z-core-suite-v1-results.json",
  "release_note": "Known-good baseline after prompt and retrieval stabilization"
}
```

Purpose:
- define what "regression" is relative to
- prevent ambiguous comparisons across datasets or model versions

## Dataset Manifest

Add:

```json
{
  "dataset_name": "core-agent-regression-suite",
  "dataset_version": "v1.2.0",
  "owner": "team-or-role",
  "scenarios": [
    {
      "scenario_id": "scenario-001",
      "source": "synthetic|curated|production-derived",
      "required": true,
      "tags": ["happy-path", "latency-critical"],
      "expected_output_ref": "labels/scenario-001.json",
      "adjudication_status": "approved"
    }
  ]
}
```

Purpose:
- make evaluation reproducible
- separate product changes from dataset changes
- support filtered benchmark runs by tag or scenario

## Template Changes

### `templates/eval-plan-template.md`

Add sections:

- `## Benchmark Policy`
  - benchmark command
  - dataset manifest path
  - minimum scenario count
  - aggregation policy

- `## Baseline Comparison`
  - baseline artifact path
  - comparable dimensions
  - release-blocking regression rules

- `## Performance Metrics`
  - latency P50/P95
  - token counts
  - cost per run
  - turn count

### `templates/observation-template.md`

Add sections:

- `## Run Metadata`
- `## Performance Telemetry`
- `## Decision Provenance`
- `## Review Outcome`

## Command Changes

### `/arpinine-harness:at-observe record`

Current behavior:
- writes `latest-observation.md`
- writes `trace.json`

New behavior:
- still writes `latest-*`
- also appends immutable run artifacts under `history/`
- also appends summary row to `index.jsonl`

### `/arpinine-harness:at-observe review`

New checks:
- detect missing performance telemetry when eval requires performance metrics
- detect missing provenance fields when the system makes nontrivial decisions
- detect incompatible comparison attempts across dataset versions

### `/arpinine-harness:at-eval plan`

New requirements:
- require `dataset-manifest.json` for benchmarked agent systems
- require performance thresholds when latency/cost are release concerns
- require baseline policy for regression-sensitive products

### `/arpinine-harness:at-eval run`

Keep current meaning:
- single execution or framework-native run

Clarify:
- suited for focused validation
- not sufficient for percentile-based release decisions

### `/arpinine-harness:at-eval benchmark`

New required outputs:
- `latest-results.md`
- `history/<run-id>-results.json`
- optional updated `baseline.json` only by explicit approval

### `/arpinine-harness:at-eval review`

New checks:
- compare latest benchmark results to thresholds
- compare latest benchmark results to baseline
- emit:
  - `PASS`
  - `WARN`
  - `FAIL`
  - `REGRESSION`

## Governance Rules

Add new generic enforcement rules:

| Rule | Severity | Action |
|------|----------|--------|
| Eval plan requires latency or cost metrics but observation schema data is missing | HIGH | Block completion |
| Benchmarked system has no dataset manifest | HIGH | Block benchmark approval |
| Benchmarked system has no observation history | HIGH | Block percentile-based claims |
| Regression-sensitive system has no baseline artifact | MEDIUM | Require explicit exception |
| Results compare across mismatched dataset versions | HIGH | Block regression claim |
| Agentic decision system lacks provenance fields in observation traces | HIGH | Block completion |

## Backward Compatibility

This design preserves existing workflows:
- `latest-observation.md` remains
- `trace.json` remains
- `latest-results.md` remains
- `/at-eval run` remains

Teams that do not need benchmarked evaluation can continue using the current lightweight flow.

The new features become required only when:
- the spec declares performance thresholds
- the plan declares benchmarked evaluation
- the product is agentic and regression-sensitive

## Implementation Plan

### Phase 1: Artifact Foundation

1. extend `observation-schema.yaml`
2. extend observation and eval templates
3. add history directory conventions
4. add `baseline.json` and `dataset-manifest.json` formats

### Phase 2: Command Behavior

1. update `/at-observe record` to append history
2. update `/at-eval plan` to require benchmark metadata where relevant
3. add `/at-eval benchmark`
4. update `/at-eval review` to compare against baseline

### Phase 3: Governance Enforcement

1. add audit checks for missing telemetry/history/baseline
2. add drift checks for invalid regression claims
3. add documentation and examples

## Acceptance Criteria

This proposal is complete when Arpinine Harness can:

1. record per-run performance telemetry in governed observation artifacts
2. preserve observation history across many runs
3. preserve evaluation history across many runs
4. compute benchmark aggregates such as latency P50/P95
5. compare a new benchmark run to an approved baseline
6. reject invalid regression claims when dataset or variant dimensions differ
7. do all of the above without hardcoding a domain-specific product model

## Recommended First Backlog Items

1. Extend `src/arpinine-harness-core/templates/schemas/observation-schema.yaml` with telemetry and provenance fields
2. Add history storage semantics to `/arpinine-harness:at-observe`
3. Add `benchmark` mode to `/arpinine-harness:at-eval`
4. Add `baseline.json` artifact and review logic
5. Add `dataset-manifest.json` artifact and validation logic
6. Update templates and docs to require these artifacts when benchmarked evaluation is declared
