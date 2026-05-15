# Arpinine Harness

Arpinine Harness is a plugin for anyone building software with AI coding assistants and who wants to ship real software, not just ship code.

When you build with AI coding assistants, things move fast. Too fast to track whether what you're building still matches what you intended. Specs drift. Architecture decisions get made by accident. Secrets end up hardcoded. There's no deployment plan. The code works locally and nowhere else.

Arpinine Harness gives you a team to work with, not a prompt bundle. Specialized agents each own a slice of the work: product intent, architecture, tests, security, deployment, and evaluation. They show up at the right moments and block the wrong ones.

The goal isn't to slow you down. It's to make sure that what you ship is what you meant to build.

This workflow aligns with the Two-Axis Framework in [docs/two_axis_framework.pdf](docs/two_axis_framework.pdf).
Arpinine Harness mainly operationalizes the AI engineering process maturity axis: a governed way to build AI-assisted software, regardless of how AI-native the product itself is.

## One Plugin, Team Of Agents

When you run a command, you're not talking to one assistant. You're talking to a team.

Each command routes to the specialists that matter for that stage of work:

- a `product-owner` that keeps your spec honest — scope, intent, and acceptance criteria
- a `tech-architect` that catches architecture decisions before they become accidental code structure
- a `domain-linguist` that protects bounded-context vocabulary so domain language survives contact with implementation
- a `tdd-guide` that keeps implementation test-first and task-aligned
- a `security-reviewer` that challenges anything risky or underspecified
- an `ai-engineer` that owns your model choices, prompting strategy, and AI-specific failure modes — active when your feature uses AI or LLMs
- a `devops` that closes the prod-readiness gap: deployment, secrets, CI/CD, infrastructure — active when your feature involves a deployed service or secrets
- a `data-engineer` that owns your data pipelines, RAG design, schema, and vector stores — active when your feature involves pipelines or RAG
- an `evaluation-governor` that pushes for measurable quality gates before you call something done
- a `drift-detector` that checks whether your code, plans, ADRs, and runtime evidence still agree

One command. Many responsibilities. No one agent carrying the whole load.

## Multi-Team Operating Model

Arpinine Harness also supports multiple AI coding assistants working on the same repo at the same time.

A typical setup:

- one delivery lane runs in Claude
- one delivery lane runs in Codex
- both use the same `spec.md`, `plan.md`, ADRs, eval artifacts, and delivery matrix
- task ownership is coordinated through shared claims so they don't step on each other

So there are two layers: specialist roles inside one session, and multiple assistant teams coordinated through one shared workflow.

## How To Work With Arpinine Harness

Arpinine Harness is not just a command set. It is a working team of specialist agents operating inside a governed delivery methodology.

Your responsibility:

- describe the product, problem, or intent
- answer clarification questions
- review generated outputs
- approve promotions, scope changes, and major decisions

The plugin's responsibility:

- create and refine the spec
- generate the implementation plan
- surface ADRs when decisions matter
- implement under the governed workflow
- run evaluation, audit drift, and enforce the methodology

You are the decision-maker and reviewer.
The plugin is the delivery team.

## Start Here

If you want to use Arpinine Harness rather than just read its files, start here:

- [Vibe Coder Process](docs/vibe-coder-process.md)

That guide covers the day-to-day operating model for anyone using Arpinine Harness with an AI coding assistant.

## Getting Started By Situation

Arpinine Harness works best as a workflow, not as a bag of unrelated commands.

In normal use, you do not manually author the core delivery artifacts. The agent team creates and updates them. You guide the process by giving intent, answering questions, reviewing results, and approving important transitions.

If you're new, do not start by memorizing every command. Start by identifying your situation:

- you have only a rough idea
- you know what you want to build, but nothing is structured yet
- you already have a product or codebase and want to bring it under governance
- you already have specs or plans and want to improve execution quality

### Choose Your Path

