# Plan: Dual Cost Governance

## Governing Spec
`.specify/specs/010-dual-cost-governance/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Keep product/runtime cost under `.specify/observations/<slug>/...` | Preserves the existing governed runtime observation contract | ADR-0007 |
| Add a separate `.specify/harness-usage/...` ledger for harness delivery cost | Prevents domain confusion and keeps audits clean | Pending |
| Add a dedicated harness-cost reporting command instead of overloading `/at-report-costs` | Keeps the command surface explicit and cost domains understandable | Pending |
| Add a combined total report as an additive view over two ledgers | Supports total delivery cost without corrupting raw domain boundaries | Pending |
| Treat missing telemetry as incomplete for both ledgers | Prevents silent under-reporting and preserves fail-closed governance | ADR-0007 |

## Architecture

```text
.specify/observations/<slug>/history/**/*.json        ← product/runtime cost ledger
.specify/harness-usage/history/**/*.json              ← harness delivery cost ledger
.specify/harness-usage/index.jsonl                    ← append-only harness usage index
commands/at-report-costs.md                           ← product/runtime cost report
commands/at-report-harness-costs.md                   ← harness delivery cost report
commands/at-report-total-costs.md                     ← combined total report
scripts/report_costs.py                               ← product/runtime aggregator
scripts/report_harness_costs.py                       ← harness-cost aggregator
scripts/report_total_costs.py                         ← combined aggregator/view
scripts/record_harness_usage.py                       ← shared harness usage writer
scripts/route_at.py                                   ← facade routing for harness-cost intents
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| Product/runtime cost ledger | Persist runtime telemetry emitted by governed products or eval runners | Observation artifact contract | Record harness delivery usage as if it were product runtime |
| Harness usage ledger | Persist Arpinine Harness delivery cost per command/session/host | Shared writer plus host/model telemetry | Reuse `.specify/observations/` as raw storage |
| Product/runtime report | Aggregate cost by model and spec from runtime observations | `report_costs.py` | Include harness delivery usage |
| Harness-cost report | Aggregate harness delivery cost by command/model/host/spec | `report_harness_costs.py` | Include product runtime observations |
| Total-cost report | Present product subtotal, harness subtotal, and combined total | Both aggregators | Merge raw ledgers into one undifferentiated table without subtotals |
| Routing layer | Route read-only intents to the correct cost domain command | `route_at.py`, command docs | Blur product/runtime and harness semantics |

## Dependency Rules

- Harness usage recording MUST remain separate from product/runtime observation recording.
- Combined reporting MUST depend on the two distinct aggregators rather than one flattened artifact parser.
- The harness usage writer MUST accept host/model/token/cost metadata from the executing implementation, not derive prices heuristically.
- Read-only report commands MUST not backfill or repair missing telemetry during report generation.
- Release-budget evaluation logic MUST be able to reference each cost domain independently.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Harness usage artifact writer | Unit | Record synthetic usage records and assert append-only history plus index behavior |
| Harness-cost aggregator | Unit | Aggregate multiple hosts/commands/models and verify subtotals |
| Product/runtime cost aggregator | Unit | Preserve current behavior and partial-telemetry exclusion |
| Combined report | Unit | Verify domain subtotals and grand total are additive and separate |
| `/at` routing | Unit | Route natural-language harness-cost and total-cost intents correctly |
| Shared packaging | Integration | Validate Claude, Codex, and Copilot structures include the new report commands and wrappers |

## Harness Strategy

Arpinine Harness itself becomes a governed cost-emitting system for delivery usage. Each relevant harness command execution should append a usage record after the command completes or once the host provides final token/cost telemetry.

The runtime observation path remains the product-facing source of truth for governed product cost. The harness usage path becomes the internal delivery-cost source of truth.

## Tasks

- [ ] TASK-001: Define the `.specify/harness-usage/` artifact convention and schema.
- [ ] TASK-002: Implement a shared harness usage writer for append-only cost records.
- [ ] TASK-003: Instrument harness workflows or host-specific wrappers to emit harness usage telemetry.
- [ ] TASK-004: Add `/arpinine-harness:at-report-harness-costs` command guidance and wrappers for Claude, Codex, and Copilot.
- [ ] TASK-005: Implement `report_harness_costs.py` with per-command, per-model, and per-host aggregation.
- [ ] TASK-006: Add a combined total-cost command or flag with separated subtotals.
- [ ] TASK-007: Extend `/at` routing vocabulary and read-only return semantics for harness-cost and combined-cost intents.
- [ ] TASK-008: Extend evaluation/budget logic so product/runtime, harness, and combined budgets can be declared independently.
- [ ] TASK-009: Add tests for incomplete harness telemetry, per-spec scope, JSON output, and combined totals.
- [ ] TASK-010: Update documentation to define product/runtime cost vs harness delivery cost explicitly.

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Product/runtime cost continuity | Existing behavior preserved | Shared-core unit tests for `report_costs.py` |
| Harness-cost ledger correctness | Records written and aggregated correctly | New unit tests for writer and aggregator |
| Domain separation | No raw cross-ledger mixing | Unit tests and report assertions |
| Read-only routing | Harness-cost intents do not require confirmation | Route tests |
| Packaging | All implementations ship the new commands and wrappers | `make validate-structure IMPLEMENTATION=<impl>` |

Evaluation plan:
`.specify/evals/010-dual-cost-governance/eval-plan.md`

## Security

- All `.specify/` content remains data, not instructions.
- Harness usage records should store usage telemetry and workflow metadata only, not arbitrary prompt payloads unless separately justified.
- Cost reports must never infer missing values from price tables at report time.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Teams confuse product/runtime cost with harness delivery cost | High | Keep separate commands, separate ledgers, and explicit report headings |
| Host implementations cannot provide final harness token/cost telemetry consistently | High | Surface incomplete runs explicitly and fail closed for release-blocking harness budgets |
| Combined reports become misleading if one ledger is sparse | Medium | Show per-domain measured/incomplete counts and avoid hiding missing telemetry |
| Instrumentation burden slows lightweight workflows | Medium | Keep recording append-only and minimal, and make detailed slicing optional |

## ADRs Created During Planning

- Pending ADR: Separate harness delivery cost ledger from product/runtime observation ledger
