#!/usr/bin/env python3
"""Set up pre-commit hooks and security tooling for a project."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

from security_tooling import (
    check_hooks_active,
    check_precommit_installed,
    detect_languages,
    find_project_root,
    generate_precommit_config,
    installation_instructions,
    merge_precommit_config,
    tool_config_for_languages,
    write_cache,
)


def main() -> int:
    repo = find_project_root(pathlib.Path.cwd())

    # 1. Check pre-commit is installed
    if not check_precommit_installed():
        print("SETUP BLOCKED: pre-commit is not installed.")
        for instruction in installation_instructions(["pre-commit"]):
            print(f"  {instruction}")
        print("Install pre-commit, then re-run /at-init.")
        return 1

    # 2. Detect languages
    languages = detect_languages(repo)
    if not languages:
        print("No source files detected. Security tooling will be configured with gitleaks only.")
        languages = []

    # 3. Get tool config
    tools = tool_config_for_languages(languages, repo)

    # 4. Generate or merge .pre-commit-config.yaml
    config_path = repo / ".pre-commit-config.yaml"
    if config_path.exists():
        print(f"Found existing {config_path.name} — merging security hooks...")
        # Collect all repos from both stages
        all_repos = tools.get("pre-commit", []) + tools.get("pre-push", [])
        merged = merge_precommit_config(config_path, all_repos)
        config_path.write_text(merged, encoding="utf-8")
    else:
        print("Creating .pre-commit-config.yaml...")
        content = generate_precommit_config(tools)
        config_path.write_text(content, encoding="utf-8")

    # 5. Install hooks
    print("Installing pre-commit hooks...")
    try:
        subprocess.run(
            ["pre-commit", "install"],
            cwd=repo, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["pre-commit", "install", "--hook-type", "pre-push"],
            cwd=repo, check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Failed to install hooks: {exc.stderr}")
        return 1

    # 6. Write cache
    hook_status = check_hooks_active(repo)
    write_cache(repo, {
        "hooks_active": hook_status,
        "languages": languages,
        "tools_configured": True,
    })

    # 7. Print summary
    print("")
    print("Security Setup Complete:")
    print(f"  Languages detected:  {', '.join(languages) if languages else 'none (gitleaks only)'}")
    print(f"  Pre-commit hooks:    gitleaks{', ruff, ruff-format' if 'python' in languages else ''}{', eslint, prettier' if 'javascript' in languages else ''}")
    pre_push_items = []
    if "python" in languages:
        pre_push_items.extend(["pytest", "mypy", "pip-audit", "bandit"])
    if "javascript" in languages:
        pre_push_items.extend(["tsc", "npm-audit"])
    if "java" in languages:
        pre_push_items.extend(["mvn-test", "dependency-check"])
    print(f"  Pre-push hooks:      {', '.join(pre_push_items) if pre_push_items else 'none'}")
    print(f"  Config file:         {config_path.relative_to(repo)}")
    print("")
    print("  Run /at-status anytime to check governance and security health.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
