---
governs: specs/001-support-triage-openai-agent
supersedes: ~
status: Accepted
date: 2026-05-03
covers:
  - decision:001-support-triage-openai-agent:harness-boundary
---

# ADR-0001: OpenAI Responses Adapter Boundary

## Status
Accepted

## Context
The demo needs to show a practical harness application on top of a real model provider without leaking SDK usage into product code.

## Decision
Use an internal `SupportAgentRuntime` interface in the application layer and implement `OpenAIHarnessRuntime` in the adapter layer.

The application service owns deterministic ticket classification and priority rules. The adapter owns prompt construction, OpenAI API calls, approval evidence, and session-scoped runtime events.

## Consequences
- Positive: product logic is testable without network access.
- Positive: provider-specific code has an explicit replacement seam.
- Positive: harness-specific evidence remains observable and evaluable.
- Negative: live evaluation depends on credentials and network access.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Direct OpenAI SDK import in application code | Couples product logic to the provider and violates the harness strategy |
| Put classification and priority generation inside the model prompt | Makes business behavior harder to test and less stable across runs |
