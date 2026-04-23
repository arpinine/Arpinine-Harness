---
governs: specs/001-support-triage-agent
supersedes: ~
status: Accepted
date: 2026-04-23
covers:
  - decision:001-support-triage-agent:harness-boundary
---

# ADR-0001: Fake Harness Adapter Boundary

## Status
Accepted

## Context
The demo needs to show harness governance without requiring a real harness runtime or external service. The product behavior still needs tool-call evidence, approval evidence, and session-scoped memory evidence.

## Decision
Use an internal `SupportAgentRuntime` interface in the application layer and implement `FakeHarnessRuntime` in the adapter layer.

Product domain and application code must not depend directly on a harness SDK. A future OpenHarness or other runtime implementation can replace the fake adapter behind the same interface.

## Consequences
- Positive: the demo is runnable with only Python and still shows the harness boundary.
- Positive: runtime-specific code has an explicit adapter seam.
- Negative: the fake adapter does not prove production runtime behavior.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Direct harness SDK import in application code | Couples product logic to the runtime and violates the harness strategy |
| Require OpenHarness for the demo | Makes the first-run demo heavier and less portable |
