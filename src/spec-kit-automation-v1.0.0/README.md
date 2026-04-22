# Spec-Kit Automation Plugin

ADR tracking + drift detection on top of spec-kit.

## Commands

| Command | Purpose |
|---------|---------|
| `/spec-init` | Initialize spec-kit + ADR directory |
| `/spec-new` | Create spec (spec-kit) |
| `/spec-plan` | Generate plan and tasks (spec-kit) |
| `/spec-implement` | Implement with TDD (spec-kit) |
| `/spec-adr` | Create and manage ADRs |
| `/spec-audit` | Detect drift; drive ADR resolution |
| `/spec-review` | Validate against constitution |

## Quick Start

```bash
/spec-init
/spec-new "Your feature"
/spec-plan .specify/specs/001-your-feature/
/spec-adr new "Key architectural decision"
/spec-implement .specify/specs/001-your-feature/
/spec-audit .specify/specs/001-your-feature/
```

## ADR Storage

```
.specify/
  adr/
    ADR-INDEX.md
    ADR-0001-<title>.md
```

Each ADR links to its spec via `governs:` frontmatter.
Each spec lists governing ADRs in `## Related ADRs`.
