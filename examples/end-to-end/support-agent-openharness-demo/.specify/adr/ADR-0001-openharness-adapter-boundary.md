---
governs: specs/001-support-triage-openharness-agent
supersedes: ~
status: Accepted
date: 2026-05-03
covers:
  - decision:001-support-triage-openharness-agent:harness-boundary
---

# ADR-0001: OpenHarness Adapter Boundary

## Status
Accepted

## Context
The demo uses OpenHarness (HKUDS/OpenHarness) as the agent runtime for response drafting. OpenHarness provides `BaseTool`, `ToolRegistry`, `PermissionChecker`, and `QueryEngine` — all of which are SDK-specific types. Product code must not couple to these types directly.

Two additional governance risks are specific to OpenHarness:
- Memory persists cross-session by default via MEMORY.md. Session isolation requires explicit `engine.clear()` after each call.
- 43+ tools are available in the registry by default. Narrow allowlist must be enforced at registration time.

## Decision
Use an internal `SupportAgentRuntime` interface in the application layer. Implement `OpenHarnessAdapter` in the adapter layer. Only the adapter file imports from `openharness.*`.

The adapter owns:
- `DraftSupportReplyTool` (`BaseTool` subclass) — the only registered tool
- `ToolRegistry` with a single tool entry
- `PermissionSettings(mode=PermissionMode.DEFAULT, allowed_tools=["draft_support_reply"])`
- `QueryEngine` construction and session lifecycle
- `engine.clear()` after every triage call to enforce session scope

Classification and priority logic remain in the application service — deterministic, testable without network.

## Consequences
- Positive: product logic is testable without OpenHarness or network access (FakeQueryEngine injected in tests).
- Positive: OpenHarness import is contained to one file — `quick_drift_check.py` enforces this after every write.
- Positive: swapping the harness requires changing only the adapter file.
- Positive: session memory scope is guaranteed by `engine.clear()` — verifiable in observation traces.
- Negative: live evaluation requires `ANTHROPIC_API_KEY` and network access.
- Negative: model may not call `draft_support_reply` on every run — system prompt must instruct it to.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Import `QueryEngine` directly in `SupportTriageService` | Couples application logic to OpenHarness SDK — violates harness strategy |
| Disable MEMORY.md via config file | Requires per-project config management; `engine.clear()` is explicit and testable |
| Register all 43 default tools | Violates narrow tool allowlist requirement — harness-governor blocks implementation |
