# Assistant Implementation Abstraction

## Goal

Separate AgentAlign into:
- a shared workflow core
- thin assistant-specific implementation overlays

## Shared Core

`src/agent-align-core/` owns assets that should not depend on a specific coding assistant:
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
- `codex/` is a placeholder to keep the abstraction seam explicit while the implementation contract is still unknown

## Guardrails

- do not add Claude-specific metadata back into `src/agent-align-core/`
- do not create a fake Codex implementation until the runtime contract is concrete
- keep the shared workflow content identical across implementations unless there is a verified assistant limitation
