#!/usr/bin/env python3
"""
Pre-edit gate: require an active task claim before implementation-path edits.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

from task_coordination import (
    claimer_id,
    find_project_root,
    is_live_lease,
    load_registry,
    parse_plan_tasks,
    registry_path,
    resolve_runtime_identity,
    sync_registry_with_plan,
)

CODE_PREFIXES = ("src/", "lib/", "app/", "packages/", "services/", "internal/", "cmd/", "tests/")


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def candidate_specs(spec_root: pathlib.Path, file_path: str) -> list[pathlib.Path]:
    specs = sorted(spec_root.glob("*/spec.md"))
    if not specs:
        return []

    matched: list[pathlib.Path] = []
    for spec in specs:
        try:
            text = spec.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if file_path in text:
            matched.append(spec)

    if matched:
        return matched
    if len(specs) == 1:
        return specs
    return []


def active_claims_for_team(repo: pathlib.Path, slug: str, team_id: str, instance_id: str | None) -> list[str]:
    plan_file = repo / ".specify" / "specs" / slug / "plan.md"
    if not plan_file.exists():
        return []

    plan_tasks = parse_plan_tasks(plan_file)
    registry = load_registry(registry_path(repo, slug), slug)
    sync_registry_with_plan(registry, plan_tasks)

    active: list[str] = []
    expected = claimer_id(team_id, instance_id) if instance_id else None
    for task_id, record in registry.get("tasks", {}).items():
        if not is_live_lease(record):
            continue
        if record.get("team_id") != team_id:
            continue
        if expected and record.get("claimed_by") != expected:
            continue
        active.append(task_id)
    return sorted(active)


def main() -> int:
    payload = load_payload()
    tool_input = payload.get("tool_input", {})
    file_path = str(tool_input.get("file_path", ""))
    if not file_path or not file_path.startswith(CODE_PREFIXES):
        return 0

    repo = find_project_root(pathlib.Path.cwd())
    spec_root = repo / ".specify" / "specs"
    if not spec_root.exists():
        return 0

    team_id, instance_id = resolve_runtime_identity()
    if not team_id:
        print("VIOLATION: implementation edit attempted without a resolved team identity")
        print("Set `AGENT_ALIGN_TEAM_ID` to `claude` or `codex` only if the host runtime does not expose its plugin identity.")
        return 1

    specs = candidate_specs(spec_root, file_path)
    if not specs:
        print(f"VIOLATION: cannot determine governing spec for {file_path}")
        print("Reference the implementation path in the relevant spec or narrow work to a single active spec before coding.")
        return 1

    allowed_claims: list[tuple[str, list[str]]] = []
    missing = []
    for spec in specs:
        slug = spec.parent.name
        active = active_claims_for_team(repo, slug, team_id, instance_id)
        if active:
            allowed_claims.append((slug, active))
        else:
            missing.append(slug)

    if allowed_claims:
        return 0

    print("VIOLATION: implementation edit attempted without an active task claim")
    if instance_id:
        print(f"Resolved identity: {team_id}:{instance_id}")
    else:
        print(f"Resolved identity: {team_id}")
    print(f"Governing specs without active claims: {', '.join(missing)}")
    print(
        "Claim a task first with "
        "`scripts/claim_task.py --slug <slug>` "
        "and only then change implementation files."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
