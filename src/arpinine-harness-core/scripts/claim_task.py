#!/usr/bin/env python3
"""
Atomically claim the next eligible task for a team/instance.
"""

from __future__ import annotations

import argparse
from datetime import timedelta
import json
import pathlib
import sys

from task_coordination import (
    claimer_id,
    find_project_root,
    isoformat,
    is_live_lease,
    locked_registry,
    parse_plan_tasks,
    plan_path,
    resolve_runtime_identity,
    sync_registry_with_plan,
    utc_now,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--team-id")
    parser.add_argument("--instance-id")
    parser.add_argument("--task-id")
    parser.add_argument("--lease-seconds", type=int, default=1800)
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
    by_id = {task["task_id"]: task for task in plan_tasks}
    if args.task_id and args.task_id not in by_id:
        print(json.dumps({"ok": False, "error": f"unknown task: {args.task_id}"}))
        return 1

    now = utc_now()
    lease_until = now + timedelta(seconds=max(args.lease_seconds, 1))
    claim_name = claimer_id(team_id, instance_id)

    with locked_registry(repo, args.slug) as (_, registry):
        sync_registry_with_plan(registry, plan_tasks)

        candidates = [by_id[args.task_id]] if args.task_id else plan_tasks
        for task in candidates:
            record = registry["tasks"].setdefault(task["task_id"], {})
            assigned_team = task["assigned_team"]
            if task["status"] != "none":
                continue
            if assigned_team and assigned_team != team_id:
                continue
            if is_live_lease(record, now) and record.get("claimed_by") != claim_name:
                continue

            record.update(
                {
                    "task_id": task["task_id"],
                    "state": "claimed",
                    "assigned_team": assigned_team,
                    "team_id": team_id,
                    "instance_id": instance_id,
                    "claimed_by": claim_name,
                    "claimed_at": isoformat(now),
                    "lease_until": isoformat(lease_until),
                }
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "slug": args.slug,
                        "task_id": task["task_id"],
                        "line_no": task["line_no"],
                        "assigned_team": assigned_team,
                        "claimed_by": claim_name,
                        "lease_until": record["lease_until"],
                    }
                )
            )
            return 0

    print(json.dumps({"ok": False, "error": "no eligible task available"}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
