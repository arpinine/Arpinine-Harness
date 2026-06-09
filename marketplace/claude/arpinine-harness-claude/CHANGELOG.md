# Changelog

## [Unreleased]

### Added
- `make release IMPLEMENTATION=<impl>` — packages a self-contained, marketplace-addable GitHub release bundle in `dist/<impl>/release/`, separate from `assemble`/`build`/`install` (existing targets and their behavior are unchanged). Backed by `tools/release/package_release.sh`. The bundle rewrites the marketplace `source` to a bundle-relative path so consumers install without building. Claude and Codex bundles are fully portable (env-var / plugin-relative hook paths); the Copilot bundle restores the relocatable `__COPILOT_PLUGIN_INSTALL_PATH__` placeholder and ships `install.sh`, a one-command consumer installer that resolves hook paths to `~/.copilot/installed-plugins/...` on their machine. README documents the no-build "Install from a GitHub Release" procedure per host
- `make release-all` and `make release-publish` — build bundles for all three implementations, and (publish) create/update a GitHub Release with all three zips via the `gh` CLI. Backed by `tools/release/publish_release.sh`; tag defaults to `v<version>`, overridable with `TAG=`, draft via `DRAFT=1`. Guards on `gh` auth before doing any work
- `make publish-marketplace` — refreshes a committed, in-repo plugin marketplace so consumers can `marketplace add arpinine/Arpinine-Harness` directly from GitHub with no download or build (hybrid distribution). Backed by `tools/release/publish_marketplace.sh`: assembles the portable Claude and Codex trees into `marketplace/<impl>/` and writes the root `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` with bundle-relative sources. Refuses to publish any tree containing machine-absolute paths. Copilot is excluded by design (absolute hook paths are not portable) and remains zip-only. README documents the per-host install matrix (GitHub marketplace vs release zip vs source)

## [1.6.0] - 2026-06-09

### Added
- `fullstack-react-fastapi` archetype — stack-specific fullstack structure (React 18 + Vite + TypeScript frontend, Python 3.13+ FastAPI backend, AWS ECS Fargate + CDK) with `frontend/`, `backend/`, `iac/cdk`, and `docs` layout. Enforced by the shared pre-edit hook across claude/codex/copilot: route handlers in `backend/api/` stay thin (no DB/ORM access), the frontend never imports from `backend/` (HTTP API boundary), server state stays in React Query (Zustand stores reject `axios`/`fetch`/React Query), and AWS CDK is confined to `iac/cdk/` (no app↔infra cross-imports). The Pydantic↔Zod API-contract rule is a cross-file, same-commit invariant documented as a constitution principle and enforced at review (not the single-edit hook). Ships regression tests (listing, scaffold, one blocking case per enforced rule plus allow cases) and `README`, core `README`, and `docs/vibe-coder-process.md` entries. Complements the technology-agnostic `fullstack-app` for teams whose stack is settled

## [1.5.0] - 2026-06-09

### Added
- `fullstack-app` archetype — technology-agnostic fullstack structure (`src/backend`, `src/frontend`, `src/domain`, `src/db`, `src/observability`, `infra`, `evals`, `tests`). Fixes the layer *boundaries*, not the stack: frameworks appear only as examples in detection patterns, and the concrete technology is chosen per product and recorded in an ADR via the `at-plan` tech-architect. Enforced by the shared pre-edit hook across claude/codex/copilot: domain stays framework/transport/persistence/frontend-free, the frontend reaches the backend only through the API boundary, database drivers/ORM are confined to `src/db/`, and infrastructure-as-code is isolated in `infra/` with no app↔infra cross-imports. Ships regression tests and `README`/core `README` entries

## [1.4.9] - 2026-05-31

