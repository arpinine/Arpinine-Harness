# AgentAlign Plugin

AgentAlign is a Claude plugin for governed vibe coding.

It creates an agent-assisted governance layer for product and engineering teams: specialized agents, workflow commands, hooks, and evidence checks that keep AI-assisted product development aligned with shared specifications, architecture rules, evaluations, and runtime observations.

The goal is not to stop fast AI-assisted execution. The goal is to make it safe, repeatable, and team-aligned.

The goal is a repeatable team workflow that keeps product intent, engineering execution, and AI assistance aligned.

## Agent Team

| Capability | Role |
|------------|------|
| Product alignment | `product-owner` keeps business cases, acceptance criteria, and execution aligned with `spec.md` |
| Architecture | `tech-architect` and `architecture-governor` help define modular boundaries and consequential decisions |
| Delivery | `tdd-guide` keeps implementation test-first and task-aligned |
| Security | `security-reviewer` checks implementation risk before completion |
| Evaluation | `evaluation-governor` enforces quality metrics, thresholds, and evidence |
| Harness governance | `harness-governor` keeps product agent runtimes behind explicit boundaries |
| Realignment | `drift-detector`, ADRs, observations, and rules detect when code diverges from intent |

These agents do not replace team ownership. They help the team govern vibe-coded work through explicit artifacts and automated checks.

## Workflow

| Stage | Output |
|-------|--------|
| Define | `spec.md` |
| Refine | reviewed and clarified spec |
| Plan | `plan.md` and tasks |
| Architect | module boundaries, dependency rules, harness strategy, ADRs |
| Decide | ADRs for consequential choices |
| Evaluate | eval plan and results |
| Execute | tested implementation |
| Realign | drift findings, spec updates, ADR updates |
| Learn | retro lessons persisted as rules in `.specify/rules/` |

## Commands

| Command | Stage | Purpose |
|---------|-------|---------|
| `/at-init` | Setup | Initialize the workflow, ADR structure, and rules directory |
| `/at-new` | Define | Create a specification from a feature request |
| `/at-review` | Refine | Tighten clarity, scope, and measurability |
| `/at-plan` | Plan | Generate plan and tasks from the spec |
| `/at-adr` | Decide | Create and manage decision records |
| `/at-eval` | Evaluate | Define and run framework-agnostic evaluation |
| `/at-observe` | Evaluate | Record and review observed runtime behavior |
| `/at-implement` | Execute | Implement with TDD and security review |
| `/at-audit` | Realign | Detect drift, attribute failures, trigger refinement |
| `/at-retro` | Learn | Extract lessons as compounding rules |
| `/at-status` | Govern | Project-wide governance overview and onboarding brief |

## Team Contract

| Team Role | Responsibility |
|-----------|----------------|
| Product | Owns the problem, user value, scope, business case, and acceptance criteria in `spec.md` |
| Engineering | Owns `plan.md`, task breakdown, and implementation approach |
| Engineering | Owns module boundaries, dependency rules, and testability by boundary |
| Engineering | Owns harness strategy when product features depend on an agent runtime |
| Engineering | Owns evaluation strategy, release thresholds, and runtime evidence expectations for agentic systems |
| Tech Leads | Own consequential decisions and approve ADRs when needed |
| AI Agents | Help execute within the rules set by the spec, plan, ADRs, eval plan, and observation evidence |

Human ownership stays with the team. AgentAlign agents act as governed specialists inside that contract.

## Agent Responsibilities

| Agent | Responsibility In The Governed Codebase | Primary Skills Used |
|-------|------------------------------------------|---------------------|
| `product-owner` | Keeps the business case, scope, and acceptance criteria aligned from `spec.md` through planning, implementation, evaluation, and audit | `constitution-enforcer`, `evaluation-governor`, `drift-detector` |
| `tech-architect` | Protects modular design, identifies consequential decisions, and pushes architecture changes into ADRs before they become accidental code structure | `architecture-governor`, `adr-manager` |
| `tdd-guide` | Keeps implementation task-aligned and test-first so code changes stay traceable to planned work and verifiable by tests | `constitution-enforcer` |
| `security-reviewer` | Reviews plans and implementation for security-sensitive gaps and blocks completion when risky behavior is undocumented or unsafe | `constitution-enforcer`, `rule-manager` |
| Governance skills | Provide the codebase-wide enforcement layer for architecture, harness boundaries, evaluation, drift detection, ADR discipline, and compounding rules | `architecture-governor`, `harness-governor`, `evaluation-governor`, `drift-detector`, `adr-manager`, `rule-manager` |

