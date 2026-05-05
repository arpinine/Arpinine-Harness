# Agent Application Checklist

Steps to create a governed agent application using Arpinine Harness. Follow in order — each stage gates the next.

---

## Stage 1 — Setup

- [ ] Install the Arpinine Harness plugin in Claude Code
- [ ] Run `/arpinine-harness:at-init` from the project root
  For a brand-new repo, optionally scaffold the `agent-app` archetype during init before drafting the first spec.
  - Confirms `.specify/` structure exists
  - Records `.specify/archetype.json` if an archetype is selected
  - Extends the constitution with archetype-specific invariants
  - Validates specification provider
  - Sets up `adr/`, `specs/`, `evals/`, `observations/`, `rules/`, `coordination/`
  - Seeds starter archetype rules and shared hook enforcement
  - Installs pre-commit security hooks
- [ ] Verify `scripts/check-dependencies.sh` passes (Python 3.10+, provider configured)
- [ ] If using a real harness runtime: confirm it is installable (`pip install openharness-ai` or equivalent)

---

## Stage 2 — Spec

- [ ] Run `/arpinine-harness:at-new` with the feature description
  - Output: `.specify/specs/<slug>/spec.md`
- [ ] Confirm `spec.md` contains:
  - [ ] Problem statement
  - [ ] User value
  - [ ] Scope (in and out)
  - [ ] Measurable acceptance criteria (AC-01, AC-02 …)
- [ ] Run `/arpinine-harness:at-review` to tighten clarity and scope
  - `product-owner` agent verifies business case and acceptance criteria
- [ ] Confirm spec does NOT contain implementation detail — product intent only

---

## Stage 3 — Plan

- [ ] Run `/arpinine-harness:at-plan <slug>`
- [ ] Confirm `plan.md` contains all required sections:
  - [ ] `## Module Boundaries` — which module owns what, no overlapping responsibilities
  - [ ] `## Dependency Rules` — direction of dependencies explicit (domain ← application ← adapter)
  - [ ] `## Testability By Boundary` — each boundary has a named test type and isolation strategy
  - [ ] `## Technical Decisions` — key choices listed with rationale and ADR reference
  - [ ] `## Tasks` — task list with IDs, checkboxes unchecked

### Harness-specific plan sections (mandatory when using an agent runtime)

- [ ] `## Harness Strategy` is present and complete:
  - [ ] Why a harness is needed (not just a single LLM call)
  - [ ] Which runtime is selected (e.g. OpenHarness, LangGraph, custom)
  - [ ] Product abstraction boundary named (interface class and file path)
  - [ ] Tool access model: explicit allowlist, each tool justified
  - [ ] Memory/state model: scope declared, reset condition named
  - [ ] Permission and safety model: which actions require approval, callback pattern described
  - [ ] Swap strategy: what changes if the harness is replaced (must be adapter only)
- [ ] If no harness is needed, `## Harness Strategy` is still present and its body is exactly an explicit `N/A` rationale rather than removing or renaming the section
- [ ] `## AI Design Decisions` is present if the spec uses LLMs or agent runtimes:
  - [ ] Model named and version pinned
  - [ ] System prompt defined or referenced
  - [ ] Context budget declared
  - [ ] Agent topology described (single vs multi-agent)
  - [ ] Failure modes identified (hallucination, tool misuse, context overflow)
- [ ] `## Evaluation Strategy` links to `eval-plan.md`
- [ ] Harness-specific evaluation lives in `## Evaluation Strategy` and `eval-plan.md`, not as an extra row inside `## Harness Strategy`
- [ ] If deployed service: `## Deployment Strategy` present
- [ ] If data pipeline or RAG: `## Data Pipeline` present

### Plan agent sign-offs (fired automatically by `/at-plan`)

- [ ] `product-owner` confirms plan preserves spec business case
- [ ] `architecture-governor` confirms module boundaries and dependency direction
- [ ] `harness-governor` confirms all harness controls documented (fires when harness named)
- [ ] `ai-engineer` confirms model, prompting strategy, failure modes (fires when LLM used)
- [ ] `tech-architect` has surfaced ADR candidates for consequential decisions

---

## Stage 4 — Architecture Decisions

- [ ] Run `/arpinine-harness:at-adr new "<title>"` for each consequential decision:
  - [ ] Harness runtime selection (always required when harness named in plan)
  - [ ] Model selection (cost/capability tradeoff)
  - [ ] Agent topology (single vs multi-agent, orchestration pattern)
  - [ ] Context management strategy (if non-default)
  - [ ] Any decision that would be hard to reverse or explain later
- [ ] Each ADR contains:
  - [ ] `governs:` pointing to the spec path
  - [ ] `covers:` with a stable decision key (e.g. `decision:001-slug:harness-boundary`)
  - [ ] Status: Accepted
  - [ ] Context, Decision, Consequences, Alternatives Considered
- [ ] `ADR-INDEX.md` updated

---

## Stage 5 — Evaluation Design

- [ ] Run `/arpinine-harness:at-eval plan <slug>`
- [ ] Confirm `eval-plan.md` contains:
  - [ ] At least 3 required scenarios covering representative inputs
  - [ ] Metrics and thresholds for each dimension
  - [ ] Execution command (`benchmark command`)
  - [ ] Baseline artifact path

### Harness-specific eval metrics (mandatory when harness named)

