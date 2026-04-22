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
- which harness/runtime is selected
- what abstraction boundary isolates the application from the harness
- what tools the harness can access
- what memory/state model is allowed
- how permissions and safety checks are handled
- how the harness is evaluated and monitored

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

## Enforcement Rules

| Rule | Severity | Action |
|------|----------|--------|
| Harness-based feature missing `## Harness Strategy` | HIGH | Block implementation |
| Plan does not define abstraction boundary around the harness | HIGH | Block implementation |
| Tool, memory, or permission model is undocumented | HIGH | Block implementation |
| Harness choice has long-term impact but no ADR exists | MEDIUM | Suggest ADR creation |
| Evaluation plan ignores harness-specific behavior | MEDIUM | Require plan improvement |

## Review Questions

1. Why does this feature need a harness instead of a simpler workflow?
2. Where is the boundary between product logic and harness runtime?
3. Which tools and permissions does the harness require?
4. How is state or memory persisted, scoped, and reset?
5. How would the team replace the harness later with minimal product change?
