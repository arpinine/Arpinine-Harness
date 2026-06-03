# Routing Policy

This document defines the decision rules consumed by the `/at` facade to route user intent to the correct underlying command.

The policy operates on two inputs:
- **Inspector output**: the normalized JSON object from `scripts/inspect_state.py`
- **User intent**: the natural-language input passed to `/at`

The policy produces:
- **Route**: the selected underlying command
- **Confidence**: `high`, `medium`, or `low`
- **Reason**: one sentence explaining the routing decision
- **Alternative**: an alternative route when confidence is not high (optional)

The facade applies this policy. The policy does not execute commands.

---

## Command Classes

Commands are classified by whether they take over the conversation for multiple turns or return control to the facade immediately.

### Handoff commands

The facade delegates fully. After invocation the facade emits no further output for that session. The delegated command owns its own next-step guidance.

| Command | Reason for handoff class |
|---------|--------------------------|
| `/at-map` | Multi-turn project decomposition interview |
| `/at-discover` | Multi-turn feature discovery interview |
| `/at-bootstrap-from-code` | Multi-turn codebase assessment |
| `/at-implement` | Multi-turn implementation loop |

### Return commands

The facade may optionally summarize the outcome and recommend a next step after the command completes.

| Command | Notes |
|---------|-------|
| `/at-init` | One-time setup; returns structured report |
| `/at-new` | Single spec creation; may ask clarifying questions but is bounded |
| `/at-status` | Read-only report; always returns |
| `/at-plan` | Plan generation for one spec; bounded |
| `/at-review` | Spec review for one spec; bounded |
| `/at-ask` | Single specialist question; bounded |
| `/at-audit` | Drift check for one spec; bounded |
| `/at-eval` | Eval run for one spec; bounded |
| `/at-retro` | Retrospective for one spec; bounded |
| `/at-adr` | ADR creation; bounded |
| `/at-observe` | Observation recording; bounded |

---

## Routing Rules

Rules are evaluated **in order**. The first matching rule wins. Hard gates are evaluated before soft heuristics.

### Gate 1 — No project root

**Condition:** `repo_root == null`

**Action:** Do not route. Report that no project root could be found and ask the user to navigate to their project directory.

**Confidence:** N/A (error, not a routing decision)

---

### Gate 2 — Ungoverned repository

**Condition:** `governed == false`

**Action:** Route to `/at-init`.

**Reason:** No `.specify/` directory exists. Governance must be initialized before any other command can operate.

**Confidence:** High

**Exception:** If intent clearly references an existing codebase and `has_existing_codebase == true`, offer `/at-bootstrap-from-code` as the alternative. Ask which the user wants before executing.

---

### Gate 3 — Bootstrap candidate

**Condition:** `bootstrap_candidate == true` (i.e., `has_existing_codebase == true` AND `spec_count == 0`)

**Action:** Ask whether the user wants to bootstrap governance from the existing codebase (`/at-bootstrap-from-code`) or start from a new product goal (`/at-map`). Do not auto-select.

**Confidence:** Medium (state is clear; intent determines which branch)

---

### Gate 4 — Active session pre-emption

Evaluated after gates 1–3 pass.

**Condition A:** `active_map_sessions` is non-empty AND user intent is consistent with broad-goal or project-level continuation (see Intent Vocabulary below).

**Action:** Offer to resume the active map session before starting fresh. List sessions by slug. Do not auto-resume.

**Confidence:** High if intent is clearly broad-goal. Medium if intent is ambiguous.

**Condition B:** `active_discovery_sessions` is non-empty AND user intent is consistent with single-feature continuation.

**Action:** Offer to resume the active discovery session before starting fresh.

**Confidence:** High if intent is clearly feature-level. Medium if ambiguous.

**Condition C:** Both A and B match simultaneously (active map AND active discovery, ambiguous intent).

**Action:** List both sessions. Ask the user which context they are continuing.

**Confidence:** Low

---

### Soft heuristics — Intent classification

Evaluated after all gates pass and no active session pre-emption applies.

