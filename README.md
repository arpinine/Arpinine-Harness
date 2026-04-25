# AgentAlign

AgentAlign is a governed AI workflow plugin with a shared core and assistant-specific implementations.

It creates an agent-assisted governance layer for product and engineering teams: specialized agents, workflow commands, hooks, and evidence checks that keep AI-assisted product development aligned with shared specifications, architecture rules, evaluations, and runtime observations.

The goal is not to stop fast AI-assisted execution. The goal is to make it safe, repeatable, and team-aligned.

It standardizes how work moves from idea to specification, from specification to evaluation and execution, and from execution back into refinement when reality diverges from intent.

## One Plugin, Team Of Agents

AgentAlign should be understood as a virtual delivery team, not as a single assistant with a prompt bundle.

The user interacts with one plugin entrypoint, but each workflow command activates a coordinated set of specialized agent roles. In practice, the plugin behaves like:

- a `product-owner` that clarifies intent, scope, and acceptance criteria
- a `tech-architect` that shapes boundaries, dependencies, and ADR-worthy decisions
- a `tdd-guide` that keeps execution task-aligned and test-first
- a `security-reviewer` that challenges risky or underspecified changes
- an `evaluation-governor` that pushes for measurable quality gates
- a `drift-detector` that checks whether code, plans, ADRs, and runtime evidence still agree

This is the core operating model: one plugin surface, many specialized agent responsibilities.

## Multi-Team Operating Model

AgentAlign also supports multiple assistant teams sharing the same governed repository at the same time.

Typical example:

- one delivery lane runs in Claude
- one delivery lane runs in Codex
- both teams use the same `spec.md`, `plan.md`, ADRs, eval artifacts, and delivery matrix
- implementation ownership is coordinated through shared task claims and optional team tags in `plan.md`

So the operating model has two layers:

- specialist roles inside one assistant session
- multiple assistant teams coordinated through one governed workflow

## Start Here

If you want to use AgentAlign as an operator rather than just inspect its files, start with the vibe-coder operating guide:

- [Vibe Coder Process](docs/vibe-coder-process.md)

Use the process guide for day-to-day operation of the plugin.

## Agent Team

AgentAlign coordinates a small team of focused AI roles and governance skills:


| Capability         | Role                                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------------- |
| Product alignment  | `product-owner` keeps business cases, acceptance criteria, and execution aligned with `spec.md`         |
| Architecture       | `tech-architect` and `architecture-governor` help define modular boundaries and consequential decisions |
| Delivery           | `tdd-guide` keeps implementation test-first and task-aligned                                            |
| Security           | `security-reviewer` checks implementation risk before completion                                        |
| Evaluation         | `evaluation-governor` enforces quality metrics, thresholds, and evidence                                |
| Harness governance | `harness-governor` keeps product agent runtimes behind explicit boundaries                              |
| Realignment        | `drift-detector`, ADRs, observations, and rules detect when code diverges from intent                   |


These agents do not replace team ownership. They help the team govern vibe-coded work through explicit artifacts and automated checks.

## Team Workflow

The plugin is built around a shared delivery loop:

1. Define: capture product intent in `spec.md`
2. Refine: review and tighten requirements before implementation
3. Plan: turn approved intent into an engineering plan and tasks
4. Architect: define module boundaries, dependency rules, harness strategy, and clean separation of concerns
5. Decide: record consequential architecture and implementation choices in ADRs
6. Evaluate: define how the team will measure quality and readiness
7. Execute: implement with test-first discipline
8. Realign: audit drift between spec, decisions, code, and evaluation results
9. Refine again: update the spec, plan, ADRs, or eval plan when learning changes the work

This is the core value of the plugin: not just generating files, but giving the team a stable operating model.

When multiple assistant teams are active, the same workflow still applies, but implementation work is lease-based rather than first-come/first-served.

## Team Contract


| Team Role   | Responsibility                                                                                      |
| ----------- | --------------------------------------------------------------------------------------------------- |
| Product     | Owns the problem, user value, scope, business case, and acceptance criteria in `spec.md`            |
| Engineering | Owns `plan.md`, task breakdown, and implementation approach                                         |
| Engineering | Owns module boundaries, dependency rules, and testability by boundary                               |
| Engineering | Owns evaluation strategy, release thresholds, and runtime evidence expectations for agentic systems |
| Tech Leads  | Own consequential decisions and approve ADRs when needed                                            |
| AI Agents   | Help execute within the rules set by the spec, plan, ADRs, eval plan, and observation evidence      |


Human ownership stays with the team. AgentAlign agents act as governed specialists inside that contract.

## Agent Responsibilities


