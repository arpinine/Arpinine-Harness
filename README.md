# Arpinine Harness

A plugin for anyone building software with AI coding assistants who wants to ship what they intended, not just ship code.

When you build with AI, things move fast. Specs drift. Architecture decisions happen by accident. Secrets end up hardcoded. Arpinine Harness gives you a team of specialized agents — product, architecture, security, TDD, domain language, deployment, data, and evaluation — that show up at the right moments and block the wrong ones.

---

## Start Here

Use `/arpinine-harness:at` as the front door. It is the facade over the Arpinine Harness agent team: you describe the intent in plain language, the facade inspects the repository's current state, selects the right specialist-led workflow command, explains the decision, and delegates.

```text
/arpinine-harness:at "I want to build a product for remote retrospectives"
/arpinine-harness:at "we already have code, bring it under governance"
/arpinine-harness:at "what should I do next?"
```

The router classifies your intent against actual repo state and responds with a structured decision:

```text
AT: facade
STATE: governed repo, no active sessions
INTERPRETATION: broad product goal
RECOMMENDATION: /at-map
WHY: The request spans project-level decomposition rather than one feature spec.
ALTERNATIVE: /at-discover
CONFIRM: proceed with /at-map?
```

From an initial state, that means:

- in an ungoverned or mostly empty repo, the facade routes to `/arpinine-harness:at-init`
- in an existing codebase with no governance artifacts, it routes or confirms toward `/arpinine-harness:at-bootstrap-from-code`
- in a governed repo with a broad goal, it routes to `/arpinine-harness:at-map`
- in a governed repo with one feature idea, it routes to `/arpinine-harness:at-discover`
- when the next step is unclear, it routes to `/arpinine-harness:at-status`

Typical routed outcomes:

| Your intent | Route |
|-------------|-------|
| Broad goal in a governed repo | `/at-map` |
| Feature-sized idea | `/at-discover` |
| Ungoverned repo | `/at-init` |
| Existing codebase, no governance | confirm between `/at-init` and `/at-bootstrap-from-code` |
| "What should I do next?" | `/at-status` |

---

## Commands

| Command | Stage | Purpose |
|---------|-------|---------|
| `/arpinine-harness:at` | Facade | Inspect repo state, route intent, explain choice, delegate |
| `/arpinine-harness:at-init` | Setup | Initialize governance; optionally scaffold an archetype |
| `/arpinine-harness:at-map` | Discover | Decompose a broad goal into a project brief and ordered feature backlog |
| `/arpinine-harness:at-discover` | Discover | Refine one feature idea into a spec-ready brief, then promote on confirmation |
| `/arpinine-harness:at-new` | Define | Create a governed `spec.md` from a product request |
| `/arpinine-harness:at-bootstrap-from-code` | Define | Seed governed artifacts from an existing codebase |
| `/arpinine-harness:at-review` | Refine | Improve clarity, scope, and measurability before execution |
| `/arpinine-harness:at-plan` | Plan | Produce `plan.md` and tasks from an approved spec |
| `/arpinine-harness:at-adr` | Decide | Create and manage Architecture Decision Records |
| `/arpinine-harness:at-eval` | Evaluate | Define, run, and benchmark evaluation |
| `/arpinine-harness:at-observe` | Evaluate | Record and review runtime observations |
| `/arpinine-harness:at-implement` | Execute | Implement with TDD and security review |
| `/arpinine-harness:at-audit` | Realign | Detect drift and trigger refinement |
| `/arpinine-harness:at-retro` | Learn | Extract lessons as compounding rules |
| `/arpinine-harness:at-status` | Govern | Project-wide governance overview |
| `/arpinine-harness:at-ask` | Any stage | Ask a named specialist with spec and plan as context |

---

## Delivery Loop

The workflow is a loop, not a checklist:

1. **Define** — product intent in `spec.md`
2. **Refine** — tighten before engineering starts
3. **Plan** — `plan.md` and tasks from the approved spec
4. **Decide** — consequential choices in ADRs before they become implicit
5. **Evaluate** — define metrics, thresholds, and scenarios
6. **Execute** — implement test-first
7. **Realign** — audit drift between spec, code, and evidence
8. **Repeat** — update artifacts when what you learn changes the work

---

## Agent Team

`/arpinine-harness:at` does not replace this team. It is the facade that decides which part of the team should lead next based on repo state and user intent.

Each command routes to the specialists that matter for that stage.

**Always on:**