### Added
- Semantic drift detection (Layer 2) for `/at-audit`, gated behind an opt-in `--semantic` flag and governed by `ADR-0012`. Detects behavioral contradictions a structural check cannot see (e.g. spec says "rate-limit per user", code limits per IP). Never runs in the PostToolUse hook and never hard-blocks
- `scripts/semantic_drift_prep.py` — deterministic preparation that pairs each spec clause (`##` section) with the code **that clause** references (resolved from the clause body, so a Billing clause is not judged against Auth code), reusing `quick_drift_check.py` related-code resolution. Excerpt line numbers are absolute source lines, so judge citations point at real `file:line`. Judging is performed by the `/at-audit` agent via the new prompt template, keeping the deterministic and non-deterministic parts separated
- `skills/drift-detector/semantic-judge-prompt.md` — versioned LLM-as-judge prompt template. Output reuses the structural severity vocabulary (`CRITICAL`/`HIGH`/`MEDIUM`) with cited spec phrase and code `file:line`, so semantic and structural findings merge into one `/at-audit` report
- `src/implementations/copilot/` — GitHub Copilot CLI implementation overlay with `plugin.json`, marketplace metadata, Copilot-native hooks, and thin skill wrappers for the shared workflow
- Copilot hook adapter scripts that normalize Copilot `preToolUse` and `postToolUse` payloads to the shared governance check contract instead of forking the underlying workflow logic

### Fixed
- Copilot hook commands no longer resolve against the user's repository. Copilot runs command hooks with the working directory set to the repo root and exposes no plugin-root environment variable, so the previous bare `./scripts/...` commands in `src/implementations/copilot/hooks/hooks.json` pointed at files that do not exist in a consumer repo — the Copilot governance hooks would never fire after install (a functional regression that still passed the green build). Hook commands now use a `__COPILOT_PLUGIN_INSTALL_PATH__` placeholder that `make assemble` rewrites to the **durable installed-plugin directory** `~/.copilot/installed-plugins/<marketplace>/<plugin>` — where Copilot copies marketplace plugins on install and loads their hooks from — rather than the repo-local `dist/` tree. The installed plugin therefore survives `make clean`, repo moves, and build-tree changes (mirrors the Codex `__CODEX_PLUGIN_INSTALL_PATH__` → system-dir model). `make validate-structure IMPLEMENTATION=copilot` parses the assembled `hooks.json` and fails if any hook command is non-absolute, points outside the installed-plugin dir, references a script not shipped as an executable in the artifact, or still contains the unresolved placeholder. The install base is overridable via `COPILOT_PLUGIN_HOME`; the baked `$HOME` is resolved at assemble time, so assemble on the installing machine/user (same constraint as Codex). `${COPILOT_PLUGIN_DATA}` is a data dir, not the code dir, so it cannot reach bundled scripts
- Copilot enforcement gates no longer fail open. `hooks/hooks.json` previously pointed `check-style-governance`, `check-task-claim`, and `quick-drift-check` at the bare core scripts, which parse the Claude-shaped `tool_input.file_path`. Copilot sends `toolArgs.filePath`, so those scripts received an empty path and returned 0 (allow), silently disabling style, task-claim, and drift checks on Copilot. They now route through `copilot-check-style-governance.sh`, `copilot-check-task-claim.sh`, and `copilot-quick-drift-check.sh`, which normalize the payload first — restoring `ADR-0008` blocking-gate parity. `check-security-setup.sh` stays raw (it reads repo state, not the payload)
- Claude plugin manifest must NOT declare `hooks`. Claude Code auto-loads `hooks/hooks.json` from the plugin root; a `"hooks"` reference in `.claude-plugin/plugin.json` triggers a `Duplicate hooks file detected` load failure (`✘ failed to load`). The `make validate-structure IMPLEMENTATION=claude` check previously *required* the declaration — that requirement was wrong and is now inverted: validation asserts the Claude manifest does not declare `hooks` while `hooks/hooks.json` exists on disk. Codex and Copilot keep their explicit manifest hook declarations, which their runtimes require

### Changed
- `drift-detector` skill and `at-audit` command document the two-layer model (structural always-on + semantic opt-in) and record that embedding/cosine-similarity detection is rejected per `ADR-0012`
- `001-plugin-abstraction` spec/plan, `ADR-0005`, and the `009` evaluation plan/results now record Copilot as a first-class third implementation alongside Claude and Codex (FR-002 raised to "at least three"; validate-structure scenario + threshold added for Copilot)
- `Makefile` now supports `IMPLEMENTATION=copilot` for `assemble`, `register`, `install`, `uninstall`, and `validate-structure`, while keeping host-specific packaging under `src/implementations/copilot/`
- shared coordination identity detection now recognizes Copilot via `COPILOT_PLUGIN_ROOT`, and task-claim guidance now documents `copilot` as a valid team id

## [1.4.8] - 2026-05-21