| Your Situation | Start With | Goal |
| --- | --- | --- |
| I have only an idea | `/arpinine-harness:at-discover` | turn a vague idea into a spec-ready brief |
| I know what I want to build | `/arpinine-harness:at-new` | create the first governed `spec.md` |
| I already have a codebase | `/arpinine-harness:at-bootstrap-from-code` | generate initial governed artifacts from implementation evidence |
| I already have a spec but it is weak | `/arpinine-harness:at-review` | improve clarity, scope, and measurability |
| I already have an approved spec | `/arpinine-harness:at-plan` | generate execution plan and tasks |

### Recommended Methodology

#### For A New Product

1. Run `/arpinine-harness:at-init`.
2. If the product idea is still vague, run `/arpinine-harness:at-discover`.
3. When discovery reaches `spec-ready-awaiting-confirmation`, explicitly move to specification.
4. Let `/arpinine-harness:at-new` create the first governed `spec.md`.
5. Tighten the spec with `/arpinine-harness:at-review` if needed.
6. Create the engineering plan with `/arpinine-harness:at-plan`.
7. Capture consequential decisions with `/arpinine-harness:at-adr`.
8. If the feature uses AI, agents, or LLMs, define evaluation with `/arpinine-harness:at-eval`.
9. Implement with `/arpinine-harness:at-implement`.
10. Use `/arpinine-harness:at-audit` when reality diverges from intent.
11. Use `/arpinine-harness:at-retro` to turn lessons into lasting rules.

#### For An Existing Product You Want To Structure

1. Run `/arpinine-harness:at-init`.
2. Run `/arpinine-harness:at-bootstrap-from-code`.
3. Review the generated `spec.md`, `plan.md`, and related artifacts.
4. Tighten product intent with `/arpinine-harness:at-review`.
5. Re-run `/arpinine-harness:at-plan` if the plan needs to be regenerated from the improved spec.
6. Continue with normal governed execution: ADRs, evals, implementation, audit, and retro.

### Minimal First Session Examples

#### Example A: I Want To Build Something New

```bash
/arpinine-harness:at-init
/arpinine-harness:at-discover "I want to build a product that helps remote teams run better retrospectives"
# answer the one-question-at-a-time discovery prompts
# then say: move to specification
/arpinine-harness:at-review .specify/specs/<slug>/spec.md
/arpinine-harness:at-plan .specify/specs/<slug>/
```

#### Example B: I Already Have A Codebase

```bash
/arpinine-harness:at-init
/arpinine-harness:at-bootstrap-from-code .
/arpinine-harness:at-review .specify/specs/<slug>/spec.md
/arpinine-harness:at-plan .specify/specs/<slug>/
```

### Command Roles

- `/arpinine-harness:at-discover` turns vague ideas into a spec-ready brief.
- `/arpinine-harness:at-new` creates the first governed `spec.md`.
- `/arpinine-harness:at-review` improves an existing spec before execution.
- `/arpinine-harness:at-plan` turns product intent into engineering work.
- `/arpinine-harness:at-bootstrap-from-code` reverse-engineers governance from an existing product.
- `/arpinine-harness:at-implement` executes under the plan with test-first and security discipline.
- `/arpinine-harness:at-audit` checks drift between intent, code, and evidence.

### Common Mistakes

- Do not start with `/arpinine-harness:at-plan` before the spec is clear.
- Do not use `/arpinine-harness:at-new` for vague ideas; use `/arpinine-harness:at-discover` first.
- Do not use `/arpinine-harness:at-bootstrap-from-code` for greenfield work.
- Do not treat the commands as isolated utilities; they are stages in one governed workflow.

If you're unsure where to begin: run `/arpinine-harness:at-init`, then choose between `/arpinine-harness:at-discover`, `/arpinine-harness:at-new`, or `/arpinine-harness:at-bootstrap-from-code` depending on whether you have an idea, a request, or existing code.

## Agent Team

