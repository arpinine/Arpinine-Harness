# Arpinine Harness Core

This package contains the shared workflow assets that power Arpinine Harness across all assistant implementations.

Commands, agents, hooks, scripts, skills, and templates all live here. Assistant-specific metadata (manifests, registration files, implementation-specific skill wrappers) lives under `src/implementations/<assistant>/` and gets overlaid during the build step. Nothing in this package assumes Claude, Codex, or any specific assistant — the workflow is the abstraction.

Specification generation and planning also go through an adapter layer. Arpinine Harness keeps `.specify/` as the canonical artifact contract, while `.specify/specification-provider.json` selects the backend that generates or updates `spec.md` and `plan.md`.

The shared core also owns the cross-team coordination model. When multiple assistants run against the same repo, they all rely on:

- shared task ownership and leases under `.specify/coordination/`
- shared claim and release scripts
- shared pre-edit claim enforcement
- shared style-governance hooks and canonical style-config discovery

## Platform Requirements

- **Python 3.10+** is required for all governance scripts.
- **Unix/macOS**: fully supported. Task coordination uses `fcntl` file locking.
- **Windows**: not currently supported. Task coordination requires Unix file locking (`fcntl`). A future version will migrate to the cross-platform `filelock` package.

## Agent Team

| Capability | Role |
|------------|------|
| Product alignment | `product-owner` keeps business cases, acceptance criteria, and execution aligned with `spec.md` |
| Architecture | `tech-architect` and `architecture-governor` define modular boundaries and surface consequential decisions |
| Domain language | `domain-linguist` and `vocabulary-guardian` keep bounded-context vocabulary consistent from spec through code |
| Delivery | `tdd-guide` keeps implementation test-first and task-aligned |
| Security | `security-reviewer` checks implementation risk before completion |
| Evaluation | `evaluation-governor` enforces quality metrics, thresholds, and evidence |
| Harness governance | `harness-governor` keeps product agent runtimes behind explicit boundaries |
| AI design | `ai-engineer` owns model selection, prompting strategy, agent topology, and AI-specific failure modes — scoped to AI/LLM features |
| Prod-readiness | `devops` owns deployment, secrets hygiene, CI/CD, and infrastructure — scoped to deployed services, secrets, or CI/CD |
| Data architecture | `data-engineer` owns data pipelines, RAG design, schema, vector stores, and data quality — scoped to pipeline or RAG features |
| Realignment | `drift-detector`, ADRs, observations, and rules catch when code diverges from intent |

These agents don't replace your team. They help you govern AI-assisted work through explicit artifacts and automated checks.

## Agent Activation Model

Not every specialist shows up for every feature — that would be noise. Security review matters on every spec. But you don't need a data engineer reviewing a settings page.

Arpinine Harness splits the team into two groups.

### Always-On

These agents activate on every spec, no matter what. They cover concerns that every feature shares.

| Agent | Why it always fires |
|-------|---------------------|
| `product-owner` | Every spec has a business case and acceptance criteria worth protecting |
| `tech-architect` | Every plan has architectural decisions worth surfacing |
| `architecture-governor` | Every plan needs module boundary and dependency enforcement |
| `domain-linguist` | Every plan needs bounded-context vocabulary enforced before generic technical naming hardens into structure |
| `tdd-guide` | Every implementation needs test-first discipline |
| `security-reviewer` | Every feature has a security surface |

### Scoped

These agents activate only when the spec signals their domain. They stay quiet otherwise.

| Agent | Activates when spec involves |
|-------|------------------------------|
| `harness-governor` | An agent harness or runtime in the product |
| `evaluation-governor` | Agentic or AI-assisted workflows needing quality gates |
| `ai-engineer` | AI, LLMs, agent runtimes, or prompt-driven behavior |
| `devops` | A deployed service, external API keys, secrets, or CI/CD pipeline |
| `data-engineer` | Data pipelines, RAG, vector stores, ETL, or multi-source ingestion |

Scope is evaluated during `/at-plan` by reading what the spec and plan actually describe. When a scoped agent activates, it also requires a corresponding section in `plan.md` — `## Observability Strategy`, `## AI Design Decisions`, `## Deployment Strategy`, or `## Data Pipeline` as applicable — so the plan is complete for that domain before implementation starts.

## Domain Vocabulary

