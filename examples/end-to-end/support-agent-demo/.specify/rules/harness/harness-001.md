---
rule-id: harness-001
category: harness
triggers:
  - "Harness runtime import outside adapter or infrastructure layer"
prevents: "Product code coupling directly to a harness SDK"
source-adr: ADR-0001
evidence-project: 001-support-triage-agent
severity: HIGH
active: true
file_patterns:
  - "app/**/*.py"
forbidden_patterns:
  - "openharness"
allowed_paths:
  - "app/support_triage/adapters/**"
---

## Rule
Harness runtime imports must appear only in adapter or infrastructure modules, never in product domain or application service code.

## Detection Pattern

- File path is outside adapter or infrastructure modules
- File content imports or references a concrete harness runtime

## Correct Pattern

```text
product feature / application service
        |
        v
internal runtime interface
        |
        v
harness adapter
```