| Capability | Role |
| --- | --- |
| Product alignment | `product-owner` keeps business cases, acceptance criteria, and execution aligned with `spec.md` |
| Architecture | `tech-architect` and `architecture-governor` define modular boundaries and surface consequential decisions |
| Domain language | `domain-linguist` and `vocabulary-guardian` keep bounded-context vocabulary consistent from spec through code |
| Delivery | `tdd-guide` keeps implementation test-first and task-aligned |
| Security | `security-reviewer` checks implementation risk before completion |
| AI design | `ai-engineer` owns model selection, prompting strategy, agent topology, and AI-specific failure modes — scoped to AI/LLM features |
| Prod-readiness | `devops` owns deployment, secrets hygiene, CI/CD, and infrastructure — scoped to deployed services, secrets, or CI/CD |
| Data architecture | `data-engineer` owns data pipelines, RAG design, schema, vector stores, and data quality — scoped to pipeline or RAG features |
| Evaluation | `evaluation-governor` enforces quality metrics, thresholds, and evidence |
| Harness governance | `harness-governor` keeps product agent runtimes behind explicit boundaries |
| Realignment | `drift-detector`, ADRs, observations, and rules catch when code diverges from intent |

These agents don't replace your team. They help you govern AI-assisted work through explicit artifacts and automated checks so that "it looked right in the session" doesn't become the only quality gate you have.

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
| `domain-linguist` | Every plan needs bounded-context vocabulary enforced before implementation naming drifts into generic abstractions |
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

## Domain Vocabulary As Architecture

Arpinine Harness now treats domain language as part of the system design, not as commentary that can be ignored once coding starts.

- `spec.md` defines `## Domain Vocabulary`: canonical terms, definitions, forbidden synonyms, and disambiguation notes
- `/arpinine-harness:at-plan` turns that into `## Vocabulary Decisions` in `plan.md`
- `domain-linguist` reviews module, class, and interface naming against the declared vocabulary
- `vocabulary-guardian` plus `python3 scripts/check_vocabulary_drift.py --spec <slug>` provide the executable enforcement path before completion

This is the guardrail against specs saying `FulfillmentBatch` while the code quietly turns into `OrderProcessor`, `SettlementManager`, or other generic names that dissolve the domain model.

## Team Workflow

The plugin is built around a delivery loop that repeats, not a linear checklist:

1. **Define** — capture product intent in `spec.md`
2. **Refine** — tighten requirements before engineering starts
3. **Plan** — turn the approved spec into an engineering plan and task list
4. **Architect** — define module boundaries, dependency rules, harness strategy
5. **Decide** — record consequential choices in ADRs before they become implicit
6. **Evaluate** — define how you'll measure quality and readiness
7. **Execute** — implement with test-first discipline
8. **Realign** — audit drift between spec, decisions, code, and evaluation results
9. **Refine again** — update spec, plan, ADRs, or eval plan when what you learn changes the work

When multiple assistant teams are active, the same loop applies — but task ownership is lease-based so teams don't collide.

## Team Contract

| Role | Owns |
|------|------|
| User / Product Owner | Product intent, clarifications, review, approval, and final decisions |
| Product | The problem, user value, scope, business case, and acceptance criteria in `spec.md` |
| Engineering | `plan.md`, task breakdown, and implementation approach |
| Engineering | Bounded-context vocabulary in `spec.md` and `## Vocabulary Decisions` in `plan.md` |
| Engineering | Module boundaries, dependency rules, and testability by boundary |
| Engineering | Harness strategy when product features depend on an agent runtime |
| Engineering | Evaluation strategy, release thresholds, and runtime evidence expectations for agentic systems |
| Engineering | AI design decisions — when the feature uses AI or LLMs |
| Engineering | Prod-readiness — when the feature involves deployed services or secrets |
| Engineering | Data architecture — when the feature involves data pipelines or RAG |
| Tech Leads | Consequential decisions; ADR approval when needed |
| AI Agents | Creation and refinement of governed artifacts, implementation execution, and workflow enforcement within the approved methodology and the rules set by the spec, plan, ADRs, eval plan, and observation evidence |

