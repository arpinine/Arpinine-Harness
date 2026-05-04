---
governs: specs/001-plugin-abstraction
supersedes: ~
status: Proposed
date: 2026-04-25
covers:
  - decision:001-plugin-abstraction:assemble-as-build-primitive
---

# ADR-0003: assemble target as composition primitive for build and install

## Status
Proposed

## Context
The plugin has two production targets: a zip artifact for distribution and an installed copy for local development. Both require the same composition step — merging `src/arpinine-harness-core/` with `src/implementations/<assistant>/` into a single directory.

Without a shared primitive, `build` and `install` would each need to duplicate the merge logic, risking divergence (e.g., install copies files that build omits, or vice versa). A one-step `make build` that implicitly does everything is opaque and harder to debug when assembly fails mid-way.

## Decision
`make assemble IMPLEMENTATION=<assistant>` is the single composition primitive. It:
1. Cleans the prior build directory
2. Copies `src/arpinine-harness-core/` into `BUILD_DIR`
3. Overlays `src/implementations/<assistant>/` onto `BUILD_DIR`
4. Removes dev artifacts (pycache, pyc, empty dirs)
5. Copies `BUILD_DIR` to `dist/plugins/<assistant>/` as the stable registration target

Both `make build` and `make install` call `assemble` as their first step. Neither duplicates the merge logic.

## Consequences
- Positive: Build and install are guaranteed to produce identical composed output from the same source.
- Positive: The composition logic is in one place — bugs in merge order or file exclusion are fixed once.
- Positive: `assemble` can be run independently for inspection without producing a zip or triggering install.
- Negative: Every `make build` or `make install` starts with a clean + full copy, even when only one file changed. No incremental assembly.
- Negative: Developers unfamiliar with the pattern must learn that `dist/plugins/` is an assemble output, not a source directory.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Inline merge logic in both `build` and `install` | Duplication; divergence between targets is guaranteed over time |
| Single `make all` target combining everything | Opaque; cannot inspect assembled output without also building the zip or triggering install side-effects |
| Use a scripted installer that merges at install time only | Zip artifact would not contain the composed result; distribution and installation would differ structurally |
