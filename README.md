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
| `/arpinine-harness:at-report-costs` | Evaluate | Report token consumption and cost by model from recorded telemetry |
| `/arpinine-harness:at-report-harness-costs` | Evaluate | Report Arpinine Harness delivery cost by command, host, and model |
| `/arpinine-harness:at-report-total-costs` | Evaluate | Report separated product/runtime and harness subtotals plus a combined total |
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
| `observation artifacts` | Runtime evidence; source for product/runtime cost reports |
| `coordination/*.json` | Multi-assistant task leases |
| `harness-usage/` | Local-only (gitignored) harness delivery-cost ledger; source for harness and total cost reports |

---

## Multi-Team Coordination

Claude, Codex, and GitHub Copilot CLI can run the **same** Arpinine Harness against the **same** repository at the same time. Each assistant is a distinct *team* working from one shared source of truth — and the harness keeps them from stepping on each other.

This is what lets a developer run several coding assistants in parallel and route work to whichever one is strongest for the job: planning and brainstorming on one team, implementation on another, evaluation on a third. The coordination layer is what makes that safe instead of chaotic.

### One source of truth, many assistants

Every team reads and writes the same governance artifacts — there is no per-assistant fork of the plan:

- the same `spec.md`, `plan.md`, ADRs, and eval artifacts
- the same constitution, rules, and hooks
- the same drift reports and runtime observations

Because intent lives in shared files rather than in any one assistant's context, Claude can plan a feature, Codex can implement it, and Copilot can evaluate it — each picking up exactly where the last left off.

### Team identity

Each assistant is automatically resolved to a team id (`claude`, `codex`, or `copilot`) from its host runtime unless `ARPININE_HARNESS_TEAM_ID` is already set. When that environment variable is present, the harness treats it as the canonical team identity and uses host detection only as fallback.

### Task ownership through leases

Work is divided into tasks in `plan.md`. A task can optionally be reserved for one team with a tag:

```markdown
- [ ] TASK-014: Build the ingestion pipeline [team: codex]
- [ ] TASK-015: Wire up the eval harness   [team: claude]
```

Untagged tasks are open to any team; tagged tasks are eligible only for that team. Ownership is then coordinated through **lease-based claims** so two assistants never grab the same task:

- **`scripts/claim_task.py`** atomically selects the next eligible task. It takes a file lock on a per-spec registry (`coordination/*.json`), then claims the first task that is unstarted, eligible for the calling team, and not already under a live lease held by someone else. The claim records who owns it and a `lease_until` expiry (default **30 minutes**).
- Leases **expire**. If a team crashes or walks away, its claim lapses and the task becomes available again — no manual cleanup. Tightening a task's `[team: …]` tag also revokes a claim held by a now-ineligible team.
- **`check-task-claim.sh`** runs as a pre-edit hook. It blocks edits to implementation paths (`src/`, `lib/`, `app/`, `packages/`, `services/`, `internal/`, `cmd/`, `tests/`) unless the current team owns an **active, unexpired** claim on a task under the governing spec. No claim, no code change.

### Why it matters

The result is a shared, governed work queue across heterogeneous assistants. The developer picks the best assistant per kind of work, assigns it a team, and lets the lease protocol arbitrate who edits what — coordinated, collision-free, and always anchored to one spec.

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
| `record-harness-usage.sh` | Records harness delivery cost/tokens to the local `harness-usage/` ledger after every write (incomplete when the host exposes no telemetry — never faked) |

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

The repository is private, so the bootstrap is fetched with the authenticated
`gh` CLI (an unauthenticated `raw.githubusercontent.com` fetch 404s on a private
repo). Run `gh auth login` first; `gh auth setup-git` also lets the installer's
HTTPS clone authenticate without a separate `GIT_REMOTE_URL`.

```bash
gh api repos/arpinine/Arpinine-Harness/contents/tools/release/install_codex_remote.sh \
  -H "Accept: application/vnd.github.raw" | bash
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
REF=v1.7.0
gh api "repos/arpinine/Arpinine-Harness/contents/tools/release/install_codex_remote.sh?ref=$REF" \
  -H "Accept: application/vnd.github.raw" | REMOTE_REF=$REF bash
```

> **Why not `codex plugin marketplace add arpinine/Arpinine-Harness`?** Codex resolves this multi-host repo against the root Claude marketplace manifest, so a direct root-level add installs the Claude payload instead of the Codex one. The installer stages a Codex-only marketplace root to avoid that conflict.
>
> **Access:** the installer clones the repo over HTTPS by default. For private repos, use an authenticated HTTPS URL or set `GIT_REMOTE_URL=git@github.com:owner/repo.git`.
>
> **Copilot** cannot install from the committed marketplace (it bakes machine-absolute hook paths at install time). It installs from a release zip instead — see **Copilot** below.

### Copilot

Copilot installs from a release zip, not the marketplace: it runs hooks from the
repo-root working directory with no plugin-root env var, so hook paths must be
absolute and are baked into `hooks.json` at install time by the bundled
`install.sh`. The repo is private, so download the asset with the authenticated
`gh` CLI (`gh auth login` first):