The agents don't own anything on this list. Your team does. The agents help you hold the line.

## Agent Responsibilities

| Agent | What it does | Primary skills |
|-------|-------------|----------------|
| `product-owner` | Keeps business case, scope, and acceptance criteria aligned through planning, implementation, evaluation, and audit | `constitution-enforcer`, `evaluation-governor`, `drift-detector` |
| `tech-architect` | Catches architecture decisions early and pushes them into ADRs before they become accidental code structure | `architecture-governor`, `adr-manager` |
| `domain-linguist` | Enforces domain language as architecture by checking declared vocabulary against plan and implementation naming decisions | `vocabulary-guardian`, `drift-detector` |
| `tdd-guide` | Keeps implementation task-aligned and test-first so changes stay traceable and verifiable | `constitution-enforcer` |
| `security-reviewer` | Reviews plans and code for security gaps; blocks completion when risky behavior is undocumented or unsafe | `constitution-enforcer`, `rule-manager` |
| `ai-engineer` | Owns LLM design: model selection, prompting strategy, context management, agent topology, failure modes, and AI-specific eval metrics. Fires only on AI/LLM features | `evaluation-governor`, `adr-manager` |
| `devops` | Owns prod-readiness: deployment, secrets hygiene, CI/CD, env config, infrastructure. Fires only when the spec involves deployed services, secrets, or CI/CD | `adr-manager`, `rule-manager` |
| `data-engineer` | Owns data architecture: pipelines, RAG design, schema and migrations, vector store selection, data quality. Fires only on pipeline or RAG features | `adr-manager`, `rule-manager` |
| Governance skills | Codebase-wide enforcement: architecture, harness boundaries, evaluation, drift detection, ADR discipline, compounding rules | `architecture-governor`, `harness-governor`, `evaluation-governor`, `drift-detector`, `adr-manager`, `rule-manager` |

## Shared Artifacts

| Artifact | Purpose |
|----------|---------|
| `spec.md` | What problem is being solved, for whom, and how success is measured |
| `## Domain Vocabulary` | Canonical bounded-context terms, forbidden synonyms, and concept disambiguation rules |
| `plan.md` | How the team intends to implement the work |
| `## Vocabulary Decisions` | Mapping from declared domain terms to code constructs and module locations |
| `observability strategy` | Contract for observation/evaluation providers, env vars, score linkage, and swap boundaries for AI/LLM features |
| `harness strategy` | Product-application contract for harness choice, abstraction boundary, tool access, memory, and permissions |
| `module boundaries` | Architectural contract for responsibilities, dependency direction, and replaceable seams |
| `eval-plan.md` | Quality gate: how you measure readiness, regressions, and release fitness |
| `dataset-manifest.json` | Versioned scenario and label contract for reproducible benchmarked evaluation |
| `baseline.json` | Approved comparison target for regression-sensitive benchmark runs |
| `observation artifacts` | Runtime evidence: how the system actually behaved |
| `observation history` | Append-only runtime telemetry and provenance across repeated runs |
| `eval history` | Append-only evaluation and benchmark result snapshots |
| `ADR-*.md` | Why key decisions were made |
| `ADR-INDEX.md` | Global index of decisions and drift coverage |
| `coordination/*.json` | Multi-assistant task leases and ownership state for concurrent execution |
| `tools/style/` | Canonical style standards shared by all teams and implementations |

## Commands

