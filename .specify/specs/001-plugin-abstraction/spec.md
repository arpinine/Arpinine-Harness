# Spec: Plugin Platform Abstraction

## Business Case

AgentAlign governance workflows should be available to any team regardless of which AI coding assistant they use. Tying the plugin to a single assistant platform limits adoption and forces teams to choose between governance and their preferred tooling. A platform abstraction separates the shared governance core from assistant-specific delivery so both can evolve independently.

## User Stories

- As a plugin author, I want to maintain one shared governance core and add new assistant implementations independently, so that new platform support does not require changes to existing workflow logic.
- As a team member using Claude Code, I want to install and use AgentAlign governance commands natively in my assistant, so that the workflow fits my existing tool.
- As a team member using Codex, I want to install and use AgentAlign governance commands in Codex, so that I get the same governance guarantees without switching assistants.
- As a plugin author, I want to build and package the plugin for a specific assistant from a single command, so that releases are repeatable and not error-prone.

## Requirements

- FR-001: The system SHALL maintain a shared core containing all governance behavior — commands, runtime hooks, agent definitions, and reusable templates — independent of any assistant platform.
- FR-002: The system SHALL support at least two assistant implementations: Claude Code and Codex.
- FR-003: Each assistant implementation SHALL contribute only the artifacts required by that platform. Governance behavior SHALL NOT be duplicated in implementation layers.
- FR-004: The build process SHALL compose core and implementation into a single deployable artifact per assistant.
- FR-005: The deployed plugin SHALL be installable from a stable local path that persists across builds.
- FR-006: The build process SHALL be invocable via a single command that accepts an implementation selector, so that builds for different assistants do not require editing build scripts.
- FR-007: The system SHALL validate that required source directories exist before beginning assembly and SHALL fail with a named error identifying the missing component.

## Non-Functional Requirements

- NFR-001: Adding a new assistant implementation SHALL require no changes to the shared core.
- NFR-002: The assembly process SHALL be idempotent — running it twice from the same source state SHALL produce output with identical file contents and directory structure.
- NFR-003: The stable registration target SHALL survive clean rebuilds without requiring re-registration.
- NFR-004: The build output SHALL not include development artifacts (caches, bytecode, empty directories).

## Acceptance Criteria

- [ ] AC-001: Given a build invoked with the Claude implementation selector, a zip artifact is produced and the stable registration directory is populated with the assembled plugin.
- [ ] AC-002: Given a build invoked with the Codex implementation selector, a zip artifact is produced and the stable Codex registration directory is populated with the assembled plugin.
- [ ] AC-003: Given a missing core or implementation source directory, the build halts with an error naming the missing component before creating any output files or directories.
- [ ] AC-004: Given a build run twice from the same source, a recursive file-content comparison of the two outputs reports no differences.
- [ ] AC-005: Given a Claude Code install, all core governance commands are available as `/agent-align:at-new`, `/agent-align:at-plan`, `/agent-align:at-implement`, and the remaining `/agent-align:at-*` commands.
- [ ] AC-006: Given a Codex install, the implemented subset of governance commands is available and the remaining commands are absent or marked explicitly as not yet implemented.
- [ ] AC-007: Given a new implementation directory added under the implementations source root, the build produces a valid assembled artifact without changes to the shared core source.

## Out of Scope

- Auto-discovery of new implementations at build time
- Remote marketplace publishing or version management
- Runtime feature flags or capability negotiation between implementations
- Workflow parity between Claude Code and Codex implementations (parity is a separate concern)
- CI/CD pipeline automation for releases

## Operating Constraints

- The plugin has no agent runtime dependency. No harness strategy is required.
- Each assistant platform imposes its own plugin manifest format. The abstraction must accommodate divergent manifest schemas without leaking platform details into the shared core.
- The local marketplace registration path must remain stable across `make clean` cycles to avoid requiring manual re-registration after each rebuild.

## Open Questions

- OQ-001: Should a new implementation require a specific directory contract (required files, naming conventions) enforced at build time, or is the current convention-based approach sufficient?
- OQ-002: What is the intended parity target for Codex — full parity with Claude, or a stable supported subset?
- OQ-003: Should `make install` validate the plugin manifest format before registering to the marketplace?
- OQ-004: Is there a planned third implementation (e.g., Gemini, Cursor Agent) that would stress-test the abstraction boundary?

## Related ADRs

- ADR-0001: Separate shared core from assistant-specific implementations — governs core/impl boundary
- ADR-0002: Stable plugins/ dir as local marketplace registration target — governs registration path
- ADR-0003: assemble target as composition primitive for build and install — governs build composition
