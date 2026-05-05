# Project Conventions

## Module Structure

- `src/agents/` — orchestrators; compose tools and domain logic; no raw I/O
- `src/tools/` — atomic, side-effectful operations (API calls, file I/O, DB queries)
- `src/domain/` — pure business logic; no framework or infrastructure imports
- `evals/` — evaluation cases and datasets
- `tests/` — unit and integration tests

## Architecture Rules

- Dependency direction: agents -> tools -> domain. Domain imports nothing from this project.
- Tool functions accept explicit dependencies; independently testable without an agent runtime.
- No business logic in tools. No I/O in domain.

## Evaluation

- Each agent-facing workflow should have a corresponding evaluation case in `evals/`.
- Evaluation plans live in `.specify/evals/`.
- Choose the evaluation runner and runtime-specific policy in governed spec and plan artifacts, not in this bootstrap file.

## Testing

- Domain logic: unit tests with minimal or no mocks.
- Tools: integration tests against real dependencies or contract-tested stubs.
- Orchestration layers: test at the boundary appropriate for the chosen runtime and delivery model.
