# Plan: Plugin Platform Abstraction

## Governing Spec
`.specify/specs/001-plugin-abstraction/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Split source into shared core + per-platform implementation directories | Isolates governance logic from platform manifest requirements; adding a new platform requires no core changes | ADR-0001 |
| `dist/plugins/<assistant>/` as stable marketplace registration target | Keeps all generated artifacts under `dist/` while preserving a deterministic registration path recreated by each assemble | ADR-0002 |
| `assemble` as shared primitive invoked by both `build` and `install` | Ensures both targets produce identical composed output; avoids duplicating merge logic | ADR-0003 |
| Implementation overlay merges core first, then impl on top | Allows implementations to override individual core files where platform requires it; core files are the default, impl files are the delta | Not an ADR — this is a consequence of ADR-0001 and ADR-0003 |

## Architecture

Two-layer source structure, single-step composition:

```
src/
  arpinine-harness-core/       ← platform-agnostic governance logic
    agents/               ← agent role definitions
    commands/             ← at-* workflow command definitions
    hooks/                ← hooks.json (PreToolUse, PostToolUse)
    scripts/              ← validation and drift check scripts
    skills/               ← skill definitions (adr-manager, drift-detector, etc.)
    templates/            ← reusable document templates

  implementations/
    claude/               ← Claude Code platform adapter
      .claude-plugin/     ← Claude manifest (plugin.json)
    codex/                ← Codex platform adapter
      .codex-plugin/      ← Codex manifest (plugin.json)
      skills/             ← Codex skill wrappers
    copilot/              ← GitHub Copilot CLI platform adapter
      plugin.json         ← Copilot manifest
      hooks/              ← Copilot hook manifest (PreToolUse/PostToolUse)
      scripts/            ← Copilot hook wrappers that normalize payloads to the shared shape
      skills/             ← Copilot skill wrappers

Makefile                  ← build orchestrator (assemble, build, install, validate)

dist/                     ← all generated artifacts, isolated per implementation under dist/<impl>
  <impl>/
    plugins/              ← stable registration targets (generated, ignored)
      arpinine-harness/   ← assembled plugin for that implementation
  <name>-<impl>-v<ver>.zip
