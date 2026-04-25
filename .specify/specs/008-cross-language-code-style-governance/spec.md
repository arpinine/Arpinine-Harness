# Spec: Cross-Language Code Style Governance

## Business Case

AgentAlign now supports multiple teams and assistant implementations working in the same repository. Without one shared code-style contract, Claude, Codex, and future teams can all produce valid code that still diverges in formatting, lint expectations, and file conventions by language.

That inconsistency increases review noise, weakens trust in generated changes, and makes governance less reliable because style becomes dependent on which assistant or human happened to edit a file. The workflow needs one repository-owned, language-specific style standard that all teams follow and that shared hooks can validate before implementation edits proceed.

## User Stories

- As an engineering lead, I want all teams and plugins to follow the same language-specific style rules so repository output remains consistent.
- As a developer, I want the repository to define canonical style config locations rather than relying on assistant-local defaults.
- As a maintainer, I want style governance enforced through shared hooks and checked-in configs rather than assistant-specific instructions.

## Requirements

- FR-001: The constitution SHALL declare that repository-defined, language-specific code style standards are mandatory across all teams and plugins.
- FR-002: The repository SHALL store canonical style configuration files in one shared location rather than scattering them across assistant-specific overlays.
- FR-003: The plugin SHALL provide checked-in style configuration for Python, JavaScript/TypeScript, Java, and Rust.
- FR-004: A shared PreToolUse governance hook SHALL block implementation-path edits when a language is used without a declared repository style standard.
- FR-005: The shared style-governance hook SHALL recognize the canonical style-config directory as the source of truth.
- FR-006: The repository SHALL document the canonical style-config paths and how teams should invoke the relevant tools against them.
- FR-007: The plugin SHALL provide automated tests for style-governance blocking and allow-path behavior.

## Non-Functional Requirements

- NFR-001: Style governance SHALL remain implementation-neutral and live in shared core tooling.
- NFR-002: Style-config discovery SHALL be deterministic for the same repository contents.
- NFR-003: Teams SHALL be able to inspect the style standard without relying on assistant-local memory or hidden defaults.
- NFR-004: The style-governance hook SHALL allow editing the canonical style-config files themselves so the repository can evolve its standards.

## Acceptance Criteria

- [x] AC-001: Given a Python edit, the shared style-governance hook blocks the write when no repository Python style config is present and allows it when the canonical Python config exists.
- [x] AC-002: Given a JavaScript or TypeScript edit, the shared style-governance hook blocks the write when no repository frontend style config is present and allows it when canonical ESLint or Prettier config exists.
- [x] AC-003: Given a Java edit, the shared style-governance hook allows the write when canonical Java style config exists.
- [x] AC-004: Given a Rust edit, the shared style-governance hook allows the write when canonical Rust style config exists.
- [x] AC-005: Given the canonical style-config directory, the repository documents the path conventions clearly enough for plugin teams and humans to use the same configs.
- [x] AC-006: Given the style-governance tests, automated coverage verifies both blocking and allow-path behavior for supported languages.

## Out of Scope

- Automatically running every formatter and linter during every file write
- Defining style standards for every language the repository might ever add
- IDE/editor integration beyond checked-in repository documentation and config paths
- Replacing language-native tooling with AgentAlign-specific style engines

## AI-Nativeness Assessment

**AIN Target Level**: 2 = AI-assisted internal tooling

**Agent-Callable Operations** (for AIN >= 3):
- Not applicable. This feature governs repository standards and hooks rather than product-facing agent operations.

**Human-in-the-Loop Gates** (for AIN >= 3):
- Not applicable. Human teams still choose the exact style standard, but this feature does not add autonomous product decisions.

**Feedback Channels**:
- Pre-edit style-governance hook violations
- Repository-visible style config under `tools/style/`
- Automated tests for style-governance behavior

**Evaluation Required**: NO

## Operating Constraints

- Style governance must remain compatible with the existing shared hook model.
- The canonical style-config location must be visible to all teams and plugin implementations.
- Style rules should use language-native tools and config formats where possible.

## Open Questions

- OQ-001: Should later phases add executable wrapper targets for running each formatter or linter through the canonical config path?
- OQ-002: Which additional languages should be standardized next if the repository grows beyond the current set?

## Related ADRs

- ADR-0001: Separate shared core from assistant-specific implementations
- ADR-0006: Centralize cross-language style standards under a shared repository directory
