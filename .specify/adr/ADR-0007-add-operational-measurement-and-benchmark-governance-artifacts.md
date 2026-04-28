---
governs: specs/009-operational-measurement-and-benchmark-governance
supersedes: ~
status: Proposed
date: 2026-04-28
covers:
  - decision:009-operational-measurement-and-benchmark-governance:benchmark-history-baseline-model
  - decision:009-operational-measurement-and-benchmark-governance:telemetry-schema-extension
  - decision:009-operational-measurement-and-benchmark-governance:append-only-history-model
  - decision:009-operational-measurement-and-benchmark-governance:dataset-manifest-model
---

# ADR-0007: Add operational measurement and benchmark governance artifacts

## Status
Proposed

## Context

Arpinine Harness already governs planning, architecture, harness strategy, evaluation contracts, and runtime observations. That governance model is strong enough for many workflows, but it currently lacks the artifact structure needed to prove performance and regression behavior over time.

The current model keeps:
- latest observation artifacts
- latest evaluation results
- evaluation plans that may declare latency, cost, and quality thresholds

However, that is not enough for benchmarked or regression-sensitive agent systems because:
- observation traces do not store the telemetry needed to compute latency, token, and cost metrics reliably
- observation history is not preserved across runs
- evaluation result history is not preserved across runs
- there is no first-class benchmark mode under `/arpinine-harness:at-eval`
- there is no approved baseline artifact for regression comparison
- dataset versions are not first-class governed inputs

Without these capabilities, Arpinine Harness can describe operational quality expectations but cannot consistently enforce or verify them from shared governed artifacts.

## Decision

Arpinine Harness will extend its generic governance model with an operational-measurement layer built on six capabilities:

1. richer observation schema with performance telemetry and optional decision provenance
2. append-only observation history in addition to current latest observation artifacts
3. append-only evaluation result history in addition to current latest result artifacts
4. benchmark aggregation under `/arpinine-harness:at-eval benchmark <slug>`
5. first-class `baseline.json` artifact for approved regression comparisons
6. first-class `dataset-manifest.json` artifact for versioned, reproducible benchmark inputs

The model remains framework-agnostic and domain-neutral:
- teams may use custom harnesses, pytest suites, benchmark runners, or other evaluation frameworks
- the plugin will not specialize itself around business opportunities or any single product domain
- the new capabilities become required only when the workflow declares benchmarked or regression-sensitive evaluation needs

Latest summary artifacts remain in place:
- `.specify/observations/<slug>/latest-observation.md`
- `.specify/observations/<slug>/trace.json`
- `.specify/evals/<slug>/latest-results.md`

These continue to serve operator readability, while the new history and baseline artifacts provide durable evidence and comparison semantics.

## Consequences

- Positive: Arpinine Harness can govern performance and regression claims using repository-owned evidence rather than one-off manual interpretation.
- Positive: Teams can compute aggregate metrics such as latency P50/P95, token/cost summaries, and failure rates from governed artifacts.
- Positive: Benchmark runs become reproducible because dataset version and baseline selection are explicit.
- Positive: The plugin remains generic across domains while becoming stronger for serious agent products.
- Positive: Existing lightweight workflows remain supported because the convenience artifacts and single-run paths are preserved.
- Negative: The artifact model becomes larger and more operationally complex.
- Negative: Teams must curate baselines and dataset manifests explicitly rather than relying on ad hoc comparisons.
- Negative: Product runtimes, harness adapters, or evaluation runners must populate the required telemetry fields; Arpinine Harness can govern the schema and review semantics, but it cannot manufacture missing runtime telemetry at write time.
- Negative: Audit and evaluation commands will need additional logic to reject invalid comparisons across incompatible versions or variants.

Existing projects that only use latest-only observation and evaluation artifacts remain valid after upgrade; history, baseline, and dataset-manifest artifacts are additive and become required only for benchmarked or regression-sensitive workflows.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Keep the current latest-only observation and eval model | Cannot support percentile metrics, trend analysis, or trustworthy regression detection |
| Add a separate top-level `/at-benchmark` command | Splits evaluation semantics unnecessarily; benchmarking is a mode of evaluation, not a different governance stage |
| Push measurement history entirely into external observability tools | Breaks the repository-owned governance model and makes eval evidence less portable across teams and assistants |
| Specialize the plugin around one product type such as business-opportunity agents | Violates the goal of keeping Arpinine Harness generic and reusable across agent products |
