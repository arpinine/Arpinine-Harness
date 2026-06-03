# Observation Report: [FEATURE NAME]

## Governing Spec
`.specify/specs/[SPEC-NUMBER]-[name]/spec.md`

## Runtime
- Runtime class: [embedded agent runtime / hosted coding agent / other]
- Runtime implementation: [name]
- Scenario: [id or title]
- Timestamp: [ISO-8601]

## Run Metadata
- Run id: [YYYYMMDDTHHMMSSZ-scenario-variant]
- Variant id: [model/prompt/runtime variant]
- Dataset version: [optional]
- Model name: [optional]
- Model version: [optional]
- Started at: [ISO-8601]
- Completed at: [ISO-8601]

## Performance Telemetry
- Latency ms: [wall-clock duration]
- Turn count: [for conversational systems]
- Tool call count:
- Token input:
- Token output:
- Cost USD:
- Error count:
- Baseline comparable: [true / false]

## Observed Behavior
- Tools used:
- Approval events:
- Memory/state behavior:
- Failures/retries:
- Final outcome:

## Decision Provenance
- Conversation ids:
- Run-wide evidence refs:
- Decision records:
  - Decision type:
  - Decision id:
  - Confidence:
  - Rationale:
  - Decision-level evidence refs:
  - Review required:
  - Review outcome:

## Drift Signals
- Undeclared tool use:
- Approval mismatch:
- Memory model mismatch:
- Eval coverage gap:
- Other behavioral drift:

## Recommendation
- [spec update / plan update / harness strategy update / ADR / code fix / eval update]