| Command | Stage | Purpose |
|---------|-------|---------|
| `/arpinine-harness:at-init` | Setup | Initialize the shared workflow and ADR structure, and optionally scaffold a new project from an archetype |
| `/arpinine-harness:at-discover` | Discover | Refine a raw idea into a spec-ready brief through a one-question-at-a-time product-owner conversation, then promote it to specification on explicit confirmation |
| `/arpinine-harness:at-new` | Define | Create a new specification from a product request |
| `/arpinine-harness:at-bootstrap-from-code` | Define | Assess an existing codebase and seed the first governed spec, plan, eval, and ADR artifacts |
| `/arpinine-harness:at-review` | Refine | Improve clarity, measurability, and alignment before execution |
| `/arpinine-harness:at-plan` | Plan | Produce plan and tasks from an approved spec |
| `/arpinine-harness:at-adr` | Decide | Create and manage Architecture Decision Records |
| `/arpinine-harness:at-eval` | Evaluate | Define, run, benchmark, and review framework-agnostic evaluation |
| `/arpinine-harness:at-observe` | Evaluate | Record and review runtime observations |
| `/arpinine-harness:at-implement` | Execute | Implement the plan with TDD and security review |
| `/arpinine-harness:at-audit` | Realign | Detect drift and trigger refinement, ADR updates, or eval reruns |
| `/arpinine-harness:at-retro` | Learn | Extract lessons from completed work as compounding rules |
| `/arpinine-harness:at-status` | Govern | Project-wide governance overview and onboarding brief |
| `/arpinine-harness:at-ask` | Any stage | Ask a focused question to a named specialist agent with spec and plan as context |

## Example Flow

```bash
# Initialize team workflow in an existing repo
/arpinine-harness:at-init

# Or initialize a new repo with an explicit archetype
/arpinine-harness:at-init --archetype agent-app

# Or bootstrap a governed slice from an existing codebase
/arpinine-harness:at-bootstrap-from-code .

# Refine a raw idea before generating the spec
/arpinine-harness:at-discover "User login with email and password"

# After the plugin reaches spec-ready-awaiting-confirmation
# explicitly promote the idea into specification
"move to specification"

# Define product intent from the refined brief
/arpinine-harness:at-new "User login with email and password"

# Refine before engineering starts
/arpinine-harness:at-review .specify/specs/001-user-login/spec.md

# Create implementation plan
/arpinine-harness:at-plan .specify/specs/001-user-login/

# Review vocabulary-to-code mappings while the plan is still cheap to change
# plan.md now includes ## Vocabulary Decisions and specialist vocabulary review

# Before completion, enforce that code naming still matches the declared domain language
python3 scripts/check_vocabulary_drift.py --spec 001-user-login

# If the plan requires AI observation/evaluation wiring, scaffold it now
python3 scripts/scaffold_observability_setup.py --spec 001-user-login

# Record important decision if needed
/arpinine-harness:at-adr new "Session storage strategy"

# Define or run evaluation
/arpinine-harness:at-eval plan .specify/specs/001-user-login/

# Record observed runtime behavior
/arpinine-harness:at-observe record .specify/specs/001-user-login/

# Execute with test-first discipline
/arpinine-harness:at-implement .specify/specs/001-user-login/

# Realign when implementation and intent diverge
/arpinine-harness:at-audit .specify/specs/001-user-login/
```

## Observation And Evaluation Scaffolding

For AI, LLM, or agent-runtime features, the plugin now helps implementation directly instead of only describing the desired abstraction.

The flow is:

- `/arpinine-harness:at-plan` writes `## Observability Strategy` when observation/evaluation is required
- `python3 scripts/scaffold_observability_setup.py --spec <slug>` scaffolds missing provider abstractions, default Langfuse/DeepEval implementations when the plan selects them, `noop` providers, and `.env.example`
- `/arpinine-harness:at-implement` reruns that scaffold step, then blocks on `scripts/check-observability-setup.sh --spec <slug>` if provider files are missing or SDK imports leak outside the designated provider modules

That keeps product code dependent on `ObservationProvider` and `EvaluationProvider`, not directly on Langfuse or DeepEval.

## Vocabulary Enforcement

Bounded-context vocabulary is enforced in two stages:

- planning: `domain-linguist` and `vocabulary-guardian` review plan module names and `## Vocabulary Decisions`
- implementation: `python3 scripts/check_vocabulary_drift.py --spec <slug>` scans planned modules and referenced code for forbidden synonyms, generic naming drift, and missing vocabulary coverage

