# Plan: Context Rot Minimization Governance

## Governing Spec
`.specify/specs/012-context-rot-minimization-governance/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Use one canonical per-spec `working-state.md` artifact | Gives every governed command a compact current-state entrypoint instead of conversation archaeology | ADR-0020 |
| Keep working state derived and stale-aware, never authoritative | Prevents summaries from silently replacing source-of-truth artifacts | ADR-0020 |
| Introduce deterministic context tiers and a shared context-slice builder | Reduces over-contexting and keeps command prompt assembly consistent across hosts | ADR-0021 |
| Summarize large tool output into `ToolFactSummary` plus raw pointer | Preserves action-relevant facts without dragging raw noise into every turn | ADR-0022 |
| Refresh or invalidate working state from shared PostToolUse hooks | Keeps state current without relying on the operator to remember manual summary maintenance | ADR-0020 |
| Treat freshness uncertainty as stale and fall back to authoritative artifacts | Fail-closed behavior is safer than hallucinating freshness | ADR-0020 |

## Vocabulary Decisions

| Domain Term | Code Construct | Module | Deviation Justification |
|-------------|---------------|--------|------------------------|
| WorkingStateSnapshot | `working-state.md` artifact + `update_working_state.py` | `.specify/specs/<slug>/`, `scripts/` | none — exact domain match |
| ContextSlice | `build_context_slice.py` output payload | `scripts/` | none |
| ContextTier | `tier` fields / constants | `scripts/build_context_slice.py` | none |
| ToolFactSummary | `tool_fact_summary.py` output record | `scripts/` | none |
| FreshnessMetadata | freshness block in `working-state.md` + inspection payload | `scripts/`, `.specify/specs/<slug>/` | none |

New terms introduced during planning (requires spec `## Domain Vocabulary` update before implementation):
- [none]

## Architecture

```text
src/arpinine-harness-core/
  scripts/
    update_working_state.py         ← derive / refresh canonical working-state artifact
    build_context_slice.py          ← select Tier 1 / Tier 2 / Tier 3 inputs for a command
    tool_fact_summary.py            ← summarize large tool output into capped facts + raw pointer
    check_working_state.py          ← freshness / fallback / artifact validation entrypoint
    inspect_state.py                ← extended to report working-state freshness
    spec_status.py                  ← extended to surface stale/missing working-state state
  hooks/
    hooks.json                      ← PostToolUse refresh / invalidate wiring
  commands/
    at-plan.md                      ← consume working state + context tiers
    at-implement.md                 ← consume working state + context tiers
    at-review.md                    ← consume working state + context tiers
    at-status.md                    ← report working-state freshness
  templates/
    working-state-template.md       ← canonical artifact layout
    tool-fact-summary-template.md   ← optional summary structure fixture
.specify/specs/<slug>/
  spec.md
  plan.md
  working-state.md                  ← derived WorkingStateSnapshot
```

## Module Boundaries

| Module / Component | Responsibility | Depends On | Interface / Adapter |
|--------------------|----------------|------------|---------------------|
| `update_working_state.py` | Read governing artifacts and emit deterministic `working-state.md` | spec/plan/ADR/task artifacts | CLI + pure derivation helpers |
| `build_context_slice.py` | Select minimal relevant context for a spec + command | working state, source artifacts, tier policy | JSON-emitting CLI |
| `tool_fact_summary.py` | Convert large tool output into capped decision facts plus raw pointer | raw output file/path, configured thresholds | pure summarizer + CLI |
| `check_working_state.py` | Validate freshness and decide fallback vs fresh use | working state, source mtimes / metadata | CLI for hooks and commands |
| Hook wiring | Trigger refresh / invalidation after relevant writes | shared scripts | `hooks.json` command hooks |
| Command guidance | Tell hosts which context slice to load first | shared scripts + governed artifact model | assembled markdown command contract |
| Status surfaces | Report fresh/stale/missing working-state state | working-state checker | `inspect_state.py`, `spec_status.py` |

## Dependency Rules

- `working-state.md` is always derived from authoritative artifacts; no module may treat it as the source of truth for governance decisions.
- Hook wiring may call shared scripts, but shared scripts must not depend on host-specific implementation directories.
- Context-slice assembly must depend on explicit tier rules, not free-form chat history heuristics.
- Tool-output summarization must preserve a raw pointer/path and must not delete raw artifacts.
- Freshness checks must fail closed: unknown or partial metadata counts as stale.
- Compression integration is optional and orthogonal; these modules must not depend on `ContextCompressionProvider`.

