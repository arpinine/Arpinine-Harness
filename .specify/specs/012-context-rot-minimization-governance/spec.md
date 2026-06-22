# Spec: Context Rot Minimization Governance

## Business Case

Arpinine Harness already improves long-running delivery by pushing intent into durable artifacts under `.specify/`: specs, plans, ADRs, rules, observations, and delivery state. That solves part of the memory problem. Important decisions no longer live only in the chat transcript.

But governed work still suffers from **context rot**. On a long session, the assistant must reconstruct current truth by rereading a large mix of conversation history, plan text, drift reports, task tables, file edits, and raw tool output. Even when the right answer exists somewhere in the repo, the live turn can still use stale or over-broad context. The result is familiar: the model loses the plot, revives old assumptions, or spends tokens reloading the same history again and again.

The compression feature in spec 011 addresses **payload size**. It does not, by itself, solve **state selection**. Compressed stale context is still stale context.

Arpinine Harness therefore needs an explicit context-rot minimization layer for its own governed workflow: one canonical per-spec working-state artifact, one deterministic context-slice policy, one tool-output summarization path, and one freshness model that marks derived state stale when the source artifacts move. The goal is not to replace specs or plans. The goal is to make the current truth cheap to recover and hard to confuse with dead history.

Release 1 targets harness-side workflow only. It must remain additive to spec 011: teams may adopt working-state and context slicing regardless of whether compression is enabled.

## User Stories

- As a harness operator resuming work after a long session or compaction, I want one compact working-state snapshot per spec so the assistant can recover the current truth without replaying the whole conversation.
- As a maintainer, I want shared hooks to refresh that working-state snapshot automatically after meaningful artifact edits so it does not silently drift behind the repo.
- As an implementer, I want large tool output summarized into decision-relevant facts so the assistant sees what matters without dragging raw noise through every turn.
- As an auditor, I want derived context artifacts marked stale when their sources changed so summaries never masquerade as authoritative truth.
- As an engineering lead, I want context-slice rules shared across Claude, Codex, and Copilot so governed commands pull the same minimal relevant state instead of each host inventing its own prompt-loading habits.

## Requirements

- FR-001: The plugin SHALL define one canonical derived artifact per active spec: `.specify/specs/<slug>/working-state.md`.
- FR-002: `working-state.md` SHALL be explicitly derived, never authoritative. Source-of-truth artifacts remain `spec.md`, `plan.md`, ADRs, rules, observations, and task state.
- FR-003: `working-state.md` SHALL contain, at minimum, machine-readable or deterministically parseable sections for: current goal, active task slice, confirmed decisions, open risks, touched files, next action, and freshness metadata.
- FR-004: The plugin SHALL provide a shared script to refresh `working-state.md` idempotently from explicit inputs instead of relying on free-form manual edits.
- FR-005: Shared PostToolUse hook wiring SHALL refresh or invalidate `working-state.md` after relevant edits to governing artifacts or task-tracked implementation files.
- FR-006: The plugin SHALL define one deterministic context-slice policy that groups prompt inputs by tier:
  - Tier 1: working state, current task slice, touched files
  - Tier 2: directly relevant spec / plan / ADR sections
  - Tier 3: older conversation or historical artifacts only on demand
- FR-007: The plugin SHALL provide a shared script to build a context slice for a spec and command from that tier policy.
- FR-008: Large tool output or command stdout SHALL be summarized into a derived `ToolFactSummary` before being included in working state or context slices, while preserving a pointer to the raw source on disk.
- FR-009: `ToolFactSummary` SHALL capture only decision-relevant facts such as errors, warnings, changed files, counts, and next-action signals; it SHALL NOT embed full raw payloads by default.
- FR-010: The plugin SHALL mark `working-state.md` stale when any governing input used to derive it has changed since the last refresh.
- FR-011: When `working-state.md` is missing or stale, governed commands SHALL fall back to authoritative artifacts and emit an observable signal indicating degraded context recovery.
- FR-012: Shared status/inspection surfaces SHALL report whether each spec has a current, stale, or missing working-state artifact.
- FR-013: The feature SHALL remain additive to context compression. It MUST work when compression is disabled and MUST NOT require a compression proxy.
- FR-014: The feature SHALL use one shared implementation path across Claude, Codex, and Copilot, differing only where host-specific hook or command assembly requires it.

## Non-Functional Requirements

- NFR-001: Working-state refresh for one spec SHALL be deterministic and idempotent: the same inputs produce byte-identical output.
- NFR-002: Derived working-state and tool summaries SHALL remain plain-text governed artifacts under `.specify/`.
- NFR-003: No raw tool output longer than the configured cap SHALL be embedded directly in `working-state.md`.
- NFR-004: The stale-detection path SHALL fail closed: uncertain freshness is treated as stale, not fresh.
- NFR-005: The context-slice builder SHALL be implementation-neutral across Claude, Codex, Copilot, and future hosts.
- NFR-006: The feature SHALL not require any external database, vector store, or network service.

