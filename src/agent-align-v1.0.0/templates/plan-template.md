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

## Tasks
- [ ] TASK-001: Write failing tests for [module]
- [ ] TASK-002: Implement [module]
- [ ] TASK-003: Integration test for [flow]

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