Arpinine Harness now treats bounded-context language as an architectural constraint, not a style preference.

- `spec.md` defines `## Domain Vocabulary`: canonical terms, definitions, forbidden synonyms, and disambiguation notes
- `/arpinine-harness:at-plan` maps those terms into `## Vocabulary Decisions` in `plan.md`
- `domain-linguist` reviews module, class, and interface naming for vocabulary drift and semantic conflation
- `vocabulary-guardian` and `scripts/check_vocabulary_drift.py` enforce the declared vocabulary during planning and implementation

This is meant to stop the common failure mode where good product language in the spec degrades into `Manager`, `Handler`, `Processor`, or other generic abstractions once coding starts.

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
| `/arpinine-harness:at-init` | Setup | Initialize the workflow, ADR structure, and rules directory, and optionally scaffold a new project archetype |
| `/arpinine-harness:at-discover` | Discover | Refine a raw idea into a spec-ready brief through a one-question-at-a-time product-owner conversation |
| `/arpinine-harness:at-new` | Define | Create a specification from a feature request |
| `/arpinine-harness:at-bootstrap-from-code` | Define | Assess an existing repo and seed governed artifacts from implementation evidence |
| `/arpinine-harness:at-review` | Refine | Tighten clarity, scope, and measurability |
| `/arpinine-harness:at-plan` | Plan | Generate plan and tasks from the spec |
| `/arpinine-harness:at-adr` | Decide | Create and manage decision records |
| `/arpinine-harness:at-eval` | Evaluate | Define and run framework-agnostic evaluation |
| `/arpinine-harness:at-observe` | Evaluate | Record and review runtime observations |
| `/arpinine-harness:at-implement` | Execute | Implement with TDD and security review |
| `/arpinine-harness:at-audit` | Realign | Detect drift, attribute failures, trigger refinement |
| `/arpinine-harness:at-retro` | Learn | Extract lessons as compounding rules |
| `/arpinine-harness:at-status` | Govern | Project-wide governance overview and onboarding brief |
| `/arpinine-harness:at-ask` | Any stage | Ask a focused question to a named specialist agent with spec and plan as context |

## Pre-Spec Discovery

Use `/arpinine-harness:at-discover` when the user has an idea but not yet a specification-quality request.

- routes the conversation through `product-owner`
- asks exactly one question at a time
- keeps the conversation product-facing instead of implementation-led
- stops once the idea is sufficiently bounded and measurable
- waits for explicit user confirmation to move forward
- then hands off to `/arpinine-harness:at-new` with a spec-ready brief

## Multi-Team Note

The shared core is the source of truth for multi-team behavior. Claude, Codex, and any future implementation must all:

- honor shared task claims and leases
- follow shared style-governance rules
- read and write the same governed artifacts — no assistant-local workflow state

## Archetype Scaffolding

`/arpinine-harness:at-init` can scaffold a new project before the normal governance setup runs.

Current shared archetypes:

- `agent-app` — starter structure for agent-oriented applications with `src/agents`, `src/tools`, `src/domain`, `evals`, and `tests`
- `ml-pipeline` — starter structure for ML/data applications with `src/pipelines`, `src/features`, `src/models`, `data/`, `notebooks`, `evals`, and `tests`

The archetype contract is intentionally narrow:

- shared core defines structure and neutral conventions only
- generated `PROJECT_CONVENTIONS.md` documents starter boundaries without binding the repo to a specific assistant
- dependency installation, framework selection, and runtime-specific policy remain governed decisions for later `spec.md` and `plan.md` artifacts

When an archetype is selected, the shared core also records `.specify/archetype.json`, appends an archetype addendum to the generated constitution, writes starter rules under `.specify/rules/archetype/`, and enables shared pre-edit enforcement through the common hook layer used by both Claude and Codex.

The scaffold entrypoint is `scripts/scaffold_archetype.py`:

```bash
python3 scripts/scaffold_archetype.py --list
python3 scripts/scaffold_archetype.py agent-app --target-dir . --skip-if-nonempty
python3 scripts/scaffold_archetype.py ml-pipeline --target-dir . --force
```

## Team Contract

