# Project Conventions

## Technology Selection

This archetype is **technology-agnostic**. It defines layer *boundaries*, not a fixed stack.
Choose the concrete stack per product and record it in an ADR (the `at-plan` tech-architect
prompts this). Examples a product might pick — none are mandated:

- `src/backend/`  — Python + FastAPI, Node + Express, Go + chi, ...
- `src/frontend/` — React + Vite, Vue + Vite, SvelteKit, ...
- `src/db/`       — Postgres + SQLAlchemy, Prisma, MongoDB, ...
- `infra/`        — AWS CDK, Terraform, Pulumi, ...

The boundary rules below hold for **any** of these choices.

## Module Structure

- `src/backend/` — routes, controllers, request handlers; composes domain logic and persistence; no business rules
- `src/frontend/` — UI components and assets; talks to the backend only over the HTTP/API boundary
- `src/domain/` — pure business logic; no framework, transport, persistence, or frontend imports
- `src/db/` — persistence adapters; database drivers, ORM sessions, and raw queries live here only
  - exposes repository functions/classes; callers depend on these abstractions, never on the driver
- `src/observability/` — observation provider abstraction and implementations
  - the provider interface is the only import allowed outside this package; SDK imports stay inside it
- `infra/` — infrastructure-as-code; compute, networking, and secrets definitions live here only
- `evals/` — evaluation cases and datasets
- `tests/` — unit and integration tests

## Architecture Rules

- Dependency direction: backend -> domain, backend -> db. Domain imports nothing from this project.
- The frontend depends only on the published API contract (request/response shapes); it never imports `src/backend/`, `src/domain/`, or `src/db/`.
- No business logic in route handlers or the persistence layer. No I/O in domain.
- Persistence access is confined to `src/db/`; backend and domain modules depend on repository or data-access interfaces.
- Infrastructure-as-code stays in `infra/`; application code under `src/` never imports IaC constructs, and `infra/` never imports application business logic. The app is packaged and deployed by the infra definitions; they communicate through configuration and environment.
- Repositories and the `ObservationProvider` are injected at the composition root; never resolved inside backend, domain, or db modules.
- Observability SDK imports are confined to the selected provider module under `src/observability/`. No exceptions.

## Observability

- Inbound requests and non-trivial backend operations should be wrapped in `ObservationProvider.span()`.
- `ObservationProvider.flush()` must be called on application shutdown.
- Backend-specific observability env vars must be documented in `.env.example`. Never hardcode credentials.

## Evaluation

- Each user-facing workflow should have a corresponding evaluation case in `evals/`.
- Evaluation plans live in `.specify/evals/`.
- Choose the evaluation runner and runtime-specific policy in governed spec and plan artifacts, not in this bootstrap file.

## Testing

- Domain logic: unit tests with minimal or no mocks.
- Persistence (`src/db/`): integration tests against a real or contract-tested database.
- Backend: integration tests at the API boundary.
- Frontend: component and end-to-end tests against the API contract.
