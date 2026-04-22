# AgentAlign Plugin

AgentAlign gives teams a common way of working across specification, refinement, planning, architecture governance, evaluation, execution, and realignment.

It builds on spec-kit, but the primary goal is not just artifact generation. The goal is a repeatable team workflow that keeps product intent, engineering execution, and AI assistance aligned.

## Workflow

| Stage | Output |
|-------|--------|
| Define | `spec.md` |
| Refine | reviewed and clarified spec |
| Plan | `plan.md` and tasks |
| Architect | module boundaries, dependency rules, ADRs |
| Decide | ADRs for consequential choices |
| Evaluate | eval plan and results |
| Execute | tested implementation |
| Realign | drift findings, spec updates, ADR updates |

## Commands

| Command | Stage | Purpose |
|---------|-------|---------|
| `/spec-init` | Setup | Initialize the workflow and ADR structure |
| `/spec-new` | Define | Create a specification from a feature request |
| `/spec-review` | Refine | Tighten clarity, scope, and measurability |
| `/spec-plan` | Plan | Generate plan and tasks from the spec |
| `/spec-adr` | Decide | Create and manage decision records |
| `/spec-eval` | Evaluate | Define and run framework-agnostic evaluation |
| `/spec-implement` | Execute | Implement with TDD and security review |
| `/spec-audit` | Realign | Detect drift and trigger refinement |

## Team Responsibilities

- Product owns intent, value, scope, and acceptance criteria in `spec.md`
- Engineering owns the delivery approach in `plan.md`
- Engineering must define modular boundaries and dependency rules before implementation
- Engineering also owns the evaluation strategy for agentic systems
- ADRs record decisions that materially shape implementation
- Audit identifies when the spec, decisions, and code no longer match

## Alignment Rules

- `spec.md` is for product intent, not implementation detail
- `plan.md` is for engineering detail and execution order
- clean architecture and modularity are enforced through plan boundaries, dependency rules, and ADRs
- eval plans are for quality gates, metrics, thresholds, and results
- ADRs capture the why behind major choices
- hooks provide lightweight drift hints after edits
- implementation edits are blocked until required architecture sections exist
- refinement is continuous and happens before and after implementation

## ADR Storage

```text
.specify/
  adr/
    ADR-INDEX.md
    ADR-0001-<title>.md
```

Each ADR links to:
- its governing spec via `governs:`
- a specific decision or drift item via `covers:`