| Role | Owns |
|------|------|
| Product | The problem, user value, scope, business case, and acceptance criteria in `spec.md` |
| Engineering | `plan.md`, task breakdown, and implementation approach |
| Engineering | Bounded-context vocabulary in `spec.md` and `## Vocabulary Decisions` in `plan.md` |
| Engineering | Module boundaries, dependency rules, and testability by boundary |
| Engineering | Harness strategy when product features depend on an agent runtime |
| Engineering | Evaluation strategy, release thresholds, and runtime evidence expectations for agentic systems |
| Engineering | AI design decisions — model selection, prompting strategy, context management, agent topology, failure modes — when spec uses AI/LLMs |
| Engineering | Prod-readiness — deployment pipeline, secrets management, env config, CI/CD, infrastructure — when spec involves deployed services or secrets |
| Engineering | Data architecture — pipeline design, schema and migrations, RAG pipeline, vector store selection, data quality — when spec involves data pipelines or RAG |
| Tech Leads | Consequential decisions; ADR approval when needed |
| AI Agents | Execution within the rules set by the spec, plan, ADRs, eval plan, and observation evidence |

The agents don't own anything on this list. Your team does.

## Agent Responsibilities

| Agent | What it does | Primary skills |
|-------|-------------|----------------|
| `product-owner` | Keeps business case, scope, and acceptance criteria aligned through planning, implementation, evaluation, and audit | `constitution-enforcer`, `evaluation-governor`, `drift-detector` |
| `tech-architect` | Catches architecture decisions early and pushes them into ADRs before they become accidental code structure | `architecture-governor`, `adr-manager` |
| `domain-linguist` | Enforces domain language as architecture by checking declared vocabulary against plan and implementation naming decisions | `vocabulary-guardian`, `drift-detector` |
| `tdd-guide` | Keeps implementation task-aligned and test-first so changes stay traceable and verifiable | `constitution-enforcer` |
| `security-reviewer` | Reviews plans and code for security gaps; blocks completion when risky behavior is undocumented or unsafe | `constitution-enforcer`, `rule-manager` |
| `ai-engineer` | Owns LLM design: model selection, prompting strategy, context management, agent topology, failure modes, and AI-specific eval metrics. Fires only on AI/LLM features | `evaluation-governor`, `adr-manager` |
| `devops` | Owns prod-readiness: deployment, secrets hygiene, CI/CD, env config, infrastructure. Fires only when spec involves deployed services, secrets, or CI/CD | `adr-manager`, `rule-manager` |
| `data-engineer` | Owns data architecture: pipelines, RAG design, schema and migrations, vector store selection, data quality. Fires only on pipeline or RAG features | `adr-manager`, `rule-manager` |
| Governance skills | Codebase-wide enforcement: architecture, harness boundaries, evaluation, drift detection, ADR discipline, compounding rules | `architecture-governor`, `harness-governor`, `evaluation-governor`, `drift-detector`, `adr-manager`, `rule-manager` |

## Alignment Rules

- `spec.md` is for product intent, not implementation detail
- `## Domain Vocabulary` in `spec.md` is a first-class architectural input, not optional prose
- `plan.md` is for engineering detail and execution order
- `## Vocabulary Decisions` in `plan.md` maps domain terms to concrete modules, classes, and interfaces
- architecture and modularity are enforced through plan boundaries, dependency rules, and ADRs
- harness-based features must define harness choice, abstraction boundary, tool model, memory model, and permission model
- eval plans define quality gates, metrics, thresholds, and results
- observations capture actual runtime behavior for later drift analysis
- ADRs capture the why behind major choices
- hooks provide lightweight drift hints after edits
- implementation edits are blocked until required architecture sections exist
- drift findings are attributed as precondition failures (spec was unclear) or postcondition failures (deviated from a clear spec)
- rules compound — each retro lesson becomes a permanent constraint that fires on future specs
- refinement is continuous, not a one-time step at the start

## Artifact Storage

```text
.specify/
  specification-provider.json
  discovery/
    <slug>/
      discovery.md
  specs/
    001-<slug>/
      spec.md
      plan.md
  observations/
    001-<slug>/
      latest-observation.md
      trace.json
      index.jsonl
      history/
        <run-id>.json
        <run-id>.md
  adr/
    ADR-INDEX.md
    ADR-0001-<title>.md
  evals/
    001-<slug>/
      eval-plan.md
      latest-results.md
      dataset-manifest.json
      baseline.json
      history/
        <run-id>-results.json
        <run-id>-results.md
  rules/
    security/
      auth-001.md
    architecture/
      arch-001.md
```

