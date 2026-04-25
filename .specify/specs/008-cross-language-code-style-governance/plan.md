# Plan: Cross-Language Code Style Governance

## Governing Spec
`.specify/specs/008-cross-language-code-style-governance/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Declare style governance in the constitution and enforce it through a shared hook | Keeps style as both a governance principle and an executable check | ADR-0006 |
| Centralize checked-in style configs under `tools/style/` | Gives plugins and humans one canonical location for style standards | ADR-0006 |
| Use language-native config formats such as Ruff, Prettier, ESLint, Checkstyle, and rustfmt | Keeps style standards understandable and reusable outside AgentAlign hooks | ADR-0006 |
| Allow edits to the canonical style-config files even when no style standard is yet active for a language | Prevents the governance hook from blocking repository bootstrap and future updates | No separate ADR |

## Architecture

```text
.specify/CONSTITUTION.md                    ← policy-level requirement for shared style standards
tools/style/                               ← canonical repository style-config directory
tools/style/python/pyproject.toml          ← Python style standard
tools/style/frontend/.prettierrc.json      ← frontend formatting standard
tools/style/frontend/eslint.config.cjs     ← frontend lint standard
tools/style/java/checkstyle.xml            ← Java style standard
tools/style/rust/rustfmt.toml              ← Rust style standard
tools/style/shared/.editorconfig           ← shared text and indentation defaults
scripts/check_style_governance.py          ← shared style-governance hook logic
scripts/check-style-governance.sh          ← hook entrypoint
tests/test_style_governance.py             ← blocking and allow-path coverage
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| Constitution | Define style-governance policy | Shared governance model | Contain tool-specific command lines |
| `tools/style/` | Store canonical checked-in style standards | Repository-owned config files | Depend on assistant-specific overlays |
| Style-governance hook | Enforce presence of style standards before code edits | Constitution intent and canonical config paths | Reimplement formatter logic |
| Tests | Prove hook behavior for supported languages | Hook entrypoint and canonical config locations | Depend on assistant-local runtime state |
| Makefile/docs | Surface canonical style paths to teams | `tools/style/` | Become the source of style semantics |

## Dependency Rules

- Style-governance enforcement MUST read canonical config markers from `tools/style/`.
- Assistant implementations MUST not define divergent style-config locations for the same language.
- The constitution SHOULD define the policy while hooks enforce the executable subset of that policy.
- Language-specific style standards SHOULD be expressed through native config files rather than custom AgentAlign-only formats.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| Python style governance | Unit | Assert blocked and allowed hook behavior against canonical Python config path |
| Frontend style governance | Unit | Assert blocked and allowed hook behavior against canonical ESLint and Prettier config paths |
| Java and Rust style governance | Unit | Assert allowed hook behavior against canonical config paths |
| Canonical config edit path | Unit | Assert governance hook allows editing constitution/style config files directly |
| Packaging stability | Integration | Validate assembled Claude and Codex plugin structures |

## Harness Strategy

Not applicable. This feature governs repository style standards and shared hooks, not a product harness runtime.

## Tasks

- [x] TASK-001: Add constitution language that makes cross-team repository style standards mandatory
- [x] TASK-002: Implement a shared style-governance hook and shell entrypoint in shared core scripts
- [x] TASK-003: Add canonical Python style configuration
- [x] TASK-004: Add canonical frontend style configuration for JavaScript and TypeScript
- [x] TASK-005: Add canonical Java style configuration
- [x] TASK-006: Add canonical Rust style configuration
- [x] TASK-007: Move all style config into a shared `tools/style/` directory and update hook discovery to use it
- [x] TASK-008: Add tests for blocking and allow-path behavior across supported languages
- [x] TASK-009: Document canonical style-config locations for the team and plugin implementations

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Governance enforcement | AC-001 through AC-004 | Unit tests for hook block/allow behavior |
| Team usability | AC-005 | Documentation and canonical path review |
| Regression safety | AC-006 | Automated test suite plus shared packaging validation |

Evaluation plan:
`N/A`

## Security

- The style-governance hook must only inspect repository paths and config presence, not execute arbitrary repository content
- Canonical config paths should remain checked-in and reviewable by the team
- Hook failure messages should be explicit enough to guide remediation without leaking unrelated details

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Teams assume tool auto-discovery still works after moving configs out of root | Medium | Document explicit canonical paths and surface them through Makefile targets |
| The hook becomes too permissive by accepting generic markers instead of canonical config files | Medium | Keep canonical path checks explicit per language |
| Additional languages arrive without style standards | Medium | Fail closed for supported languages and extend the config directory deliberately |

## ADRs Created During Planning

- ADR-0006: Centralize cross-language style standards under a shared repository directory