HIGH findings block completion. MEDIUM findings require either a rename or an explicit vocabulary clarification in the governing spec.

## End-to-End Demo

There are complete runnable demo products in the repo:

```text
examples/end-to-end/support-agent-demo/
examples/end-to-end/support-agent-openai-demo/
```

It covers the full Arpinine Harness loop on a small support triage agent: product request, governed `spec.md`, `plan.md` with module boundaries and harness strategy, fake harness adapter (no external runtime needed), runnable tests and evaluation script, observation trace, ADR and rule examples, and an intentional drift example for audit discussion.

```bash
cd examples/end-to-end/support-agent-demo
python3 -m unittest discover -s app/tests
python3 app/eval/run_eval.py
python3 ../../../src/arpinine-harness-core/scripts/run_benchmark.py --slug 001-support-triage-agent
```

## How Alignment Works

- `spec.md` stays product-facing and measurable
- `## Domain Vocabulary` keeps business concepts explicit and stable across planning and implementation
- `plan.md` captures implementation detail and delivery steps
- `## Vocabulary Decisions` ties those business concepts to concrete code structures before coding starts
- architecture rules enforce modularity before coding starts
- harness rules enforce how product applications depend on agent runtimes and how those runtimes are isolated
- eval plans define metrics, thresholds, scenarios, and execution commands
- observation artifacts show whether actual runtime behavior matches the planned harness model
- ADRs explain why key decisions were made
- hooks catch obvious violations and lightweight spec drift during editing
- audit catches drift when code, specs, and evaluation evidence stop matching
- refinement happens continuously, not only at the beginning

Automatic hooks fire on every file write:

- **PreToolUse**: `check-constitution.sh` — catches tech leakage in `spec.md` and hardcoded secrets
- **PreToolUse**: `check-architecture-readiness.sh` — blocks implementation edits until the plan defines module boundaries, dependency rules, and testability by boundary
- **PreToolUse**: `check-style-governance.sh` — blocks implementation edits when no declared style standard exists for that language
- **PreToolUse**: `check-task-claim.sh` — blocks implementation edits unless the current team identity owns an active task claim
- **PostToolUse**: `quick-drift-check.sh` — lightweight spec-alignment pass after every write

## Multi-Assistant Coordination

Claude and Codex can share the same governed workflow. Concurrent execution needs explicit task ownership or they'll collide.

- `plan.md` stays the source of task intent and progress
- `.specify/coordination/<slug>.json` stores machine-managed task claims and lease expiry
- optional task tags (`[team: claude]`, `[team: codex]`) restrict which team may claim a task
- `scripts/claim_task.py` atomically selects the next eligible task using a file lock
- `scripts/release_task.py` marks a task available again or completed
- `scripts/check-task-claim.sh` blocks implementation-path edits unless the current team identity owns an active claim
- `.specify/delivery.md` shows assigned team, active claimer, and lease state

Set `ARPININE_HARNESS_TEAM_ID` or `ARPININE_HARNESS_INSTANCE_ID` only when you need to override automatic identity resolution. By default the scripts derive both from the host plugin environment.

## Multi-Team Style Governance

Multiple teams only stay interchangeable if they follow the same style rules.

- `.specify/CONSTITUTION.md` declares style standards that are mandatory across all teams and plugins
- `tools/style/` is the canonical location for checked-in language-specific style configs
- `check-style-governance.sh` blocks implementation edits for supported languages when no canonical style config exists
- all teams must use the same repo-defined config paths, not assistant-local defaults

## ADR Lifecycle

```text
Proposed -> Accepted -> Implemented -> Superseded
                    -> Rejected
```

All ADRs live in `.specify/adr/`. Each one links to its governing spec via `governs:` and to a concrete decision or drift key via `covers:`.

## Implementation Layout

```text
src/
  arpinine-harness-core/      # commands, agents, hooks, scripts, skills, templates
  implementations/
    claude/              # working Claude implementation
    codex/               # Codex plugin implementation
tools/
  style/                 # canonical cross-team style standards by language
```

