# AgentAlign

AgentAlign is a Claude plugin for teams that want a common way of working across product, engineering, harness-based application design, architecture, and AI-assisted execution.

It standardizes how work moves from idea to specification, from specification to evaluation and execution, and from execution back into refinement when reality diverges from intent.

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

## Team Contract

| Role | Responsibility |
|------|----------------|
| Product | Owns the problem, user value, scope, and acceptance criteria in `spec.md` |
| Engineering | Owns `plan.md`, task breakdown, and implementation approach |
| Engineering | Owns module boundaries, dependency rules, and testability by boundary |
| Engineering | Owns evaluation strategy and release thresholds for agentic systems |
| Tech Leads | Own consequential decisions and approve ADRs when needed |
| AI Agents | Help execute within the rules set by the spec, plan, and ADRs |

## Shared Artifacts

| Artifact | Purpose |
|----------|---------|
| `spec.md` | Product intent: what problem is being solved, for whom, and how success is measured |
| `plan.md` | Engineering approach: how the team intends to implement the work |
| `harness strategy` | Product-application contract for harness choice, abstraction boundary, tool access, memory, and permissions |
| `module boundaries` | Architectural contract for responsibilities, dependency direction, and replaceable seams |
| `eval-plan.md` | Quality gate: how the team measures readiness, regressions, and release fitness |
| `ADR-*.md` | Decision record for choices that affect architecture, operations, security, or long-term maintainability |
| `ADR-INDEX.md` | Global index of decisions and drift coverage |

## Commands

| Command | Stage | Purpose |
|---------|-------|---------|
| `/spec-init` | Setup | Initialize the shared workflow and ADR structure |
| `/spec-new` | Define | Create a new specification from a product request |
| `/spec-review` | Refine | Improve clarity, measurability, and alignment before execution |
| `/spec-plan` | Plan | Produce plan and tasks from an approved spec |
| `/spec-adr` | Decide | Create and manage Architecture Decision Records |
| `/spec-eval` | Evaluate | Define and run framework-agnostic evaluation |
| `/spec-implement` | Execute | Implement the plan with TDD and security review |
| `/spec-audit` | Realign | Detect drift and trigger refinement, ADR updates, or eval reruns |

## Example Flow

```bash
# Initialize team workflow
/spec-init

# Define product intent
/spec-new "User login with email and password"

# Refine before engineering starts
/spec-review .specify/specs/001-user-login/spec.md

# Create implementation plan
/spec-plan .specify/specs/001-user-login/

# Record important decision if needed
/spec-adr new "Session storage strategy"

# Define or run evaluation
/spec-eval plan .specify/specs/001-user-login/

# Execute with test-first discipline
/spec-implement .specify/specs/001-user-login/

# Realign when implementation and intent diverge
/spec-audit .specify/specs/001-user-login/
```

## How Alignment Works

- `spec.md` stays product-facing and measurable
- `plan.md` captures implementation detail and delivery steps
- architecture rules enforce modularity and clean separation of concerns before coding starts
- harness rules enforce how product applications depend on agent runtimes and how those runtimes are isolated
- eval plans define metrics, thresholds, scenarios, and execution commands
- ADRs explain why key decisions were made
- hooks catch obvious violations and lightweight spec drift during editing
- audit catches drift when code, specs, and evaluation evidence stop matching
- refinement happens continuously, not only at the beginning

Automatic hooks fire on every file write:
- **PreToolUse**: `check-constitution.sh` validates pending edits for tech leakage in `spec.md` and hardcoded secrets
- **PreToolUse**: `check-architecture-readiness.sh` blocks implementation edits until the governing plan defines module boundaries, dependency rules, and testability by boundary
- **PostToolUse**: `quick-drift-check.sh` performs a lightweight spec-alignment pass for missing file references, endpoint mismatch hints, and stale eval results

## ADR Lifecycle

```text
Proposed -> Accepted -> Implemented -> Superseded
                    -> Rejected
```

All ADRs live in `.specify/adr/`.
Each ADR has:
- `governs:` to link it to a spec
- `covers:` to link it to a concrete decision key or drift key

## Installation

```bash
# 1. Install spec-kit
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude

# 2. Build this plugin
make build

# 3. Install plugin in Claude
/plugin install dist/agent-align-v1.0.0.zip

# 4. Initialize the workflow
/spec-init
```

## License

MIT
