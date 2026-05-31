# Evaluation Plan: Operational Measurement And Benchmark Governance

## Governing Spec
`.specify/specs/009-operational-measurement-and-benchmark-governance/spec.md`

## Scope
- Validate shared-core artifact contracts, benchmark runner behavior, and assembled plugin structure for the operational measurement feature.
- Applies to `src/arpinine-harness-core/**` plus assembled Claude, Codex, and Copilot plugin outputs.

## Evaluation Objective
- Prove that the shared core preserves the lightweight path, supports benchmarked evaluation, and fails closed on invalid baseline comparisons.

## Evaluation Framework
- Framework: Python unittest plus structure validation targets
- Execution command: `python3 -m unittest discover -s src/arpinine-harness-core/tests`
- Owner: Arpinine Harness maintainers

## Benchmark Policy
- Benchmark required: No
- Benchmark command: `python3 src/arpinine-harness-core/scripts/run_benchmark.py --slug 001-support-triage-agent`
- Dataset manifest path: `.specify/evals/009-operational-measurement-and-benchmark-governance/dataset-manifest.json`
- Minimum scenario count for aggregated reporting: 3
- Aggregation policy: single-run governance validation for this feature; benchmark execution is verified through unit and demo integration coverage

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| shared-core unit suite | validate schema, history, benchmark, and fail-closed logic | local tests | Yes |
| Claude structure assembly | validate assembled Claude plugin content | `make validate-structure IMPLEMENTATION=claude` | Yes |
| Codex structure assembly | validate assembled Codex plugin content | `make validate-structure IMPLEMENTATION=codex` | Yes |
| Copilot structure assembly | validate assembled Copilot plugin content | `make validate-structure IMPLEMENTATION=copilot` | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Shared-core regression | unittest pass rate | >= 1.00 | block completion |
| Claude packaging | validate-structure exit status | >= 1.00 | block completion |
| Codex packaging | validate-structure exit status | >= 1.00 | block completion |
| Copilot packaging | validate-structure exit status | >= 1.00 | block completion |

## Regression Policy
- Rerun evaluation after changes to shared scripts, commands, templates, or tests under `src/arpinine-harness-core/`.
- Any failing shared-core test blocks completion.
- Any assembled plugin structure failure blocks completion.

## Baseline Comparison
- Baseline required: No
- Baseline artifact path: `.specify/evals/009-operational-measurement-and-benchmark-governance/baseline.json`
- Comparable dimensions: not applicable for this governance feature
- Failure policy when baseline dimensions differ: not applicable

## Reporting
- Latest results path: `.specify/evals/009-operational-measurement-and-benchmark-governance/latest-results.md`
- Historical storage: optional; this feature uses test and structure evidence rather than benchmark history to close implementation
- Observation history source: not applicable

## Approval Rule
- Work is not complete until the shared-core test suite passes and all assembled plugin structures (Claude, Codex, Copilot) validate.
