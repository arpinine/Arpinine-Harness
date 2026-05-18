# Plan: [FEATURE NAME]

## Governing Spec
`.specify/specs/[SPEC-NUMBER]-[name]/spec.md`

## Technical Decisions
| Decision | Rationale | ADR |
|----------|-----------|-----|
| [choice] | [why] | ADR-XXXX |

## Vocabulary Decisions
| Domain Term | Code Construct | Module | Deviation Justification |
|-------------|---------------|--------|------------------------|
| [FulfillmentBatch] | `FulfillmentBatch` | `fulfillment/domain/` | none — exact match |
| [SettlementWindow] | `SettlementWindow` | `settlement/domain/` | none — exact match |

New terms introduced during planning (requires spec `## Domain Vocabulary` update before implementation):
- [none]

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

## Observability Strategy

<!-- DECISION GATE — replace this section with BLOCK A or BLOCK B, then delete the other and these comments -->

<!-- BLOCK A: No observability needed — paste this line as the entire section body:
N/A — feature makes no LLM calls and produces no AI-driven output. Standard logging is sufficient.
-->

<!-- BLOCK B: Observability required — fill every row; observability-governor blocks /at-implement if any row is empty -->
| Concern | Decision |
|---------|----------|
| Observation required | Yes |
| ObservationProvider interface | [file path — e.g. `src/observability/base.py`] |
| Default implementation | OpenTelemetry or Langfuse — [justify if using another backend] |
| Env var configuration | [document backend env vars in `.env.example`, e.g. `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT` or `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`] |
| Evaluation required | Yes |
| EvaluationProvider interface | [file path — e.g. `src/evaluation/base.py`] |
| Default implementation | DeepEval — [justify if not DeepEval] |
| Observation-evaluation bridge | Attach eval metric scores to traces via `ObservationProvider.score()` |
| Swap strategy | [what changes when provider is replaced — must be adapter file only; no agent, tool, or domain code changes] |

Implementation handoff: run `python3 scripts/scaffold_observability_setup.py --spec <slug>` before `/arpinine-harness:at-implement` to scaffold provider files from this section.
Provider templates: `templates/observation-provider-template.py`, `templates/opentelemetry-observation-provider-template.py`, `templates/langfuse-observation-provider-template.py`, `templates/evaluation-provider-template.py`, `templates/deepeval-evaluation-provider-template.py`

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
