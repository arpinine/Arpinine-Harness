---
governs: specs/002-arpinine-harness-core-workflow
supersedes: ~
status: Proposed
date: 2026-04-25
covers:
  - decision:002-arpinine-harness-core-workflow:agent-team-structure
---

# ADR-0004: Specialized role-based agent team

## Status
Proposed

## Context
The Arpinine Harness workflow requires AI-assisted reasoning at multiple stages: validating product intent before implementation, enforcing TDD discipline during implementation, identifying architectural decisions during planning, and reviewing security before completion.

A single general-purpose agent could be invoked at each stage, but it would need to reason about product alignment, test discipline, architecture, and security simultaneously. In practice, a general agent deprioritizes concerns outside its current instruction focus — a product review instruction crowds out security analysis, and vice versa.

The team needed each governance concern to be independently enforced, with a distinct system prompt and scope, so that no concern is silently dropped when multiple concerns are active in the same workflow stage.

## Decision
The plugin defines four specialized agents, each with a single governing concern:

| Agent | Domain | Invoked At |
|-------|--------|------------|
| `product-owner` | Business case, user value, scope, acceptance criteria | Pre-implementation, pre-completion, during audit |
| `tech-architect` | Architectural decisions, ADR identification, module boundaries | During planning |
| `tdd-guide` | RED → GREEN → REFACTOR discipline, test-before-code enforcement | During implementation |
| `security-reviewer` | Security risk in plan and code changes before completion | Post-implementation, post-drift |

Each agent is invoked independently by the orchestrating command. Agents return analysis and verdicts. They do not write artifacts — that responsibility remains with the command.

## Consequences
- Positive: Each concern is enforced by a focused prompt with no competing instructions; no concern is silently dropped.
- Positive: Agents are independently invocable by any command that needs their domain, without coupling concerns together.
- Positive: Adding a new concern requires a new agent file, not modifying existing agents.
- Negative: Multiple agent invocations per command increase latency and token consumption relative to a single general agent.
- Negative: Agents must be explicitly invoked by commands — there is no automatic concern selection. A command that omits an agent invocation silently drops that concern.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Single general-purpose agent for all governance concerns | Cannot reliably enforce all concerns simultaneously; product, TDD, architecture, and security reasoning compete for attention within one prompt |
| One agent per command (ad hoc, not role-based) | Concerns are not cleanly aligned to commands (e.g., product-owner is needed at both planning and completion stages); coupling concern to command prevents reuse |
| No dedicated agents — inline reasoning in command prompts | Commands become monolithic; governance quality degrades as command instructions grow; no clear boundary between orchestration and reasoning |
