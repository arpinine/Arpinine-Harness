# AgentAlign Core

AgentAlign is a governed AI workflow plugin with shared core assets and assistant-specific implementations.

It creates an agent-assisted governance layer for product and engineering teams: specialized agents, workflow commands, hooks, and evidence checks that keep AI-assisted product development aligned with shared specifications, architecture rules, evaluations, and runtime observations.

The goal is not to stop fast AI-assisted execution. The goal is to make it safe, repeatable, and team-aligned.

The goal is a repeatable team workflow that keeps product intent, engineering execution, and AI assistance aligned across different coding assistant implementations.

The shared core now also owns the cross-team coordination model:

- shared task ownership and leases under `.specify/coordination/`
- shared claim and release scripts
- shared pre-edit claim enforcement
- shared style-governance hooks and canonical style-config discovery

The directories in this package are implementation-agnostic. Assistant-specific metadata belongs under `src/implementations/<assistant>/` and is overlaid during build time.

## Agent Team

| Capability | Role |
|------------|------|
| Product alignment | `product-owner` keeps business cases, acceptance criteria, and execution aligned with `spec.md` |
| Architecture | `tech-architect` and `architecture-governor` help define modular boundaries and consequential decisions |
| Delivery | `tdd-guide` keeps implementation test-first and task-aligned |
| Security | `security-reviewer` checks implementation risk before completion |
| Evaluation | `evaluation-governor` enforces quality metrics, thresholds, and evidence |
| Harness governance | `harness-governor` keeps product agent runtimes behind explicit boundaries |
| AI design | `ai-engineer` owns model selection, prompting strategy, agent topology, and AI-specific failure modes — scoped to AI/LLM features |
| Prod-readiness | `devops` owns deployment, secrets hygiene, CI/CD, and infrastructure decisions — scoped to deployed services, secrets, or CI/CD |
| Data architecture | `data-engineer` owns data pipelines, RAG design, schema, vector stores, and data quality — scoped to pipeline or RAG features |
| Realignment | `drift-detector`, ADRs, observations, and rules detect when code diverges from intent |

These agents do not replace team ownership. They help the team govern vibe-coded work through explicit artifacts and automated checks.

## Agent Activation Model

Not every agent fires on every spec. AgentAlign uses two activation modes to keep governance proportional to what the feature actually requires.

### Always-On

These agents activate on every spec, regardless of content. They govern concerns that every feature shares.

| Agent | Fires because |
|-------|---------------|
| `product-owner` | Every spec has a business case and acceptance criteria to protect |
| `tech-architect` | Every plan has architectural decisions worth surfacing |
| `architecture-governor` | Every plan needs module boundary and dependency enforcement |
| `tdd-guide` | Every implementation requires test-first discipline |
| `security-reviewer` | Every feature has a security surface |

### Scoped

These agents activate only when the spec signals their domain. Invoking them unconditionally would create noise and irrelevant blockers on features that don't need them.

| Agent | Activates when spec involves |
|-------|------------------------------|
| `harness-governor` | An agent harness or runtime in the product |
| `evaluation-governor` | Agentic or AI-assisted workflows requiring quality gates |
| `ai-engineer` | AI, LLMs, agent runtimes, or prompt-driven behavior |
| `devops` | A deployed service, external API keys, secrets, or CI/CD pipeline |
| `data-engineer` | Data pipelines, RAG, vector stores, ETL, or multi-source ingestion |

The scope condition is evaluated during `/at-plan` by reading the spec and plan content. When a scoped agent activates, it also requires its corresponding section in `plan.md` — `## AI Design Decisions`, `## Deployment Strategy`, or `## Data Pipeline` — ensuring the plan is complete for the feature's domain before implementation begins.

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
| `/agent-align:at-init` | Setup | Initialize the workflow, ADR structure, and rules directory |
| `/agent-align:at-new` | Define | Create a specification from a feature request |
| `/agent-align:at-review` | Refine | Tighten clarity, scope, and measurability |
| `/agent-align:at-plan` | Plan | Generate plan and tasks from the spec |
| `/agent-align:at-adr` | Decide | Create and manage decision records |
| `/agent-align:at-eval` | Evaluate | Define and run framework-agnostic evaluation |
| `/agent-align:at-observe` | Evaluate | Record and review observed runtime behavior |
| `/agent-align:at-implement` | Execute | Implement with TDD and security review |
| `/agent-align:at-audit` | Realign | Detect drift, attribute failures, trigger refinement |
| `/agent-align:at-retro` | Learn | Extract lessons as compounding rules |
| `/agent-align:at-status` | Govern | Project-wide governance overview and onboarding brief |

## Multi-Team Note

The shared core is the source of truth for multi-team behavior. Claude, Codex, and future implementations must all:

- honor shared task claims and leases
- honor shared style-governance rules
- read and write the same governed artifacts rather than keeping assistant-local workflow state

## Team Contract

| Team Role | Responsibility |
|-----------|----------------|
| Product | Owns the problem, user value, scope, business case, and acceptance criteria in `spec.md` |
| Engineering | Owns `plan.md`, task breakdown, and implementation approach |
| Engineering | Owns module boundaries, dependency rules, and testability by boundary |
| Engineering | Owns harness strategy when product features depend on an agent runtime |
| Engineering | Owns evaluation strategy, release thresholds, and runtime evidence expectations for agentic systems |
| Engineering | Owns AI design decisions: model selection, prompting strategy, context management, agent topology, and AI-specific failure modes — when spec uses AI/LLMs |
| Engineering | Owns prod-readiness: deployment pipeline, secrets management, environment configuration, CI/CD, and infrastructure decisions — when spec involves deployed services or secrets |
| Engineering | Owns data architecture: pipeline design, schema and migrations, RAG pipeline, vector store selection, and data quality — when spec involves data pipelines or RAG |
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
| `ai-engineer` | Owns AI/LLM design decisions: model selection, prompting strategy, context management, agent topology, failure modes, and AI-specific evaluation metrics. Scoped: invoked only when spec uses AI, LLMs, or agent runtimes | `evaluation-governor`, `adr-manager` |
| `devops` | Owns prod-readiness: deployment strategy, secrets hygiene, CI/CD, environment configuration, and infrastructure decisions. Scoped: invoked only when spec involves deployed services, external APIs, secrets, or CI/CD | `adr-manager`, `rule-manager` |
| `data-engineer` | Owns data pipeline architecture, RAG pipeline design, schema and migration strategy, vector store selection, and data quality. Scoped: invoked only when spec involves data pipelines, RAG, vector stores, ETL, or multi-source ingestion | `adr-manager`, `rule-manager` |
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
