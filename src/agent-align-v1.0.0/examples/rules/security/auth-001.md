---
rule-id: auth-001
category: security
triggers:
  - spec contains "login" OR "authenticate" AND no rate-limiting requirement exists
  - auth endpoint added to code without corresponding rate-limit entry in spec
prevents: authentication bypass via unconstrained brute-force login attempts
source-adr: ~
evidence-project: example
severity: CRITICAL
active: true
---

## Rule

Any spec that introduces a login or authentication flow must include an explicit rate-limiting requirement (FR or NFR). Implementations that add auth endpoints without this requirement are blocked until the spec is updated.

## Detection Pattern

- Spec contains keywords: `login`, `authenticate`, `sign in`, `password`
- No requirement matching: `rate.limit`, `throttl`, `max.*attempt`, `lockout`
- OR: implementation path contains `/auth/`, `/login`, `/session` with no corresponding spec requirement

## Correct Pattern

```markdown
## Non-Functional Requirements
- NFR-002: Login endpoint SHALL enforce a maximum of 5 failed attempts per account per 15 minutes before locking the account temporarily.
```