Match the user's intent text against the vocabulary below. Select the route whose vocabulary produces the strongest signal match. When two routes match with equal strength, apply the conflict resolution rules.

#### Intent vocabulary by route

| Route | Strong signal keywords and phrases |
|-------|-----------------------------------|
| `/at-map` | "build a product", "broad goal", "initiative", "multiple features", "start from scratch", "product vision", "decompose", "feature backlog", "roadmap", "whole system" |
| `/at-discover` | "add a feature", "one feature", "this idea", "user story", "workflow for X", "I want users to be able to", "before I write a spec" |
| `/at-new` | "create a spec", "write a spec", "new spec for", "specify", "document the feature" |
| `/at-plan` | "plan the implementation", "how to build", "generate a plan", "implementation plan", "technical plan", "before I implement" |
| `/at-review` | "review the spec", "tighten the spec", "refine scope", "spec is unclear", "improve the spec", "acceptance criteria" |
| `/at-ask` | "ask the", "get a second opinion", "what does the architect think", "what would security say", "check with", "specialist" |
| `/at-implement` | "implement", "code it", "build it", "write the code", "start development", "TDD", "make it work" |
| `/at-audit` | "something drifted", "implementation diverged", "doesn't match the spec", "check drift", "audit", "misalignment" |
| `/at-eval` | "run the eval", "evaluate", "measure", "thresholds", "check metrics", "does it meet criteria" |
| `/at-retro` | "retrospective", "what did we learn", "after shipping", "post-mortem", "lessons learned" |
| `/at-adr` | "decision record", "ADR", "architectural decision", "document this choice" |
| `/at-observe` | "record observation", "log runtime behavior", "what happened in prod", "observation" |
| `/at-status` | "what should I do next", "what's the state", "show me the status", "what's left", "where are we" |
| `/at-bootstrap-from-code` | "existing codebase", "bootstrap from code", "reverse engineer the specs", "already have code", "legacy system" |

#### State-informed adjustments

After keyword matching, adjust the route candidate using inspector state:

| Inspector condition | Adjustment |
|--------------------|------------|
| `specs_without_plan` non-empty AND intent matches `/at-plan` | Confirm which spec to plan; list `specs_without_plan` |
| `specs_with_open_drift` non-empty AND intent is vague or status-oriented | Surface drift as a recommended next action alongside `/at-status` |
| `eval_gaps` non-empty AND intent matches `/at-eval` | Confirm which spec; list `eval_gaps` |
| `spec_count == 0` AND intent matches `/at-plan`, `/at-review`, `/at-implement`, `/at-audit`, `/at-eval` | Redirect to `/at-map` or `/at-discover`; no spec exists to operate on |

---

## Conflict Resolution

When two or more routes match with equal signal strength, apply these rules in order:

1. **Resume over start fresh.** An active session for the matching command takes priority over starting a new one.
2. **Hard gate over soft heuristic.** A gate match overrides any keyword match.
3. **Specific over general.** `/at-plan` beats `/at-status`; `/at-audit` beats `/at-status`.
4. **Earlier workflow stage over later stage when state is ambiguous.** Discovery before planning; planning before implementation.
5. **Explicit user phrase over inferred intent.** If the user names a command directly (e.g., "run at-plan"), honor it.

---

## Confidence Scoring

Confidence is computed from the routing conditions that fired, not estimated subjectively.

| Level | Conditions that produce it |
|-------|---------------------------|
| **High** | Exactly one hard gate matched, OR exactly one intent vocabulary route matched with no competing route at equal strength, AND inspector state is unambiguous (no `incomplete_state`, no conflicting active sessions) |
| **Medium** | Two routes match with similar signal strength, OR intent keywords are present but weak, OR inspector state has relevant gaps (`incomplete_state == true`, multiple active sessions of different types), OR gate 3 applies |
| **Low** | User intent is underspecified (fewer than one strong keyword match), OR multiple routes remain equally plausible after conflict resolution, OR inspector state is inconsistent, OR the user's request does not map to any known vocabulary |

---

## Behavior per Confidence Level

