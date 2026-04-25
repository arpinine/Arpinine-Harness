---
governs: specs/001-plugin-abstraction
supersedes: ~
status: Proposed
date: 2026-04-25
covers:
  - decision:001-plugin-abstraction:local-marketplace-registration-path
---

# ADR-0002: Stable plugins/ dir as local marketplace registration target

## Status
Proposed

## Context
Claude Code's local marketplace registration (`claude plugin marketplace add <path>`) requires a stable directory path. Once registered, that path is stored in the user's Claude config and must remain valid across rebuilds.

The `make assemble` step outputs to `dist/`, which is cleaned on every `make clean`. If `dist/` were used as the registration target, every rebuild would break the marketplace registration and require manual re-registration. This would make the install flow fragile and error-prone for developers working on the plugin.

## Decision
The assembled Claude plugin output is copied to `plugins/agent-align-claude/` after every assemble. This directory is:
- excluded from `make clean` for the purpose of re-registration (the clean step removes it before re-copying, not before registration)
- used as the sole target for `claude plugin marketplace add ./`
- committed to the repo so it is always present after clone

The `dist/` directory is used only for the zip artifact, not for registration. The `plugins/` directory is the stable registration target.

## Consequences
- Positive: `make install` is idempotent — marketplace registration survives multiple rebuilds without manual steps.
- Positive: New contributors can install from the repo without running assemble first.
- Positive: The registration path is predictable and documentable.
- Negative: `plugins/agent-align-claude/` is a generated artifact committed to the repo. It must stay in sync with `src/`. Forgetting to run `make assemble` before committing leaves a stale copy.
- Negative: Two copies of the assembled plugin exist simultaneously (`plugins/` and potentially `dist/`). The `plugins/` copy is the installed one; the zip is the distributable. These can diverge if not built together.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Use `dist/<build-name>/` as registration target | Cleaned on `make clean`; registration breaks after every rebuild |
| Use `src/agent-align-core/` directly as registration target | Core directory lacks implementation-specific artifacts; not a valid assembled plugin |
| Register from a fixed symlink pointing to `dist/` | Symlinks are fragile across clean cycles and not portable across operating systems |
