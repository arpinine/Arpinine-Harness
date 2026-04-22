# Changelog

## [1.0.0] - 2026-04-22

### Added
- `/spec-adr` command: create, list, show, and update Architecture Decision Records
- `/spec-audit` command: detect spec-code drift and drive ADR resolution
- `adr-manager` skill: auto-numbering, ADR-INDEX.md, lifecycle management, spec linking
- `drift-detector` skill: file existence, API, and data model comparison with drift→ADR pipeline
- `constitution-enforcer` skill: ADR-linkage and drift-coverage rules extending spec-kit
- `security-reviewer` agent: blocks CRITICAL security violations before merge
- `tdd-guide` agent: enforces test-first development during spec-implement
- `tech-architect` agent: suggests ADR creation for each architectural decision in plan.md
- PreToolUse hook: constitution check on every file write
- PostToolUse hook: quick drift check after every file write
- Templates: spec, plan, ADR, constitution with linking conventions

## [1.0.1] - 2026-04-22

### Fixed
- PreToolUse constitution check now validates pending edit content instead of only the on-disk file
- PostToolUse quick drift check now scopes analysis to the edited spec or specs that reference the edited file
- ADR coverage model now requires explicit `covers:` linkage for drift items and planned decisions
- Slash command prompts now define concrete agent and review workflows instead of one-line delegations

## [1.1.0] - 2026-04-22

### Added
- `/spec-eval` command for framework-agnostic evaluation planning, execution, and review
- `templates/eval-plan-template.md` for metrics, thresholds, datasets, and execution commands
- `examples/example-eval-plan.md` showing a DeepEval-backed plan without hard-coding the plugin to one framework
- `evaluation-governor` skill to enforce evaluation contracts for agentic systems

### Changed
- Planning now requires evaluation strategy for agentic work
- Implementation now blocks completion on failing required evaluation
- Audit now considers evaluation regressions and missing reruns
- PostToolUse quick drift hook now surfaces lightweight spec drift hints for endpoints and stale eval results

## [1.2.0] - 2026-04-22

### Added
- `architecture-governor` skill to enforce modular and clean architecture expectations
- plan template sections for module boundaries, dependency rules, and testability by boundary

### Changed
- Constitution now requires modular boundaries and isolation of business rules from framework concerns
- Planning now requires explicit architecture sections before implementation
- Implementation guidance now blocks completion when planned boundaries are broken without refinement
- PreToolUse now blocks implementation-path edits until architecture sections exist in the governing plan