Each ADR links to its governing spec via `governs:` and to a concrete decision or drift key via `covers:`.

Discovery artifacts preserve pre-spec idea refinement, one-question-at-a-time Q&A history, the latest spec-ready brief, and promotion state before `spec.md` exists.

Observation artifacts let you compare documented harness strategy against actual tool use, documented permission model against actual approval events, and documented memory model against actual state behavior.

When benchmarked evaluation is enabled, observation and eval history support aggregate metrics such as latency P50/P95, token/cost summaries, and regression comparison against an approved baseline.

Each rule documents what pattern triggers it (`triggers:`), what failure it prevents (`prevents:`), and which retro or ADR it came from (`source-adr:`, `evidence-project:`).

## Recommended Arpinine Harness + OpenHarness Architecture

When a team uses OpenHarness as the harness implementation, the recommended structure is:

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

Key rules:
- product code depends on an internal runtime interface, not directly on `@openharness/*`
- OpenHarness code lives in the adapter or infrastructure layer
- tool registration is explicit and narrow
- approval callbacks are documented for any sensitive action
- session and state handling are defined up front
- evaluation covers task quality plus harness-specific failure modes

## Dependency Model

Arpinine Harness doesn't install external dependencies during plugin installation. It validates them during setup and before the relevant workflow stage:

- the configured specification provider is required only for automated spec generation and planning
- harness runtimes are required only when `## Harness Strategy` explicitly selects one
- eval tools are required only when `eval-plan.md` selects them

If `## Harness Strategy` is `N/A`, no harness runtime is needed. Use `scripts/check-dependencies.sh` to check local readiness.

## Observation And Evaluation Scaffolding

For AI, LLM, or agent-runtime features, `/arpinine-harness:at-plan` writes `## Observability Strategy` into `plan.md` and hands implementation off to a scaffolder instead of relying on manual provider setup.

Implementation path:

- `/arpinine-harness:at-plan` decides whether observation and evaluation are required
- `python3 scripts/scaffold_observability_setup.py --spec <slug>` creates missing provider abstractions, default Langfuse/DeepEval implementations when the plan selects them, `noop` providers, and `.env.example` entries
- `scripts/check-observability-setup.sh --spec <slug>` verifies that provider files exist and SDK imports stay inside the designated provider modules before implementation continues

The scaffolder is idempotent. Existing files are preserved and reported as skipped rather than overwritten.

## Script-Backed Governance

Commands are stronger when they start from executable checks rather than prompt text alone.

Available helpers:
- `scripts/check-dependencies.sh --json` — machine-readable environment readiness
- `scripts/bootstrap_from_code.py --json --write-artifacts [--git-log]` — existing-codebase assessment with docs, tests, monorepo, and optional git-history intent signals
- `scripts/check_vocabulary_drift.py --spec <slug> [--json|--all]` — enforce declared domain vocabulary against plan module names and code identifiers
- `scripts/scaffold_observability_setup.py --spec <slug>` — scaffold observation/evaluation provider layers from `## Observability Strategy`
- `scripts/spec_status.py [--spec <slug>] [--onboard]` — project governance report
- `scripts/quick_drift_check.py --spec .specify/specs/<slug>/spec.md` — lightweight drift and static conformance hints
- `scripts/run_benchmark.py --slug <slug>` — execute required benchmark scenarios from `dataset-manifest.json` and emit the governed aggregate result

The post-write drift hook runs `quick_drift_check.py` automatically, so endpoint mismatches, stale eval runs, harness import leakage, and framework leakage into domain layers surface right after edits. `/arpinine-harness:at-implement` adds an explicit vocabulary gate by running `check_vocabulary_drift.py` before completion.

For benchmarked evaluation, `run_benchmark.py` runs the declared benchmark command once per required dataset scenario and passes scenario context through `ARPININE_HARNESS_*` environment variables. The benchmark tool remains product-specific; Arpinine Harness governs the artifact contract and aggregates the results.
Benchmark history is partitioned by session under `.specify/evals/<slug>/history/<session-id>/` and `.specify/observations/<slug>/history/<session-id>/`. Aggregate reporting defaults to the latest recorded benchmark session.