| Agent               | Responsibility In The Governed Codebase                                                                                                              | Primary Skills Used                                                                                                 |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `product-owner`     | Keeps the business case, scope, and acceptance criteria aligned from `spec.md` through planning, implementation, evaluation, and audit               | `constitution-enforcer`, `evaluation-governor`, `drift-detector`                                                    |
| `tech-architect`    | Protects modular design, identifies consequential decisions, and pushes architecture changes into ADRs before they become accidental code structure  | `architecture-governor`, `adr-manager`                                                                              |
| `tdd-guide`         | Keeps implementation task-aligned and test-first so code changes stay traceable to planned work and verifiable by tests                              | `constitution-enforcer`                                                                                             |
| `security-reviewer` | Reviews plans and implementation for security-sensitive gaps and blocks completion when risky behavior is undocumented or unsafe                     | `constitution-enforcer`, `rule-manager`                                                                             |
| Governance skills   | Provide the codebase-wide enforcement layer for architecture, harness boundaries, evaluation, drift detection, ADR discipline, and compounding rules | `architecture-governor`, `harness-governor`, `evaluation-governor`, `drift-detector`, `adr-manager`, `rule-manager` |


## Shared Artifacts


| Artifact                | Purpose                                                                                                     |
| ----------------------- | ----------------------------------------------------------------------------------------------------------- |
| `spec.md`               | Product intent: what problem is being solved, for whom, and how success is measured                         |
| `plan.md`               | Engineering approach: how the team intends to implement the work                                            |
| `harness strategy`      | Product-application contract for harness choice, abstraction boundary, tool access, memory, and permissions |
| `module boundaries`     | Architectural contract for responsibilities, dependency direction, and replaceable seams                    |
| `eval-plan.md`          | Quality gate: how the team measures readiness, regressions, and release fitness                             |
| `observation artifacts` | Runtime evidence: how the system actually behaved under real or simulated execution                         |
| `ADR-*.md`              | Decision record for choices that affect architecture, operations, security, or long-term maintainability    |
| `ADR-INDEX.md`          | Global index of decisions and drift coverage                                                                |
| `coordination/*.json`   | Multi-assistant task leases and ownership state for concurrent execution                                    |
| `tools/style/`          | Canonical repository style standards shared by all teams and plugin implementations                         |


## Commands


| Command                     | Stage    | Purpose                                                          |
| --------------------------- | -------- | ---------------------------------------------------------------- |
| `/agent-align:at-init`      | Setup    | Initialize the shared workflow and ADR structure                 |
| `/agent-align:at-new`       | Define   | Create a new specification from a product request                |
| `/agent-align:at-review`    | Refine   | Improve clarity, measurability, and alignment before execution   |
| `/agent-align:at-plan`      | Plan     | Produce plan and tasks from an approved spec                     |
| `/agent-align:at-adr`       | Decide   | Create and manage Architecture Decision Records                  |
| `/agent-align:at-eval`      | Evaluate | Define and run framework-agnostic evaluation                     |
| `/agent-align:at-observe`   | Evaluate | Record and review runtime observations                           |
| `/agent-align:at-implement` | Execute  | Implement the plan with TDD and security review                  |
| `/agent-align:at-audit`     | Realign  | Detect drift and trigger refinement, ADR updates, or eval reruns |


## Example Flow

```bash
# Initialize team workflow
/agent-align:at-init

# Define product intent
/agent-align:at-new "User login with email and password"

# Refine before engineering starts
/agent-align:at-review .specify/specs/001-user-login/spec.md

# Create implementation plan
/agent-align:at-plan .specify/specs/001-user-login/

# Record important decision if needed
/agent-align:at-adr new "Session storage strategy"

# Define or run evaluation
/agent-align:at-eval plan .specify/specs/001-user-login/

# Record observed runtime behavior
/agent-align:at-observe record .specify/specs/001-user-login/

# Execute with test-first discipline
/agent-align:at-implement .specify/specs/001-user-login/

# Realign when implementation and intent diverge
/agent-align:at-audit .specify/specs/001-user-login/
```

## End-to-End Demo

The repository includes a complete runnable demo product:

```text
examples/end-to-end/support-agent-demo/
```

It shows the full AgentAlign loop on a small support triage agent:

- product request and governed `spec.md`
- `plan.md` with module boundaries, dependency rules, harness strategy, and eval strategy
- fake harness adapter so no external runtime is required
- runnable tests and evaluation script
- observation trace
- ADR and rule examples
- intentional drift example for audit discussion

Start with:

```bash
cd examples/end-to-end/support-agent-demo
PYTHONPATH=app python3 -m unittest discover -s app/tests
PYTHONPATH=app python3 app/eval/run_eval.py
```

## How Alignment Works

- `spec.md` stays product-facing and measurable
- `plan.md` captures implementation detail and delivery steps
- architecture rules enforce modularity and clean separation of concerns before coding starts
- harness rules enforce how product applications depend on agent runtimes and how those runtimes are isolated
- eval plans define metrics, thresholds, scenarios, and execution commands
- observation artifacts show whether actual runtime behavior matches the planned harness model
- ADRs explain why key decisions were made
- hooks catch obvious violations and lightweight spec drift during editing
- audit catches drift when code, specs, and evaluation evidence stop matching
- refinement happens continuously, not only at the beginning

Automatic hooks fire on every file write:

