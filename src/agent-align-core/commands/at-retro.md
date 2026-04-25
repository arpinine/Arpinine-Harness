---
description: "Run a delivery retrospective after a feature ships. Extract lessons as rule candidates, add them to rules/, and update ADR-INDEX. Turns completed work into compounding team knowledge."
---

# /at-retro

Extract lessons from completed work and persist them as rules.

## Usage
`/at-retro [spec-path]`

If no path: use most recently modified spec under `.specify/specs/`.

---

## Steps

### 1. Locate the completed spec

- With path: use that `spec.md`
- Without path: find most recently modified spec — `find .specify/specs -name "spec.md" | xargs ls -t | head -1`
- Confirm: "Running retro for: [spec path]"

### 2. Load all artifacts

Gather:
- `spec.md` — original intent
- `plan.md` — engineering approach
- `ADR-*.md` files with `governs:` matching this spec
- `eval-plan.md` and `latest-results.md` (if present)
- observation artifacts under `.specify/observations/<slug>/` (if present)
- drift findings from the last `/agent-align:at-audit` run (check `.specify/specs/<slug>/drift-report.md` if it exists)

### 3. Ask structured retro questions

Work through each question. Record answers:

**Intent vs Reality**
- Did the delivered system match the acceptance criteria in `spec.md`? Which ACs were not met?
- Were there requirements not in `spec.md` that had to be implemented anyway?

**Process failures**
- Were any drift items found in audit that were not caught earlier?
- Were any ADRs created reactively (after implementation) rather than proactively?
- Were any evaluation thresholds adjusted to pass rather than raised because the system improved?

**Architecture observations**
- Were any module boundaries crossed or bypassed?
- Were there dependencies that violated the direction rules in `plan.md`?

**Harness observations**
- Were any harness tool calls observed that were outside the documented tool model?
- Were any approval events that contradicted the permission model?
- Does the harness strategy need an ADR that does not exist yet?

**Rule candidates**
- For each "yes" above: is this a pattern the team should prevent in future specs?
- Would a rule have caught this earlier in the workflow (at PreToolUse, at audit, at planning)?

### 4. Classify lessons

For each lesson surfaced:

```text
LESSON [N]:
  Observation: [What happened]
  Root cause: [Why it happened — spec gap, process skip, implementation choice]
  Attribution: PRECONDITION FAILURE (spec/plan was unclear) | POSTCONDITION FAILURE (deviated from clear spec)
  Rule candidate? YES | NO
  Proposed rule: [One sentence: "When X, require Y to prevent Z"]
  Category: security | architecture | harness | spec-quality | evaluation | process
  Severity: CRITICAL | HIGH | MEDIUM | LOW
```

### 5. Persist confirmed rules

For each lesson confirmed as a rule candidate:
1. Invoke `rule-manager` skill → `add-rule(finding, source_type="retro", source_ref=spec_slug)`
2. Confirm: "Rule [rule-id] created: [prevents value]"
3. If the lesson traces to a specific drift finding with an ADR: set `source-adr` automatically

### 6. Update ADR-INDEX if needed

If any ADR was used reactively (created during audit or after implementation):
- Flag it in the retro summary as a process gap
- Propose adding a rule that would trigger ADR creation at planning time instead

### 7. Retro summary

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RETRO: .specify/specs/001-user-login/spec.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lessons surfaced: 4
Rules added:      2 (arch-001, harness-001)
Rules declined:   2 (one-off, not generalizable)
ADR gaps:         1 (ADR-0003 was reactive — add planning trigger rule)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rules now compound into future specs automatically.
```

## Error Conditions

- No `spec.md` found → "Run `/agent-align:at-new` to create a spec first"
- Spec not marked complete → "This spec has open ACs. Run `/agent-align:at-audit` first to confirm delivery state"
- No `plan.md` or ADRs → still proceed, note missing artifacts in retro summary
