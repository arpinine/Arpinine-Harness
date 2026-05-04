---
governs: specs/002-arpinine-harness-core-workflow
supersedes: ~
status: Accepted
date: 2026-05-04
covers:
  - decision:002-arpinine-harness-core-workflow:hook-enforcement-as-hard-gate
---

# ADR-0008: PreToolUse hooks as blocking enforcement gates

## Status
Accepted

## Context
The governance workflow must prevent implementation-path edits that violate declared constraints — missing architecture readiness, undeclared style standards, absent task claims, or constitution violations. Two enforcement models are possible: advisory (warn but allow) and blocking (deny the tool use until the condition is resolved).

Advisory enforcement relies on developer discipline. In a multi-team context where sessions are independent and context is not persisted between runs, advisory warnings are routinely skipped under delivery pressure. The governance contract then becomes optional rather than enforced.

## Decision
All spec-gated enforcement scripts are wired to the `PreToolUse` hook with `matcher: Edit|Write`. A non-zero exit code from a hook script causes Claude Code to block the tool use and surface the error to the user. Scripts exit 0 to allow, exit 1 to block.

PostToolUse hooks (drift check, delivery matrix update) remain advisory — they exit 0 regardless and surface warnings without blocking.

Scripts MUST be stateless: given the same artifact store contents, a script MUST return the same exit code. No session state is read or written between invocations.

## Consequences
- Positive: Governance is enforced structurally, not by discipline — teams cannot skip gates without resolving the underlying condition.
- Positive: Stateless scripts are deterministic and testable with mock inputs without session setup.
- Positive: The gate boundary is explicit in `hooks/hooks.json`; no logic is embedded in the hook manifest.
- Negative: A misconfigured enforcement script that exits 1 incorrectly blocks all writes — false positives have high impact. Scripts must fail open (exit 0) on unexpected input rather than blocking.
- Negative: Hook enforcement applies only when the plugin is installed and active. Governance is not enforced in environments where the plugin is absent.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Advisory warnings only (PostToolUse) | Warnings are ignored under pressure; governance becomes effectively optional |
| Enforcement at commit time (pre-commit hook) | Catches violations after edits are made; does not prevent violations from entering the working tree |
| Inline model-level warnings without scripts | Non-deterministic; model behavior is not a reliable gate |
