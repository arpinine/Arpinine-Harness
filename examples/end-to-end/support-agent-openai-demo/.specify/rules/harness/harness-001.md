---
rule-id: harness-001
category: harness
triggers:
  - "Model SDK import outside adapter or infrastructure layer"
prevents: "Product code coupling directly to a model provider SDK"
source-adr: ADR-0001
evidence-project: 001-support-triage-openai-agent
severity: HIGH
active: true
file_patterns:
  - "app/**/*.py"
forbidden_patterns:
  - "from openai import OpenAI"
  - "import openai"
allowed_paths:
  - "app/support_triage/adapters/**"
  - "app/_drift_fixtures/**"
---

## Rule
Model SDK imports must appear only in adapter or infrastructure modules, never in domain or application service code.
