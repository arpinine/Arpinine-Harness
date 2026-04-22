# Changelog

## [Unreleased]

### Added
- `harness-governor` skill to enforce harness strategy for product-facing agent systems
- `## Harness Strategy` section in the plan template for harness choice, abstraction boundary, tool access, memory, permissions, and swap strategy

### Changed
- planning and implementation guidance now enforce harness design documentation before building product features on top of an agent runtime

## [1.4.0] - 2026-04-22

### Added
- `rule-manager` skill to manage compounding machine-readable rules in `.specify/rules/`
- `rules/<category>/<rule-id>.md` format with frontmatter: `triggers`, `prevents`, `source-adr`, `evidence-project`, `severity`, `active`
- `/spec-retro` command to extract lessons from completed work and persist them as rules
- `/spec-status` command for project-wide governance overview and new team member onboarding (`--onboard` flag)
- `rules/` directory initialized by `/spec-init`
- Example rules: `examples/rules/security/auth-001.md`, `examples/rules/architecture/arch-001.md`
- Machine-readable schemas: `templates/schemas/spec-schema.yaml`, `templates/schemas/adr-schema.yaml`
- AIN (AI-Nativeness) assessment section in `spec-template.md` with AIN target level, agent-callable operations, human-in-the-loop gates, and feedback channels

### Changed
- `/spec-audit` now attributes each drift finding as PRECONDITION FAILURE (spec unclear) or POSTCONDITION FAILURE (implementation deviated from clear spec) before triggering ADR creation
- `/spec-audit` now checks active rules via `rule-manager` before creating ADRs — known patterns reported as rule violations instead
- `drift-detector` skill now invokes `rule-manager` before ADR coverage check
- `spec-audit` summary now includes attribution counts and rule violation count

## [1.3.0] - 2026-04-22

### Changed
- renamed project identity to `AgentAlign`
- renamed plugin/package to `agent-align`
- renamed source directory from `src/spec-kit-automation-v1.0.0` to `src/agent-align-v1.0.0`
- updated build and installation paths to produce `dist/agent-align-v1.2.0.zip`

## [1.2.0] - 2026-04-22

### Added
- `architecture-governor` skill to enforce modular and clean architecture expectations during planning and implementation
- architecture-ready planning sections:
  - `## Module Boundaries`
  - `## Dependency Rules`
  - `## Testability By Boundary`
- `check-architecture-readiness.sh` pre-write gate to block implementation-path edits until architecture requirements exist in the governing plan

### Changed
- the workflow now treats architecture as a first-class concern alongside planning, evaluation, execution, and realignment
- constitution rules now require modular boundaries and isolation of business rules from framework and infrastructure concerns
- planning now requires explicit architecture sections before implementation can begin
- implementation guidance now sends work back into refinement when planned boundaries are broken without rationale
- `PreToolUse` now blocks implementation-path edits until architecture sections exist in the governing plan

## [1.1.0] - 2026-04-22

### Added
- `/spec-eval` command for framework-agnostic evaluation planning, execution, and review
- `evaluation-governor` skill to enforce evaluation contracts for agentic systems
- `templates/eval-plan-template.md` for metrics, thresholds, datasets, execution commands, and pass/fail policy
- `examples/example-eval-plan.md` showing a DeepEval-backed example without coupling the plugin to a single framework

### Changed
- the delivery workflow now includes an explicit evaluation stage
- planning now requires an evaluation strategy for agentic or AI-assisted work
- implementation now blocks completion on failing required evaluation
- audit now considers evaluation regressions and missing reruns
- plugin metadata and documentation now position evaluation as framework-agnostic rather than vendor-specific

## [1.0.1] - 2026-04-22

### Fixed
- `check-constitution.sh` now validates pending edit content from hook input instead of only inspecting the on-disk file
- ADR coverage model now requires explicit `covers:` linkage for drift items and planned decisions
- slash command prompts now define concrete workflows instead of one-line delegations

### Changed
- `quick-drift-check.sh` was upgraded from a latest-spec file-reference check to a lightweight spec-alignment hook
- `PostToolUse` now surfaces:
  - missing file references from specs
  - endpoint mismatch hints between spec and code
  - stale or missing eval result hints for agentic specs

## [1.0.0] - 2026-04-22

### Added
- initial plugin scaffold for a spec-driven team workflow on top of spec-kit
- commands:
  - `/spec-init`
  - `/spec-new`
  - `/spec-plan`
  - `/spec-implement`
  - `/spec-adr`
  - `/spec-audit`
  - `/spec-review`
- agent roles:
  - `tech-architect`
  - `tdd-guide`
  - `security-reviewer`
- skills:
  - `adr-manager`
  - `drift-detector`
  - `constitution-enforcer`
  - `reverse-diff-audit`
- templates for:
  - spec
  - plan
  - ADR
  - constitution
- hook wiring for pre-write constitution validation and post-write drift checks
- ADR lifecycle management with `governs:` linkage and index maintenance
