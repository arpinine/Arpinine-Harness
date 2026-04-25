# Spec: Multi-Team Task Coordination

## Business Case

AgentAlign now supports more than one assistant implementation, but delivery coordination still breaks down if Claude and Codex can start the same task concurrently. A shared workflow only becomes operationally safe for multi-team use when task ownership is explicit, machine-readable, and enforced before implementation edits land.

This feature gives the governed workflow a real coordination contract so one team can work in Claude while another works in Codex without silently duplicating effort or overwriting each other's ownership.

## User Stories

- As an engineering lead, I want Claude and Codex to coordinate through one shared task registry so concurrent work does not collide.
- As a developer using one assistant implementation, I want the next eligible task to exclude work already assigned to or claimed by the other team.
- As a maintainer, I want task coordination to live in shared core tooling so host overlays do not fork ownership semantics.

## Requirements

- FR-001: The plugin SHALL maintain a shared coordination registry for each governed spec under `.specify/coordination/`.
- FR-002: The plugin SHALL support explicit task ownership hints in `plan.md` using optional team tags such as `[team: claude]` and `[team: codex]`.
- FR-003: The plugin SHALL provide deterministic shared scripts to claim and release tasks with lease-based ownership.
- FR-004: The plugin SHALL prevent a team from claiming a task that is actively leased by another team or explicitly assigned to another team.
- FR-005: The plugin SHALL block implementation-path edits unless the current runtime identity owns an active task claim for the governing spec.
- FR-006: Delivery reporting SHALL expose assigned team, active claimer, and lease state alongside task progress.
- FR-007: Runtime identity resolution SHALL work across Claude and Codex without requiring divergent coordination semantics in host overlays.
- FR-008: The plugin SHALL provide automated tests for ownership tags, active lease blocking, lease expiry, and pre-edit claim enforcement.

## Non-Functional Requirements

- NFR-001: Task coordination SHALL be implemented in shared core tooling rather than assistant-specific business logic.
- NFR-002: Claim and release behavior SHALL be deterministic for the same repository state and runtime identity.
- NFR-003: The coordination mechanism SHALL tolerate interrupted sessions through lease expiry rather than permanent locks.
- NFR-004: Coordination output SHALL remain inspectable by humans through repository artifacts.

## Acceptance Criteria

- [ ] AC-001: Given a task tagged `[team: codex]`, Claude cannot claim it while Codex can.
- [ ] AC-002: Given an actively leased shared task, a second team cannot claim it until the lease expires or is released.
- [ ] AC-003: Given an expired lease, another eligible team can claim the task successfully.
- [ ] AC-004: Given an implementation-path edit without an active claim, the shared pre-edit gate blocks the write with a clear ownership message.
- [ ] AC-005: Given a claimed task, delivery reporting shows assigned team, active claimer, and lease state.
- [ ] AC-006: Given Claude and Codex plugin sessions, runtime identity resolves consistently enough that claim, release, and edit-gating flows agree on task ownership.

## Out of Scope

- Coordinating across separate remote persistence backends such as Redis or Postgres
- General-purpose portfolio scheduling across repositories
- Automatic decomposition of one planned task into sub-tasks per assistant
- Replacing `plan.md` as the human-readable source of task intent

## AI-Nativeness Assessment

**AIN Target Level**: 2 = AI-assisted internal tooling

**Agent-Callable Operations** (for AIN >= 3):
- Not applicable. This feature governs internal workflow coordination rather than agent-callable product operations.

**Human-in-the-Loop Gates** (for AIN >= 3):
- Not applicable. Human approval remains part of normal governed delivery decisions, but this feature does not add product-facing agent autonomy.

**Feedback Channels**:
- Delivery matrix visibility in `.specify/delivery.md`
- Claim-gate violation messages during implementation edits
- Automated test failures for ownership, lease, and gate regressions

**Evaluation Required**: NO

## Operating Constraints

- Coordination state must be stored in repository artifacts so both implementations can inspect the same source of truth.
- Claim enforcement must remain compatible with the shared hook model already used for constitution and architecture checks.
- Host overlays may infer runtime identity differently, but claim semantics must remain identical once identity is resolved.

## Open Questions

- OQ-001: Should a later phase add heartbeats for long-running sessions or is lease renewal on repeated claims sufficient for now?
- OQ-002: Should multi-machine coordination stay file-based or move to a shared backend when the repo needs distributed execution?

## Related ADRs

- ADR-0001: Separate shared core from assistant-specific implementations
- ADR-0004: Specialized role-based agent team
