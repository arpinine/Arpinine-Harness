# Plan: Support Triage Agent With OpenAI

## Governing Spec
`.specify/specs/001-support-triage-openai-agent/spec.md`

## Technical Decisions
| Decision | Rationale | ADR |
|----------|-----------|-----|
| Keep classification and priority logic in application code | Keeps deterministic business rules testable without a network dependency | ADR-0001 |
| Use an OpenAI-backed adapter for response drafting only | Demonstrates practical harness application while minimizing provider coupling | ADR-0001 |

## Architecture
The demo has a small clean architecture slice: domain entities, application service, and a concrete OpenAI adapter behind an internal runtime interface.

## Module Boundaries
| Module / Component | Responsibility | Depends On | Interface / Adapter |
|--------------------|----------------|------------|---------------------|
| app/support_triage/domain | Ticket and triage result data structures | none | Domain model |
| app/support_triage/application | Triage use case and internal runtime port | app/support_triage/domain | SupportAgentRuntime |
| app/support_triage/adapters | OpenAI runtime implementation | app/support_triage/application, app/support_triage/domain | OpenAIHarnessRuntime |
| app/tests | Behavioral and adapter tests | app/support_triage/application, app/support_triage/adapters, app/support_triage/domain | unittest |
| app/eval | Live evaluation runner | app/support_triage/application, app/support_triage/adapters, app/support_triage/domain | custom Python script |

## Dependency Rules
- Domain code must not depend on application, adapter, framework, persistence, or model SDK details.
- Application code may depend on domain code and internal runtime interfaces only.
- Adapter code may depend on application ports, domain models, and the OpenAI SDK.
- Product code must not import the OpenAI SDK directly; runtime-specific code belongs behind an adapter.

## Testability By Boundary
| Boundary | Test Type | Isolation Strategy |
|----------|-----------|--------------------|
| domain | unit | dataclass value checks |
| application | unit | fake runtime implementation |
| adapter | unit | injected fake OpenAI client |
| live eval | scenario | real API call with fixed synthetic scenarios |

## Harness Strategy
| Concern | Decision |
|---------|----------|
| Why harness is needed | The product behavior includes LLM-backed drafting, approval evidence, and runtime event recording. |
| Harness/runtime class | OpenAI Responses API adapter |
| Product abstraction boundary | `SupportAgentRuntime` interface in the application layer |
| Tool access model | One remote text-generation call for response drafting only |
| Memory/state model | Session-scoped event list only; no persistent cross-customer memory |
| Permission and safety model | `create_support_case` requires an approval callback before completion evidence is accepted |
| Swap strategy | Replace `OpenAIHarnessRuntime` with another provider adapter without changing the application service |

## Tasks
- [x] TASK-001: Define domain ticket and triage result models
- [x] TASK-002: Define `SupportAgentRuntime` port
- [x] TASK-003: Implement OpenAI adapter with injectable client and approval callback
- [x] TASK-004: Add unit tests for classification, priority, prompt dispatch, and approval event recording
- [x] TASK-005: Add a live evaluation script for the real adapter
- [x] TASK-006: Document the harness boundary and drift rule

## Evaluation Strategy
| Dimension | Metric / Check | Threshold | Framework | Evidence |
|-----------|----------------|-----------|-----------|----------|
| Task success | required scenarios complete | 100% | custom Python script | `.specify/evals/001-support-triage-openai-agent/latest-results.md` |
| Permission safety | approval check present | 100% scenarios | custom Python script | `.specify/evals/001-support-triage-openai-agent/latest-results.md` |
| Memory scope | no persistent memory event | 100% session scoped | custom Python script | `.specify/evals/001-support-triage-openai-agent/latest-results.md` |
| Draft quality floor | non-empty draft and no false case-creation claim | 100% scenarios | custom Python script | `.specify/evals/001-support-triage-openai-agent/latest-results.md` |

## Security
The demo reads credentials from the environment only. It does not expose shell access, filesystem tools, or CRM mutation through the runtime.

## Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Network or credential failure blocks live eval | High | Keep unit tests fully offline and fail fast with a clear message in the live script |
| Provider-specific SDK coupling leaks into app code | High | Enforce the adapter boundary with ADR and rule |
| LLM output varies across runs | Medium | Keep evaluation thresholds focused on safety and contract checks, not exact wording |

## ADRs Created During Planning
- ADR-0001: OpenAI Responses adapter boundary
