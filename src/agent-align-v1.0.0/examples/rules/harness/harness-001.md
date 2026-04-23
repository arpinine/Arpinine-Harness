---
rule-id: harness-001
category: harness
triggers:
  - "OpenHarness import outside adapter or infrastructure layer"
prevents: "Product code coupling directly to a harness SDK"
source-adr: ~
evidence-project: example-product
severity: HIGH
active: true
---

## Rule
OpenHarness imports must appear only in adapter or infrastructure modules, never in product domain or application service code.

## Detection Pattern

- Import path matches an OpenHarness package
- File path is outside adapter, gateway, integration, or infrastructure modules
- Product-facing module depends directly on the runtime SDK instead of an internal runtime interface

## Correct Pattern

```text
product feature / application service
        |
        v
internal runtime interface
        |
        v
OpenHarness adapter
```
