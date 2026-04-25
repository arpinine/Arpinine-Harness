---
description: Record and review runtime observations so actual harness behavior can be compared against the spec, plan, harness strategy, and evaluation contract.
---

# /at-observe

Record or review runtime observations.

## Usage
- `/agent-align:at-observe record <slug>` — create or update observation artifacts for a scenario or trace
- `/agent-align:at-observe review <slug>` — summarize observed runtime behavior and highlight drift signals

`<slug>`: feature slug matching a directory under `.specify/specs/`, e.g. `001-user-login`

## Workflow: `record`

1. Locate `.specify/specs/<slug>/spec.md`, `.specify/specs/<slug>/plan.md`, and optional harness strategy.
2. Create or update:
   - `.specify/observations/<spec-slug>/latest-observation.md`
   - `.specify/observations/<spec-slug>/trace.json`
3. Capture, at minimum:
   - runtime class
   - runtime implementation
   - scenario id
   - timestamp
   - tool calls
   - permission or approval events
   - memory or state events
   - failures
   - final outcome
4. Normalize the trace using `templates/schemas/observation-schema.yaml`.
5. Record raw runtime evidence only. Do not classify drift in this step.
6. Leave `## Drift Signals` empty or marked `pending review` until `/agent-align:at-observe review` runs.

## Workflow: `review`

1. Read `latest-observation.md` and `trace.json`.
2. Compare observed behavior against:
   - `spec.md`
   - `plan.md`
   - `## Harness Strategy`
   - evaluation plan
3. Report observation drift classes when found:
   - `TOOL_DRIFT`
   - `PERMISSION_DRIFT`
   - `MEMORY_DRIFT`
   - `EVAL_COVERAGE_DRIFT`
   - `RUNTIME_BEHAVIOR_DRIFT`
4. Recommend whether the next action is:
   - refine spec
   - update plan
   - update harness strategy
   - create or update ADR
   - fix implementation
   - extend evaluation coverage

## Required Outputs

- `.specify/observations/<spec-slug>/latest-observation.md`
- `.specify/observations/<spec-slug>/trace.json`

## Error Conditions

- Observation artifacts missing → "Run `/agent-align:at-observe record` first"
- Trace missing required event data → "Normalize trace against observation-schema.yaml"
