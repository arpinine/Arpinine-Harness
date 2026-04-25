# Codex Implementation Placeholder

This directory reserves the Codex-specific implementation layer for AgentAlign.

Current scope:
- define the boundary between the shared AgentAlign core and any Codex-specific metadata
- avoid leaking Claude-specific packaging assumptions into the shared workflow assets
- provide a stable place for future Codex command, agent, or packaging adapters

Planned responsibilities for a future Codex implementation:
- implementation-specific metadata and packaging
- implementation-specific command wiring
- implementation-specific installation and validation steps

Non-goals for this placeholder:
- pretending Codex packaging is already defined
- copying Claude metadata into a second implementation directory without a real contract
