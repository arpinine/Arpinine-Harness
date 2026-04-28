# Spec: Operational Measurement And Benchmark Governance

## Business Case

Arpinine Harness already governs specs, plans, ADRs, evaluation, observations, and drift. That is sufficient for lightweight AI-assisted delivery, but not for serious agent products that need to prove quality, performance, and regression behavior over time.

Today the workflow can declare metrics such as latency P50/P95, token cost, and pass/fail thresholds, but the governed artifact model does not preserve enough telemetry or history to compute those metrics reliably. Observation artifacts only keep the latest run. Evaluation artifacts only keep the latest results. There is no first-class benchmark mode, no approved baseline artifact, and no versioned dataset manifest for reproducible comparisons.

That gap weakens Arpinine Harness as a governance layer for any agent product that must demonstrate operational quality rather than just functional correctness. This is not specific to business-opportunity systems. It applies equally to conversational agents, support agents, workflow agents, coding agents, and memoryful multi-step systems.

The workflow needs a generic operational-measurement layer so teams can benchmark multiple scenarios, archive run history, compare against approved baselines, and govern latency, token, cost, and quality regressions through shared artifacts.

## User Stories

- As an engineering lead, I want Arpinine Harness to preserve performance and quality history so teams can detect regressions before release.
- As an AI engineer, I want benchmarked evaluation to aggregate many scenarios into one governed verdict rather than relying on one-off runs.
- As a data engineer, I want datasets and expected outputs versioned so benchmark results are reproducible and comparable across runs.
- As a reviewer, I want observation traces to include telemetry and decision provenance so I can understand why an agent passed, failed, or regressed.
- As a product team, I want these capabilities to remain generic so the plugin can govern many classes of agent products without domain-specific specialization.

## Requirements

- FR-001: The plugin SHALL extend governed observation artifacts to capture runtime performance telemetry including latency, token counts, cost, and turn count.
- FR-002: The plugin SHALL preserve append-only observation history in addition to the existing latest observation artifacts.
- FR-003: The plugin SHALL preserve append-only evaluation result history in addition to the existing latest results artifact.
- FR-004: The plugin SHALL support `/arpinine-harness:at-eval benchmark <slug>` as a benchmarked evaluation mode that runs multiple scenarios and emits aggregated results.
- FR-005: The benchmark workflow SHALL compute aggregate metrics across scenarios, including percentile-based latency metrics when the underlying telemetry exists.
- FR-006: The plugin SHALL support a first-class baseline artifact that defines the approved comparison target for regression-sensitive systems.
- FR-007: The plugin SHALL support a first-class dataset manifest artifact that versions benchmark inputs and expected outputs for reproducible measurement.
- FR-008: The plugin SHALL block or warn when a team claims performance or regression outcomes without the required telemetry, history, baseline, or dataset metadata.
- FR-009: The observation schema SHALL support optional decision-provenance fields including `conversation_ids`, top-level `evidence_refs` for run-wide evidence, and `decision_records[]` with `decision_type`, `decision_id`, `confidence`, `rationale`, decision-level `evidence_refs`, `review_required`, and `review_outcome` so teams can trace outputs and correlations back to source evidence when required by the product.
- FR-010: The benchmark and history model SHALL remain framework-agnostic and SHALL work with custom harnesses, pytest-based suites, benchmark runners, or other evaluation tools.
- FR-011: Existing `latest-observation.md`, `trace.json`, and `latest-results.md` convenience artifacts SHALL remain supported for operator readability.
- FR-012: The plugin SHALL enforce benchmarked evaluation for specs whose plan declares release-blocking latency, token, cost, or regression thresholds, and SHALL allow single-run evaluation for workflows that do not declare those benchmarked release gates.

## Non-Functional Requirements

- NFR-001: Historical observation and evaluation artifacts SHALL be append-only so prior evidence is not silently lost.
- NFR-002: Performance and quality comparisons SHALL be reproducible for the same dataset version, variant id, and model/runtime configuration.
- NFR-003: The design SHALL remain implementation-neutral across Claude, Codex, and future assistant implementations.
- NFR-004: Teams that do not need benchmarked evaluation SHALL be able to continue using the existing lightweight workflow without mandatory heavy measurement overhead.
- NFR-005: Aggregated benchmark results SHALL make it possible to compute latency P50/P95, token/cost summaries, and failure-rate summaries when telemetry is present.
- NFR-006: Baseline comparisons SHALL fail closed when dataset versions or other declared comparability dimensions do not match.
- NFR-007: Existing projects using latest-only observation and evaluation artifacts SHALL remain readable without migration before benchmark history is adopted.

