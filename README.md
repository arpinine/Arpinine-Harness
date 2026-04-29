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

## Start Here

If you want to use Arpinine Harness rather than just read its files, start here:

- [Vibe Coder Process](docs/vibe-coder-process.md)

That guide covers the day-to-day operating model for anyone using Arpinine Harness with an AI coding assistant.

## Agent Team

| Capability | Role |
| --- | --- |
| Product alignment | `product-owner` keeps business cases, acceptance criteria, and execution aligned with `spec.md` |
| Architecture | `tech-architect` and `architecture-governor` define modular boundaries and surface consequential decisions |
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

Scope is evaluated during `/at-plan` by reading what the spec and plan actually describe. When a scoped agent activates, it also requires a corresponding section in `plan.md` — `## AI Design Decisions`, `## Deployment Strategy`, or `## Data Pipeline` — so the plan is complete for that domain before implementation starts.

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
| Product | The problem, user value, scope, business case, and acceptance criteria in `spec.md` |
| Engineering | `plan.md`, task breakdown, and implementation approach |
| Engineering | Module boundaries, dependency rules, and testability by boundary |
| Engineering | Harness strategy when product features depend on an agent runtime |
| Engineering | Evaluation strategy, release thresholds, and runtime evidence expectations for agentic systems |
| Engineering | AI design decisions — when the feature uses AI or LLMs |
| Engineering | Prod-readiness — when the feature involves deployed services or secrets |
| Engineering | Data architecture — when the feature involves data pipelines or RAG |
| Tech Leads | Consequential decisions; ADR approval when needed |
| AI Agents | Execution within the rules set by the spec, plan, ADRs, eval plan, and observation evidence |

The agents don't own anything on this list. Your team does. The agents help you hold the line.

## Agent Responsibilities

| Agent | What it does | Primary skills |
|-------|-------------|----------------|
| `product-owner` | Keeps business case, scope, and acceptance criteria aligned through planning, implementation, evaluation, and audit | `constitution-enforcer`, `evaluation-governor`, `drift-detector` |
| `tech-architect` | Catches architecture decisions early and pushes them into ADRs before they become accidental code structure | `architecture-governor`, `adr-manager` |
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
| `plan.md` | How the team intends to implement the work |
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
| `/arpinine-harness:at-init` | Setup | Initialize the shared workflow and ADR structure |
| `/arpinine-harness:at-new` | Define | Create a new specification from a product request |
| `/arpinine-harness:at-review` | Refine | Improve clarity, measurability, and alignment before execution |
| `/arpinine-harness:at-plan` | Plan | Produce plan and tasks from an approved spec |
| `/arpinine-harness:at-adr` | Decide | Create and manage Architecture Decision Records |
| `/arpinine-harness:at-eval` | Evaluate | Define, run, benchmark, and review framework-agnostic evaluation |
| `/arpinine-harness:at-observe` | Evaluate | Record and review runtime observations |
| `/arpinine-harness:at-implement` | Execute | Implement the plan with TDD and security review |
| `/arpinine-harness:at-audit` | Realign | Detect drift and trigger refinement, ADR updates, or eval reruns |

## Example Flow

```bash
# Initialize team workflow
/arpinine-harness:at-init

# Define product intent
/arpinine-harness:at-new "User login with email and password"

# Refine before engineering starts
/arpinine-harness:at-review .specify/specs/001-user-login/spec.md

# Create implementation plan
/arpinine-harness:at-plan .specify/specs/001-user-login/

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

## End-to-End Demo

There's a complete runnable demo product in the repo:

```text
examples/end-to-end/support-agent-demo/
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
- `plan.md` captures implementation detail and delivery steps
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
    codex/               # Codex plugin implementation in progress
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

# 2. Install from Claude's native CLI
make install

# 3. Initialize the workflow (run inside a Claude Code session)
/arpinine-harness:at-init
```

Cross-implementation registration:

```bash
make register IMPLEMENTATION=claude
make register IMPLEMENTATION=codex
```

After Codex registration, enable `arpinine-harness` from the Codex marketplace UI if your client requires a separate confirmation step.

Session-only load without installing (dev/testing):

```bash
make assemble IMPLEMENTATION=claude
claude --plugin-dir ./plugins/arpinine-harness-claude
```

## Dependency Handling

Arpinine Harness doesn't install the configured specification provider, harness runtimes, or eval frameworks during plugin installation. It validates them during setup and before the relevant workflow stage:

- the configured specification provider is required for automated generation and planning
- harness runtimes are required only when `## Harness Strategy` explicitly selects one
- eval tools are required only when `eval-plan.md` selects them

The provider is selected in `.specify/specification-provider.json`. The default adapter targets `spec-kit`, but the command surface stays the same if you switch providers.

Run `src/arpinine-harness-core/scripts/check-dependencies.sh --json` for a machine-readable readiness report.
