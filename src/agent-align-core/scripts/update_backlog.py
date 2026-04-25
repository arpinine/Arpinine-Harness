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
import re
import sys
from datetime import datetime

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
        sys.exit(0)


def find_project_root(start: pathlib.Path) -> pathlib.Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / ".specify").exists():
            return candidate
    return pathlib.Path(".").resolve()


repo = find_project_root(pathlib.Path.cwd())
spec_root = repo / ".specify" / "specs"

if not spec_root.exists():
    sys.exit(0)

TASK_RE = re.compile(r"^-\s+\[([ ~xX])\]\s+(TASK-\d+):", re.IGNORECASE)

STATUS_MAP = {
    " ": "none",
    "~": "partial",
    "x": "full",
}

sections: list[tuple[str, list[tuple[str, str, int]]]] = []
total = 0
count_full = 0
count_partial = 0

for plan_file in sorted(spec_root.glob("*/plan.md")):
    slug = plan_file.parent.name
    tasks: list[tuple[str, str, int]] = []
    try:
        text = plan_file.read_text()
    except OSError:
        continue
    for line_no, line in enumerate(text.splitlines(), start=1):
        m = TASK_RE.match(line.strip())
        if m:
            mark = m.group(1).lower()
            status = STATUS_MAP.get(mark, "none")
            task_id = m.group(2)
            tasks.append((task_id, status, line_no))
            total += 1
            if status == "full":
                count_full += 1
            elif status == "partial":
                count_partial += 1
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
        "Run `/agent-align:at-plan <slug>` to create a plan, or add tasks to an existing `plan.md`.",
        "",
    ]

for slug, tasks in sections:
    plan_rel = f"specs/{slug}/plan.md"
    spec_rel = f"specs/{slug}/spec.md"
    done = sum(1 for _, s, _ in tasks if s == "full")
    partial = sum(1 for _, s, _ in tasks if s == "partial")

    lines.append(f"## [{slug}]({spec_rel})")
    lines.append(f"Plan: [{plan_rel}]({plan_rel}) &nbsp;|&nbsp; Progress: {done}/{len(tasks)} full, {partial} partial")
    lines.append("")
    if not tasks:
        lines.append("No `TASK-*` entries found in this plan yet.")
        lines.append("")
        continue
    lines.append("| Task | Status |")
    lines.append("|------|--------|")
    for task_id, status, line_no in tasks:
        lines.append(f"| [{task_id}]({plan_rel}#L{line_no}) | {status} |")
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

sys.exit(0)