## Testability By Boundary

| Boundary | Test Type | Isolation Strategy |
|----------|-----------|--------------------|
| Working-state derivation | Unit | temporary spec/plan/ADR fixtures, deterministic output assertions |
| ToolFactSummary | Unit | synthetic large stdout fixtures with capped-fact assertions |
| Freshness detection | Unit | controlled mtime / metadata fixtures |
| Context-slice builder | Unit | fixture artifacts + command name matrix |
| Hook-triggered refresh / invalidation | Integration | invoke hook entrypoints against temp repo state |
| Command guidance assembly | Integration | assert command docs reference working state and tier policy |
| Status reporting | Unit / Integration | temp repo with fresh/stale/missing working-state artifacts |

## Harness Strategy

N/A — single LLM call sufficient. No agent loop, tool execution, or session state required.

This feature governs artifact refresh and prompt assembly policy for the harness workflow. It is not itself a product-side agent runtime.

## Observability Strategy

N/A — feature makes no LLM calls and produces no AI-driven output. Standard logging plus explicit `working_state_fallback` signals are sufficient.

## Tasks

- [ ] TASK-000: Author ADR-0020 through ADR-0022 covering working-state derivation, context tiers, and tool-output summary policy. `[team: claude]`
- [ ] TASK-001: Add `working-state-template.md` and define the canonical artifact layout and freshness metadata fields. `[team: claude]`
- [ ] TASK-002: Implement `update_working_state.py` with deterministic derivation helpers and unit tests. `[team: codex]`
- [ ] TASK-003: Implement `tool_fact_summary.py` with capped-fact output and raw-pointer retention tests. `[team: codex]`
- [ ] TASK-004: Implement `check_working_state.py` and extend `inspect_state.py` / `spec_status.py` to report fresh, stale, and missing working-state state. `[team: codex]`
- [ ] TASK-005: Implement `build_context_slice.py` and codify Tier 1 / Tier 2 / Tier 3 selection rules. `[team: codex]`
- [ ] TASK-006: Update `hooks/hooks.json` and any shared shell entrypoints so relevant writes refresh or invalidate working state through shared core logic. `[team: codex]`
- [ ] TASK-007: Update `/arpinine-harness:at-plan`, `/arpinine-harness:at-implement`, `/arpinine-harness:at-review`, and `/arpinine-harness:at-status` command guidance to consume working state and context tiers first. `[team: copilot]`
- [ ] TASK-008: Add integration tests for hook behavior, fallback signaling, and assembled command guidance across hosts. `[team: codex]`
- [ ] TASK-009: Update documentation to explain authoritative artifacts vs derived working state, stale-state behavior, and the additive relationship to compression. `[team: copilot]`

## Evaluation Strategy

N/A — no separate eval plan required. Release verification is deterministic through unit and integration tests over artifact derivation, hook behavior, fallback signaling, and assembled command contracts.

## Security

- `working-state.md` and `ToolFactSummary` remain DATA, not instructions. They inherit the same injection boundary expectations as the underlying `.specify/` artifacts.
- Raw tool output pointers must not point outside repository-owned or approved temp paths without explicit justification.
- Derived summaries must not embed secrets or credentials from raw output when a capped fact summary is sufficient.
- Freshness metadata must be trustworthy and not editable by hosts in a way that bypasses stale detection.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Working-state artifact becomes a second conflicting source of truth | High | Keep artifact derived-only, explicit freshness block, authoritative fallback path |
| Hooks become noisy or slow | Medium | Keep PostToolUse scope narrow and deterministic; avoid repo-wide rescans |
| Tool summaries omit a critical fact | Medium | Preserve raw pointer, cap only default inclusion, add fallback signal and tests |
| Hosts ignore tier policy and keep loading full history | Medium | Put policy in shared command contracts and integration tests |
| Stale detection misses a relevant upstream change | Medium | Fail closed on uncertainty; track source metadata explicitly |

## ADRs Created During Planning

- ADR-0020: Canonical working-state artifact and freshness model
- ADR-0021: Tiered context-slice policy for governed commands
- ADR-0022: ToolFactSummary contract and raw-output retention policy
