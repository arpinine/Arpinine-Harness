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

<!-- DECISION GATE — replace this section with BLOCK A or BLOCK B, then delete the other and these comments -->

<!-- BLOCK A: No harness needed — paste this line as the entire section body:
N/A — single LLM call sufficient. No agent loop, tool execution, or session state required.
-->

<!-- BLOCK B: Harness required — fill every row; harness-governor blocks /at-implement if any row is empty -->
| Concern | Decision |
|---------|----------|
| Why harness is needed | [describe why a single LLM call is insufficient — e.g. multi-turn tool loop, mid-execution approval gate, session state required] |
| Runtime selected | [e.g. OpenHarness (`pip install openharness-ai`) / LangGraph / Pydantic AI / Semantic Kernel / custom] |
| Product abstraction boundary | [interface name and file path — e.g. `SupportAgentRuntime` in `app/support_triage/application/triage_service.py`] |
| Tool access model | [explicit allowlist — name every tool and justify inclusion; no wildcard grants] |
| Memory / state model | [scope: session-only / persistent / none — name reset mechanism, e.g. `engine.clear()` after each call] |
| Permission and safety model | [which actions require human approval, approval callback pattern, any auto-approved read-only tools] |
| Swap strategy | [what changes when runtime is replaced — must be adapter layer only; domain and application code unchanged] |

Harness-specific evaluation belongs in `## Evaluation Strategy` and the linked `eval-plan.md`, not as an extra row in this table.

## Tasks
- [ ] TASK-001: Write failing tests for [module] [team: codex]
- [ ] TASK-002: Implement [module] [team: claude]
- [ ] TASK-003: Integration test for [flow]

Team tags are optional. When present, only that team may claim the task during `/arpinine-harness:at-implement`.

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