### Fixed
- Codex marketplace registration now points at the durable system install dir. `src/implementations/codex/marketplace.json` uses a `__CODEX_PLUGIN_INSTALL_PATH__` placeholder that the `Makefile` assemble step rewrites to the absolute `$(CODEX_SYSTEM_PLUGIN_DIR)`. Previously the manifest used a repo-local `./dist/plugins/...` path, so any `make clean` or update cycle orphaned the installed reference and produced `Plugin arpinine-harness not found in marketplace arpinine-harness-local`

### Changed
- `make validate-structure IMPLEMENTATION=codex` now verifies the generated marketplace manifest exists, its `source.path` matches `$(CODEX_SYSTEM_PLUGIN_DIR)`, and no unresolved `__CODEX_PLUGIN_INSTALL_PATH__` placeholder remains — closing the validation gap that let the marketplace-orphan regression pass
- Build output is now isolated per implementation under `dist/<impl>` (`DIST_DIR := dist/$(IMPLEMENTATION)`). Previously both implementations shared a single `dist/` and `assemble` ran a full `clean`, so assembling one implementation wiped the other's installed marketplace target and produced `Marketplace arpinine-harness-local failed to load: cache-miss` (and the earlier `not found in marketplace`). Each implementation now cleans and registers only its own `dist/<impl>` subtree
- `/at` facade delegation now resolves the router's `/at-<name>` policy shorthand to the wrapping skill and invokes it through the skill mechanism instead of emitting a bare `/at-<name>` slash string, which the host rejected as `Unknown command`. Claude builds use the `arpinine-harness:at-<name>` skill id; Codex builds strip the namespace at assemble-time to the bare `at-<name>` skill name. Direct `/arpinine-harness:at-<name>` command invocation is unchanged

## [1.4.7] - 2026-05-21

### Fixed
- `/at` facade router invocation under Claude Code — command markdown now resolves `scripts/route_at.py` via `${CLAUDE_PLUGIN_ROOT}/scripts/route_at.py` instead of a bare relative path. Previously the LLM resolved the bare path against the user's target repo CWD, causing `Router unavailable` errors when running `/at` in any repo outside the plugin install dir
- Same plugin-root prefix applied to all shared-script invocations across `at-init.md`, `at-bootstrap-from-code.md`, `at-plan.md`, `at-implement.md`, `at-eval.md`, `templates/plan-template.md`, `state-inspector.md`, and the core README so the bug cannot recur through copy-paste of those references
- `test_at_facade_contract.py` updated to assert the new `${CLAUDE_PLUGIN_ROOT}`-prefixed invocation

### Changed
- Codex assemble step in `Makefile` now strips `${CLAUDE_PLUGIN_ROOT}/` from `*.md`, `*.json`, `*.sh`, and `*.py` files during build, since Codex resolves relative `scripts/...` paths from the plugin root and does not set `${CLAUDE_PLUGIN_ROOT}`. Single source of truth in core; per-impl rewrite happens at build time
- Source prose in commands and docs updated to explain the plugin-root convention and document the Codex assemble-time rewrite so the same content reads correctly in both installations

## [1.4.6] - 2026-05-21

### Added
- `/at` facade — single entry point that inspects repo state, applies `routing-policy.md` deterministically via `scripts/route_at.py`, explains the routing decision, and delegates to the correct `/at-*` command
- `scripts/route_at.py` — executable router backing the facade; combines inspector output with user intent to produce a normalized routing decision (route, confidence, reason, alternative, command class, confirmation mode)
- `scripts/inspect_state.py` — deterministic state inspector; emits normalized JSON facts about governance state consumed by the router
- `state-inspector.md` — contract defining the inspector output schema and derivation rules
- `routing-policy.md` — written routing policy defining hard gates, soft heuristics, confidence scoring, and command classes
- `/at-map` command — project-level decomposition; turns a broad goal into a clarified project brief and ordered feature backlog before feature specs are created
- `tests/test_inspect_state.py`, `tests/test_route_at.py`, `tests/test_at_facade_contract.py` — test suites covering inspector behavior, router routing scenarios, and facade contract conformance

### Changed
- `at.md` updated to consume router output from `scripts/route_at.py` instead of deriving routing from prose-only reasoning
- `at-init` now creates `.specify/map/` as part of the governed directory structure
- README simplified from 859 to 237 lines; `/at` facade promoted as the primary front door

## [1.4.5] - 2026-05-17

