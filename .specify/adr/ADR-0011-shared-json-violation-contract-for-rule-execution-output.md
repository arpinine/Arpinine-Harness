---
governs: specs/005-deterministic-rule-engine
supersedes: ~
status: Accepted
date: 2026-05-04
covers:
  - decision:005-deterministic-rule-engine:shared-json-violation-contract
---

# ADR-0011: Shared JSON violation contract as the output format for rule execution

## Status
Accepted

## Context
The deterministic rule engine (`check_rules.py`) produces violation findings that are consumed by three downstream surfaces: PreToolUse hooks (blocking gate), `at-audit` (severity classification and routing), and `at-status` (violation counts and summary). Each consumer needs the same violation data in a stable, parseable format.

Without a frozen contract, each consumer would parse rule output independently. Any change to the output format — a renamed field, a restructured object, a changed severity label — would silently break one or more consumers. The hook consumer is the highest-stakes: a broken format causes hooks to either fail open (miss violations) or fail closed (block all writes).

## Decision
`check_rules.py` emits a JSON array of violation objects on stdout when invoked with `--json`. The contract is:

```json
[
  {
    "rule_id": "<string>",
    "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
    "file": "<repo-relative path or null>",
    "line": "<integer or null>",
    "message": "<human-readable description>"
  }
]
```

This contract is stable. Fields may not be removed or renamed without a migration plan that updates all consumers. New optional fields may be added. The `--json` flag is the machine-readable interface; plain text output (no flag) is for human display only and is not a contract.

Tests in `tests/` include snapshot-style assertions against the `--json` output using known fixture inputs. A test failure on the JSON shape is a breaking change signal.

## Consequences
- Positive: All consumers (hooks, audit, status) parse one format — format changes surface as test failures before reaching consumers.
- Positive: The contract is testable offline with fixture files; no live rule execution is needed for consumer unit tests.
- Positive: New consumers (future CI integrations, reporting dashboards) have a stable interface to target.
- Negative: The contract must be versioned explicitly if breaking changes ever become necessary; consumers must be updated in the same commit.
- Negative: JSON stdout means `check_rules.py` cannot emit diagnostic logs to stdout when `--json` is active; diagnostics must go to stderr.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Plain text output parsed by each consumer | Fragile; any formatting change silently breaks consumers; no shared test surface |
| Exit code only (no structured output) | Insufficient for audit and status, which need violation detail, not just pass/fail |
| Consumer-specific output flags (--hooks-format, --audit-format) | Divergence by design; defeats the purpose of a shared rule engine |
