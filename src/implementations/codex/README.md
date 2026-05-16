# Codex Implementation Plan

This directory owns the Codex-specific implementation layer for Arpinine Harness.

The intended abstraction is the common-denominator implementation contract:
- `assemble`
- `build`
- `delivery`
- `register`
- `validate-structure`

Codex participates in that shared contract. Claude-specific native operations such as plugin install/uninstall/native validate are not part of the common abstraction.

## Current Status

Implemented now:
- `.codex-plugin/plugin.json` manifest for Codex
- source marketplace template at `src/implementations/codex/marketplace.json`
- shared hook wiring through `hooks/hooks.json`, including automatic delivery-matrix refresh on `plan.md` writes
- shared multi-team coordination inherited from the core, including task-claim enforcement and style-governance checks
- generated marketplace manifest at `dist/.agents/plugins/marketplace.json`
- real marketplace registration via `codex plugin marketplace add ./dist`
- first Codex skills that wrap the shared Arpinine Harness workflows:
  - `at-discover`
  - `at-bootstrap-from-code`
  - `at-adr`
  - `at-audit`
  - `at-eval`
  - `at-implement`
  - `at-init`
  - `at-new`
  - `at-observe`
  - `at-review`
  - `at-retro`
  - `at-status`
  - `at-plan`
- Codex-native specialist skill wrappers for shared agent roles:
  - `product-owner`
  - `tech-architect`
  - `security-reviewer`
  - `ai-engineer`
  - `devops`
  - `data-engineer`
  - `tdd-guide`
  - `domain-linguist`

Not implemented yet:
- richer install-surface metadata beyond the current marketplace registration flow

Build packaging intentionally strips test directories from assembled plugin artifacts so host/plugin validation does not re-run the shared core test suite from `dist/plugins/`.

## Goal

Add a real Codex implementation without changing the shared Arpinine Harness core contract and without regressing the working Claude implementation.

Codex is expected to participate in the same multi-team operating model as Claude:

- shared governed artifacts under `.specify/`
- shared task leases under `.specify/coordination/`
- shared style standards under `tools/style/`
- no Codex-specific fork of task-ownership or style-governance semantics

## Scope

1. Define the Codex host contract.
   Determine what a Codex implementation means for this repo:
   - metadata format
   - command surface
   - installation flow
   - validation entrypoints
   - hooks model
   - agent and skill support

2. Map Arpinine Harness core features to Codex capabilities.
   Classify shared core assets as:
   - directly reusable
   - requires Codex-specific adaptation
   - unsupported in Codex v1

3. Create the Codex implementation package layout.
   Add only Codex-specific files under this directory:
   - implementation metadata
   - command wiring
   - register and validate docs
   - optional adapter files if Codex needs a different package shape

4. Add build support for Codex.
   Extend the implementation-aware build so `IMPLEMENTATION=codex` assembles a valid Codex package without affecting Claude behavior.

5. Implement the smallest supported Codex feature set first.
   Initial target:
   - `/arpinine-harness:at-init`
   - `/arpinine-harness:at-discover`
   - `/arpinine-harness:at-new`
   - `/arpinine-harness:at-review`
   - `/arpinine-harness:at-plan`

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
5. Docs and registration flow are complete.

## Key Decisions

- whether Codex supports the same packaging model as Claude
- whether hooks exist natively in Codex or need script-backed/manual alternatives
- whether agents and skills are reusable as-is or need Codex-specific wrappers
- what counts as Codex v1 support if some Claude behaviors do not map cleanly

## Guardrails

- do not add Claude-specific metadata back into `src/arpinine-harness-core/`
- do not copy Claude metadata into this directory without a concrete Codex contract
- keep the shared workflow content identical across implementations unless there is a verified assistant limitation

## Main Risk

The largest risk is assuming Codex has a Claude-like plugin model. This implementation should start with contract discovery, not with cloning Claude packaging.
