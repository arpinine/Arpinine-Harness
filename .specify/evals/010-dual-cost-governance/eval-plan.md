# Evaluation Plan: Dual Cost Governance

## Governing Spec
`.specify/specs/010-dual-cost-governance/spec.md`

## Scope

- Validate the new dual-cost artifact model, reporting commands, routing behavior, and implementation packaging.
- Applies to shared-core reporting scripts, `/at` routing, and assembled Claude, Codex, and Copilot plugin outputs.

## Evaluation Objective

- Prove that Arpinine Harness can report product/runtime cost and harness delivery cost as separate domains, while also supporting a trustworthy combined total.

## Evaluation Framework

- Framework: Python unittest plus structure validation targets
- Execution command: `python3 -m unittest discover -s src/arpinine-harness-core/tests`
- Owner: Arpinine Harness maintainers

## Benchmark Policy

- Benchmark required: No
- Benchmark command: `python3 src/arpinine-harness-core/scripts/report_total_costs.py --slug 010-dual-cost-governance --json`
- Dataset manifest path: not applicable
- Minimum scenario count for aggregated reporting: 1
- Aggregation policy: validate report correctness and fail-closed budget semantics through shared-core tests and structure validation

## Datasets And Scenarios

| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| product/runtime cost fixtures | validate existing observation-driven cost aggregation | shared-core unit tests | Yes |
| harness usage fixtures | validate harness delivery cost aggregation | shared-core unit tests | Yes |
| combined report fixtures | validate separated subtotals and grand total | shared-core unit tests | Yes |
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
| Product runtime budget | product_cost_total_usd | <= 5.00 | block release |
| Harness delivery budget | harness_cost_total_usd | <= 5.00 | block release |
| Combined delivery budget | combined_cost_total_usd | <= 10.00 | block release |

> **Dual-cost budget gate.** Product/runtime cost, harness delivery cost, and combined delivery cost are separate governed thresholds. Missing required telemetry for any release-blocking threshold must fail closed rather than degrade into an implicit pass.

## Regression Policy

- Rerun evaluation after changes to shared scripts, commands, route logic, or tests under `src/arpinine-harness-core/`.
- Any failing shared-core test blocks completion.
- Any assembled plugin structure failure blocks completion.
- Any release-blocking cost-domain threshold exceeded or rendered unverifiable by missing telemetry blocks release.

## Baseline Comparison

- Baseline required: No
- Baseline artifact path: optional future extension
- Comparable dimensions: host, command, model/runtime variant, and governed spec scope when baseline support is later added
- Failure policy when baseline dimensions differ: fail closed

## Reporting

- Latest results path: `.specify/evals/010-dual-cost-governance/latest-results.md`
- Historical storage: optional for this governance feature; correctness is proven by tests and structure validation
- Product/runtime cost source: `.specify/observations/<slug>/history/**/*.json`
- Harness delivery cost source: `.specify/harness-usage/history/**/*.json`
- Combined report source: additive view over the two governed ledgers

## Approval Rule

- Work is not complete until shared-core tests pass, route behavior is validated, and assembled Claude, Codex, and Copilot plugin structures validate with the new cost-reporting surfaces present.
