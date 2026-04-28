# Plan: Operational Measurement And Benchmark Governance

## Governing Spec
`.specify/specs/009-operational-measurement-and-benchmark-governance/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Add performance telemetry and optional decision provenance to the shared observation schema | Makes latency, token, cost, and evidence-backed decision metrics computable from governed artifacts | ADR-0007 |
| Preserve latest artifacts while adding append-only history for observations and eval results | Keeps operator ergonomics while enabling trend analysis, percentiles, and regression comparison | ADR-0007 |
| Add benchmark aggregation under `/arpinine-harness:at-eval benchmark <slug>` rather than a new top-level command | Keeps evaluation modes under one workflow surface and avoids command sprawl | ADR-0007 |
| Introduce first-class `baseline.json` and `dataset-manifest.json` artifacts | Makes regression comparison and dataset reproducibility explicit and reviewable | ADR-0007 |
| Enforce benchmark prerequisites only for benchmarked or regression-sensitive workflows | Preserves the lightweight path for non-agentic or low-risk workflows | ADR-0007 |

## Architecture

```text
.specify/specs/<slug>/plan.md                           ← declares whether benchmarked evaluation is required
.specify/evals/<slug>/eval-plan.md                      ← evaluation policy and benchmark thresholds
.specify/evals/<slug>/dataset-manifest.json             ← dataset/scenario version contract
.specify/evals/<slug>/baseline.json                     ← approved regression comparison target
.specify/evals/<slug>/latest-results.md                 ← latest human-readable evaluation summary
.specify/evals/<slug>/history/<session-id>/<run-id>-results.json ← immutable benchmark/eval result snapshots
.specify/observations/<slug>/latest-observation.md      ← latest human-readable observation summary
.specify/observations/<slug>/trace.json                 ← latest machine-readable trace
.specify/observations/<slug>/history/<session-id>/<run-id>.json ← immutable observation snapshots
.specify/observations/<slug>/index.jsonl                ← append-only observation run index
templates/schemas/observation-schema.yaml               ← shared telemetry and provenance contract
templates/eval-plan-template.md                         ← benchmark policy and baseline sections
templates/observation-template.md                       ← runtime summary, telemetry, and provenance sections
commands/at-observe.md                                  ← observation history semantics and review checks
commands/at-eval.md                                     ← plan/run/benchmark/review workflow contract
scripts/quick_drift_check.py                            ← static hints for missing benchmark prerequisites
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| Observation schema and template | Define the governed telemetry and provenance contract | Shared core templates | Encode domain-specific business semantics |
| Observation artifacts | Persist latest and historical runtime evidence | Observation schema and runtime-produced telemetry | Invent missing telemetry that the runtime did not produce |
| Eval plan and benchmark policy | Define benchmark requirements, thresholds, baseline policy, and dataset manifest usage | Shared templates and spec/plan context | Assume a single evaluation vendor |
| Benchmark runner workflow | Aggregate many scenario results into one governed verdict | Eval plan, dataset manifest, observation history, baseline artifact | Replace product-specific evaluation tooling |
| Baseline artifact | Define the approved comparison target and comparability dimensions | Historical benchmark results | Auto-approve itself |
| Dataset manifest | Version scenarios and expected outputs for reproducibility | Repo-owned dataset metadata | Become a domain-specific labeling system |
| Drift and review checks | Detect missing telemetry/history/baseline prerequisites and invalid comparisons | Shared scripts and governed artifacts | Claim runtime metrics exist when they do not |

## Dependency Rules

