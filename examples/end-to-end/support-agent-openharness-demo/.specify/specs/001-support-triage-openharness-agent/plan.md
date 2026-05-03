# Plan: Support Triage Agent With OpenHarness

## Governing Spec
`.specify/specs/001-support-triage-openharness-agent/spec.md`

## Technical Decisions
| Decision | Rationale | ADR |
|----------|-----------|-----|
| Use internal runtime interface with OpenHarness adapter | Keeps product code decoupled from the harness SDK while using the real agent loop | ADR-0001 |
| Keep classification and priority logic in application code | Deterministic business rules must be testable without network or model dependency | ADR-0001 |
| Session reset via engine.clear() after each triage call | Satisfies session-scoped memory requirement without disabling OpenHarness internals | ADR-0001 |

## Architecture
Clean architecture slice: domain entities → application service + runtime port → OpenHarness adapter.

## Module Boundaries
| Module / Component | Responsibility | Depends On | Interface / Adapter |
|--------------------|----------------|------------|---------------------|
| app/support_triage/domain | Ticket and triage result data structures | none | Domain model |
| app/support_triage/application | Triage use case and internal runtime port | domain | SupportAgentRuntime |
| app/support_triage/adapters | OpenHarness-backed runtime implementation | application, domain | OpenHarnessAdapter |
| app/tests | Unit and adapter tests | application, adapters, domain | unittest |
| app/eval | Live evaluation runner | application, adapters, domain | custom Python script |

## Dependency Rules
- Domain code must not depend on application, adapter, framework, persistence, or harness SDK details.
- Application code may depend on domain code and internal runtime interfaces only.
- Adapter code may depend on application ports, domain models, and the OpenHarness SDK.
- Product code must not import OpenHarness modules directly; runtime-specific code belongs behind the adapter.

## Testability By Boundary
| Boundary | Test Type | Isolation Strategy |
|----------|-----------|--------------------|
| domain | unit | dataclass value checks |
| application | unit | FakeRuntime test double for SupportAgentRuntime |
| adapter/tool | unit | DraftSupportReplyTool.execute() tested directly — no API required |
| adapter/integration | integration | real OpenHarness + Anthropic API — skipped if ANTHROPIC_API_KEY absent |
| live eval | scenario | real API call with synthetic scenarios |

## Harness Strategy
| Concern | Decision |
|---------|----------|
| Why harness is needed | Response drafting uses an agent loop: model receives ticket context, calls a registered tool, returns a composed reply. Single LLM call cannot handle tool registration, permission enforcement, or event emission. |
| Harness/runtime class | OpenHarness (HKUDS/OpenHarness, `pip install openharness-ai`) |
| Product abstraction boundary | `SupportAgentRuntime` interface in `app/support_triage/application/triage_service.py` |
| Tool access model | `draft_support_reply` only — registered via `ToolRegistry`, `is_read_only()=True`, auto-approved. No filesystem, shell, email, or CRM tools registered. |
| Memory/state model | Session-scoped only. `engine.clear()` called after every triage call. No MEMORY.md written. No cross-session state. |
| Permission and safety model | `PermissionSettings(mode=PermissionMode.DEFAULT, allowed_tools=["draft_support_reply"])`. `create_support_case` is a product-level approval handled by `approval_callback`, not an OpenHarness tool. |
| Swap strategy | Replace `OpenHarnessAdapter` in `app/support_triage/adapters/` only. `SupportTriageService` and domain code unchanged. |

## Tasks
- [x] TASK-001: Define domain ticket and triage result models
- [x] TASK-002: Define `SupportAgentRuntime` port in application layer
- [x] TASK-003: Implement `DraftSupportReplyTool` as `BaseTool` subclass
- [x] TASK-004: Implement `OpenHarnessAdapter` with injectable engine and approval callback
- [x] TASK-005: Add unit tests with `FakeQueryEngine` — no network required
- [x] TASK-006: Add live evaluation script against real OpenHarness + Anthropic

## Evaluation Strategy
| Dimension | Metric / Check | Threshold | Framework | Evidence |
|-----------|----------------|-----------|-----------|----------|
| Task success | required scenarios complete | 100% | custom Python script | `.specify/evals/001-support-triage-openharness-agent/latest-results.md` |
| Permission safety | approval event present | 100% scenarios | custom Python script | `.specify/evals/001-support-triage-openharness-agent/latest-results.md` |
| Memory scope | no persistent memory event | 100% session scoped | custom Python script | `.specify/evals/001-support-triage-openharness-agent/latest-results.md` |
| Tool containment | only `draft_support_reply` in tool_call events | 100% | custom Python script | `.specify/evals/001-support-triage-openharness-agent/latest-results.md` |
| Draft quality floor | non-empty draft, no false case-creation claim | 100% | custom Python script | `.specify/evals/001-support-triage-openharness-agent/latest-results.md` |

Evaluation plan: `.specify/evals/001-support-triage-openharness-agent/eval-plan.md`

## Security
- API key read from `ANTHROPIC_API_KEY` environment variable only — never hardcoded
- No shell, filesystem, or email tools registered in the harness
- No CRM mutation; case creation gated by approval callback

## Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| OpenHarness SDK import leaks into application code | High | Enforce adapter boundary with ADR-0001 and harness-001 rule; quick_drift_check.py catches leakage after every write |
| engine.clear() does not fully reset session state | Medium | Verify with observation trace — no cross-session tool_call events across scenario runs |
| Model does not call draft_support_reply tool | Medium | System prompt instructs model to always call the tool; fallback returns empty string surfaced by eval |
| OpenHarness API changes break adapter | Low | Adapter is isolated — update only the adapter file |

## ADRs Created During Planning
- ADR-0001: OpenHarness adapter boundary
