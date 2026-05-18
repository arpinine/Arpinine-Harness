# Project Conventions

## Module Structure

- `src/agents/` — orchestrators; compose tools and domain logic; no raw I/O
- `src/tools/` — atomic, side-effectful operations (API calls, file I/O, DB queries)
- `src/domain/` — pure business logic; no framework or infrastructure imports
- `src/observability/` — observation provider abstraction and implementations
  - `base.py` — `ObservationProvider` Protocol (the only import allowed outside this package)
  - `opentelemetry.py` — `OpenTelemetryObservationProvider` (recommended generic default; all OpenTelemetry SDK imports stay here)
  - `langfuse.py` — `LangfuseObservationProvider` (supported alternative; all Langfuse SDK imports stay here)
  - `noop.py` — `NoopObservationProvider` (use in unit tests and local dev without credentials)
- `src/evaluation/` — evaluation provider abstraction and implementations
  - `base.py` — `EvaluationProvider` Protocol (the only import allowed outside this package)
  - `deepeval.py` — `DeepEvalProvider` (default; all DeepEval SDK imports stay here)
  - `noop.py` — `NoopEvaluationProvider` (use in unit tests that do not run full eval suites)
- `evals/` — evaluation cases and datasets
- `tests/` — unit and integration tests

## Architecture Rules

- Dependency direction: agents -> tools -> domain. Domain imports nothing from this project.
- Tool functions accept explicit dependencies; independently testable without an agent runtime.
- No business logic in tools. No I/O in domain.
- `ObservationProvider` and `EvaluationProvider` are injected at the composition root; never resolved inside agents, tools, or domain modules.
- Observability SDK imports are confined to the selected provider module under `src/observability/`. DeepEval SDK imports are confined to `src/evaluation/deepeval.py`. No exceptions.

## Observability

- All LLM calls must be wrapped in `ObservationProvider.trace()` + `ObservationProvider.generation()`.
- Non-trivial agent steps should be wrapped in `ObservationProvider.span()`.
- `ObservationProvider.flush()` must be called on application shutdown.
- Evaluation metric scores should be attached to traces via `ObservationProvider.score()` to surface them alongside runtime data in the selected backend.
- Backend-specific observability env vars must be documented in `.env.example`. Never hardcode credentials.

## Evaluation

- Each agent-facing workflow should have a corresponding evaluation case in `evals/`.
- Evaluation plans live in `.specify/evals/`.
- Evaluation cases use `EvaluationProvider.evaluate()` and `EvaluationProvider.assert_passes()` — never call DeepEval directly.
- Default framework: DeepEval. Justify a different choice in an ADR.
- `DEEPEVAL_API_KEY` is optional (enables Confident AI dashboard). Local evaluation works without it.
- Choose the evaluation runner and runtime-specific policy in governed spec and plan artifacts, not in this bootstrap file.

## Testing

- Domain logic: unit tests with minimal or no mocks.
- Tools: integration tests against real dependencies or contract-tested stubs.
- Orchestration layers: test at the boundary appropriate for the chosen runtime and delivery model.