## Acceptance Criteria

- [ ] AC-001: Given a governed spec with `spec.md` and `plan.md`, running the shared working-state refresh script creates `.specify/specs/<slug>/working-state.md` with the canonical sections `Freshness`, `Current Goal`, `Active Task Slice`, `Confirmed Decisions`, `Open Risks`, `Touched Files`, and `Next Action`.
- [ ] AC-002: Given the same inputs and no source changes, a second refresh produces byte-identical `working-state.md`.
- [ ] AC-003: Given an edit to `spec.md`, `plan.md`, ADR coverage, or task state, the shared PostToolUse hook either refreshes `working-state.md` or marks it stale in a deterministic way.
- [ ] AC-004: Given a stale `working-state.md`, the shared state inspection/status surface reports the spec as `stale-working-state` rather than `fresh`.
- [ ] AC-005: Given a tool output larger than the configured threshold, the shared summarization path emits a `ToolFactSummary` containing capped facts plus a pointer to the raw source, and `working-state.md` does not inline the full payload.
- [ ] AC-006: Given `/arpinine-harness:at-plan`, `/arpinine-harness:at-implement`, and `/arpinine-harness:at-review`, the command guidance defines a Tier 1 / Tier 2 / Tier 3 context-slice policy rather than instructing the host to reload full history by default.
- [ ] AC-007: Given a missing or stale working-state artifact, the context-slice builder falls back to authoritative artifacts and emits an observable `working_state_fallback` signal instead of aborting the governed command.
- [ ] AC-008: Given assembled Claude, Codex, and Copilot plugin outputs, each host inherits the same working-state and context-slice behavior from shared core scripts and hook wiring rather than divergent per-host logic.

## Out of Scope

- Outbound proxy compression or token counting at the provider boundary (spec 011)
- Replacing authoritative artifacts with summaries as the source of truth
- Product-side memory/state features for the application built with Arpinine Harness
- External memory systems such as vector databases, hosted caches, or cloud document stores
- Free-form chat summarization with no governed artifact model or freshness semantics

## AI-Nativeness Assessment

**AIN Target Level**: 2 = AI-assisted internal tooling

**Agent-Callable Operations** (for AIN >= 3):
- Not applicable. This feature governs internal delivery-state recovery and prompt assembly for harness workflow commands.

**Human-in-the-Loop Gates** (for AIN >= 3):
- Human review still owns the authoritative artifacts (`spec.md`, `plan.md`, ADRs). Derived working-state artifacts do not bypass that review path.

**Feedback Channels**:
- `working_state_fallback` signals when derived state could not be trusted
- stale/fresh status surfaced in state inspection and status reporting
- hook/test failures when working-state behavior diverges from contract

**Evaluation Required**: NO

Verification is deterministic and artifact-based. Unit and integration tests over scripts, hooks, and assembled command guidance are sufficient for release 1.

## Operating Constraints

- The feature depends on the governed artifact model introduced by spec 002 and remains repository-local under `.specify/`.
- The feature is sequenced after context compression planning, but it MUST remain independently valuable when compression is disabled.
- Hooks must remain fast enough for normal edit flow; expensive repository-wide recomputation is out of scope for the PostToolUse path.
- Derived working-state artifacts must never be mistaken for authoritative state; freshness metadata and fallback behavior are mandatory.
- Context-slice policy must be shared-core behavior, not an assistant-specific prompt convention.

## Resolved Decisions

- RD-001: The anti-rot feature is artifact-first, not chat-first: current truth is recovered from governed files, not from conversation replay.
- RD-002: One canonical per-spec `working-state.md` artifact is the primary derived context surface.
- RD-003: Context recovery is tiered. Working state and current task come first; broader artifacts are loaded only when needed.
- RD-004: Raw tool output stays on disk. Decision-relevant facts move into derived summaries.
- RD-005: Freshness is explicit. Uncertain freshness is treated as stale.
- RD-006: Release 1 is harness-side only and additive to compression; it does not require spec 011 to be enabled at runtime.

## Domain Vocabulary

- **WorkingStateSnapshot** — the canonical derived per-spec artifact stored as `working-state.md`. Avoid generic terms such as `memory`, `summary`, or `notes`.
- **ContextSlice** — the deterministic set of artifacts and summaries selected for one governed command invocation.
- **ContextTier** — the loading priority class used by the context-slice policy (`Tier 1`, `Tier 2`, `Tier 3`).
- **ToolFactSummary** — the capped fact-oriented derivative of raw tool or command output used in working state and context slices.
- **FreshnessMetadata** — the explicit source/version/timestamp markers that determine whether derived working state is still trustworthy.
- **Working-state fallback** — the degraded path that reverts to authoritative artifacts when derived state is missing or stale.

## Related ADRs

- ADR-0020: Canonical working-state artifact and freshness model
- ADR-0021: Tiered context-slice policy for governed commands
- ADR-0022: ToolFactSummary contract and raw-output retention policy
