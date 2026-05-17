# Spec: Multi-Team Task Coordination

## Business Case

Arpinine Harness now supports more than one assistant implementation, but delivery coordination still breaks down if Claude and Codex can start the same task concurrently. A shared workflow only becomes operationally safe for multi-team use when task ownership is explicit, machine-readable, and enforced before implementation edits land.

This feature gives the governed workflow a real coordination contract so one team can work in Claude while another works in Codex without silently duplicating effort or overwriting each other's ownership.

## User Stories

- As an engineering lead, I want Claude and Codex to coordinate through one shared task registry so concurrent work does not collide.
- As a developer using one assistant implementation, I want the next eligible task to exclude work already assigned to or claimed by the other team.
- As a maintainer, I want task coordination to live in shared core tooling so host overlays do not fork ownership semantics.

## Requirements

- FR-001: The plugin SHALL maintain a shared coordination registry for each governed spec under `.specify/coordination/`.
- FR-002: The plugin SHALL support explicit task ownership hints in `plan.md` using optional team tags such as `[team: claude]` and `[team: codex]`.
- FR-003: The plugin SHALL provide a deterministic coordination interface to claim and release tasks with lease-based ownership, producing a machine-readable result (JSON `{"ok": true|false, ...}`) for each operation.
- FR-004: The plugin SHALL prevent a team from claiming a task that is actively leased by another team or explicitly assigned to another team.
- FR-004a: The plugin SHALL treat untagged tasks as shared work claimable by any eligible team, subject to lease rules.
- FR-005: The plugin SHALL block edits to implementation-path files (paths under `src/`, `lib/`, `app/`, `packages/`, `services/`, `internal/`, `cmd/`, or `tests/`) unless the current runtime identity owns an active task claim for the governing spec. Blocked attempts SHALL produce a non-zero exit and a message identifying the required claim.
- FR-006: Delivery reporting SHALL expose assigned team, active claimer, and lease state alongside task progress.
- FR-008: The plugin SHALL provide automated tests for ownership tags, active lease blocking, lease expiry, and pre-edit claim enforcement.

## Non-Functional Requirements

- NFR-001: Task coordination SHALL be implemented in shared core tooling rather than assistant-specific business logic.
- NFR-002: Claim and release behavior SHALL be deterministic for the same repository state and runtime identity.
- NFR-003: The coordination mechanism SHALL tolerate interrupted sessions through lease expiry rather than permanent locks. Task leases SHALL default to 1800 seconds and SHALL be configurable per claim invocation.
- NFR-004: Coordination output SHALL remain inspectable by humans through repository artifacts.
- NFR-005: Runtime identity resolution SHALL produce identical claimer identity across direct claim invocations and hook-wrapped invocations within the same assistant session, with no divergent semantics required in host overlays.

## Acceptance Criteria

- [x] AC-001: Given a task tagged `[team: codex]`, a claim attempt by Claude returns `{"ok": false, "error": "..."}` and a claim attempt by Codex returns `{"ok": true, ...}`.
- [x] AC-002: Given an actively leased shared task, a second team's claim attempt returns `{"ok": false, "error": "..."}` until the lease expires (after its configured duration) or the task is explicitly released.
- [x] AC-003: Given a task whose lease has expired (simulated by setting `lease_until` to a past timestamp), a claim attempt by another eligible team returns `{"ok": true, ...}` and the registry reflects the new owner.
- [x] AC-004: Given an edit to a file under an implementation path (e.g., `src/`, `tests/`) without an active claim, the pre-edit gate exits non-zero and prints a message that includes the slug and the required claim action.
- [x] AC-005: Given a claimed task, the delivery report includes assigned team, active claimer name, and lease expiry alongside task progress.
- [x] AC-006: Given the same host environment, running both the claim script and the pre-edit hook produces the same `claimer_id` string (format: `<team_id>:<instance_id>`) for the same assistant session.

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
- Untagged tasks are shared tasks by default and may be claimed by any eligible team when no active lease exists.
- Lease recovery is timeout-based: interrupted sessions recover through lease expiry rather than permanent locks.
- Operators may force release a task explicitly through `scripts/release_task.py --slug <slug> --task-id <task> --state available` when human recovery is required.

## Open Questions

_(none)_

## Resolved Decisions

- RD-001: Lease renewal on repeated claim is sufficient for the current local shared-repo model; heartbeats are deferred until real session durations or distributed execution make them necessary.
- RD-002: Multi-machine coordination with a remote backend (Redis, Postgres) is explicitly out of scope for this feature. Coordination stays file-based. This question is closed for the current delivery scope.

## Related ADRs

- ADR-0001: Separate shared core from assistant-specific implementations
- ADR-0004: Specialized role-based agent team
- ADR-0005: Shared file-based task coordination for multi-team execution
- ADR-0008: PreToolUse hooks as blocking enforcement gates (governs FR-005 pre-edit claim gate)
