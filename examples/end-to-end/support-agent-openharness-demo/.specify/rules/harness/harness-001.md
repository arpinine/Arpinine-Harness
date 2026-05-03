---
rule-id: harness-001
category: harness
triggers:
  - "OpenHarness runtime import outside adapter or infrastructure layer"
prevents: "Product code coupling directly to the OpenHarness SDK"
source-adr: ADR-0001
evidence-project: 001-support-triage-openharness-agent
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
OpenHarness imports (`from openharness.*`, `import openharness`) must appear only in adapter or infrastructure modules, never in product domain or application service code.

## Detection Pattern
- File path is outside adapter or infrastructure modules
- File content imports or references an OpenHarness module

## Correct Pattern

```text
product feature / application service
        |
        v
SupportAgentRuntime interface (application layer)
        |
        v
OpenHarnessAdapter (adapters layer — only file with openharness imports)
        |
        v
QueryEngine, ToolRegistry, PermissionChecker (OpenHarness SDK)
```
