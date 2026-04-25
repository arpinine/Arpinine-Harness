# Repository Relocation Checklist

This document tracks the follow-up checks needed after moving the repository to:

- `https://github.com/arpinine/AgentAlign.git`

Its purpose is to capture the cleanup that does not live in the git worktree itself, especially GitHub-side settings and external references.

## Already Done

- local `origin` updated to `https://github.com/arpinine/AgentAlign.git`
- local `main` set to track `origin/main`
- repo-local search found no stale references to the previous repository URL

## GitHub Repository Settings

Verify these directly in the GitHub UI for `arpinine/AgentAlign`:

- repository description matches the current project scope
- repository homepage URL is correct, if used
- default branch is `main`
- branch protection rules for `main` are present and still correct
- required reviewers, status checks, or merge rules still match the intended workflow

## GitHub Automation And Integrations

Check any configuration that may exist outside the repository files:

- GitHub Actions secrets and variables
- repository webhooks
- GitHub Apps installed on the old repository
- deploy keys
- Dependabot or security settings
- project boards, milestones, and issue templates if they were configured in the GitHub UI

## External References

Update any non-repo systems that may still point to the previous location:

- local clones on other machines
- CI/CD systems
- documentation portals or wikis
- bookmarks and shared links
- chat pinned messages
- package or marketplace metadata, if published elsewhere

## Local Verification

Run these checks from the repo root when needed:

```bash
git remote -v
git status -sb
git branch -vv
```

Expected outcome:

- `origin` points to `https://github.com/arpinine/AgentAlign.git`
- `main` tracks `origin/main`
- worktree is clean

## Completion Criteria

The relocation is complete when:

- GitHub settings are verified in the new repository
- no external system still depends on the previous repository URL
- the team is using the new repository as the single active source of truth