## Alignment Rules

- `spec.md` is for product intent, not implementation detail
- `plan.md` is for engineering detail and execution order
- clean architecture and modularity are enforced through plan boundaries, dependency rules, and ADRs
- harness-based product features must define harness choice, abstraction boundary, tool model, memory model, and permission model
- eval plans are for quality gates, metrics, thresholds, and results
- observations capture actual runtime behavior for later drift analysis
- ADRs capture the why behind major choices
- hooks provide lightweight drift hints after edits
- implementation edits are blocked until required architecture sections exist
- drift findings are attributed as precondition failures (spec unclear) or postcondition failures (deviated from clear spec)
- rules compound — each retro lesson becomes a permanent constraint that fires on future specs
- refinement is continuous and happens before and after implementation

## Artifact Storage

```text
.specify/
  specs/
    001-<slug>/
      spec.md
      plan.md
      eval-plan.md
      latest-results.md
  observations/
    001-<slug>/
      latest-observation.md
      trace.json
  adr/
    ADR-INDEX.md
    ADR-0001-<title>.md
  evals/
  rules/
    security/
      auth-001.md
    architecture/
      arch-001.md
```

Each ADR links to:
- its governing spec via `governs:`
- a specific decision or drift item via `covers:`

Observation artifacts can be used to compare:
- documented harness strategy vs actual tool use
- documented permission model vs actual approval events
- documented memory model vs actual state behavior
- evaluation plan vs observed runtime paths

Each rule documents:
- what pattern triggers it (`triggers:`)
- what failure it prevents (`prevents:`)
- which retro or ADR it was sourced from (`source-adr:`, `evidence-project:`)

## Recommended AgentAlign + OpenHarness Architecture

When a team chooses OpenHarness as the harness implementation, the recommended structure is:

```text
product feature / application service
        |
        v
internal runtime interface
        |
        v
OpenHarness adapter
        |
        v
OpenHarness agent, tools, permissions, sessions
```

Recommended rules:
- product code depends on an internal runtime interface, not directly on `@openharness/*`
- OpenHarness code lives in the adapter or infrastructure layer
- tool registration is explicit and narrow
- approval callbacks are documented for any sensitive action
- session and state handling are defined up front
- evaluation covers task quality plus harness-specific failure modes

This keeps the broader AgentAlign workflow generic while giving teams a concrete implementation pattern for OpenHarness.

## Dependency Model

AgentAlign does not install external dependencies during plugin installation.
Instead, it validates them during setup and before relevant workflow stages.

Recommended interpretation:
- `spec-kit` is required for automated spec generation and planning flows
- harness runtimes are required only for features whose `## Harness Strategy` explicitly selects one
- eval tools are required only when selected in `eval-plan.md`

In practice:
- if `## Harness Strategy` is `N/A`, the project does not need a harness runtime
- if `## Harness Strategy` selects a runtime such as OpenHarness or an internal agent runtime, that runtime becomes a required dependency for that feature

Use `scripts/check-dependencies.sh` to validate local readiness and report missing tools explicitly.

## Script-Backed Governance

AgentAlign is stronger when commands can start from executable checks instead of prompt text alone.

Available helpers:
- `scripts/check-dependencies.sh --json` for machine-readable environment readiness
- `scripts/spec_status.py [--spec <slug>] [--onboard]` for a project governance report
- `scripts/quick_drift_check.py --spec .specify/specs/<slug>/spec.md` for lightweight drift and static conformance hints

The post-write drift hook already uses `quick_drift_check.py`, so endpoint mismatches, stale eval runs, harness import leakage, and framework leakage into domain layers surface immediately after edits.
It also uses declared `## Module Boundaries` from `plan.md` to flag imports that violate planned dependency direction.
