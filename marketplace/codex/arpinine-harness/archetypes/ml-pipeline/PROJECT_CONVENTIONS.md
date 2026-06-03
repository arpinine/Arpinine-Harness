# Project Conventions

## Module Structure

- `src/pipelines/` — end-to-end pipeline orchestration (data -> features -> model -> output)
- `src/features/` — feature engineering transforms; pure functions where possible
- `src/models/` — model definitions, training logic, serialization
- `src/domain/` — domain entities and business rules; no ML framework imports
- `data/raw/` — immutable raw input; never modified after ingest
- `data/processed/` — pipeline outputs; reproducible from raw + code
- `notebooks/` — exploration only; never imported by production code
- `evals/` — evaluation cases, datasets, and baselines
- `tests/` — unit and integration tests

## Architecture Rules

- `data/raw/` is read-only after ingest. All transforms write to `data/processed/`.
- `notebooks/` may import from `src/`. `src/` must never import from `notebooks/`.
- Feature transforms should stay testable without a full pipeline run.
- Model artifact storage and registry policy should be defined in governed specs and plans.

## Evaluation

- Baseline metrics and pass/fail thresholds belong in `.specify/evals/`.
- Traceability, experiment tracking, and baseline update policy should be selected explicitly by the project.

## Testing

- Feature transforms: unit tests in `tests/`.
- Pipeline stages: integration tests with small fixture datasets.
- Model quality: evaluation runs in `evals/`, with framework choice defined separately from this scaffold.