| Agent | Responsibility |
|-------|---------------|
| `product-owner` | Spec honesty — scope, intent, acceptance criteria |
| `tech-architect` | Architecture decisions surfaced early, before they become code structure |
| `domain-linguist` | Bounded-context vocabulary enforced from spec through implementation naming |
| `tdd-guide` | Test-first discipline, task-aligned |
| `security-reviewer` | Security surface on every spec and plan |

**Scoped — activates only when the spec signals the domain:**

| Agent | Activates when spec involves |
|-------|------------------------------|
| `ai-engineer` | AI, LLMs, agent runtimes, or prompt-driven behavior |
| `devops` | Deployed services, secrets, CI/CD |
| `data-engineer` | Data pipelines, RAG, vector stores, ETL |
| `evaluation-governor` | Agentic or AI-assisted workflows needing quality gates |

---

## Shared Artifacts

| Artifact | Purpose |
|----------|---------|
| `spec.md` | What problem, for whom, how success is measured |
| `plan.md` | How the team intends to build it |
| `eval-plan.md` | Quality gate: metrics, thresholds, scenarios |
| `ADR-*.md` | Why key decisions were made |
| `drift-report.md` | Where code and intent have diverged |
| `observation artifacts` | Runtime evidence |
| `coordination/*.json` | Multi-assistant task leases |

---

## Multi-Team Coordination

Claude, Codex, and GitHub Copilot CLI can share the same governed workflow.

- both use the same `spec.md`, `plan.md`, ADRs, and eval artifacts
- task ownership is coordinated through lease-based claims so they don't collide
- `scripts/claim_task.py` atomically selects the next eligible task
- `check-task-claim.sh` blocks implementation edits unless the current team owns an active claim

---

## Hooks

Automatic checks fire on every file write:

| Hook | What it enforces |
|------|-----------------|
| `check-constitution.sh` | No tech leakage in `spec.md`, no hardcoded secrets |
| `check-architecture-readiness.sh` | Module boundaries and dependency rules must exist before implementation |
| `check-style-governance.sh` | Canonical style config must exist for the language |
| `check-task-claim.sh` | Current team must own an active task claim |
| `quick-drift-check.sh` | Lightweight spec-alignment pass after every write |

---

## Prerequisites

- A supported host: **Claude Code**, **Codex CLI**, or **GitHub Copilot CLI**
- **Python 3** — the governance hooks, lease scripts, and demos run on it
- **git** — required by the Codex installer (it does a sparse checkout)

## Installation

Install from GitHub with no build. Claude can install straight from the repo-root marketplace. Codex needs a Codex-only local marketplace root staged from the committed GitHub contents because this repo also carries the Claude marketplace manifest at the root.

> The marketplace is named `arpinine-harness-local` on every host. The `-local` suffix is just the registered marketplace id — you still install live from GitHub and update from GitHub. It is not a local-only build.

### Claude

In Claude Code:

```text
/plugin marketplace add arpinine/Arpinine-Harness
/plugin install arpinine-harness@arpinine-harness-local
```

Or from the terminal:

```bash
claude plugin marketplace add arpinine/Arpinine-Harness
claude plugin install arpinine-harness@arpinine-harness-local
```

Restart Claude Code. Update later with `/plugin marketplace update arpinine-harness-local`.

