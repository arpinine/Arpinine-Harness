---
description: "Create and manage Architecture Decision Records. Subcommands: new, list, show, status. Auto-numbers ADRs and maintains ADR-INDEX.md."
---

# /spec-adr

Manage Architecture Decision Records (ADRs).

## Usage
- `/spec-adr new "title"` — create and index a new ADR
- `/spec-adr list` — display all ADRs with status
- `/spec-adr show <number>` — display ADR-NNNN full content
- `/spec-adr status <number> <status>` — update lifecycle status

---

## Steps: `new`

1. Read `.specify/adr/ADR-INDEX.md` → find highest ADR number (create index file if absent, start at 0000)
2. Increment and zero-pad: next number = `NNNN`
3. Create `.specify/adr/ADR-NNNN-<kebab-title>.md` from `templates/adr-template.md`
4. Set `date:` to today
5. If invoked from a drift alert: pre-fill `## Context` with drift details
6. Prompt user to fill: Context → Decision → Consequences → Alternatives Considered
7. Ask: "Which spec does this govern?" → set `governs:` frontmatter (e.g., `specs/001-user-login`)
8. Append row to ADR-INDEX.md: `| ADR-NNNN | <title> | Proposed | <governs> |`
9. Confirm: "ADR-NNNN created at `.specify/adr/ADR-NNNN-<title>.md`"

## Steps: `list`

Read `.specify/adr/ADR-INDEX.md` and display as table.
If index missing: "No ADRs yet. Run `/spec-adr new` to create one."

## Steps: `show <number>`

Find file matching `ADR-NNNN-*.md` in `.specify/adr/`.
Display full content.
If not found: list available ADR numbers from index.

## Steps: `status <number> <status>`

Valid statuses: `Proposed`, `Accepted`, `Implemented`, `Superseded`, `Rejected`

1. Find `ADR-NNNN-*.md`
2. Update `status:` frontmatter field
3. If `Superseded`: require user to provide the superseding ADR number → set `supersedes:` in the *new* ADR
4. Update matching row in ADR-INDEX.md

## Error Conditions
- `.specify/adr/` not found → "Run `/spec-init` first"
- ADR number not found → show ADR-INDEX.md
- Invalid status value → list valid statuses
