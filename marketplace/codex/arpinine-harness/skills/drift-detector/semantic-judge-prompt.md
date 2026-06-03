# Semantic Drift Judge — Prompt Template

Governed by [ADR-0012](../../../../.specify/adr/ADR-0012-semantic-drift-as-opt-in-llm-judge-at-audit-time.md).
Used by `/at-audit --semantic` (Layer 2). Advisory, non-blocking. One invocation per spec section paired with its related code.

## Contract

- **Input**: one spec section (clause text + clause id) and the related code excerpts.
- **Output**: zero or more findings. Each finding uses the structural-check severity vocabulary (`CRITICAL` / `HIGH` / `MEDIUM`) so it merges into the unified `/at-audit` report. No numeric confidence (see ADR-0012 — avoid fake precision).
- **No finding** when code satisfies the clause: return an empty `findings` array. Do not invent drift.

## Severity rubric

| Severity | Use when |
|----------|----------|
| `CRITICAL` | Code behavior directly contradicts an explicit MUST/guarantee in the clause (e.g. spec "rate-limit per user", code limits per IP; spec "deny by default", code allows by default). |
| `HIGH` | Code omits or only partially implements required behavior; intent diverges in a way a reviewer must resolve before merge. |
| `MEDIUM` | Plausible divergence or ambiguity — code may satisfy intent but evidence is incomplete; flag for human judgment. |

If you cannot find code evidence for or against the clause, emit a single `MEDIUM` finding stating the clause is unverifiable from the supplied code. Never guess `CRITICAL`.

## Prompt

```
You are a semantic drift judge in a spec-governance audit. You compare ONE
specification clause against the code that is supposed to implement it, and
report only behavioral contradictions — cases where the code does something
the clause does not permit, or fails to do something the clause requires.

Do NOT report structural issues (missing files, wrong endpoints, naming) —
a separate deterministic checker owns those. Report only intent/behavior drift.

SPEC CLAUSE
id: {{clause_id}}
{{clause_text}}

RELATED CODE
{{code_excerpts}}   # only code this clause references; each line is prefixed
                    # with its ABSOLUTE source line number (N\t...), so cite N directly

Decide whether the code satisfies the clause's intent. For each contradiction,
emit one finding. If the code satisfies the clause, emit no findings.

Rules:
- Severity is CRITICAL, HIGH, or MEDIUM per the rubric below. No confidence scores.
- Every finding MUST cite the exact spec phrase and the exact code location
  (file:line) that contradict each other. Use the line number shown in the
  excerpt prefix verbatim — it is the real source line, not excerpt-relative.
- Explanation is one or two sentences: what the clause requires vs. what the
  code does. No restating the clause verbatim.
- If you cannot verify the clause from the supplied code, emit one MEDIUM
  finding marking it unverifiable. Never guess CRITICAL.

Rubric:
- CRITICAL: code directly contradicts an explicit MUST/guarantee.
- HIGH: required behavior omitted or only partially implemented.
- MEDIUM: plausible divergence, ambiguity, or unverifiable from supplied code.

Output ONLY valid JSON matching this schema:
{
  "clause_id": "<id>",
  "findings": [
    {
      "severity": "CRITICAL | HIGH | MEDIUM",
      "spec_phrase": "<exact quote from the clause>",
      "code_location": "<path>:<line-range>",
      "explanation": "<1-2 sentence contradiction>"
    }
  ]
}
```

## Example output

```json
{
  "clause_id": "spec-3.2-rate-limit",
  "findings": [
    {
      "severity": "CRITICAL",
      "spec_phrase": "rate-limit each authenticated user to 100 requests per minute",
      "code_location": "src/api/middleware.py:48-61",
      "explanation": "Clause requires per-user limiting; code keys the limiter on request.remote_addr (per-IP), so users behind a shared NAT share a budget and a single user across IPs bypasses it."
    }
  ]
}
```

## Integration notes

- Caller iterates spec sections, builds `code_excerpts` from the same related-code
  resolution `quick_drift_check.py` already uses, runs this prompt per section.
- **Line-number invariant:** the `N\t` prefix in `code_excerpts` is the absolute
  source line. Whole files are sent today (start at line 1, tail truncated). If prep
  ever switches to narrow snippets, it must keep emitting true source line numbers
  (`numbered_excerpt(start_line=...)`) — the judge's `file:line` citations depend on it.
- Findings append to the `/at-audit` report alongside structural findings, then flow
  into `product-owner` precondition/postcondition attribution unchanged.
- Per ADR-0012: opt-in (`--semantic`), never in the hook, never blocking.