### Codex

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/arpinine/Arpinine-Harness/main/tools/release/install_codex_remote.sh)
```

Then **fully restart Codex** (the running client does not hot-load plugins).

The installer does a sparse Git checkout of only the Codex marketplace files,
stages them under `~/.codex/marketplaces/arpinine-harness-local-codex/`, then
runs:

```bash
codex plugin marketplace add <staged-local-root>
codex plugin add arpinine-harness@arpinine-harness-local
```

Use `REMOTE_REF=<tag|branch|sha>` to pin a version, or `GIT_REMOTE_URL=git@github.com:owner/repo.git`
for private-repo SSH access:

```bash
REMOTE_REF=v1.4.9 bash <(curl -fsSL https://raw.githubusercontent.com/arpinine/Arpinine-Harness/main/tools/release/install_codex_remote.sh)
```

> **Why not `codex plugin marketplace add arpinine/Arpinine-Harness`?** Codex resolves this multi-host repo against the root Claude marketplace manifest, so a direct root-level add installs the Claude payload instead of the Codex one. The installer stages a Codex-only marketplace root to avoid that conflict.
>
> **Access:** the installer clones the repo over HTTPS by default. For private repos, use an authenticated HTTPS URL or set `GIT_REMOTE_URL=git@github.com:owner/repo.git`.
>
> **Copilot** cannot install from the committed marketplace (it bakes machine-absolute hook paths at install time). Build a release bundle with `make release IMPLEMENTATION=copilot` and run the bundled `install.sh`. Maintainer build/release details: `make help`.

### Replace a pre-installed / local copy with the remote version

If you previously installed from a local directory or a `make install` build, remove it first so the host uses the always-updated GitHub marketplace instead of a stale local tree.

Claude — in Claude Code:

```text
/plugin uninstall arpinine-harness
/plugin marketplace remove arpinine-harness-local
/plugin marketplace add arpinine/Arpinine-Harness
/plugin install arpinine-harness@arpinine-harness-local
```

Or from the terminal:

```bash
claude plugin uninstall arpinine-harness                  # ignore "not found" if absent
claude plugin marketplace remove arpinine-harness-local   # ignore "not found" if absent
claude plugin marketplace add arpinine/Arpinine-Harness
claude plugin install arpinine-harness@arpinine-harness-local
```

Codex:

```bash
codex plugin remove arpinine-harness
codex plugin marketplace remove arpinine-harness-local
bash <(curl -fsSL https://raw.githubusercontent.com/arpinine/Arpinine-Harness/main/tools/release/install_codex_remote.sh)
```

Restart the host after switching.

### Stay on the latest version

The remote marketplace tracks `main`. Pull the newest published version anytime:

```text
/plugin marketplace update arpinine-harness-local
```

```bash
claude plugin marketplace update arpinine-harness-local
```

For Codex, rerun the installer so the staged local marketplace root is refreshed:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/arpinine/Arpinine-Harness/main/tools/release/install_codex_remote.sh)
```

Restart the host to load the updated plugin.

---

## Implementation Layout

```text
src/
  arpinine-harness-core/     # commands, agents, hooks, scripts, templates
  implementations/
    claude/                  # Claude implementation
    codex/                   # Codex plugin implementation
    copilot/                 # GitHub Copilot CLI implementation
tools/
  style/                     # canonical cross-team style configs
```

Build targets:

```bash
make assemble IMPLEMENTATION=<name>
make build IMPLEMENTATION=<name>
make delivery
```

---

## Archetypes

For new repos, `at-init` can scaffold a starter structure before governance setup. An archetype is more than a folder template — it seeds the structure, the boundary principles in your constitution, and the starter rules the hooks enforce from the first commit. Each archetype applies:

- **Directories** — a boundary-aware source layout (e.g. `src/domain/`, `src/tools/`, `evals/`, `tests/`)
- **`PROJECT_CONVENTIONS.md`** — written into the repo so intent is documented up front
- **Constitution principles** — boundary rules added to your constitution
- **Starter governance rules** — `HIGH`-severity rules the drift and architecture hooks check on every write

### `agent-app`

AI agent application with tools, domain, and evaluation support.

- Layout: `src/agents`, `src/tools`, `src/domain`, `src/observability`, `src/evaluation`, `evals`, `tests`
- Enforces:
  - `src/domain/` stays free of frameworks, runtimes, transport clients, and persistence imports
  - observability/evaluation SDKs (OpenTelemetry, Langfuse, DeepEval) stay inside `src/observability/` and `src/evaluation/`; everything else depends on the provider interfaces
  - providers are injected at the composition root — no module resolves its own

### `ml-pipeline`

Machine learning pipeline with feature engineering, model training, and evaluation.

- Layout: `src/pipelines`, `src/features`, `src/models`, `src/domain`, `data/raw`, `data/processed`, `notebooks`, `evals`, `tests`
- Enforces:
  - production code under `src/` never imports from `notebooks/` — notebooks stay exploratory
  - `data/raw/` is immutable after ingest; derived artifacts go to `data/processed/`
  - domain modules stay free of ML and dataframe framework imports

Skip archetypes when reversing an existing codebase — use `/at-bootstrap-from-code` instead, which infers structure and governance from what already exists.

---

## End-to-End Demos

Each demo covers the full loop: product request → governed spec → plan → implementation → eval → observation → ADR → drift audit. Pick the one that matches your runtime:

| Demo | Agent runtime behind the app boundary |
|------|----------------------------------------|
| `support-agent-demo` | Fake/stub adapter — no external dependencies |
| `support-agent-openai-demo` | Real OpenAI-backed adapter |
| `support-agent-openharness-demo` | [OpenHarness](https://github.com/HKUDS/OpenHarness) runtime |

Run any demo:

```bash
cd examples/end-to-end/support-agent-demo
python3 -m unittest discover -s app/tests
python3 app/eval/run_eval.py
```
