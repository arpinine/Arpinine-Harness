---
name: adr-manager
description: Creates, numbers, tracks, and links Architecture Decision Records with index management
---

# ADR Manager Skill

## Storage Layout
```
.specify/
  adr/
    ADR-INDEX.md          ← single source of truth for all ADRs
    ADR-0001-<title>.md
    ADR-0002-<title>.md
```

## Auto-Numbering
1. Read `.specify/adr/ADR-INDEX.md` to find highest existing ADR number
2. If index absent, start at `ADR-0001`
3. Increment by 1, zero-pad to 4 digits: `ADR-0001`, `ADR-0002`, ...
4. Create file, then update index (never the reverse — avoid orphaned index entries)

## ADR Index Format
```markdown
# ADR Index

| Number | Title | Status | Governs | Covers |
|--------|-------|--------|---------|--------|
| ADR-0001 | Use PostgreSQL for session storage | Accepted | specs/001-user-login | decision:001-user-login:session-storage |
| ADR-0002 | JWT over session cookies | Proposed | specs/001-user-login | decision:001-user-login:auth-token-format |
```

## ADR Lifecycle
```
Proposed → Accepted → Implemented → Superseded
                    ↘ Rejected
```

| Status | Meaning | Who transitions |
|--------|---------|-----------------|
| Proposed | Under discussion | Creator |
| Accepted | Team agreed, ready to implement | Tech lead |
| Implemented | Code reflects this decision | Engineer |
| Superseded | Replaced by a newer ADR | Must set `supersedes:` in the new ADR |
| Rejected | Decision not taken | Tech lead |

## Creating an ADR (`/at-adr new "title"`)
1. Read ADR-INDEX.md → determine next number
2. Convert title to kebab-case filename: `ADR-NNNN-use-postgresql.md`
3. Copy `templates/adr-template.md` → fill `date:` with today
4. Ask: "Which spec does this govern?" → set `governs:` frontmatter
5. Set `covers:`:
   - drift item: `drift:<spec-slug>:<type>:<identifier>`
   - planned decision: `decision:<spec-slug>:<decision-name>`
6. If triggered from drift alert: pre-fill `## Context` with drift details
7. Prompt user: Context → Decision → Consequences → Alternatives
8. Append row to ADR-INDEX.md
9. Confirm: "ADR-NNNN created and indexed."

## Updating Status (`/at-adr status <number> <new-status>`)
1. Find ADR file by number prefix in `.specify/adr/`
2. Update `status:` frontmatter field
3. If new status = `Superseded`: require `supersedes: ADR-XXXX` in the superseding ADR
4. Update matching row in ADR-INDEX.md

## Listing ADRs (`/at-adr list`)
Read ADR-INDEX.md and display as formatted table with status indicators.

## Showing an ADR (`/at-adr show <number>`)
Find and display full content of `ADR-NNNN-*.md`.

## Linking Convention
- ADR `governs:` field → spec path (e.g., `specs/001-user-login`)
- ADR `covers:` field → exact drift keys or decision keys
- Spec `## Related ADRs` section → list governing ADR numbers
- Plan `## ADRs` section → list ADRs created during planning
- Drift report → cite ADR number when drift is resolved

## Invariants
- Every ADR must have `governs:` set before status moves past Proposed
- Every CRITICAL/HIGH drift item must match an ADR `covers:` entry before implementation resumes
- `supersedes:` required if status = Superseded
- ADR-INDEX.md must stay in sync with files on disk
