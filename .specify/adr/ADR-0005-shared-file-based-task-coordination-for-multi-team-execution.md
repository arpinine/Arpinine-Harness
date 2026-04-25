---
governs: specs/007-multi-team-task-coordination
supersedes: ~
status: Accepted
date: 2026-04-25
covers:
  - decision:007-multi-team-task-coordination:shared-file-based-task-coordination
---

# ADR-0005: Shared file-based task coordination for multi-team execution

## Status
Accepted

## Context
AgentAlign supports multiple assistant implementations, but the original implementation workflow assumed one active delivery team at a time. Task selection was effectively derived from `plan.md` checkbox state alone, which is sufficient for sequential work but unsafe for concurrent execution by Claude and Codex.

The workflow needed a coordination mechanism that both implementations could inspect and update without introducing assistant-specific semantics or requiring an external service. That mechanism also had to preserve `plan.md` as the human-readable planning artifact while preventing one runtime from starting work already assigned to or claimed by the other.

The repository already uses shared scripts, hooks, and generated artifacts as the common cross-implementation seam. Multi-team coordination needed to follow that same design rather than pushing ownership logic into Claude-only or Codex-only overlays.

## Decision
AgentAlign stores multi-team task ownership in a shared file-based coordination registry under `.specify/coordination/<slug>.json`.

The coordination model is:

| Artifact / Mechanism | Role |
|----------------------|------|
| `plan.md` | Human-readable task intent, task status, and optional ownership hints such as `[team: claude]` or `[team: codex]` |
| `.specify/coordination/<slug>.json` | Machine-managed lease and claimer state for tasks in one governed spec |
| `claim_task.py` | Atomically claim the next eligible task using file locking |
| `release_task.py` | Release or complete a previously claimed task |
| `check_task_claim.py` | Block implementation-path edits unless the current runtime identity owns an active claim |
| `update_backlog.py` | Render assigned team, active claimer, and lease visibility into `.specify/delivery.md` |

Task ownership follows these rules:

- A task may be claimed only if its checkbox is `[ ]`
- A task tagged `[team: other-team]` is not eligible for the current team
- An active lease blocks other teams from claiming the task until the lease expires or is released
- `plan.md` remains the source of task meaning and progress, while the coordination registry is the source of active ownership
- Runtime identity is resolved from the host plugin environment when available, with deterministic fallback instance ids so direct script calls and hook-wrapped checks agree on ownership

This decision keeps coordination semantics in shared core tooling and makes multi-team execution inspectable through repository artifacts rather than hidden assistant state.

## Consequences
- Positive: Claude and Codex can coordinate through one shared, implementation-neutral ownership model.
- Positive: Ownership state is visible and auditable in repository artifacts rather than buried in one assistant session.
- Positive: Lease expiry allows interrupted sessions to recover without permanent locks.
- Positive: The same shared scripts can be used by hooks, delivery reporting, and future orchestration improvements.
- Negative: File-based coordination is suitable for shared-repo execution but does not solve distributed multi-machine coordination by itself.
- Negative: The workflow now depends on runtime identity resolution staying stable across direct script execution and hook execution paths.
- Negative: Operators must still assign team tags deliberately in `plan.md` when they want explicit ownership rather than opportunistic claiming.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Keep task ownership implicit in `plan.md` checkbox state only | Two runtimes can still select the same eligible task; no machine-managed concurrency control exists |
| Store active ownership only in assistant-local memory or host-specific session state | Ownership becomes invisible to the other implementation and breaks the shared-core abstraction |
| Introduce an external coordination backend such as Redis or Postgres now | Adds infrastructure and deployment complexity before the repo has proven the local shared-repo coordination model |
| Fork separate coordination semantics for Claude and Codex | Violates the implementation-abstraction goal and creates inconsistent task-ownership behavior across hosts |