## Acceptance Criteria

- [x] AC-001: Given an observation trace for an agentic system, the governed observation schema can record `latency_ms`, `token_count_input`, `token_count_output`, `cost_usd`, and `turn_count`.
- [x] AC-002: Given repeated observation runs for the same spec, Arpinine Harness preserves immutable history artifacts while still updating `latest-observation.md` and `trace.json`.
- [x] AC-003: Given repeated evaluation runs for the same spec, Arpinine Harness preserves immutable result-history artifacts while still updating `latest-results.md`.
- [x] AC-004: Given a spec with benchmarked evaluation enabled, `/arpinine-harness:at-eval benchmark <slug>` runs multiple required scenarios and emits aggregated PASS/WARN/FAIL output.
- [x] AC-005: Given 3 or more benchmark runs for the same spec, dataset version, and variant id, the aggregated results include percentile-based latency reporting and summarized token/cost metrics.
- [x] AC-006: Given an approved `baseline.json`, Arpinine Harness can compare the latest benchmark results to the baseline and report regression status.
- [x] AC-007: Given a mismatched dataset version or incompatible baseline dimensions, Arpinine Harness blocks or rejects regression claims instead of producing misleading comparisons.
- [x] AC-008: Given a benchmarked system without the required dataset manifest, baseline policy, or telemetry fields, Arpinine Harness reports the missing operational prerequisites explicitly.
- [x] AC-009: Given a product that makes nontrivial AI decisions, the observation artifact model can capture `conversation_ids`, `evidence_refs`, and `decision_records[]` entries with confidence, rationale, and review outcome fields without requiring domain-specific schema specialization.
- [x] AC-010: Given a non-agentic or low-risk workflow, teams can still use the existing single-run `/arpinine-harness:at-eval run` path without mandatory benchmark artifacts.

## Out of Scope

- Choosing a single benchmark vendor or evaluation framework
- Defining one domain-specific label schema for business opportunities, support tickets, or any other product category
- Automatically approving or rotating baselines without human review
- Building a complete data-labeling system inside Arpinine Harness
- Replacing product-specific observability platforms or business analytics tools

## AI-Nativeness Assessment

**AIN Target Level**: 2 = AI-assisted internal tooling

**Agent-Callable Operations** (for AIN >= 3):
- Not applicable. This feature extends governance artifacts and benchmark workflows rather than defining a product-facing agent API.

**Human-in-the-Loop Gates** (for AIN >= 3):
- Baseline approval remains human-controlled.
- Release decisions remain human-controlled when benchmark thresholds fail or regressions are detected.

**Feedback Channels**:
- benchmark summaries and aggregated pass/fail output
- historical observation traces
- historical evaluation result snapshots
- baseline comparison output
- drift and audit findings for missing measurement prerequisites

**Evaluation Required**: NO

This feature extends governance artifact schemas and command definitions. It does not introduce autonomous executable business logic that requires its own evaluation contract.

## Operating Constraints

- The design must preserve compatibility with the existing shared artifact model under `.specify/`.
- Teams must be able to use benchmark governance without coupling the plugin to a specific agent runtime.
- The artifact model must support both lightweight operator-readable summaries and machine-readable historical records.
- Baseline comparisons must be explicit about comparable dimensions such as dataset version, model/runtime variant, prompt/config variant, and scenario set.
- Telemetry fields are populated by the product runtime, harness adapter, or evaluation runner; Arpinine Harness governs their presence and review semantics but cannot synthesize missing runtime telemetry at artifact-write time.

## Open Questions

- OQ-001: Should observation history use JSON snapshots only, or both JSON and Markdown summaries for each run?

## Resolved Decisions

- RD-001: Benchmark aggregation belongs under `/arpinine-harness:at-eval` rather than as a separate top-level command.
- RD-002: Existing latest-result and latest-observation artifacts remain as convenience views rather than being replaced.
- RD-003: Operational measurement capabilities are generic governance capabilities and not a domain-specific product extension.
- RD-004: Regression claims require matching dataset version, model/runtime variant, prompt/config variant, and scenario set between the baseline and the compared run.
- RD-005: Benchmarked evaluation is mandatory when a plan declares release-blocking latency, token, cost, or regression thresholds; otherwise single-run evaluation remains acceptable.

## Related ADRs

- ADR-0001: Separate shared core from assistant-specific implementations
- ADR-0007: Add operational measurement and benchmark governance artifacts