Build and registration targets work across implementations:

```bash
make assemble IMPLEMENTATION=<name>
make build IMPLEMENTATION=<name>
make delivery
make register IMPLEMENTATION=<name>
make validate-structure IMPLEMENTATION=<name>
```

Claude also has native targets for install, uninstall, and validator-backed validation. Codex uses the shared abstraction plus marketplace registration.

## Usage Model

```bash
# 1. Install the default specification provider (spec-kit), or configure another provider later
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude

# 2a. New project: initialize the workflow with an explicit archetype
/arpinine-harness:at-init --archetype agent-app

# 2b. Existing project: initialize the workflow without scaffolding
/arpinine-harness:at-init

# 3. Reverse/bootstrap an existing codebase
/arpinine-harness:at-bootstrap-from-code . --git-log
```

When `at-init` runs in a repo that does not yet look like an application, it can scaffold a thin starter structure before creating `.specify/`. The current shared archetypes are:

- `agent-app` — `src/agents`, `src/tools`, `src/domain`, `evals`, `tests`
- `ml-pipeline` — `src/pipelines`, `src/features`, `src/models`, `src/domain`, `data/*`, `notebooks`, `evals`, `tests`

## Archetypes

Archetypes are starter project shapes for new repos. They exist to solve a specific problem: when a repo is empty, governance alone is not enough. You also need an initial structure that nudges the team toward clean boundaries before the first feature is implemented.

An archetype does not try to generate a full application. It gives you a deliberate starting point:

- a directory layout that matches a common application shape
- a neutral `PROJECT_CONVENTIONS.md` file that explains the intended boundaries
- a recorded archetype choice in `.specify/archetype.json`
- constitution addenda and starter rules that keep the archetype’s core invariants active from the beginning

This is why archetypes are intentionally thin. They do not pin frameworks, dependencies, model providers, or deployment tooling. Those are product and engineering choices that should still be made explicitly in governed artifacts such as `spec.md`, `plan.md`, and ADRs.

The goal is not scaffolding for its own sake. The goal is to start from a structure that makes good boundaries easier to preserve and bad coupling harder to introduce.

## Archetype Usage

Use archetypes when you are starting a new repo and want Arpinine Harness to create a starter structure before governance artifacts are generated.

Choose `agent-app` when the product is centered on agent workflows, tool orchestration, runtime adapters, or evaluation of agent behaviour.

Choose `ml-pipeline` when the product is centered on data ingestion, feature transforms, model training, reproducibility, and evaluation/baseline workflows.

Skip archetype scaffolding when:

- the repo already has an application structure you want to preserve
- you are reverse-bootstrapping an existing codebase with `/arpinine-harness:at-bootstrap-from-code`
- the project shape is unusual enough that a generic starter structure would add noise

Interactive usage through `at-init`:

```text
/arpinine-harness:at-init
```

Explicit usage through `at-init`:

```text
/arpinine-harness:at-init --archetype agent-app
/arpinine-harness:at-init --archetype ml-pipeline
```

What happens during archetype init:

1. Arpinine Harness checks whether the repo already looks like an application.
2. If the repo looks empty, it can scaffold the selected archetype before the normal governance setup.
3. The scaffold creates the starter directories and `PROJECT_CONVENTIONS.md`.
4. The selected archetype is recorded in `.specify/archetype.json`.
5. After the base constitution is generated, Arpinine Harness applies an archetype-specific addendum and starter rules.
6. Shared pre-edit hook checks then enforce the supported archetype invariants in both Claude and Codex.

Expected flow without an explicit archetype:

1. `at-init` detects that the repo does not yet look like an application.
2. It offers archetype scaffolding.
3. You choose one of the shared archetypes or skip scaffolding.
4. The scaffold runs before the normal `.specify/` setup.

Direct shared script usage from the assembled plugin root:

