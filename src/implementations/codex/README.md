# Codex Implementation Plan

This directory owns the Codex-specific implementation layer for AgentAlign.

## Current Status

Implemented now:
- `.codex-plugin/plugin.json` manifest for Codex
- initial repo marketplace entry at `.agents/plugins/marketplace.json`
- first Codex skills that wrap the shared AgentAlign workflows:
  - `at-init`
  - `at-new`
  - `at-review`
  - `at-plan`

Not implemented yet:
- remaining workflow commands
- Codex-specific hook wiring
- agent wrapper strategy for `product-owner`, `tech-architect`, `security-reviewer`, and `tdd-guide`
- published plugin assets and richer install-surface metadata

## Goal

Add a real Codex implementation without changing the shared AgentAlign core contract and without regressing the working Claude implementation.

## Scope

1. Define the Codex host contract.
   Determine what a Codex implementation means for this repo:
   - metadata format
   - command surface
   - installation flow
   - validation entrypoints
   - hooks model
   - agent and skill support

2. Map AgentAlign core features to Codex capabilities.
   Classify shared core assets as:
   - directly reusable
   - requires Codex-specific adaptation
   - unsupported in Codex v1

3. Create the Codex implementation package layout.
   Add only Codex-specific files under this directory:
   - implementation metadata
   - command wiring
   - install and validate docs
   - optional adapter files if Codex needs a different package shape

4. Add build support for Codex.
   Extend the implementation-aware build so `IMPLEMENTATION=codex` assembles a valid Codex package without affecting Claude behavior.

5. Implement the smallest supported Codex feature set first.
   Initial target:
   - `/agent-align:at-init`
   - `/agent-align:at-new`
   - `/agent-align:at-review`
   - `/agent-align:at-plan`

6. Add Codex-specific shims only where required.
   Keep shared prompts and workflow assets in the core unless Codex imposes a real limitation.

7. Validate end to end.
   Required checks:
   - `make assemble IMPLEMENTATION=codex`
   - Codex package structure validation
   - smoke test for at least one Codex command flow
   - regression build for `IMPLEMENTATION=claude`

## Recommended Milestones

1. Codex contract note or ADR.
2. `IMPLEMENTATION=codex` assembles successfully.
3. Minimal command set works in Codex.
4. Remaining commands and hooks are ported or explicitly marked unsupported.
5. Docs and install flow are complete.

## Key Decisions

- whether Codex supports the same packaging model as Claude
- whether hooks exist natively in Codex or need script-backed/manual alternatives
- whether agents and skills are reusable as-is or need Codex-specific wrappers
- what counts as Codex v1 support if some Claude behaviors do not map cleanly

## Guardrails

- do not add Claude-specific metadata back into `src/agent-align-core/`
- do not copy Claude metadata into this directory without a concrete Codex contract
- keep the shared workflow content identical across implementations unless there is a verified assistant limitation

## Main Risk

The largest risk is assuming Codex has a Claude-like plugin model. This implementation should start with contract discovery, not with cloning Claude packaging.
