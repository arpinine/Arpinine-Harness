# Plan: Multi-Team Task Coordination

## Governing Spec
`.specify/specs/007-multi-team-task-coordination/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Store task coordination in `.specify/coordination/<slug>.json` | Keeps ownership state in shared repo artifacts visible to both Claude and Codex | Consequence of ADR-0001 |
| Keep `plan.md` as task intent and progress while the coordination registry owns leases | Separates human planning from machine-managed concurrency state | No separate ADR |
| Enforce active claims through a shared PreToolUse gate | Prevents implementation edits from bypassing task ownership | No separate ADR |
| Derive runtime identity from host environment with deterministic fallback instance ids | Reduces operator friction while keeping claims stable across hook and script paths | No separate ADR |

## Architecture

```text
.specify/specs/<slug>/plan.md          ← task intent, status, optional [team: ...] tags
.specify/coordination/<slug>.json      ← machine-managed ownership and lease registry
scripts/task_coordination.py           ← shared parsing, registry, identity, lease helpers
scripts/claim_task.py                  ← atomic claim path
scripts/release_task.py                ← release/completion path
scripts/check_task_claim.py            ← pre-edit enforcement gate
scripts/update_backlog.py              ← delivery rendering of team and lease state
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| `plan.md` task list | Human-readable task intent, status, and optional team hints | Governed spec workflow | Own active lease state |
| Coordination registry | Persist claimed owner, lease, and completion metadata | `.specify/coordination/`, parsed task list | Redefine task descriptions |
| `task_coordination.py` | Shared identity, plan parsing, file locking, and registry sync helpers | Local filesystem and repo artifacts | Contain host-specific business rules |
| Claim/release scripts | Transition task ownership deterministically | Shared coordination helpers | Bypass registry locking |
| Pre-edit claim gate | Block implementation edits without ownership | Shared coordination helpers and hook payload | Mutate tasks itself |
| Delivery report | Surface ownership and lease visibility | Plan and registry state | Become the source of task definition |

## Dependency Rules

- Claim, release, and pre-edit enforcement MUST use shared coordination helpers.
- Host overlays MUST not redefine team-ownership semantics or lease rules.
- Delivery reporting MUST render ownership from the coordination registry without replacing `plan.md` as the source of task intent.
- Automatic runtime identity resolution MUST produce the same effective claimer across direct script calls and hook-wrapped calls in one assistant session.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Team-tag claim eligibility | Unit | Assert tagged tasks accept only the matching team |
| Lease blocking and expiry | Unit | Claim tasks, simulate active/expired leases, and assert eligibility |
| Pre-edit enforcement | Unit | Feed hook payloads and assert blocked vs allowed edits |
| Runtime identity stability | Unit | Run claim and hook flows with host-env-derived identity and assert consistent claimer resolution |
| Shared packaging | Integration | Validate assembled Claude and Codex plugin structures |

## Harness Strategy

Not applicable. This feature coordinates governed repository work and hooks, not a product harness runtime.

## Tasks

- [x] TASK-001: Define a shared coordination registry format under `.specify/coordination/`
- [x] TASK-002: Extend shared task parsing to support optional `[team: claude]` and `[team: codex]` ownership hints
- [x] TASK-003: Implement shared `claim_task.py` and `release_task.py` with deterministic file locking and lease semantics
- [x] TASK-004: Extend `update_backlog.py` so delivery output shows assigned team, active claimer, and lease state
- [x] TASK-005: Add a shared pre-edit claim gate that blocks implementation-path edits without an active claim
- [x] TASK-006: Implement automatic runtime identity resolution for Claude and Codex with stable default instance ids
- [x] TASK-007: Add automated tests for team tags, lease conflicts, lease expiry, and claim-gate enforcement
- [x] TASK-008: Update workflow docs and implementation guidance to explain multi-team coordination behavior

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Ownership correctness | AC-001 through AC-003 | Unit tests for claims, conflicts, and lease expiry |
| Enforcement correctness | AC-004 | Unit test of the pre-edit claim gate with hook-style payloads |
| Operator visibility | AC-005 | Delivery rendering check against plan and coordination state |
| Runtime consistency | AC-006 | Host-env identity resolution test plus structure validation for Claude and Codex |

Evaluation plan:
`N/A`

## Security

- Coordination scripts must not execute repository code while parsing task ownership or hook payloads
- File locking must stay within repository-owned coordination artifacts
- The pre-edit gate should fail clearly when identity or ownership is missing rather than allowing silent bypass

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Automatic instance identity differs between direct calls and hooks | Medium | Derive fallback identity from stable host/session signals and test both paths |
| Team tags are documented but ignored by future host changes | Low | Keep eligibility logic in shared core and cover it with tests |
| File-based coordination becomes insufficient for distributed execution | Medium | Keep scope local-repo first and treat remote coordination as a later spec |

## ADRs Created During Planning

No new ADR required at planning time.
