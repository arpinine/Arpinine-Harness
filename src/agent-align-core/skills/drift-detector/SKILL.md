---
name: drift-detector
description: Detects and classifies drift between specs and code; triggers ADR creation for unresolved divergence
---

# Drift Detector Skill

## When to Run
- After any file edit (quick check via PostToolUse hook)
- On `/at-audit` command (full analysis)
- Before PR merge

The PostToolUse hook is intentionally lightweight:
- missing file references from spec
- endpoint mismatch hints
- stale or missing eval result hints for agentic specs

Use `/at-audit` for the full comparison workflow.

## Detection Methods

### 1. File Existence Check
Scan `spec.md` for file references matching:
```
(src|lib|app|packages|services|internal|cmd)/[a-zA-Z0-9_/.-]+\.(py|js|ts|go|rs|java|rb|kt|swift)
```
- File exists → pass
- File missing → HIGH drift

### 2. API / Endpoint Comparison
Extract endpoints from spec (patterns: `GET /`, `POST /`, `PUT /`, `DELETE /`, `PATCH /`).
Extract endpoints from code (grep routes, decorators, handlers, router files).

| Condition | Severity |
|-----------|----------|
| In spec, missing from code | MEDIUM (unimplemented) |
| In code, missing from spec | HIGH (undocumented feature) |
| Spec says GET, code uses POST | CRITICAL (conflict) |

### 3. Data Model Comparison
Extract field names from spec schema/model tables or lists.
Compare against code data models, ORMs, or schema files.

| Condition | Severity |
|-----------|----------|
| Field in spec, missing in code | MEDIUM |
| Field in code, missing in spec | HIGH |
| Type mismatch | CRITICAL |

### 4. Rule Check
Before any ADR creation, invoke `rule-manager` skill → `check-rules(file_path, content)`:
- If an active rule's `triggers` match the finding → report as **RULE VIOLATION** with the rule-id and `prevents` value
- Rule violations escalate to at least the rule's severity
- Rule violations do NOT need a new ADR — they need the code or spec fixed to comply with the existing rule

### 5. ADR Coverage Check
For every CRITICAL or HIGH item not already covered by a rule:
- Derive a stable drift key: `drift:<spec-slug>:<type>:<identifier>`
- Search `.specify/adr/ADR-INDEX.md` and ADR files for both:
  - `governs:` matches the spec path
  - `covers:` contains that exact drift key
- No matching ADR found → flag for ADR creation (see Drift→ADR Pipeline)

### 6. Observation Check
If observation artifacts exist for the spec:
- compare observed tool calls against the harness strategy tool model
- compare observed approval events against the permission model
- compare observed memory events against the memory/state model
- compare observed scenarios and failures against the eval plan

Map observation mismatches to:
- `TOOL_DRIFT`
- `PERMISSION_DRIFT`
- `MEMORY_DRIFT`
- `EVAL_COVERAGE_DRIFT`
- `RUNTIME_BEHAVIOR_DRIFT`

## Alert Levels

| Severity | Condition | Action |
|----------|-----------|--------|
| CRITICAL | Spec says X, code does Y — direct conflict | Block + require ADR |
| HIGH | Code has feature absent from spec | Require spec update or ADR |
| MEDIUM | Spec has feature absent from code | Track; note in report |
| LOW | Naming / style mismatch | Note only |

## Drift→ADR Pipeline

When CRITICAL or HIGH drift detected without a matching ADR:
1. Report drift item with severity and location
2. Derive and print the drift key
3. Prompt: "Create ADR to document this decision? (yes/no)"
4. If yes → invoke `adr-manager` skill with Context pre-filled from drift details and `covers:` set to the drift key
5. Link created ADR number back to drift report line
6. Update spec with `## Related ADRs` entry or add inline comment

## Output Format

```
📋 Drift Report: .specify/specs/001-user-login/spec.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL  src/auth/login.py:45 — rate limiting in code, absent from spec
HIGH      GET /api/users/profile — in code, not in spec
MEDIUM    Spec mentions email verification, not yet implemented
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 issues found (1 CRITICAL, 1 HIGH, 1 MEDIUM)
Run /at-audit for full analysis and ADR resolution.
```

## Supersedes
`reverse-diff-audit` skill — consolidated here.
