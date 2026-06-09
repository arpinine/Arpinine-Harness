# Project Conventions

## Stack

| Layer | Tool |
|-------|------|
| Frontend | React 18 + Vite + TypeScript |
| UI Components | shadcn/ui v4 |
| Styling | Tailwind CSS v4 |
| App State | Zustand |
| Server State | TanStack React Query v5 |
| Routing | React Router v6 |
| HTTP Client | Axios |
| Backend | Python 3.13+ + FastAPI |
| Validation | Pydantic v2 (backend), Zod (frontend) |
| Testing | Vitest + Playwright (frontend), pytest + httpx (backend) |
| Packages | pnpm (frontend), uv (backend) |
| Deploy | AWS ECS Fargate + CDK |

This is a **stack-specific** archetype: the stack above is the default. Record any deviation
in `docs/TECH_STACK.md` and, for consequential swaps, an ADR. If you want a stack-neutral
fullstack layout instead, use the `fullstack-app` archetype.

## Module Structure

- `frontend/src/components/ui/` — shadcn/ui primitives; owned code, not a package import; modify freely
- `frontend/src/components/` — feature and layout components; compose from ui primitives
- `frontend/src/pages/` — route-level components; compose from components; no direct API calls
- `frontend/src/hooks/` — custom hooks; data hooks use React Query, UI behavior hooks use local state
- `frontend/src/stores/` — Zustand stores; UI-only state exclusively; never mirror server state here
- `frontend/src/services/` — Axios API client and typed request/response functions
- `backend/api/` — FastAPI route files; thin wrappers only; no business logic or data access
- `backend/core/` — services and domain logic; owns all non-trivial computation and persistence access
- `backend/data/` — JSON persistence files and runtime config
- `backend/prompts/` — prompt templates (populate only if AI features are present)
- `backend/tests/unit/` — pytest unit tests for core logic; no HTTP required
- `backend/tests/api/` — pytest route tests via httpx `TestClient`
- `docs/` — ARCHITECTURE.md, TECH_STACK.md, RULES.md
- `iac/cdk/` — AWS CDK infrastructure (Python)

## Architecture Rules

- Dependency direction: `frontend/src/pages/` → `frontend/src/components/` → `frontend/src/hooks/` → `frontend/src/services/`. Pages do not call services directly.
- The frontend never imports from `backend/`; all data crosses the API boundary over HTTP.
- Route handlers in `backend/api/` call into `backend/core/`. Never the reverse. No DB/ORM access in `backend/api/`.
- React Query owns all server state. Zustand owns UI-only state. No manual sync between them.
- Pydantic models define the API contract. Zod schemas on the frontend mirror them. Both change in the same commit.
- shadcn/ui components under `frontend/src/components/ui/` are owned code — copy in, modify freely, never import as a package dependency.
- AWS CDK stays in `iac/cdk/`; application code never imports CDK and infra never imports `backend/core/`.
- `.env` for local secrets. SSM Parameter Store for production. Nothing committed.

## What the pre-edit governance hook enforces automatically

The shared hook (`check_archetype_governance.py`, active for all assistants once this
archetype is selected) blocks edits that violate:

- ORM / database-driver imports under `backend/api/` (route-handler boundary)
- `backend/` imports inside `frontend/` files (frontend ↔ backend boundary)
- `axios` / React Query / `fetch(` usage inside `frontend/src/stores/` (server state in store)
- `aws_cdk` / `constructs` imports in application code, and `backend/core` imports in `iac/`

The **API contract rule** (Pydantic ↔ Zod) is a cross-file, same-commit invariant. The
single-edit hook cannot see it; it is enforced during review in `at-plan`/`at-implement`.

## API Contract Rule

When a Pydantic response model changes, the corresponding Zod schema changes in the same commit. If `openapi-typescript` or equivalent generation is configured, regenerate and commit the output in the same PR.

## State Management Rule

If the data comes from an API endpoint → React Query.
If it is purely local UI state → Zustand or `useState`.
Never put API response data in a Zustand store.

## Testing

```bash
# Frontend
pnpm test           # Vitest unit tests
pnpm test:e2e       # Playwright E2E

# Backend
uv run pytest                # all tests
uv run pytest tests/unit/    # unit only
uv run pytest tests/api/     # route tests only
```

## Commit Message Format

```
<what changed> (imperative voice, max 72 chars)

Why: <brief rationale>
Spec: <spec items addressed, if applicable>
```