### Added
- `domain-linguist` added to `/at-ask` routing so it can be queried directly during active development alongside all other specialist agents
- `CODEX_PLUGIN_HOME` configurable Makefile variable (default `~/.agents`) controls where the Codex plugin is installed
- `make install IMPLEMENTATION=codex` and `make uninstall IMPLEMENTATION=codex` targets; Codex deployment is now a first-class operation alongside Claude

### Changed
- Codex plugin now installs to `$(CODEX_PLUGIN_HOME)/plugins/arpinine-harness` (system directory) instead of `dist/`; `make clean` no longer breaks a live Codex installation
- Codex marketplace manifest now references the installed system path as an absolute path instead of a relative `dist/` path
- `validate-structure IMPLEMENTATION=codex` now also verifies the system plugin directory and its hooks file
- README Codex install and update instructions updated to use `make install` / `make uninstall` + `make install`; order of Claude and Codex installs is no longer load-bearing
- `make help` now shows `IMPLEMENTATION=claude|codex`, `CODEX_PLUGIN_HOME` default, and Claude-only target note

### Removed
- Empty `reverse-diff-audit` stub directory (consolidated into `drift-detector` in a prior release)

### Added
- shared `src/arpinine-harness-core/` package plus `src/implementations/<assistant>/` overlays
- `src/implementations/codex/README.md` placeholder to reserve the future Codex implementation seam
- initial Codex plugin scaffold with `.codex-plugin/plugin.json`, repo marketplace metadata, and first workflow skills for `at-init`, `at-new`, `at-review`, and `at-plan`
- `/at-bootstrap-from-code` shared workflow for assessing an existing repo and seeding governed artifacts from implementation evidence
- `scripts/bootstrap_from_code.py` for assistant-agnostic codebase assessment and bootstrap recommendations
- `tests/test_bootstrap_from_code.py` coverage for API and agentic bootstrap signals
- `harness-governor` skill to enforce harness strategy for product-facing agent systems
- `## Harness Strategy` section in the plan template for harness choice, abstraction boundary, tool access, memory, permissions, and swap strategy
- `/at-observe` command for recording and reviewing runtime observation artifacts
- `templates/observation-template.md` and `templates/schemas/observation-schema.yaml`
- `examples/rules/harness/harness-001.md` as an example harness governance rule
- `scripts/check_dependencies.py` for machine-readable dependency validation
- `scripts/spec_status.py` for executable project-wide governance reports
- `product-owner` agent to keep business cases, acceptance criteria, plans, implementation, and drift resolution aligned with `spec.md`
- end-to-end support triage demo under `examples/end-to-end/support-agent-demo`

### Changed
- `bootstrap_from_code.py` now prunes ignored directories during traversal, validates invalid paths and empty repos explicitly, keeps timestamped assessment history, and exposes bounded sampling limits in the report
- bootstrap assessment now reads docs/test/git intent signals, detects monorepo service candidates, adds confidence-weighted agentic detection, and derives subdirectory-aware spec slugs
- build now assembles an assistant implementation package from shared core content plus implementation-specific metadata
- planning and implementation guidance now enforce harness design documentation before building product features on top of an agent runtime
- `harness-governor` now includes OpenHarness-specific checks for adapter isolation, approval flow, and session handling when OpenHarness is selected
- audit and governance rules now incorporate observation-driven drift checks for tool, permission, memory, and eval-coverage mismatches
- `check-architecture-readiness.sh` now blocks harness-based implementation work when `## Harness Strategy` is missing or still a placeholder
- `at-status` now reports harness strategy and observation state
- `at-retro` now asks harness-focused retrospective questions and produces harness-category rules
- `at-observe record` now captures raw data only; drift analysis happens in `review`
- dependency validation is now explicit during setup; Arpinine Harness validates `spec-kit`, harness, and eval tools instead of trying to install them during plugin installation
- `check-dependencies.sh` now supports script-backed JSON output through `check_dependencies.py`
- `quick_drift_check.py` now includes lightweight static conformance checks for harness import leakage and framework leakage into domain layers
- `quick_drift_check.py` now parses declared `## Module Boundaries` from `plan.md` and flags imports that violate planned dependency direction
- `at-status` and `at-audit` now start from script-backed outputs when those helpers are available
- spec review, planning, implementation, and audit flows now invoke the `product-owner` agent for product-intent alignment checks
- `spec_status.py` now treats `Result: PASS` as authoritative and avoids counting `ADR-INDEX.md` as an ADR

## [1.4.0] - 2026-04-22

