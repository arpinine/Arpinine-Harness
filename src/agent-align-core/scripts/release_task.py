#!/usr/bin/env python3
"""
Release or complete a previously claimed task.
"""

from __future__ import annotations

import argparse
import json
import pathlib

from task_coordination import (
    claimer_id,
    find_project_root,
    locked_registry,
    parse_plan_tasks,
    plan_path,
    resolve_runtime_identity,
    sync_registry_with_plan,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--team-id")
    parser.add_argument("--instance-id")
    parser.add_argument("--state", choices=["available", "completed"], default="available")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    resolved_team, resolved_instance = resolve_runtime_identity()
    team_id = (args.team_id or resolved_team or "").lower()
    instance_id = args.instance_id or resolved_instance
    if not team_id:
        print(json.dumps({"ok": False, "error": "missing team identity"}))
        return 1
    repo = find_project_root(pathlib.Path.cwd())
    plan_file = plan_path(repo, args.slug)
    if not plan_file.exists():
        print(json.dumps({"ok": False, "error": f"missing plan: {plan_file}"}))
        return 1

    plan_tasks = parse_plan_tasks(plan_file)
    if args.task_id not in {task["task_id"] for task in plan_tasks}:
        print(json.dumps({"ok": False, "error": f"unknown task: {args.task_id}"}))
        return 1

    expected_claimer = claimer_id(team_id, instance_id)

    with locked_registry(repo, args.slug) as (_, registry):
        sync_registry_with_plan(registry, plan_tasks)
        record = registry["tasks"].setdefault(args.task_id, {})
        current_claimer = record.get("claimed_by")
        if current_claimer and current_claimer != expected_claimer:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": f"task is claimed by {current_claimer}",
                    }
                )
            )
            return 2

        record["state"] = args.state
        record["team_id"] = None if args.state == "available" else team_id
        record["instance_id"] = None if args.state == "available" else instance_id
        record["claimed_by"] = None
        record["lease_until"] = None
        print(
            json.dumps(
                {
                    "ok": True,
                    "slug": args.slug,
                    "task_id": args.task_id,
                    "state": args.state,
                }
            )
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
