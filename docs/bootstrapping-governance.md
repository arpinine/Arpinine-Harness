# Bootstrapping Governance for Existing Work

Use this when the codebase already exists and you want to retrofit AgentAlign governance retroactively.

## Prerequisites

- AgentAlign plugin installed (`make install`)
- spec-kit installed (`specify --version`)
- Open a Claude Code session in this repo

---

## Step 1 — Initialize the structure

```
/agent-align:at-init
```

Creates `.specify/specs/`, `.specify/adr/`, `.specify/evals/`, `.specify/observations/`, `.specify/rules/`, and `ADR-INDEX.md`.

Verify with:

```
/agent-align:at-status
```

---

## Step 2 — Create a spec for each major feature

For each piece of existing work, run:

```
/agent-align:at-new <feature name>
```

The plugin reads the existing code and generates a spec from what was built. Review the output and:

- keep product intent, user stories, and acceptance criteria
- remove implementation details (those go in `plan.md`)
- mark open questions explicitly

### Features to spec for this repo

Run these in order:

```
/agent-align:at-new agent-align core workflow
/agent-align:at-new plugin platform abstraction
```

Each creates `.specify/specs/NNN-<slug>/spec.md`.

---

## Step 3 — Capture architectural decisions as ADRs

For each major technical decision already made, run:

```
/agent-align:at-adr new "<decision title>"
```

Link each ADR to the relevant spec via the `governs:` field.

### ADRs to create for this repo

```
/agent-align:at-adr new "Separate shared core from assistant-specific implementations"
```
→ governs: `002-plugin-platform-abstraction`

```
/agent-align:at-adr new "Stable plugins/ dir as local marketplace registration target"
```
→ governs: `002-plugin-platform-abstraction`

```
/agent-align:at-adr new "assemble target as composition primitive for build and install"
```
→ governs: `002-plugin-platform-abstraction`

Each ADR lives at `.specify/adr/ADR-NNNN-<title>.md`.

---

## Step 4 — Create implementation plans

For each spec, run:

```
/agent-align:at-plan <slug>
```

The plugin derives a `plan.md` from the existing code. Review and confirm:

- module boundaries match actual directory structure
- dependency rules reflect what the Makefile enforces
- harness strategy is `N/A` for this repo (no agent runtime dependency)

Each creates `.specify/specs/NNN-<slug>/plan.md`.

---

## Step 5 — Verify governance state

```
/agent-align:at-status
```

Expected at this point:

- specs: 2 (one per feature)
- ADRs: 3+ linked to specs
- plans: present for each spec
- eval: missing (acceptable — no runtime yet)
- observations: none (acceptable — no runtime yet)

---

## What to skip for now

| Command | Why skip |
|---|---|
| `/agent-align:at-eval` | Needs a running system with measurable outputs |
| `/agent-align:at-observe` | Needs runtime traces from actual executions |
| `/agent-align:at-audit` | Run after first implementation cycle completes |
| `/agent-align:at-retro` | Run after first delivery milestone |

---

## Ongoing: new features going forward

For any new work after governance is bootstrapped, use the full forward flow:

```
/agent-align:at-new → /agent-align:at-plan → /agent-align:at-implement → /agent-align:at-eval → /agent-align:at-observe → /agent-align:at-retro
```

Do not skip `/agent-align:at-plan` before implementation — hooks will block you if architecture sections are missing.