```

`make assemble IMPLEMENTATION=<name>` merges core → BUILD_DIR, then overlays implementation → BUILD_DIR, then copies BUILD_DIR → `dist/plugins/<name>/`.

## Module Boundaries

| Module | Responsibility | Depends On | Interface |
|--------|----------------|------------|-----------|
| `src/arpinine-harness-core/` | All governance behavior: commands, hooks, agents, skills, templates | Nothing | File-system directory; consumed by assemble overlay |
| `src/implementations/<name>/` | Platform manifest and any platform-required skill wrappers | Nothing from core (overlay only) | File-system directory; overlaid onto core by assemble |
| `Makefile` | Orchestrates assembly, packaging, install, validate, clean | Reads: core + implementation dirs. Writes: dist/ | Shell targets with IMPLEMENTATION variable |
| `dist/plugins/<name>/` | Stable registration target; assembled copy of the plugin | None (output only) | Local directory path registered with assistant marketplace |
| `dist/` | Staging, assembled plugin dirs, and zip artifact | None (output only) | Cleaned before each assemble; zip is the distributable |

## Dependency Rules

- `src/arpinine-harness-core/` MUST NOT reference any path or artifact under `src/implementations/`.
- `src/implementations/<name>/` MUST NOT contain governance artifacts — no commands, no agent definitions, no templates, no shared scripts. Platform-specific skill wrappers (Codex only) are permitted only where the platform cannot load the shared command format directly.
- `Makefile` reads from `src/` directories and writes to `dist/`. Source directories MUST NOT reference generated output.
- `dist/` is generated output. No source file, test, or script MUST depend on its contents.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Core independence | Static check | `grep -r "implementations/" src/arpinine-harness-core/` returns empty |
| Implementation boundary | Static check | No `commands/`, `agents/`, `templates/` dirs exist under any `src/implementations/<name>/` |
| Assemble idempotency (NFR-002) | Functional | Run `make assemble` twice; `diff -r dist/plugins/arpinine-harness-claude/ <second-output>/` reports no differences |
| Validation (AC-001, AC-002) | Functional | `claude plugin validate dist/plugins/arpinine-harness-claude/` exits 0 |
| Error on missing dir (AC-003, FR-007) | Functional | Rename core dir; run `make assemble`; assert exit non-zero with named error message |
| Stable registration (NFR-003) | Functional | Run `make clean && make assemble`; confirm the local registration target is recreated at `dist/plugins/arpinine-harness-claude/` |
| Command availability (AC-005) | Manual | After install, confirm `/arpinine-harness:at-new`, `/arpinine-harness:at-plan`, `/arpinine-harness:at-implement`, and all other `at-*` commands respond |
| Codex subset (AC-006) | Manual | After Codex install, confirm `at-init`, `at-new`, `at-review`, `at-plan` respond; others absent |

## Harness Strategy

N/A — this plugin has no agent runtime dependency. The plugin governs harness use in downstream product applications; it does not itself use a harness.

## Tasks

### Verification (retroactive — implementation already exists)
- [ ] TASK-001: Run `grep -r "implementations/" src/arpinine-harness-core/` and confirm empty — verifies core independence
- [ ] TASK-002: Confirm no `commands/`, `agents/`, or `templates/` dirs under any `src/implementations/<name>/` — verifies implementation boundary
- [ ] TASK-003: Run `make assemble IMPLEMENTATION=claude` twice; diff both `dist/plugins/arpinine-harness-claude/` outputs — verifies NFR-002 idempotency
- [ ] TASK-004: Rename `src/arpinine-harness-core/` temporarily; run `make assemble`; confirm exit non-zero with error naming the missing component — verifies AC-003 and FR-007
- [ ] TASK-005: Run `claude plugin validate dist/plugins/arpinine-harness-claude/` — verifies AC-001
- [ ] TASK-006: Confirm all `/arpinine-harness:at-*` commands respond after Claude install — verifies AC-005
- [ ] TASK-007: Document Codex parity gap explicitly in `src/implementations/codex/README.md` — resolves OQ-002

### Open question resolution
- [ ] TASK-008: Decide whether OQ-001 (implementation directory contract) should be enforced in `make assemble` via validation; update `make validate` if yes
- [ ] TASK-009: Decide whether OQ-003 (manifest format validation in `make install`) is worth the coupling to assistant-specific validation tools

## Evaluation Strategy

Not applicable. This feature is a build process, not an agentic or AI-assisted workflow. No evaluation plan required.

| Dimension | Check | Framework |
|-----------|-------|-----------|
| Build correctness | TASK-003 through TASK-006 | Shell scripts / manual |
| Boundary enforcement | TASK-001, TASK-002 | grep / static analysis |

## Security

- Build scripts run locally; no network calls, no credentials, no secrets
- `make install` delegates to `claude plugin install` — uses Claude Code's verified install channel
- `scripts/` files are chmod'd executable during assemble; acceptable for local governance scripts
- No user-supplied input reaches the build process (IMPLEMENTATION is a developer-controlled variable)

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Local registration target removed by `make clean` | Medium | Document that `make assemble` must be rerun before install, validate, or marketplace registration |
| Codex parity gap grows silently over time | Medium | TASK-007: explicit parity statement in Codex README; reviewed at each core change |
| New implementation violates boundary (adds governance logic) | Low | TASK-008: enforce directory contract in `make validate` |
| Overlay merge silently drops a core file if impl shadows it unintentionally | Low | TASK-003 idempotency check catches regressions across builds |

## ADRs Created During Planning

All governing ADRs were created before planning:
- ADR-0001: Separate shared core from assistant-specific implementations
- ADR-0002: Stable dist/plugins/ dir as local marketplace registration target
- ADR-0003: assemble target as composition primitive for build and install

No new ADRs identified during planning. The overlay merge order (core-first, impl-override) is a direct consequence of ADR-0001 and ADR-0003 and does not warrant a separate record.
