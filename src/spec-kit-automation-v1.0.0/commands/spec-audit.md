---
description: Detect drift between specs and code, then send the work back into refinement or ADR creation so the team realigns on a shared source of truth.
---

# /spec-audit

Detect drift and drive realignment.

## Usage
`/spec-audit [spec-path]`

If no path given: scan all specs under `.specify/specs/`.

---

## Steps

### 1. Locate specs
- With path argument: use that `spec.md` directly
- Without argument: `find .specify/specs -name "spec.md"` and process each

### 2. Run drift detection (invoke `drift-detector` skill)
For each spec:
- File existence check
- API/endpoint comparison
- Data model comparison
- ADR coverage check using both:
  - `governs:` matches the spec path
  - `covers:` contains the exact drift key for the finding

### 3. Report findings
Print report in format:
```
📋 Drift Report: .specify/specs/001-user-login/spec.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL  src/auth/login.py:45 — rate limiting in code, absent from spec
HIGH      GET /api/users/profile — in code, not in spec
MEDIUM    Spec mentions email verification, not implemented
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 issues (1 CRITICAL, 1 HIGH, 1 MEDIUM)
```

### 4. Drift→ADR resolution (for each CRITICAL and HIGH item)
For each unresolved CRITICAL or HIGH drift:
1. Derive a stable drift key from the finding, e.g.:
   - `drift:001-user-login:file:src/auth/login.py`
   - `drift:001-user-login:route:GET-/api/users/profile`
   - `drift:001-user-login:model:user.email`
2. Check ADR files for both:
   - matching `governs: specs/001-user-login`
   - matching entry in `covers:`
3. If no matching ADR exists:
   - Show: "No ADR covers: [drift description]"
   - Prompt: "Create ADR to document this decision? (yes/no)"
   - If yes: invoke `adr-manager` skill with Context pre-filled from drift details
   - Record created ADR number in summary

### 5. Summary
```
Summary: 3 drift items found, 1 ADR created (ADR-0003).
Remaining: 1 CRITICAL unresolved — implementation blocked.
```

If any CRITICAL item remains without a matching ADR `covers:` entry: remind that `constitution-enforcer` blocks implementation.

### 6. Realignment actions
For each confirmed drift item, choose the right correction path:
- spec was wrong or incomplete -> refine `spec.md`
- engineering approach changed -> update `plan.md`
- consequential decision changed -> create or update ADR
- implementation is incorrect -> fix code to match the agreed artifacts

### 7. Evaluation regression check
- Compare the latest evaluation results against the eval plan thresholds
- If quality regressed without a corresponding spec or ADR update, mark as realignment required
- If the evaluated system changed and evals were not rerun, report a HIGH issue

## Error Conditions
- `.specify/specs/` not found → "Run `/spec-init` first"
- Spec not readable → report file path and skip
- No specs found at given path → list available specs