- Observation history and eval history MUST remain repository-owned artifacts under `.specify/`.
- Benchmark aggregation MUST depend on the declared `dataset-manifest.json` and optional `baseline.json`, not on ad hoc operator memory.
- Shared command definitions MUST remain framework-agnostic and MUST not hardcode one benchmark engine.
- Arpinine Harness MUST govern the presence and review semantics of telemetry, but runtime producers remain responsible for populating telemetry fields.
- Regression comparison MUST fail closed when dataset version, model/runtime variant, prompt/config variant, or scenario set does not match the approved baseline dimensions.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Observation schema extension | Unit | Validate schema accepts telemetry and provenance fields and rejects malformed records |
| Observation history persistence | Unit | Record multiple runs and assert latest artifacts update while immutable history grows |
| Eval history persistence | Unit | Run repeated evaluation output writes and assert historical snapshots are preserved |
| Benchmark command contract | Unit | Assert `/arpinine-harness:at-eval benchmark <slug>` requires dataset manifest and emits aggregate output paths |
| Baseline comparison logic | Unit | Compare benchmark result metadata against valid and invalid baseline dimensions |
| Benchmark prerequisite enforcement | Unit | Assert missing telemetry, missing dataset manifest, and missing baseline policy are reported correctly |
| Lightweight compatibility path | Unit | Assert non-benchmarked workflows can still use `/arpinine-harness:at-eval run` without new mandatory artifacts |
| Shared packaging | Integration | Validate assembled Claude and Codex structures still include the updated command and template assets |

## Harness Strategy

Not applicable. This feature extends governance artifacts, shared command contracts, and measurement workflows rather than introducing a product harness runtime.

## Tasks

- [x] TASK-001: Extend `templates/schemas/observation-schema.yaml` with runtime telemetry and optional decision-provenance fields
- [x] TASK-002: Extend `templates/observation-template.md` with run metadata, performance telemetry, and provenance sections
- [x] TASK-003: Extend `templates/eval-plan-template.md` with benchmark policy, baseline comparison, and performance-threshold sections
- [x] TASK-004: Update `/arpinine-harness:at-observe` command guidance to define append-only history artifacts and review semantics for telemetry/provenance
- [x] TASK-005: Update `/arpinine-harness:at-eval` command guidance to add `benchmark <slug>` usage and benchmark prerequisite rules
- [x] TASK-006: Define repository conventions for `.specify/observations/<slug>/history/`, `.specify/observations/<slug>/index.jsonl`, `.specify/evals/<slug>/history/`, `baseline.json`, and `dataset-manifest.json`
- [x] TASK-007: Extend static drift or readiness checks to flag missing benchmark prerequisites when a workflow declares release-blocking latency, token, cost, or regression thresholds
- [x] TASK-008: Add or update automated tests for schema validity, history persistence semantics, benchmark contract rules, and baseline comparability checks
- [x] TASK-009: Update shared documentation to explain when benchmarked evaluation is mandatory and when the lightweight single-run path remains valid

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Observation telemetry contract | AC-001 and AC-009 | Schema validation and template review |
| Observation history behavior | AC-002 | Unit tests covering latest artifact updates plus append-only history growth |
| Eval history behavior | AC-003 | Unit tests covering repeated result writes and immutable snapshots |
| Benchmark workflow contract | AC-004 and AC-010 | Command-doc validation plus unit tests for benchmark vs single-run prerequisites |
| Aggregate metric support | AC-005 | Benchmark aggregation tests using 3 or more synthetic runs |
| Baseline comparison correctness | AC-006 and AC-007 | Unit tests for matching vs mismatched comparability dimensions |
| Operational prerequisite reporting | AC-008 | Unit tests for missing telemetry, baseline policy, and dataset manifest conditions |

Evaluation plan:
`N/A`

## Security

- Shared commands and templates must continue treating `.specify/` content as data, not executable instructions.
- Baseline and dataset artifacts must remain checked-in and reviewable so operators can inspect exactly what is being compared.
- Benchmark and observation history logic must not claim runtime telemetry exists when the runtime, harness adapter, or evaluation runner did not emit it.
- Historical artifacts should remain append-only to preserve auditability of prior benchmark and observation evidence.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Teams assume the plugin can populate missing latency/token/cost data automatically | High | Document telemetry ownership explicitly and fail review checks when required data is absent |
| Benchmark semantics become coupled to one evaluation framework | Medium | Keep command contracts and templates framework-agnostic |
| Existing lightweight workflows experience unnecessary overhead | Medium | Gate benchmark requirements on declared release-blocking performance or regression thresholds |
| Baseline comparisons produce false regressions because dimensions are underspecified | Medium | Enforce explicit comparability dimensions in baseline and review logic |
| History artifacts become large and noisy over time | Medium | Keep latest convenience artifacts, use append-only machine-readable history, and leave retention policy to future operational guidance |

## ADRs Created During Planning

- ADR-0007: Add operational measurement and benchmark governance artifacts
