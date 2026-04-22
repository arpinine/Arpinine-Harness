---
description: Detect drift between specs and code. Reports CRITICAL/HIGH/MEDIUM issues and prompts ADR creation for any unresolved divergence.
---

# /spec-audit

Detect spec-code drift and drive resolution via ADR creation.

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
- ADR coverage check (search ADR-INDEX.md for matching `governs:`)

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
1. Check if ADR-INDEX.md has a governing ADR for this spec
2. If no governing ADR:
   - Show: "No ADR covers: [drift description]"
   - Prompt: "Create ADR to document this decision? (yes/no)"
   - If yes: invoke `adr-manager` skill with Context pre-filled from drift details
   - Record created ADR number in summary

### 5. Summary
```
Summary: 3 drift items found, 1 ADR created (ADR-0003).
Remaining: 1 CRITICAL unresolved — implementation blocked.
```

If any CRITICAL item remains without ADR: remind that `constitution-enforcer` blocks implementation.

## Error Conditions
- `.specify/specs/` not found → "Run `/spec-init` first"
- Spec not readable → report file path and skip
- No specs found at given path → list available specs
