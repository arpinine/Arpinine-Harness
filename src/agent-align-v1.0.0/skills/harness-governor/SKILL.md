---
name: harness-governor
description: Enforces harness strategy, abstraction boundaries, and operational guidelines for product-facing agent systems
---

# Harness Governor Skill

## Purpose

This skill ensures teams do not embed a harness into product code casually or opaquely.
It requires teams to document why a harness is needed, how it is isolated, and how tools, memory, permissions, and evaluation are governed.

## When To Apply

- During planning for any product feature that uses an agent harness
- Before implementation begins for agentic application flows
- During audit when failures may be caused by harness misuse, weak boundaries, or missing controls

## Required Harness Strategy

For harness-based features, the plan must define:
- why a harness is needed
- which runtime class is selected
- what abstraction boundary isolates the application from the harness
- what tools the harness can access
- what memory/state model is allowed
- how permissions and safety checks are handled
- how the harness is evaluated and monitored
- how the harness could be replaced later with bounded application change

## Good Signs

- application code depends on an internal interface, not directly on a harness SDK everywhere
- tool permissions are explicit and narrow
- memory usage is bounded and intentional
- swapping harnesses would change an adapter, not the whole product
- evaluation covers task quality and harness-specific failure modes

## Warning Signs

- product logic is tightly coupled to a single harness API
- tool access is broad without justification
- memory/state handling is undocumented
- agent behavior cannot be reproduced or tested outside a full runtime
- evaluation ignores harness-specific risks like tool misuse or uncontrolled autonomy

## OpenHarness-Specific Checks

When the plan selects OpenHarness explicitly:
- require a product-facing abstraction boundary such as an internal runtime interface or adapter
- require OpenHarness-specific code to stay in the adapter or infrastructure layer
- require the plan to describe tool registration and approval callback behavior
- require the plan to describe session/message state handling and reset behavior
- require evaluation to cover tool permission failures, approval flow correctness, and runtime recovery paths

## Observation Integration

Observation artifacts can validate whether actual runtime behavior matches the documented harness strategy.
Use them to check:
- observed tool calls vs tool allowlist
- observed approval events vs permission model
- observed memory writes vs memory model
- observed failures and retries vs evaluation coverage

## Enforcement Rules

| Rule | Severity | Action |
|------|----------|--------|
| Harness-based feature missing `## Harness Strategy` | HIGH | Block implementation |
| Plan does not define abstraction boundary around the harness | HIGH | Block implementation |
| Tool, memory, permission, or swap strategy is undocumented | HIGH | Block implementation |
| Product code is expected to call the harness directly rather than through an internal boundary | HIGH | Block implementation |
| Harness choice has long-term impact but no ADR exists | MEDIUM | Suggest ADR creation |
| Evaluation plan ignores harness-specific behavior | MEDIUM | Require plan improvement |
| OpenHarness is selected but adapter-layer isolation is not defined | HIGH | Block implementation |
| OpenHarness is selected but approval callback or permission flow is undocumented | HIGH | Block implementation |
| OpenHarness is selected but session or state handling is undocumented | HIGH | Block implementation |
| Observation artifacts show tool, permission, or memory behavior that contradicts the harness strategy | CRITICAL | Block completion |

## Review Questions

1. Why does this feature need a harness instead of a simpler workflow?
2. Where is the boundary between product logic and harness runtime?
3. Which tools and permissions does the harness require?
4. How is state or memory persisted, scoped, and reset?
5. How would the team replace the harness later with minimal product change?
6. If OpenHarness is used, which adapter owns the OpenHarness dependency?
7. If OpenHarness is used, how are tool approvals and session lifecycle controlled?
