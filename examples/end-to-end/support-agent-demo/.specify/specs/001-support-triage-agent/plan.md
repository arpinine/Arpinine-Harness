# Plan: Support Triage Agent

## Governing Spec
`.specify/specs/001-support-triage-agent/spec.md`

## Technical Decisions
| Decision | Rationale | ADR |
|----------|-----------|-----|
| Use internal runtime interface with fake adapter | Keeps product code decoupled from a harness SDK while demonstrating agent runtime behavior | ADR-0001 |

## Architecture
The demo has a small clean architecture slice: domain entities, application service, and adapter-backed runtime.

## Module Boundaries
| Module / Component | Responsibility | Depends On | Interface / Adapter |
|--------------------|----------------|------------|---------------------|
| app/support_triage/domain | Ticket and triage result data structures | none | Domain model |
| app/support_triage/application | Triage use case and internal runtime port | app/support_triage/domain | SupportAgentRuntime |
| app/support_triage/adapters | Fake harness runtime implementation | app/support_triage/application, app/support_triage/domain | FakeHarnessRuntime |
| app/tests | Behavioral tests | app/support_triage/application, app/support_triage/adapters, app/support_triage/domain | unittest |
| app/eval | Evaluation runner and scenario evidence | app/support_triage/application, app/support_triage/adapters, app/support_triage/domain | custom eval script |

## Dependency Rules
- Domain code must not depend on application, adapter, framework, persistence, or harness runtime details.
- Application code may depend on domain code and internal runtime interfaces only.
- Adapter code may depend on application ports and domain models.
- Product code must not import a harness SDK directly; runtime-specific code belongs behind an adapter.

## Testability By Boundary
| Boundary | Test Type | Isolation Strategy |
|----------|-----------|--------------------|
| domain | unit | dataclass value checks |
| application | unit | fake runtime adapter |
| adapter | integration-style unit | inspect emitted events |
| eval | scenario | synthetic ticket scenarios |

## Harness Strategy
| Concern | Decision |
|---------|----------|
| Why harness is needed | The product behavior models an agent runtime that drafts responses, records tool calls, and requests approval before case creation. |
| Harness/runtime class | Embedded agent runtime simulated by a fake adapter |
| Product abstraction boundary | `SupportAgentRuntime` interface in the application layer |
| Tool access model | `draft_support_reply` only; no filesystem, shell, email, or CRM access |
| Memory/state model | Session-scoped event list only; no persistent cross-customer memory |
| Permission and safety model | `create_support_case` requires a permission check before completion evidence is accepted |
| Swap strategy | Replace `FakeHarnessRuntime` with a real harness adapter without changing domain or application code |

## Tasks
- [x] TASK-001: Define domain ticket and triage result models
- [x] TASK-002: Define `SupportAgentRuntime` port
- [x] TASK-003: Implement fake harness adapter
- [x] TASK-004: Add unit tests for classification, priority, and approval event
- [x] TASK-005: Add custom evaluation scenarios
- [x] TASK-006: Record observation trace

## Evaluation Strategy
| Dimension | Metric / Check | Threshold | Framework | Evidence |
|-----------|----------------|-----------|-----------|----------|
| Task success | scenario pass rate | >= 1.00 | custom Python script | `.specify/evals/001-support-triage-agent/latest-results.md` |
| Permission safety | approval check present | 100% scenarios | custom Python script | `.specify/evals/001-support-triage-agent/latest-results.md` |
| Memory scope | no persistent memory event | 100% session scoped | observation review | `.specify/observations/001-support-triage-agent/trace.json` |

Evaluation plan:
`.specify/evals/001-support-triage-agent/eval-plan.md`

## Security
No secrets, external network, shell access, email sending, or CRM mutation are used in the demo. Case creation is represented by an approval event only.

## Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Fake adapter hides real runtime risk | Medium | Keep harness strategy explicit and require eval/observation evidence before replacing the adapter |
| Classification rules are too simple | Medium | Evaluation scenarios document the accepted demo scope |
| Product code couples to harness SDK later | High | ADR-0001 and harness-001 rule require adapter isolation |

## ADRs Created During Planning
- ADR-0001: Fake harness adapter boundary
