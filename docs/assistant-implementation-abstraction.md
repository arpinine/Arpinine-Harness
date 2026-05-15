# Assistant Implementation Abstraction

## Goal

Separate Arpinine Harness into:
- a shared workflow core
- thin assistant-specific implementation overlays

## Shared Core

`src/arpinine-harness-core/` owns assets that should not depend on a specific coding assistant:
- commands
- agents
- hooks
- scripts
- skills
- templates
- shared documentation and changelog

## Implementation Overlay

`src/implementations/<assistant>/` owns only assistant-specific concerns:
- plugin metadata
- installation contract
- validation entrypoints
- any future assistant adapter files that cannot live in the shared core

## Feature Addition Strategy

Every new feature should follow the same pattern:

1. Define the workflow once in `src/arpinine-harness-core/`
2. Keep agent behavior and command semantics assistant-agnostic
3. Add only the minimum implementation overlay each host needs to expose that shared workflow
4. Do not fork workflow logic between Claude and Codex unless the host contract forces a real divergence

Applied concretely:

- Claude consumes shared `commands/` directly through the assembled plugin
- Codex consumes the same shared `commands/` through thin skill wrappers under `src/implementations/codex/skills/`
- both implementations ship the same underlying workflow after `make assemble`

## Source Vs Build Output

Only `src/` is source-of-truth.

- `src/arpinine-harness-core/` is the shared workflow source
- `src/implementations/claude/` and `src/implementations/codex/` are thin assistant-specific overlays
- `dist/plugins/arpinine-harness-claude/` and `dist/plugins/arpinine-harness-codex/` are assembled build outputs created by `make assemble`
- `dist/.claude-plugin/marketplace.json` and `dist/.agents/plugins/marketplace.json` are generated marketplace manifests used for local registration
- `dist/` contains all generated build and release artifacts

`dist/` is generated from `src/` and can be safely removed and recreated. Do not treat it as an independent implementation source tree.

## Current Status

- `claude/` contains the existing working implementation, including `.claude-plugin/plugin.json`
- `codex/` now contains the first real Codex plugin scaffold: `.codex-plugin/plugin.json`, a repo marketplace entry, and initial skill wrappers for the shared workflow

## Guardrails

- do not add Claude-specific metadata back into `src/arpinine-harness-core/`
- do not create a fake Codex implementation until the runtime contract is concrete
- keep the shared workflow content identical across implementations unless there is a verified assistant limitation
