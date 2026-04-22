---
name: architecture-governor
description: Enforces modular and clean architecture expectations for planned and implemented systems
---

# Architecture Governor Skill

## Purpose

This skill ensures the team turns specifications into systems with explicit boundaries, low coupling, and testable dependencies.
It does not force a single architecture style, but it requires architectural discipline.

## Core Expectations

- responsibilities are split into coherent modules
- business rules are isolated from delivery and infrastructure concerns
- dependency direction is intentional and documented
- external integrations sit behind explicit interfaces or adapters
- modules can be tested without booting the whole system

## Required Architectural Checks

For any non-trivial feature, plan.md must define:
- module or component boundaries
- responsibility of each boundary
- allowed dependency direction
- integration seams or adapter points
- testing strategy per boundary

## Clean Architecture Heuristics

Good signs:
- domain logic does not depend directly on framework code
- transport, persistence, and third-party APIs are replaceable
- orchestration is separated from core business rules
- module APIs are small and explicit

Warning signs:
- one module owns unrelated concerns
- handlers/controllers contain business logic
- database or framework types leak across layers
- cross-module imports create circular or hidden coupling
- feature changes require edits across many unrelated files

## Enforcement Rules

| Rule | Severity | Action |
|------|----------|--------|
| Plan missing explicit module boundaries | HIGH | Block implementation |
| Plan missing dependency direction or interface seams | HIGH | Block implementation |
| Spec or plan implies tightly coupled design without rationale | HIGH | Require refinement |
| ADR-worthy architecture choice is undocumented | MEDIUM | Suggest ADR creation |
| Tests do not align with module boundaries | MEDIUM | Require plan improvement |

## Review Questions

1. What are the core modules or components for this feature?
2. Which module owns business rules?
3. Which dependencies point inward, and which are adapters?
4. How could one module be tested in isolation?
5. Which decisions are consequential enough to require ADRs?
