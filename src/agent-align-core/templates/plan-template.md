# Plan: [FEATURE NAME]

## Governing Spec
`.specify/specs/[SPEC-NUMBER]-[name]/spec.md`

## Technical Decisions
| Decision | Rationale | ADR |
|----------|-----------|-----|
| [choice] | [why] | ADR-XXXX |

## Architecture
[High-level component description or diagram]

## Module Boundaries
| Module / Component | Responsibility | Depends On | Interface / Adapter |
|--------------------|----------------|------------|---------------------|
| [module] | [single clear concern] | [allowed dependencies] | [API / port / adapter] |

## Dependency Rules
- Domain or business logic must not depend directly on framework or persistence details
- External systems should be accessed through adapters or explicit interfaces
- Cross-module dependencies must follow a documented direction

## Testability By Boundary
| Boundary | Test Type | Isolation Strategy |
|----------|-----------|--------------------|
| [module] | [unit / contract / integration] | [mock adapter / in-memory fake / fixture] |

## Harness Strategy
Use this section when the product feature depends on an agent harness or agent runtime.
Delete this section or replace the table with `N/A` if no harness is needed.

| Concern | Decision |
|---------|----------|
| Why harness is needed | [reason] |
| Harness/runtime class | [hosted coding agent / embedded agent runtime / custom orchestration layer / other] |
| Product abstraction boundary | [internal service / adapter / port] |
| Tool access model | [which tools are allowed and why] |
| Memory/state model | [session / persistent / none / bounded context] |
| Permission and safety model | [approval flow / policy / limits] |
| Swap strategy | [how to replace the harness later] |

## Tasks
- [ ] TASK-001: Write failing tests for [module] [team: codex]
- [ ] TASK-002: Implement [module] [team: claude]
- [ ] TASK-003: Integration test for [flow]

Team tags are optional. When present, only that team may claim the task during `/agent-align:at-implement`.

## Evaluation Strategy
| Dimension | Metric / Check | Threshold | Framework | Evidence |
|-----------|----------------|-----------|-----------|----------|
| [quality dimension] | [task success / hallucination / policy compliance / latency / etc.] | [pass threshold] | [DeepEval / pytest / custom / benchmark] | [results path] |

Evaluation plan:
`.specify/evals/[SPEC-NUMBER]-[name]/eval-plan.md`

## Security
[Authentication, authorization, input validation, secrets management]

## Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| [Risk] | High / Med / Low | [Mitigation] |

## ADRs Created During Planning
- ADR-XXXX: [Title]