| Level | Facade behavior |
|-------|----------------|
| **High** | State the route and reason. For return commands: execute immediately. For handoff commands: state that you are delegating, then delegate. |
| **Medium** | State the recommended route and reason. Show one alternative. For meaningful mutations (creating files, invoking handoff commands): ask confirmation before executing. For read-only return commands: may execute directly. |
| **Low** | Do not route silently. Either ask one clarifying question to resolve ambiguity, or present two to three options and ask the user to choose. If uncertainty is primarily repo-state-driven, run `/at-status` and present its output before asking. |

---

## Output Format

The facade must always expose its routing decision before acting.

**High confidence — execute:**
```text
AT: facade
STATE: <one-line summary of relevant inspector fields>
INTERPRETATION: <one-line description of classified intent>
DECISION: <command>
WHY: <one sentence>
ACTION: invoking <command> on your behalf
```

**Medium confidence — confirm:**
```text
AT: facade
STATE: <one-line summary>
INTERPRETATION: <one-line>
RECOMMENDATION: <command> [<target if applicable>]
WHY: <one sentence>
ALTERNATIVE: <command> [<target>]
CONFIRM: proceed with <command>?
```

**Low confidence — clarify:**
```text
AT: facade
STATE: <one-line summary>
INTERPRETATION: unclear
OPTIONS:
  1. <command> — <one-line reason>
  2. <command> — <one-line reason>
QUESTION: <single clarifying question>
```

---

## Full Decision Table

| Priority | Condition | Route | Confidence |
|----------|-----------|-------|------------|
| 1 | `repo_root == null` | Error | N/A |
| 2 | `governed == false` AND `has_existing_codebase == true` | `/at-init` or `/at-bootstrap-from-code` | Medium |
| 3 | `governed == false` | `/at-init` | High |
| 4 | `bootstrap_candidate == true` | `/at-bootstrap-from-code` or `/at-map` | Medium |
| 5 | Active map session AND broad-goal intent | Resume `/at-map` | High/Medium |
| 6 | Active discovery session AND feature intent | Resume `/at-discover` | High/Medium |
| 7 | Both active sessions AND ambiguous intent | Clarify | Low |
| 8 | Broad-goal intent, no active sessions | `/at-map` | High/Medium |
| 9 | Single-feature intent, no active sessions | `/at-discover` | High/Medium |
| 10 | Explicit spec creation intent | `/at-new` | High |
| 11 | Planning intent + `specs_without_plan` non-empty | `/at-plan` | High |
| 11b | Planning intent + `spec_count > 0` AND `specs_without_plan` empty | `/at-status` with explanation that all current specs already have plans | Medium |
| 12 | Planning intent + no specs | Redirect to `/at-map` or `/at-discover` | Medium |
| 13 | Spec refinement intent AND `spec_count > 0` | `/at-review` | High |
| 13b | Spec refinement intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |
| 14 | Specialist question intent | `/at-ask` | High |
| 15 | Implementation intent AND `spec_count > 0` | `/at-implement` | High |
| 15b | Implementation intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |
| 16 | Explicit drift/audit intent AND `spec_count > 0` | `/at-audit` | High |
| 16b | Explicit drift/audit intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |
| 17 | `specs_with_open_drift` non-empty AND intent is vague or status-oriented | `/at-status` with drift surfaced as a recommended next action | Medium |
| 18 | Eval intent AND `spec_count > 0` AND `eval_gaps` non-empty | `/at-eval` | High |
| 18b | Eval intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |
| 19 | Eval intent AND `spec_count > 0` AND `eval_gaps` empty | `/at-status` with explanation that all current specs already have eval plans | Medium |
| 20 | Retrospective intent AND `spec_count > 0` | `/at-retro` | High |
| 20b | Retrospective intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |
| 21 | ADR intent | `/at-adr` | High |
| 22 | Observation intent AND `spec_count > 0` | `/at-observe` | High |
| 22b | Observation intent AND `spec_count == 0` | Redirect to `/at-map` or `/at-discover` | Medium |
| 23 | Status/next-step intent OR no strong intent match | `/at-status` | Medium/Low |
