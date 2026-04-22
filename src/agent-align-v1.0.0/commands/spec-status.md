---
description: "Show governance state of all specs: open drift, ADR coverage, active rules, eval readiness, harness strategy, observation state, and team onboarding summary. Designed for new team members and release readiness checks."
---

# /spec-status

Single-command governance overview. Designed to answer: "What does a new engineer need to understand to work safely in this project?"

## Usage
`/spec-status [--spec <slug>] [--onboard]`

- No flags: project-wide governance summary
- `--spec <slug>`: deep status for one spec
- `--onboard`: include onboarding narrative for new team members

---

## Steps

### 1. Collect all artifacts

Scan `.specify/`:
- `specs/*/spec.md` → all specs
- `specs/*/plan.md` → plans
- `specs/*/eval-plan.md` and `latest-results.md` → eval state
- `observations/*/latest-observation.md` and `trace.json` → runtime evidence
- `adr/*.md` → ADR index
- `rules/**/*.md` → active rules
- `adr/ADR-INDEX.md` → global decision coverage

### 2. Build spec status table

For each spec, compute:
- **AC coverage**: count checked `[x]` vs total `[ ]` in spec.md
- **Drift state**: does a `drift-report.md` exist with open items?
- **ADR coverage**: any ADR with `governs:` matching this spec?
- **Eval state**: `eval-plan.md` exists? `latest-results.md` exists? All thresholds met?
- **Architecture**: `plan.md` contains Module Boundaries, Dependency Rules, Testability sections?
- **Harness**: `plan.md` contains a usable `## Harness Strategy` when harness-based behavior is implied?
- **Obs**: observation artifacts exist under `.specify/observations/<slug>/`?

Print:
```text
SPEC STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Spec                      ACs    Drift     ADRs  Eval     Arch  Harness  Obs
001-user-login            4/4    CLEAN     2     PASS     ✓     ✓        recorded
002-payment-flow          3/5    2 OPEN    1     MISSING  ✗     ✗        none
003-notifications         0/3    NOT RUN   0     MISSING  ✗     n/a      none
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 specs  |  1 clean  |  1 open drift  |  2 missing eval  |  1 missing harness
```

### 3. ADR summary

```text
ADR COVERAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total ADRs:      5
Active:          4  (Accepted or Implemented)
Superseded:      1
Open (Proposed): 1  ← requires team decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4. Rules summary

```text
RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active rules:    4
  security:      2
  architecture:  1
  harness:       1
Source: 3 from retro, 1 from drift ADR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5. Blocked work (if any)

List any specs where work cannot proceed due to:
- CRITICAL unresolved drift without ADR
- Missing eval plan on agentic spec
- Architecture sections absent from plan.md
- Harness strategy missing on harness-based feature
- Observation evidence contradicting harness strategy or eval coverage
- AIN target set but no agent operations defined

### 6. Onboarding narrative (`--onboard` flag)

Generate a human-readable brief for a new team member:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEAM ONBOARDING BRIEF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORKFLOW
This project uses /spec-init → /spec-new → /spec-review →
/spec-plan → /spec-eval → /spec-observe → /spec-implement →
/spec-audit → /spec-retro. Do not skip stages — hooks will
block you if constitution, architecture, or harness
requirements are not met.

ACTIVE SPECS
[list with one-line summaries]

KEY DECISIONS
[top 3-5 ADRs summarized in one sentence each]

ACTIVE RULES ([N] total)
[list rules with "prevents:" value — what the team has learned]

EVAL STATE
[which specs require an eval run before implementation can resume]

HARNESS AND OBSERVATION STATE
[which specs have a defined harness strategy and which have runtime evidence recorded]

OPEN ITEMS
[anything requiring a decision or unblocking action]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Conditions

- `.specify/` not found → "Run `/spec-init` first"
- No specs found → "No specs yet. Run `/spec-new` to create the first one"
- ADR-INDEX.md missing → note in output, suggest running `/spec-adr list`
