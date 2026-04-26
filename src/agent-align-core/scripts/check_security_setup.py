#!/usr/bin/env python3
"""PreToolUse hook: verify pre-commit security hooks are active (cached)."""

from __future__ import annotations

import pathlib
import sys

from security_tooling import (
    check_hooks_active,
    check_precommit_installed,
    find_project_root,
    installation_instructions,
    is_cache_stale,
    read_cache,
    write_cache,
)


def main() -> int:
    repo = find_project_root(pathlib.Path.cwd())

    # Check if this project uses AgentAlign (has .specify/)
    if not (repo / ".specify").exists():
        return 0

    # Fast path: check cache
    cache = read_cache(repo)
    if not is_cache_stale(cache):
        # Cache is fresh — check if hooks were active at cache time
        if cache and cache.get("hooks_active", {}).get("pre_commit", False):
            return 0

    # Cache is stale or missing — refresh
    if not check_precommit_installed():
        print("WARNING: pre-commit is not installed. Security hooks are inactive.")
        for instruction in installation_instructions(["pre-commit"]):
            print(f"  {instruction}")
        print("Run /at-init to set up security tooling.")
        return 1

    hook_status = check_hooks_active(repo)
    write_cache(repo, {
        "hooks_active": hook_status,
        "tools_configured": (repo / ".pre-commit-config.yaml").exists(),
    })

    if not hook_status.get("pre_commit", False):
        print("WARNING: Pre-commit hooks are not installed. Security checks are inactive.")
        print("  Run: pre-commit install && pre-commit install --hook-type pre-push")
        print("  Or run /at-init to set up security tooling from scratch.")
        return 1

    if not hook_status.get("pre_push", False):
        # Pre-push missing is a warning, not a block
        print("NOTE: Pre-push hooks are not installed. Dependency audits and type checks will not run before push.")
        print("  Run: pre-commit install --hook-type pre-push")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