```bash
gh release download v1.7.0 -R arpinine/Arpinine-Harness -p '*copilot*.zip'
unzip arpinine-harness-copilot-v1.7.0.zip -d arpinine-harness-copilot
cd arpinine-harness-copilot && ./install.sh
```

`install.sh` resolves hook paths to `~/.copilot/installed-plugins/arpinine-harness-local/arpinine-harness`, registers the marketplace from the extracted bundle, and installs the plugin. Restart Copilot afterward. Override the install base with `COPILOT_PLUGIN_HOME` if your Copilot home is non-default.

To **update**, remove the old plugin, then repeat with the newer tag:

```bash
copilot plugin remove arpinine-harness                       # ignore "not found"
copilot plugin marketplace remove arpinine-harness-local     # ignore "not found"
gh release download <newer-tag> -R arpinine/Arpinine-Harness -p '*copilot*.zip'
unzip arpinine-harness-copilot-<newer-tag>.zip -d arpinine-harness-copilot
cd arpinine-harness-copilot && ./install.sh
```

> Maintainer: build the bundle with `make release IMPLEMENTATION=copilot` and publish it with `make release-publish TAG=vX.Y.Z`. Details: `make help`.

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
gh api repos/arpinine/Arpinine-Harness/contents/tools/release/install_codex_remote.sh \
  -H "Accept: application/vnd.github.raw" | bash
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
gh api repos/arpinine/Arpinine-Harness/contents/tools/release/install_codex_remote.sh \
  -H "Accept: application/vnd.github.raw" | bash
```

Copilot does not track the marketplace — pull the newer release zip and re-run `install.sh` (see the **Copilot** update steps above).

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

Archetypes are auto-discovered — `at-init` lists whatever ships in `archetypes/`, and the same `HIGH` rules are enforced identically across Claude, Codex, and Copilot. List them any time with `scaffold_archetype.py --list`.

### Choosing an archetype

| Archetype | Use when | Stack |
|-----------|----------|-------|
| [`agent-app`](#agent-app) | Building an LLM/agent app with tools and evals | provider-agnostic |
| [`ml-pipeline`](#ml-pipeline) | Building an ML/data pipeline with training and notebooks | provider-agnostic |
| [`fullstack-app`](#fullstack-app) | Building a web app, stack not yet decided | technology-agnostic — choose per product via ADR |
| [`fullstack-react-fastapi`](#fullstack-react-fastapi) | Building a web app on the React/FastAPI/AWS stack | React 18 + Vite + TS / FastAPI / ECS Fargate + CDK |

The two fullstack archetypes are a pair: `fullstack-app` fixes the *layer boundaries* and leaves the technology open; `fullstack-react-fastapi` is the same shape with one concrete stack already chosen. Start agnostic if the stack is still in flux; pick the stack-specific one once it is settled.

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

### `fullstack-app`

Technology-agnostic fullstack application with backend, frontend, domain, persistence, and infrastructure layers. The archetype fixes the *layer boundaries*, not the stack — pick languages, frameworks, datastore, and IaC tool per product and record them in an ADR.

- Layout: `src/backend`, `src/frontend`, `src/domain`, `src/db`, `src/observability`, `infra`, `evals`, `tests`
- Enforces:
  - `src/domain/` stays free of web frameworks, transport clients, persistence, and frontend/UI imports
  - database drivers and ORM sessions stay inside `src/db/`; backend and domain depend on repository abstractions
  - `src/frontend/` talks to the backend only through the published API boundary — it never imports `src/backend/`, `src/domain/`, or `src/db/`
  - infrastructure-as-code stays in `infra/`; application code never imports IaC constructs and vice versa

### `fullstack-react-fastapi`

Stack-specific fullstack web app — React 18 + Vite + TypeScript frontend, Python 3.13+ FastAPI backend, AWS ECS Fargate + CDK. Use this when the stack is settled; use `fullstack-app` when you want a stack-neutral layout.

- Layout: `frontend/src/{components,pages,hooks,stores,services}`, `backend/{api,core,data,prompts,tests}`, `iac/cdk`, `docs`
- Stack: React 18 + Vite + TypeScript, shadcn/ui v4, Tailwind v4, TanStack React Query v5, Zustand, FastAPI, Pydantic v2, Zod, pytest + Vitest, AWS ECS Fargate + CDK
- Enforces (pre-edit hook):
  - FastAPI route handlers in `backend/api/` stay thin — no DB/ORM access; logic lives in `backend/core/`
  - the frontend never imports from `backend/` — data crosses the HTTP API boundary
  - React Query owns server state; Zustand stores cannot hold `axios`/`fetch`/React Query
  - AWS CDK stays in `iac/cdk/`; app code never imports CDK and infra never imports `backend/core/`
  - (review-only) Pydantic ↔ Zod contract changes ship in the same commit

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
