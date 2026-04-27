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

## Current Status

- `claude/` contains the existing working implementation, including `.claude-plugin/plugin.json`
- `codex/` now contains the first real Codex plugin scaffold: `.codex-plugin/plugin.json`, a repo marketplace entry, and initial skill wrappers for the shared workflow

## Guardrails

- do not add Claude-specific metadata back into `src/arpinine-harness-core/`
- do not create a fake Codex implementation until the runtime contract is concrete
- keep the shared workflow content identical across implementations unless there is a verified assistant limitation
