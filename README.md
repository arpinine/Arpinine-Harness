# Arpinine Harness

A plugin for anyone building software with AI coding assistants who wants to ship what they intended, not just ship code.

When you build with AI, things move fast. Specs drift. Architecture decisions happen by accident. Secrets end up hardcoded. Arpinine Harness gives you a team of specialized agents — product, architecture, security, TDD, domain language, deployment, data, and evaluation — that show up at the right moments and block the wrong ones.

---

## Start Here

Use `/arpinine-harness:at` as the front door. Describe what you want. It inspects repo state, picks the right governed command, explains the choice, and delegates.

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

## Installation

There are three paths:
- **Install directly from GitHub (marketplace)** — Claude & Codex only. No download, no build, auto-updatable. See below.
- **Install from a GitHub Release** — any host, including Copilot. Download a bundle zip. No `make`. See "Install from a GitHub Release".
- **Install from source with `make`** — maintainers/contributors building locally. See "Install from source".

## Install directly from GitHub (marketplace)

Claude and Codex resolve hook paths portably (`${CLAUDE_PLUGIN_ROOT}` / plugin-relative), so the assembled plugin is committed in this repo and the host can install it straight from GitHub — no zip, no build.

### Claude

```text
/plugin marketplace add arpinine/Arpinine-Harness
/plugin install arpinine-harness@arpinine-harness-local
```

Update later with `/plugin marketplace update arpinine-harness-local`. Restart Claude Code.

### Codex

```bash
codex plugin marketplace add arpinine/Arpinine-Harness
codex plugin install arpinine-harness@arpinine-harness-local
```

Restart Codex. (If your Codex version cannot resolve the in-repo marketplace, use the GitHub Release zip below instead.)

> **Copilot is not available this way.** Copilot bakes machine-absolute hook paths at install time, which cannot be committed portably — use the GitHub Release zip + `install.sh` below.

## Install from a GitHub Release

Each release attaches a self-contained bundle per host: `arpinine-harness-<impl>-v<version>.zip`. Download the one for your assistant, then add it as a local marketplace and install.

### Claude (no build)

```bash
# 1. Download + extract the claude bundle from the GitHub Release
unzip arpinine-harness-claude-v<version>.zip -d ~/arpinine-harness

# 2. In Claude Code, add the extracted folder as a marketplace and install
/plugin marketplace add ~/arpinine-harness/arpinine-harness-claude-v<version>
/plugin install arpinine-harness@arpinine-harness-local
```

Restart Claude Code. Claude resolves hook paths via `${CLAUDE_PLUGIN_ROOT}` at runtime, so the bundle is fully portable across machines.

### Codex (no build)

```bash
unzip arpinine-harness-codex-v<version>.zip -d ~/arpinine-harness
codex plugin marketplace add ~/arpinine-harness/arpinine-harness-codex-v<version>
codex plugin install arpinine-harness@arpinine-harness-local
```

Restart Codex. Codex hook commands are plugin-relative, so the bundle is portable.

### Copilot (no build, one install command)

GitHub Copilot CLI runs hooks from the repo-root working directory and exposes no plugin-root variable, so hook paths must be absolute to the install dir — which is machine-specific. The bundle ships a placeholder plus a one-shot installer that resolves it on your machine:

```bash
unzip arpinine-harness-copilot-v<version>.zip -d ~/arpinine-harness
cd ~/arpinine-harness/arpinine-harness-copilot-v<version>
./install.sh          # resolves hook paths to ~/.copilot/installed-plugins/..., then registers + installs
```

Restart GitHub Copilot CLI. (Override the base dir with `COPILOT_PLUGIN_HOME=/custom/.copilot ./install.sh`.)

> Maintainers build these bundles with `make release IMPLEMENTATION=<impl>` (separate from `make assemble`/`build`); the zip lands in `dist/<impl>/release/`. To build all three at once and publish them to a GitHub Release in one step (requires an authenticated `gh` CLI):
> ```bash
> make release-all                 # build all bundles, no upload
> make release-publish             # build all + create/update the GitHub Release
> make release-publish TAG=v1.4.9 DRAFT=1   # explicit tag, draft release
> ```

## Install from source

### Claude

```bash
make install IMPLEMENTATION=claude
```

To update:

```bash
make uninstall IMPLEMENTATION=claude
make install IMPLEMENTATION=claude
```

Restart Claude Code after install.

### Codex

```bash
make install IMPLEMENTATION=codex
```

To install to a custom plugin home:

```bash
make install IMPLEMENTATION=codex CODEX_PLUGIN_HOME=/path/to/.agents
```

To update:

```bash
make uninstall IMPLEMENTATION=codex
make install IMPLEMENTATION=codex
```

Restart Codex after install.

### Copilot

```bash
make install IMPLEMENTATION=copilot
```

To update:

```bash
make uninstall IMPLEMENTATION=copilot
make install IMPLEMENTATION=copilot
```

Restart GitHub Copilot CLI after install.

### Validate before installing

```bash
make validate-structure IMPLEMENTATION=claude
make validate-structure IMPLEMENTATION=codex
make validate-structure IMPLEMENTATION=copilot
```

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

For new repos, `at-init` can scaffold a starter structure before governance setup:

- `agent-app` — agent workflows, tool orchestration, runtime adapters
- `ml-pipeline` — data ingestion, feature transforms, model training, evaluation

Skip archetypes when reversing an existing codebase.

---

## End-to-End Demo

```text
examples/end-to-end/support-agent-demo/
```

Covers the full loop: product request → governed spec → plan → implementation → eval → observation → ADR → drift audit.

```bash
cd examples/end-to-end/support-agent-demo
python3 -m unittest discover -s app/tests
python3 app/eval/run_eval.py
```
