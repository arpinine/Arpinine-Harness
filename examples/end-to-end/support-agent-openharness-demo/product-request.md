# Product Request: Support Triage Agent With OpenHarness

## Request
Build a support triage agent that classifies inbound tickets, drafts first responses using an agent runtime, and gates case creation behind a human approval step.

## Why OpenHarness
Use OpenHarness (HKUDS/OpenHarness) as the harness runtime. It provides a tool-calling loop, a narrow tool allowlist via ToolRegistry, permission enforcement via PermissionChecker, and an observable event stream — all required by the harness governance model.

## Constraints
- The OpenHarness SDK must not appear in product domain or application code
- Session memory only — no MEMORY.md persistence across triage calls
- Tool allowlist: draft_support_reply only
- Case creation requires explicit approval callback

## Success
A ticket submitted to SupportTriageService returns a classified, prioritised triage result with a non-empty draft response, a recorded approval event, and session-scoped memory writes only.