### Added
- `rule-manager` skill to manage compounding machine-readable rules in `.specify/rules/`
- `rules/<category>/<rule-id>.md` format with frontmatter: `triggers`, `prevents`, `source-adr`, `evidence-project`, `severity`, `active`
- `/at-retro` command to extract lessons from completed work and persist them as rules
- `/at-status` command for project-wide governance overview and new team member onboarding (`--onboard` flag)
- `rules/` directory initialized by `/at-init`
- Example rules: `examples/rules/security/auth-001.md`, `examples/rules/architecture/arch-001.md`
- Machine-readable schemas: `templates/schemas/spec-schema.yaml`, `templates/schemas/adr-schema.yaml`
- AIN (AI-Nativeness) assessment section in `spec-template.md` with AIN target level, agent-callable operations, human-in-the-loop gates, and feedback channels

### Changed
- `/at-audit` now attributes each drift finding as PRECONDITION FAILURE (spec unclear) or POSTCONDITION FAILURE (implementation deviated from clear spec) before triggering ADR creation
- `/at-audit` now checks active rules via `rule-manager` before creating ADRs — known patterns reported as rule violations instead
- `drift-detector` skill now invokes `rule-manager` before ADR coverage check
- `at-audit` summary now includes attribution counts and rule violation count

## [1.3.0] - 2026-04-22

### Changed
- renamed project identity to `Arpinine Harness`
- renamed plugin/package to `arpinine-harness`
- renamed source directory from `src/spec-kit-automation-v1.0.0` to `src/arpinine-harness-v1.0.0`
- updated build and installation paths to produce `dist/arpinine-harness-v1.2.0.zip`

## [1.2.0] - 2026-04-22

### Added
- `architecture-governor` skill to enforce modular and clean architecture expectations during planning and implementation
- architecture-ready planning sections:
  - `## Module Boundaries`
  - `## Dependency Rules`
  - `## Testability By Boundary`
- `check-architecture-readiness.sh` pre-write gate to block implementation-path edits until architecture requirements exist in the governing plan

### Changed
- the workflow now treats architecture as a first-class concern alongside planning, evaluation, execution, and realignment
- constitution rules now require modular boundaries and isolation of business rules from framework and infrastructure concerns
- planning now requires explicit architecture sections before implementation can begin
- implementation guidance now sends work back into refinement when planned boundaries are broken without rationale
- `PreToolUse` now blocks implementation-path edits until architecture sections exist in the governing plan

## [1.1.0] - 2026-04-22

### Added
- `/at-eval` command for framework-agnostic evaluation planning, execution, and review
- `evaluation-governor` skill to enforce evaluation contracts for agentic systems
- `templates/eval-plan-template.md` for metrics, thresholds, datasets, execution commands, and pass/fail policy

### Changed
- the delivery workflow now includes an explicit evaluation stage
- planning now requires an evaluation strategy for agentic or AI-assisted work
- implementation now blocks completion on failing required evaluation
- audit now considers evaluation regressions and missing reruns
- plugin metadata and documentation now position evaluation as framework-agnostic rather than vendor-specific

## [1.0.1] - 2026-04-22

### Fixed
- `check-constitution.sh` now validates pending edit content from hook input instead of only inspecting the on-disk file
- ADR coverage model now requires explicit `covers:` linkage for drift items and planned decisions
- slash command prompts now define concrete workflows instead of one-line delegations

### Changed
- `quick-drift-check.sh` was upgraded from a latest-spec file-reference check to a lightweight spec-alignment hook
- `PostToolUse` now surfaces:
  - missing file references from specs
  - endpoint mismatch hints between spec and code
  - stale or missing eval result hints for agentic specs

## [1.0.0] - 2026-04-22

### Added
- initial plugin scaffold for a spec-driven team workflow on top of spec-kit
- commands:
  - `/at-init`
  - `/at-new`
  - `/at-plan`
  - `/at-implement`
  - `/at-adr`
  - `/at-audit`
  - `/at-review`
- agent roles:
  - `tech-architect`
  - `tdd-guide`
  - `security-reviewer`
- skills:
  - `adr-manager`
  - `drift-detector`
  - `constitution-enforcer`
  - `reverse-diff-audit`
- templates for:
  - spec
  - plan
  - ADR
  - constitution
- hook wiring for pre-write constitution validation and post-write drift checks
- ADR lifecycle management with `governs:` linkage and index maintenance
