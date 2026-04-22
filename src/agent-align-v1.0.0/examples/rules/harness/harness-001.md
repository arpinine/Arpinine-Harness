---
triggers:
  - "OpenHarness import outside adapter or infrastructure layer"
prevents: "Product code coupling directly to a harness SDK"
source-adr: ~
evidence-project: example-product
severity: HIGH
active: true
---

# harness-001

## Rule
OpenHarness imports must appear only in adapter or infrastructure modules, never in product domain or application service code.

## Why
This preserves the harness abstraction boundary and keeps the product portable across runtimes.

## Enforcement Hint
If a product-facing module imports an OpenHarness package directly, require refactoring behind an internal runtime interface or adapter.
