# Spec: Dual Cost Governance

## Business Case

Arpinine Harness now has an initial cost-reporting surface for governed observation telemetry, but that only covers one side of the economics. Teams need to answer two different questions:

- what does the governed product cost to run?
- what does Arpinine Harness cost to deliver that product?

Those are not the same number. Product/runtime cost reflects the behavior of the built system or evaluation runtime. Harness delivery cost reflects the model usage consumed by Arpinine Harness itself while discovering, specifying, planning, implementing, evaluating, and reviewing work.

If Arpinine Harness merges those numbers into one undifferentiated report, the result becomes misleading. Teams lose the ability to distinguish production operating cost from delivery overhead, and cost budgets become impossible to govern coherently.

Arpinine Harness needs a dual-cost model with separate storage, separate reporting commands, and an optional combined view. The plugin must preserve the existing governed product/runtime cost report while adding first-class harness-usage accounting so teams can reason about delivery cost as part of product governance.

## User Stories

- As a product owner, I want to know what the governed product costs to run so I can judge runtime affordability.
- As a maintainer, I want to know what Arpinine Harness itself costs to deliver work so I can judge workflow efficiency.
- As an engineering lead, I want a combined delivery-cost view so I can compare total cost across initiatives.
- As an auditor, I want product/runtime cost and harness delivery cost kept separate so reviews do not mix incompatible telemetry sources.
- As an operator, I want missing telemetry surfaced explicitly rather than silently estimated.

## Requirements

- FR-001: The plugin SHALL preserve `/arpinine-harness:at-report-costs` as the product/runtime cost report sourced from governed observation telemetry under `.specify/observations/<slug>/`.
- FR-002: The plugin SHALL add `/arpinine-harness:at-report-harness-costs` as a read-only report of Arpinine Harness usage cost.
- FR-003: The plugin SHALL add a combined read-only report surface, either `/arpinine-harness:at-report-total-costs` or an equivalent combined mode, that reports product/runtime subtotal, harness subtotal, and combined total without merging raw ledgers.
- FR-004: Harness delivery cost records SHALL be stored separately from product/runtime observation artifacts under a dedicated governed artifact tree.
- FR-005: Each harness delivery cost record SHALL support at least `run_id`, `timestamp`, `command`, `spec_slug`, `session_id`, `host`, `model_name`, `model_version`, `token_count_input`, `token_count_output`, `cost_usd`, and `outcome`.
- FR-006: Product/runtime cost and harness delivery cost reports SHALL support whole-repo aggregation and `--spec <slug>` scoping.
- FR-007: Cost reports SHALL support both human-readable table output and machine-readable JSON output.
- FR-008: The combined report SHALL compute subtotals independently from the two ledgers before presenting a grand total.
- FR-009: Runs lacking the required token or cost telemetry SHALL be reported as incomplete and excluded from totals.
- FR-010: Arpinine Harness SHALL never synthesize missing token or cost values for either cost domain.
- FR-011: The `/at` facade SHALL route natural-language harness-cost intents to the harness-cost reporting command without confirmation when the intent is read-only.
- FR-012: Evaluation plans SHALL be able to declare release-blocking budgets independently for product/runtime cost, harness delivery cost, and combined cost.

## Non-Functional Requirements

- NFR-001: Product/runtime cost and harness delivery cost SHALL remain separate governed artifact domains.
- NFR-002: Release-blocking budget checks SHALL fail closed when required telemetry for the targeted cost domain is missing.
- NFR-003: The design SHALL remain implementation-neutral across Claude, Codex, Copilot, and future assistant implementations.
- NFR-004: Read-only reporting commands SHALL not mutate governed artifacts.
- NFR-005: The cost model SHALL stay auditable by using append-only history for harness usage records.

## Acceptance Criteria

- [ ] AC-001: Given governed runtime observations with token and cost telemetry, `/arpinine-harness:at-report-costs` reports per-model product/runtime cost totals.
- [ ] AC-002: Given harness usage records for multiple commands, `/arpinine-harness:at-report-harness-costs` reports per-command and per-model harness delivery totals.
- [ ] AC-003: Given both ledgers are present, the combined report shows product/runtime subtotal, harness subtotal, and grand total without flattening the two domains.
- [ ] AC-004: Given a run missing token or cost telemetry in either domain, the report flags it as incomplete and excludes it from totals.
- [ ] AC-005: Given a release-blocking budget threshold for harness delivery cost, the governed benchmark/reporting path fails closed when the required harness telemetry is absent.
- [ ] AC-006: Given a natural-language request such as "how much has the harness itself cost us", the `/at` facade routes to the harness-cost report without unnecessary confirmation.
- [ ] AC-007: Given `--spec <slug>`, each report limits itself to that governed scope.
- [ ] AC-008: Given `--json`, each report emits machine-readable aggregates for its own cost domain.

## Out of Scope

- Billing integration with external model vendors
- Currency conversion beyond the recorded `cost_usd` field
- Automatic pricing estimation from token counts when the runtime omitted `cost_usd`
- Product business metrics such as revenue, margin, or customer-level analytics
- Time-window filtering beyond future optional extensions such as `--since` and `--until`

## AI-Nativeness Assessment

**AIN Target Level**: 2 = AI-assisted internal tooling

**Agent-Callable Operations** (for AIN >= 3):
- Not applicable. This feature governs cost ledgers and reporting surfaces rather than introducing a new product-facing agent API.

**Human-in-the-Loop Gates** (for AIN >= 3):
- Budget declarations remain human-controlled.
- Interpretation of reported cost remains human-controlled.

**Feedback Channels**:
- product/runtime cost report
- harness delivery cost report
- combined cost report
- benchmark or release-budget threshold output

**Evaluation Required**: NO

This feature extends governance artifacts, command contracts, and reporting logic. It does not introduce autonomous business execution.

## Operating Constraints

- Product/runtime cost must continue to source from `.specify/observations/<slug>/...`.
- Harness delivery cost must be stored in a separate governed ledger and must not reuse `.specify/observations/` as its primary storage root.
- Teams may define Arpinine Harness usage itself as part of product delivery cost, but the artifact model must still keep harness and product/runtime cost distinguishable.
- Arpinine Harness governs the presence and reporting semantics of telemetry; the runtime or host remains responsible for emitting actual token and cost values.
- Combined totals are valid only when both underlying ledgers preserve domain separation.

## Open Questions

- OQ-001: Should the combined view be a new top-level command or a flag on one of the existing reports?
- OQ-002: Should harness usage history be partitioned by spec first, by session first, or by a global append-only ledger with index files?

## Resolved Decisions

- RD-001: Product/runtime cost and harness delivery cost are distinct governed domains and must not be mixed in raw storage.
- RD-002: `/arpinine-harness:at-report-costs` remains the product/runtime report.
- RD-003: Harness delivery cost is first-class and requires its own governed ledger and report surface.
- RD-004: Combined totals are additive views over separate subtotals, not one merged source ledger.
- RD-005: Missing telemetry is excluded and flagged, never estimated.

## Related ADRs

- ADR-0007: Add operational measurement and benchmark governance artifacts
