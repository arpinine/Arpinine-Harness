# Plan: AgentAlign Core Workflow

## Governing Spec
`.specify/specs/002-agent-align-core-workflow/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| PreToolUse hooks as hard enforcement gates (blocking, not advisory) | Advisory warnings are ignorable; blocking gates enforce the governance contract without relying on developer discipline | Proposed — ADR-0004 |
| Plain-text version-controlled artifact store under `.specify/` | Artifacts must be reviewable, diffable, and trustworthy; a database introduces infrastructure dependency and breaks NFR-006 (session independence) | Proposed — ADR-0005 |
| Specialized role-based agent team (4 agents, each with one concern) | A single general agent cannot maintain distinct role boundaries (product vs. architecture vs. TDD vs. security) across a multi-stage workflow | Proposed — ADR-0006 |
| Commands are the orchestration layer; agents and skills contain no side effects | Keeps agents and skills reusable across commands; a command can invoke product-owner + tdd-guide independently without coupling their concerns | Consequence of ADR-0006 — no separate ADR |
| Enforcement scripts are stateless exit-code validators | Hooks expect exit 0 (allow) or exit 1 (block); stateful scripts would produce inconsistent hook behavior | Consequence of ADR-0004 — no separate ADR |

## Architecture

Seven layers with a single direction of dependency (read the artifact store; commands write it):

```
commands/at-*.md        ← workflow orchestration; one command per stage
agents/*.md             ← role-based reasoning (product-owner, tech-architect, tdd-guide, security-reviewer)
skills/*/SKILL.md       ← reusable capabilities (drift-detector, adr-manager, architecture-governor, etc.)
hooks/hooks.json        ← wires enforcement scripts to Edit/Write tool events
scripts/*.sh / *.py     ← stateless gate validators (constitution, architecture readiness, drift)
templates/              ← passive scaffolding for spec.md, plan.md, ADR, eval-plan, observation
templates/schemas/      ← YAML structural contracts (adr-schema, spec-schema, observation-schema)

.specify/               ← shared artifact store (version-controlled plain text)
  specs/<slug>/         ← spec.md, plan.md, drift-report.md per feature
  adr/                  ← ADR-NNNN-*.md + ADR-INDEX.md
  evals/<slug>/         ← eval-plan.md, latest-results.md
  observations/<slug>/  ← latest-observation.md, trace.json
  rules/                ← machine-readable compounding rules from retros
```

Commands orchestrate the full governance loop: `at-init` → `at-new` → `at-review` → `at-plan` → `at-adr` → `at-eval` → `at-observe` → `at-implement` → `at-audit` → `at-retro`. Each command is independently invocable (NFR-001).

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| `commands/` | Orchestrate each governance stage; invoke agents, skills, and templates; write artifacts | Artifact store (read), templates (read), agents (invoke), skills (invoke) | Duplicate agent or skill reasoning inline |
| `agents/` | Role-based reasoning: validate business case, enforce TDD, identify ADR candidates, review security | Artifact store (read) | Write artifacts; maintain session state; execute file-system changes |
| `skills/` | Reusable single-concern capabilities invoked by one or more commands | Artifact store (read) | Duplicate logic from other skills; depend on invocation order |
| `hooks/hooks.json` | Wire enforcement scripts to tool use events (PreToolUse, PostToolUse) | Scripts (reference by path) | Contain logic; only reference scripts |
| `scripts/` | Stateless validation; read artifacts; return exit codes for hook dispatch | Artifact store (read), schemas (read) | Write artifacts; maintain state between invocations |
| `templates/` | Passive document scaffolding | Nothing | Be modified at runtime |
| `templates/schemas/` | Structural contracts for artifact validation | Nothing | Be modified at runtime |
| `.specify/` | Shared artifact store; the ground truth for governance state | Nothing (it is the sink) | Be generated from non-command sources |

## Dependency Rules

- `commands/` MUST NOT duplicate reasoning that belongs to an agent or skill.
- `agents/` MUST NOT write to `.specify/`. Agents return analysis; commands act on it.
- `skills/` MUST be invocable in any order and from any command without requiring prior state from another skill.
- `scripts/` MUST be stateless: given the same artifact store contents, a script MUST return the same exit code.
- `hooks/hooks.json` MUST NOT contain logic; it references scripts by path only.
- `templates/` and `templates/schemas/` MUST NOT be written at runtime. They are read-only source artifacts.
- Dependency direction: `commands` → `agents` / `skills` / `scripts` / `templates` → artifact store. No layer below commands writes to the artifact store.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| `at-init` command (AC-001) | Functional | Delete `.specify/`; invoke at-init; assert full directory structure and constitution file exist |
| `at-new` command (AC-002) | Functional | Invoke at-new; assert spec.md contains user stories, requirements, ACs, out-of-scope, Related ADRs sections |
| `at-review` command (AC-003) | Functional | Write a spec with vague ACs; invoke at-review; assert ACs are rewritten and open questions documented |
| `at-plan` command (AC-004) | Functional | Invoke at-plan on an approved spec; assert plan.md contains Module Boundaries, Dependency Rules, Testability By Boundary |
| `at-adr new` command (AC-005) | Functional | Invoke at-adr new; assert ADR file created, ADR-INDEX.md updated, frontmatter fields set |
| `at-audit` command (AC-009, AC-010) | Functional | Introduce a deliberate spec/code divergence; invoke at-audit; assert report contains severity classification and routing decision |
| `at-retro` command (AC-011) | Functional | Invoke at-retro; assert at least one file created under `.specify/rules/` with machine-readable structure |
| `at-status` command (AC-012) | Functional | Invoke at-status; assert output contains AC coverage, drift state, ADR coverage, eval state, arch sections, harness, observations per spec |
| Architecture readiness hook (AC-007) | Integration | Attempt to edit a file under `src/` with a plan.md missing Module Boundaries; assert PreToolUse hook blocks the edit and names the missing section |
| Constitution hook | Integration | Attempt to edit a spec file with an implementation detail; assert PreToolUse hook detects and reports the violation |
| Enforcement scripts | Unit | Pass mock JSON inputs to `check-architecture-readiness.sh` and `check-constitution.sh`; assert exit 0 for valid state, exit 1 for violations |
| Artifact store independence (NFR-006) | Structural | Confirm each command reads only `.specify/` artifacts; no command requires in-memory state from a prior command invocation |

## Harness Strategy

N/A — the core workflow is not a harness-based product feature. The `harness-governor` skill governs harness use in downstream product applications; it is not a dependency of the workflow itself.

## Tasks

### Verification (retroactive — implementation already exists)
- [ ] TASK-001: Verify AC-001 — delete `.specify/` in a test project; run `/agent-align:at-init`; confirm all directories and constitution file created
- [ ] TASK-002: Verify AC-002 — run `/agent-align:at-new test-feature`; confirm spec.md contains all required sections
- [ ] TASK-003: Verify AC-007 — attempt to edit a `src/` file with plan.md missing Module Boundaries section; confirm hook blocks with named reason
- [ ] TASK-004: Verify AC-009/AC-010 — introduce a deliberate drift item; run `/agent-align:at-audit`; confirm CRITICAL/HIGH/MEDIUM classification and routing
- [ ] TASK-005: Verify AC-011 — run `/agent-align:at-retro`; confirm a rule file appears under `.specify/rules/`
- [ ] TASK-006: Verify AC-012 — run `/agent-align:at-status`; confirm all dimensions (AC coverage, drift, ADRs, eval, arch, harness, obs) present
- [ ] TASK-007: Unit-test enforcement scripts — pass mock inputs with known violations; assert exit 1 with correct message; pass valid inputs; assert exit 0
- [ ] TASK-008: Confirm each skill is invocable independently (invoke `drift-detector` and `adr-manager` without prior session state)

### Open question resolution
- [ ] TASK-009: Decide OQ-001 — is `/agent-align:at-review` mandatory (hook-enforced before plan) or advisory? Update hooks.json if mandatory
- [ ] TASK-010: Decide OQ-004 — do compounding rules from at-retro auto-promote to hook-level blockers or remain advisory? Update rule-manager skill if auto-promote

### ADR creation
- [ ] TASK-011: Create ADR-0004 for hook-based enforcement gate decision
- [ ] TASK-012: Create ADR-0005 for plain-text version-controlled artifact store
- [ ] TASK-013: Create ADR-0006 for specialized role-based agent team

## Evaluation Strategy

Not applicable. The core workflow is not an agentic product system with measurable output metrics. Verification is functional (does the command produce the required artifact with the required structure?) and integration (does the hook block correctly?).

| Dimension | Check | Method |
|-----------|-------|--------|
| Command output correctness | TASK-001 through TASK-006 | Manual functional verification |
| Hook enforcement | TASK-003, TASK-007 | Integration test + unit test |
| Artifact store independence | TASK-008 | Structural check |

## Security

- No credentials, network calls, or user-supplied data processed by the plugin commands themselves
- Enforcement scripts receive tool-use payloads (file paths and content) via stdin — inputs are sandboxed to local filesystem operations; no exec of user content
- `check-architecture-readiness.sh` and `check-constitution.sh` parse file paths from hook payloads; paths are validated against known prefixes before filesystem access
- Rules in `.specify/rules/` are read by enforcement scripts; malformed rule files cause script to exit 0 (fail open) — appropriate for a governance tool, not a security gate

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Hook enforcement scripts fail silently (exit 0 on unexpected input) | Medium | TASK-007: unit-test with malformed inputs; assert graceful exit 0 with no false blocks |
| Commands duplicate agent reasoning over time, eroding separation | Medium | Architecture-governor check during at-plan; flag in at-audit if command body grows beyond orchestration |
| OQ-001 resolved incorrectly — at-review advisory leads to specs reaching plan stage without measurability check | Medium | TASK-009: make the decision explicit; document in spec and enforce via hook if mandatory |
| OQ-004 resolved incorrectly — auto-promoting rules to hook blockers without review creates false positives | Low | Require explicit promotion step (human-reviewed, not automatic); document in rule-manager skill |
| Artifact store grows without pruning — drift reports, stale observations accumulate | Low | at-status surfacing stale artifacts is sufficient for now; automated cleanup is out of scope |

## ADRs Created During Planning

No ADRs created yet — three are proposed and should be created next:
- **Proposed ADR-0004**: Hook-based enforcement as the implementation gate mechanism — governs FR-012, AC-007
- **Proposed ADR-0005**: Plain-text version-controlled artifact store under `.specify/` — governs NFR-002, NFR-006
- **Proposed ADR-0006**: Specialized role-based agent team rather than single general agent — governs FR-013, AC-008
