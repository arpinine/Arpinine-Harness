---
name: rule-manager
description: Manages the growing rules/ directory. Loads, enforces, and extends machine-readable rules that compound across projects. Invoked by drift-detector and constitution-enforcer to apply learned constraints. Invoked by spec-retro to add new rules from completed work.
---

# rule-manager

Rules compound across projects. Each drift finding or retro lesson becomes a persistent rule that blocks the same failure in future work.

## Rule File Format

Rules live at `.specify/rules/<category>/<rule-id>.md`.

```yaml
---
rule-id: auth-001
category: security
triggers:
  - "rate.limit" in spec AND rate limiting absent from implementation path
  - auth endpoint added without corresponding spec entry
prevents: authentication bypass via unconstrained login attempts
source-adr: ADR-0003
evidence-project: 001-user-login
severity: CRITICAL
active: true
---

## Rule

[One paragraph describing what this rule enforces and why it exists.]

## Detection Pattern

[How to detect a violation: file patterns, code patterns, spec keywords that should trigger a check.]

## Correct Pattern

[What compliant code/spec looks like.]
```

## Categories

| Category | Description |
|----------|-------------|
| `security` | Auth, secrets, injection, access control |
| `architecture` | Module boundaries, dependency direction, coupling |
| `spec-quality` | Measurability, scope discipline, AC format |
| `evaluation` | Eval plan gaps, missing thresholds, stale results |
| `process` | ADR coverage, drift resolution, retro discipline |

## Operations

### load-rules

Load all active rules for a given category or all categories:
```
rules = load_rules(category=None)  # all active rules
```

1. Scan `.specify/rules/**/*.md` for files with `active: true`
2. Parse frontmatter: `rule-id`, `category`, `triggers`, `prevents`, `severity`
3. Return structured list grouped by category

### check-rules(file_path, content)

Given a file being written and its content, check all loaded rules:
1. Load all active rules
2. For each rule, evaluate `triggers` against file path and content
3. Return violations with: rule-id, severity, description of match, `prevents` value

### add-rule(finding, source_type, source_ref)

Convert a drift finding or retro lesson into a new rule:
1. Derive `category` from finding type (security finding → security, arch violation → architecture)
2. Generate `rule-id` as `<category-prefix>-<NNN>` (auto-increment within category)
3. Set `source-adr` if drift finding had an ADR created for it
4. Set `source-type` to `drift` or `retro`
5. Set `active: true`
6. Write to `.specify/rules/<category>/<rule-id>.md`
7. Confirm: "Rule <rule-id> added."

### list-rules

Show all rules in `.specify/rules/`:
```
RULES INDEX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID          Category       Severity  Prevents
auth-001    security       CRITICAL  Auth bypass via unconstrained login
arch-001    architecture   HIGH      Business logic coupled to HTTP layer
spec-001    spec-quality   MEDIUM    Acceptance criteria not measurable
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 active rules
```

## Integration Points

- **drift-detector**: after drift findings, calls `check-rules` to detect known patterns before creating new ADRs
- **constitution-enforcer**: calls `check-rules` on PreToolUse to block known violations
- **spec-retro**: calls `add-rule` to persist lessons from completed work
- **spec-status**: calls `list-rules` to report rule coverage in governance summary

## Invariants

- Rule IDs are stable once assigned — never reuse a rule-id, even if the rule is deactivated
- `active: false` disables enforcement without deleting the rule or its history
- Every rule sourced from a drift finding SHOULD have a `source-adr` field
- Rules accumulate — they are never deleted, only superseded by a newer rule with `supersedes: <rule-id>`