- **PreToolUse**: `check-constitution.sh` validates pending edits for tech leakage in `spec.md` and hardcoded secrets
- **PreToolUse**: `check-architecture-readiness.sh` blocks implementation edits until the governing plan defines module boundaries, dependency rules, and testability by boundary
- **PreToolUse**: `check-style-governance.sh` blocks implementation edits when the repository has no declared style standard for that language
- **PreToolUse**: `check-task-claim.sh` blocks implementation edits unless the current team identity owns an active task claim
- **PostToolUse**: `quick-drift-check.sh` performs a lightweight spec-alignment pass for missing file references, endpoint mismatch hints, and stale eval results

## Multi-Assistant Coordination

Claude and Codex can share the same governed workflow, but concurrent execution needs explicit task ownership.

- `plan.md` remains the source of task intent and progress
- `.specify/coordination/<slug>.json` stores machine-managed task claims and lease expiry
- optional task tags such as `[team: claude]` or `[team: codex]` restrict which team may claim a task
- `scripts/claim_task.py` atomically selects the next eligible task using a file lock
- `scripts/release_task.py` marks a claimed task available again or completed after `[~] -> [x]`
- `scripts/check-task-claim.sh` blocks implementation-path edits unless the current team identity owns an active claim
- `.specify/delivery.md` shows assigned team, active claimer, and lease state alongside task progress

This keeps one assistant instance from taking work already assigned or currently leased to the other.

By default the scripts derive team identity from the host plugin environment and derive a stable per-session instance id from the current host/session fingerprint. Set `AGENT_ALIGN_TEAM_ID` or `AGENT_ALIGN_INSTANCE_ID` only when you need to override that automatic identity resolution.

## Multi-Team Style Governance

Multiple teams only stay interchangeable if they follow the same repository-owned style rules.

- `.specify/CONSTITUTION.md` declares shared style standards mandatory across teams and plugins
- `tools/style/` is the canonical location for checked-in language-specific style configs
- `check-style-governance.sh` blocks implementation edits for supported languages when no canonical style config exists
- all teams must use the same repo-defined config paths rather than assistant-local defaults

## ADR Lifecycle

```text
Proposed -> Accepted -> Implemented -> Superseded
                    -> Rejected
```

All ADRs live in `.specify/adr/`.
Each ADR has:

- `governs:` to link it to a spec
- `covers:` to link it to a concrete decision key or drift key

## Implementation Layout

AgentAlign now separates shared workflow assets from assistant-specific implementations:

```text
src/
  agent-align-core/      # commands, agents, hooks, scripts, skills, templates
  implementations/
    claude/              # working Claude implementation
    codex/               # Codex plugin implementation in progress
tools/
  style/                 # canonical cross-team style standards by language
```

Each implementation overlays the same shared core.

The real cross-implementation abstraction is the common-denominator workflow:

- `make assemble IMPLEMENTATION=<name>`
- `make build IMPLEMENTATION=<name>`
- `make delivery`
- `make register IMPLEMENTATION=<name>`
- `make validate-structure IMPLEMENTATION=<name>`


Claude also has native convenience targets for install, uninstall, and validator-backed validation.
Codex uses the shared abstraction plus Codex marketplace registration.

## Usage Model

From the root of this repo:

```bash
# 1. Install spec-kit
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude

# 2. Register the Claude marketplace and install from Claude's native CLI
make install

# 3. Initialize the workflow (run inside a Claude Code session)
/agent-align:at-init
```

Cross-implementation registration:

```bash
make register IMPLEMENTATION=claude
make register IMPLEMENTATION=codex
```

After Codex registration, enable `agent-align` from the Codex marketplace UI if your client requires a separate confirmation step.

For a session-only load without installing (dev/testing):

```bash
make assemble IMPLEMENTATION=claude
claude --plugin-dir ./plugins/agent-align-claude
```

Or build explicitly for an implementation:

```bash
make build IMPLEMENTATION=claude
make assemble IMPLEMENTATION=codex
```

The versioned zip artifact under `dist/` always uses the current plugin version from the Claude manifest, so commands and docs should refer to the stable plugin directories under `plugins/` for local usage rather than a hardcoded versioned path.

Common structural validation:

```bash
make validate-structure IMPLEMENTATION=claude
make validate-structure IMPLEMENTATION=codex
```

Claude-only native operations:

```bash
make install IMPLEMENTATION=claude
make uninstall IMPLEMENTATION=claude
make validate IMPLEMENTATION=claude
```

## Dependency Handling

AgentAlign does not try to install `spec-kit`, harness runtimes, or eval frameworks during plugin installation.
Instead, it validates them during setup and before the relevant workflow stage:

- `spec-kit` is required for automated generation and planning
- harness runtimes are required only for features whose `## Harness Strategy` explicitly selects one
- eval tools are required only when `eval-plan.md` selects them

In practice:

- if `## Harness Strategy` is `N/A`, the project does not need a harness runtime
- if `## Harness Strategy` selects a runtime such as OpenHarness or an internal agent runtime, that runtime becomes a required dependency for that feature

Use `src/agent-align-core/scripts/check-dependencies.sh --json` for machine-readable readiness, or without flags for a text report.
