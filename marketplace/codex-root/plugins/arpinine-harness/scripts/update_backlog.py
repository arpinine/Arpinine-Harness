#!/usr/bin/env python3
"""
Regenerate .specify/delivery.md from all plans under .specify/specs/.

Status is read from plan.md task checkboxes:
  - [ ]  → none      (not started)
  - [~]  → partial   (in progress)
  - [x]  → full      (complete)

Task descriptions are NOT copied. The matrix links back to the exact task line in
plan.md for details.
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime

from task_coordination import (
    find_project_root,
    is_live_lease,
    locked_registry,
    parse_plan_tasks,
    sync_registry_with_plan,
)


def main() -> int:
    payload = {}
    raw_input = sys.stdin.read()
    if raw_input.strip():
        try:
            payload = json.loads(raw_input)
        except Exception:
            payload = {}

    if payload:
        tool_input = payload.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if not (file_path.endswith("plan.md") and ".specify/specs/" in file_path):
            return 0
    repo = find_project_root(pathlib.Path.cwd())
    spec_root = repo / ".specify" / "specs"

    if not spec_root.exists():
        return 0

    sections: list[tuple[str, list[dict]]] = []
    total = 0
    count_full = 0
    count_partial = 0

    for plan_file in sorted(spec_root.glob("*/plan.md")):
        slug = plan_file.parent.name
        try:
            tasks = parse_plan_tasks(plan_file)
        except OSError:
            continue

        with locked_registry(repo, slug) as (_, registry):
            sync_registry_with_plan(registry, tasks)

            for task in tasks:
                status = task["status"]
                total += 1
                if status == "full":
                    count_full += 1
                elif status == "partial":
                    count_partial += 1

                record = registry.get("tasks", {}).get(task["task_id"], {})
                task["claimed_by"] = record.get("claimed_by") if is_live_lease(record) else None
                task["lease_until"] = record.get("lease_until") if is_live_lease(record) else None

        sections.append((slug, tasks))

    remaining = total - count_full
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Paths are relative from .specify/ to .specify/specs/<slug>/plan.md
    lines: list[str] = [
        "# Delivery Status Matrix",
        "",
        "**Purpose:** Single-pane view of delivery progress across all active specs.",
        "Task descriptions and requirements live in each spec's `plan.md` — this document tracks status only.",
        "It is auto-generated; update task status by editing checkboxes in `plan.md`.",
        "",
        "**Legend:**",
        "| Symbol | Status | Meaning |",
        "|--------|--------|---------|",
        "| `[ ]` | none | Not started |",
        "| `[~]` | partial | In progress |",
        "| `[x]` | full | Complete |",
        "",
        "---",
        "",
    ]

    if not sections:
        lines += [
            "No plans found under `.specify/specs/`.",
            "",
            "Run `/arpinine-harness:at-plan <slug>` to create a plan, or add tasks to an existing `plan.md`.",
            "",
        ]

    for slug, tasks in sections:
        plan_rel = f"specs/{slug}/plan.md"
        spec_rel = f"specs/{slug}/spec.md"
        done = sum(1 for task in tasks if task["status"] == "full")
        partial = sum(1 for task in tasks if task["status"] == "partial")

        lines.append(f"## [{slug}]({spec_rel})")
        lines.append(f"Plan: [{plan_rel}]({plan_rel}) &nbsp;|&nbsp; Progress: {done}/{len(tasks)} full, {partial} partial")
        lines.append("")
        if not tasks:
            lines.append("No `TASK-*` entries found in this plan yet.")
            lines.append("")
            continue
        lines.append("| Task | Status | Assigned Team | Claimed By | Lease Until |")
        lines.append("|------|--------|---------------|------------|-------------|")
        for task in tasks:
            assigned_team = task["assigned_team"] or "-"
            claimed_by = task["claimed_by"] or "-"
            lease_until = task["lease_until"] or "-"
            lines.append(
                f"| [{task['task_id']}]({plan_rel}#L{task['line_no']}) | {task['status']} | "
                f"{assigned_team} | {claimed_by} | {lease_until} |"
            )
        lines.append("")

    lines += [
        "---",
        f"_Last updated: {timestamp}_",
        "",
        f"**Total tasks:** {total} &nbsp;|&nbsp; "
        f"**Full:** {count_full} &nbsp;|&nbsp; "
        f"**Partial:** {count_partial} &nbsp;|&nbsp; "
        f"**Remaining:** {remaining}",
    ]

    delivery_path = repo / ".specify" / "delivery.md"
    delivery_path.write_text("\n".join(lines) + "\n")

    # Remove old backlog.md if it exists from a prior version
    old_backlog = repo / ".specify" / "backlog.md"
    if old_backlog.exists():
        old_backlog.unlink()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
