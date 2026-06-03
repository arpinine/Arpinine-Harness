# Bootstrapping Governance for Existing Work

Use this when the codebase already exists and you want to retrofit Arpinine Harness governance retroactively.

If you do not want to choose the workflow command yourself, start with:

```
/arpinine-harness:at "We already have code. Bootstrap governance from this repo."
```

`/arpinine-harness:at` is the facade over the Arpinine Harness agent team. From an initial state, it first determines what kind of repository it is looking at:

- empty or ungoverned repo -> initialize governance
- existing codebase with no governed artifacts -> bootstrap governance from code
- already governed repo -> route to the next stage-specific command

It then explains the recommendation and hands off to the right underlying command. The rest of this guide shows the explicit raw-command path.

## Prerequisites

- Arpinine Harness plugin installed (`make install`)
- spec-kit installed (`specify --version`)
- Open a Claude Code session in this repo

---

## Step 1 — Initialize the structure

```
/arpinine-harness:at-init
```

Creates `.specify/specs/`, `.specify/adr/`, `.specify/evals/`, `.specify/observations/`, `.specify/rules/`, and `ADR-INDEX.md`.

Because this guide is for an existing codebase, archetype scaffolding should normally be skipped. `at-init` only scaffolds when the repo still looks empty, unless you explicitly force an archetype.

Verify with:

```
/arpinine-harness:at-status
```

---

## Step 2 — Create a spec for each major feature

For each piece of existing work, run:

```
/arpinine-harness:at-new <feature name>
```

The plugin reads the existing code and generates a spec from what was built. Review the output and:

- keep product intent, user stories, and acceptance criteria
- remove implementation details (those go in `plan.md`)
- mark open questions explicitly

### Features to spec for this repo

Run these in order:

```
/arpinine-harness:at-new arpinine-harness core workflow
/arpinine-harness:at-new plugin platform abstraction
```

Each creates `.specify/specs/NNN-<slug>/spec.md`.

---

## Step 3 — Capture architectural decisions as ADRs

For each major technical decision already made, run:

```
/arpinine-harness:at-adr new "<decision title>"
```

Link each ADR to the relevant spec via the `governs:` field.

### ADRs to create for this repo

```
/arpinine-harness:at-adr new "Separate shared core from assistant-specific implementations"
```
→ governs: `002-plugin-platform-abstraction`

```
/arpinine-harness:at-adr new "Stable dist/plugins/ dir as local marketplace registration target"
```
→ governs: `002-plugin-platform-abstraction`

```
/arpinine-harness:at-adr new "assemble target as composition primitive for build and install"
```
→ governs: `002-plugin-platform-abstraction`

Each ADR lives at `.specify/adr/ADR-NNNN-<title>.md`.

---

## Step 4 — Create implementation plans

For each spec, run:

```
/arpinine-harness:at-plan <slug>
```

The plugin derives a `plan.md` from the existing code. Review and confirm:

- module boundaries match actual directory structure
- dependency rules reflect what the Makefile enforces
- harness strategy is `N/A` for this repo (no agent runtime dependency)

Each creates `.specify/specs/NNN-<slug>/plan.md`.

---

## Step 5 — Verify governance state

```
/arpinine-harness:at-status
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
| `/arpinine-harness:at-eval` | Needs a running system with measurable outputs |
| `/arpinine-harness:at-observe` | Needs runtime traces from actual executions |
| `/arpinine-harness:at-audit` | Run after first implementation cycle completes |
| `/arpinine-harness:at-retro` | Run after first delivery milestone |

---

## Ongoing: new features going forward

For any new work after governance is bootstrapped, use the full forward flow:

```
/arpinine-harness:at-new → /arpinine-harness:at-plan → /arpinine-harness:at-implement → /arpinine-harness:at-eval → /arpinine-harness:at-observe → /arpinine-harness:at-retro
```

Do not skip `/arpinine-harness:at-plan` before implementation — hooks will block you if architecture sections are missing.