```bash
python3 scripts/scaffold_archetype.py --list
python3 scripts/scaffold_archetype.py agent-app --target-dir . --skip-if-nonempty
python3 scripts/scaffold_archetype.py ml-pipeline --target-dir . --force
```

Use `--skip-if-nonempty` for safe first-run behavior in a repo that may already contain code. Use `--force` only when you intentionally want to scaffold into a non-empty repo.

In practice, the direct script is useful for testing, automation, or debugging the scaffold contract itself. Most users should prefer `at-init`, because it wires scaffolding into the rest of the governance setup.

When an archetype is selected during `at-init`, Arpinine Harness also:

- records the selection in `.specify/archetype.json`
- extends the generated constitution with an archetype-specific addendum
- seeds starter rules under `.specify/rules/archetype/`
- activates shared pre-edit hook checks that enforce the supported archetype invariants in both Claude and Codex

## Plugin Install

### Claude

Use the Claude-native install flow.

Then install Arpinine Harness from this repo:

```bash
make validate-structure IMPLEMENTATION=claude
make assemble IMPLEMENTATION=claude
claude plugin marketplace add ./dist
claude plugin install arpinine-harness@arpinine-harness-local
```

`make assemble` generates both the assembled plugin at `dist/plugins/arpinine-harness-claude/` and the Claude marketplace manifest at `dist/.claude-plugin/marketplace.json`, so the registration target is now `./dist`, not the repo root.

Verify the install:

```bash
claude plugin list
```

Expected result:

```text
arpinine-harness@arpinine-harness-local
Status: ✔ enabled
```

If you prefer the convenience target, `make install IMPLEMENTATION=claude` is still supported, but the explicit sequence above is the most reliable way to recover from stale local marketplace registrations.

### Codex

Use the Codex marketplace registration flow:

```bash
make validate-structure IMPLEMENTATION=codex
make register IMPLEMENTATION=codex
```

This generates the Codex marketplace manifest at `dist/.agents/plugins/marketplace.json` and registers `./dist` as the local marketplace root.

If you need the explicit Codex CLI command for your local client version, use:

```bash
codex plugin marketplace add ./dist
```

After registration, enable `arpinine-harness` from the Codex marketplace UI if your client requires a separate confirmation step.

Cross-implementation registration:

```bash
make register IMPLEMENTATION=claude
make register IMPLEMENTATION=codex
```

Session-only load without installing (dev/testing):

```bash
make assemble IMPLEMENTATION=claude
claude --plugin-dir ./dist/plugins/arpinine-harness-claude
```

## Reverse An Existing Codebase

Once the plugin is installed and enabled, move into the target repo and run:

```text
/arpinine-harness:at-init
/arpinine-harness:at-bootstrap-from-code . --git-log
```

This flow is for an existing codebase. Archetype scaffolding is for new repos, not for reverse-bootstrapping code that already exists.

This creates:
- `.specify/bootstrap/latest-assessment.json`
- `.specify/bootstrap/latest-assessment.md`
- `.specify/specs/<slug>/spec.md`
- `.specify/specs/<slug>/plan.md`
- optional eval and ADR seed artifacts when the assessment warrants them

Then refine the reverse-engineered slice:

```text
/arpinine-harness:at-review .specify/specs/<slug>/spec.md
/arpinine-harness:at-audit .specify/specs/<slug>/spec.md
```

If the repo already contains code, `at-init` will skip archetype scaffolding unless you explicitly force it.

## Dependency Handling

Arpinine Harness doesn't install the configured specification provider, harness runtimes, or eval frameworks during plugin installation. It validates them during setup and before the relevant workflow stage:

- `spec-kit` is the default specification provider for automated generation and planning
- harness runtimes are required only when `## Harness Strategy` explicitly selects one
- eval tools are required only when `eval-plan.md` selects them

The provider is selected in `.specify/specification-provider.json`. The default adapter targets `spec-kit`, but the command surface stays the same if you switch providers.

Run `src/arpinine-harness-core/scripts/check-dependencies.sh --json` for a machine-readable readiness report.
