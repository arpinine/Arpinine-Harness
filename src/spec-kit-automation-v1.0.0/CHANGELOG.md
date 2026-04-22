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