- [ ] Pass rate threshold defined (`>= 1.00` recommended)
- [ ] Approval event present: `100%` scenarios
- [ ] Memory scope: session-only verified `100%`
- [ ] Tool containment: only allowlisted tools fire `100%`
- [ ] Harness-specific failure modes covered (tool misuse, approval bypass, runtime recovery)
- [ ] Latency P95 threshold set

---

## Stage 6 — Implementation

- [ ] Run `/arpinine-harness:at-implement <slug>`
- [ ] For each task: claim → RED (failing test) → GREEN (minimal impl) → REFACTOR → release
- [ ] Confirm adapter boundary enforced:
  - [ ] Harness SDK imported only in `adapters/` layer
  - [ ] Domain and application code have zero harness imports
  - [ ] `quick_drift_check.py` (PostToolUse hook) shows no harness import leakage
- [ ] Confirm tool allowlist:
  - [ ] `ToolRegistry` registers only declared tools
  - [ ] No undeclared tools reachable at runtime
- [ ] Confirm memory scope:
  - [ ] Session reset called after each agent invocation
  - [ ] No persistent cross-session state written
- [ ] Confirm approval flow:
  - [ ] Write actions emit `permission_check` event before completing
  - [ ] Approval callback tested (approved and denied paths)
- [ ] `security-reviewer` sign-off before completion:
  - [ ] No hardcoded secrets or API keys
  - [ ] All credentials read from environment
  - [ ] No shell, filesystem, or email tools registered unless explicitly in allowlist
- [ ] `devops` sign-off if deployed service:
  - [ ] `.env` in `.gitignore`
  - [ ] Deployment path implementable as written

---

## Stage 7 — Observation and Evaluation

- [ ] Run `/arpinine-harness:at-observe review <slug>` after implementation
- [ ] Confirm observation trace contains expected event sequence per scenario:
  - [ ] `tool_call` events match allowlist
  - [ ] `permission_check` event present before any write completion
  - [ ] `memory_write` events have `scope: session`
- [ ] Run `/arpinine-harness:at-eval run <slug>` (confirm before executing)
- [ ] Confirm all required thresholds pass:
  - [ ] Pass rate `>= 1.00`
  - [ ] Approval check rate `= 1.00`
  - [ ] Memory scope rate `= 1.00`
  - [ ] Tool containment `= 1.00`
  - [ ] Latency P95 within threshold
- [ ] Compare against baseline — no regressions
- [ ] If any threshold fails: attribute as precondition or postcondition failure, fix, rerun

---

## Stage 8 — Audit

- [ ] Run `/arpinine-harness:at-audit <spec-path>`
- [ ] Check drift report for:
  - [ ] `TOOL_DRIFT` — observed tool not in allowlist → fix adapter
  - [ ] `PERMISSION_DRIFT` — write action without approval event → fix adapter
  - [ ] `MEMORY_DRIFT` — cross-session memory write → fix session reset
  - [ ] `EVAL_COVERAGE_DRIFT` — observed failure path not in eval → add scenario
  - [ ] Endpoint or model mismatches between spec and code
- [ ] Each CRITICAL/HIGH finding attributed (precondition vs postcondition)
- [ ] Each postcondition failure: fix code OR create ADR ratifying the deviation
- [ ] No CRITICAL items unresolved before completion

---

## Stage 9 — Retro and Rules

- [ ] Run `/arpinine-harness:at-retro <slug>`
- [ ] Each lesson extracted as a rule in `.specify/rules/`:
  - [ ] `rule-id` unique
  - [ ] `triggers` describes the pattern
  - [ ] `prevents` names the failure
  - [ ] `source-adr` or `evidence-project` linked
  - [ ] `forbidden_patterns` and `allowed_paths` set if import/boundary rule
  - [ ] `active: true`
- [ ] Rules verified to fire on next spec via `rule-manager` + `drift-detector`

---

## Hard Blocks Summary

| Missing | Blocked at |
|---|---|
| `## Harness Strategy` in plan | `/at-implement` start |
| Abstraction boundary not defined | `/at-implement` start |
| Tool / memory / permission undocumented | `/at-implement` start |
| CRITICAL security finding in plan | `/at-implement` start |
| ADR missing for harness runtime choice | Completion |
| Eval threshold miss | Completion |
| TOOL_DRIFT / PERMISSION_DRIFT / MEMORY_DRIFT in observations | Completion |
| CRITICAL unresolved drift item without ADR | Completion |

---

## Reference

| Command | Stage |
|---|---|
| `/arpinine-harness:at-init` | Setup |
| `/arpinine-harness:at-new` | Spec |
| `/arpinine-harness:at-review` | Spec refinement |
| `/arpinine-harness:at-plan` | Plan |
| `/arpinine-harness:at-adr` | Architecture decisions |
| `/arpinine-harness:at-eval plan` | Evaluation design |
| `/arpinine-harness:at-implement` | Implementation |
| `/arpinine-harness:at-observe` | Observation |
| `/arpinine-harness:at-eval run` | Evaluation execution |
| `/arpinine-harness:at-audit` | Drift detection |
| `/arpinine-harness:at-retro` | Rule extraction |
| `/arpinine-harness:at-status` | Governance overview |
| `/arpinine-harness:at-ask <agent> "<question>"` | Any stage — focused specialist consultation |
