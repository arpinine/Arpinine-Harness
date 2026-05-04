---
governs: specs/001-plugin-abstraction
supersedes: ~
status: Accepted
date: 2026-04-25
covers:
  - decision:001-plugin-abstraction:core-impl-separation
---

# ADR-0001: Separate shared core from assistant-specific implementations

## Status
Accepted

## Context
Arpinine Harness must deliver the same governance workflow across multiple AI coding assistant platforms (Claude Code, Codex, and future assistants). Each platform has its own plugin manifest format, skill registration conventions, and extension points.

Without a clear boundary, platform-specific concerns (manifest format, skill wrappers) would bleed into governance logic (commands, hooks, agents, templates), making it impossible to support a new assistant without modifying shared behavior.

The team needed a structure where the complete governance workflow lives in one place and platform differences are contained to thin adapter directories.

## Decision
The plugin source is split into two layers:

1. `src/arpinine-harness-core/` — all governance logic: commands, hooks, agents, skills, scripts, and templates. This directory is platform-agnostic.
2. `src/implementations/<assistant>/` — platform-specific artifacts only: the assistant's plugin manifest and any skill wrappers or overrides that the platform requires.

A `make assemble IMPLEMENTATION=<assistant>` step merges core + implementation into a single deployable build directory. The assembled output contains everything needed to install the plugin into the target assistant.

## Consequences
- Positive: Adding a new assistant implementation requires no changes to `src/arpinine-harness-core/`.
- Positive: The governance workflow can be tested and reasoned about independently of any platform.
- Positive: Platform-specific bugs are isolated to the implementation layer.
- Negative: The `assemble` step is an indirection that developers must understand — files in `dist/` are generated, not authoritative.
- Negative: If the core grows platform conditionals (e.g., `if claude: ...`), the boundary is violated. Discipline required.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Single mixed directory with platform flags in files | Governance logic and platform concerns cannot be cleanly separated; every new platform requires modifying core files |
| One complete copy per platform | Duplicates all governance logic; changes must be applied N times and drift between copies is guaranteed |
| Runtime feature detection (no build step) | Platform manifests are structurally incompatible; a runtime approach cannot resolve format differences at install time |
