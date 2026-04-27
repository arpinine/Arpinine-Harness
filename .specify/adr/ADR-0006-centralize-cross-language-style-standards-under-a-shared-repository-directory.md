---
governs: specs/008-cross-language-code-style-governance
supersedes: ~
status: Proposed
date: 2026-04-25
covers:
  - decision:008-cross-language-code-style-governance:canonical-style-config-directory
---

# ADR-0006: Centralize cross-language style standards under a shared repository directory

## Status
Proposed

## Context
With multiple teams and assistant implementations operating on the same repository, style consistency can no longer depend on editor defaults, assistant-local habits, or language-specific config files scattered opportunistically through the root directory.

The repository needed one shared contract that makes style standards visible, assistant-neutral, and enforceable through shared hooks. Root-level style files would work technically, but they mix operational standards with general repository structure and make it less clear which files are the canonical style source that every team and plugin must follow.

The style-governance hook also needed an unambiguous place to look for repository-approved standards so it can block code edits when a language lacks a declared style contract.

## Decision
Arpinine Harness stores canonical code-style standards under `tools/style/` and treats that directory as the shared source of truth for repository formatting and lint expectations.

The structure is:

| Path | Role |
|------|------|
| `tools/style/shared/.editorconfig` | Shared text and indentation defaults |
| `tools/style/python/pyproject.toml` | Python style and formatting standard |
| `tools/style/frontend/.prettierrc.json` | Frontend formatting standard |
| `tools/style/frontend/eslint.config.cjs` | Frontend lint standard |
| `tools/style/java/checkstyle.xml` | Java style standard |
| `tools/style/rust/rustfmt.toml` | Rust formatting standard |
| `tools/style/README.md` | Canonical usage and path documentation |

The constitution declares shared style standards mandatory. The shared style-governance hook enforces the executable subset of that policy by checking for the presence of the canonical config files under `tools/style/` before allowing implementation-path edits in supported languages.

## Consequences
- Positive: Claude, Codex, and future teams use one canonical directory for style standards.
- Positive: Shared hooks can validate style governance deterministically without assistant-specific logic.
- Positive: Language-native config formats remain visible and reusable by humans, CI, and editor integrations.
- Positive: The repository makes style governance explicit instead of relying on root-level convention or hidden tool defaults.
- Negative: Some tools will no longer auto-discover config from the repo root and must be invoked with explicit config paths.
- Negative: The team must maintain documentation or wrapper commands so contributors know how to run tools against the canonical path.
- Negative: Moving config out of the root adds a small amount of setup friction for external tooling that assumes default discovery.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Keep style config in the repository root | Works technically, but does not provide one clearly scoped governance directory for cross-language style standards |
| Allow each assistant implementation to carry its own style config | Violates the shared-core governance model and allows team-specific drift |
| Rely only on `.editorconfig` for all languages | Too weak for language-specific linting and formatting behavior, especially for frontend, Java, and Python |
| Enforce style only through human instructions in prompts | Not reliable enough for multi-team execution and does not create an inspectable repository contract |
