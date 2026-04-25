#!/usr/bin/env python3
"""
Shared helpers for assistant-agnostic task coordination.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
import re
import socket
from typing import Iterator

TASK_RE = re.compile(r"^-\s+\[([ ~xX])\]\s+(TASK-\d+):\s*(.*)$", re.IGNORECASE)
TEAM_TAG_RE = re.compile(r"\[team:\s*([A-Za-z0-9_.-]+)\]", re.IGNORECASE)
STATUS_MAP = {
    " ": "none",
    "~": "partial",
    "x": "full",
}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def isoformat(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None


def is_live_lease(record: dict, now: dt.datetime | None = None) -> bool:
    now = now or utc_now()
    lease_until = parse_timestamp(record.get("lease_until"))
    if lease_until is None:
        return False
    return lease_until > now


def find_project_root(start: pathlib.Path) -> pathlib.Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / ".specify").exists():
            return candidate
    return pathlib.Path(".").resolve()


def coordination_root(repo: pathlib.Path) -> pathlib.Path:
    return repo / ".specify" / "coordination"


def registry_path(repo: pathlib.Path, slug: str) -> pathlib.Path:
    return coordination_root(repo) / f"{slug}.json"


def lock_path(repo: pathlib.Path) -> pathlib.Path:
    return coordination_root(repo) / ".coordination.lock"


@contextlib.contextmanager
def locked_registry(repo: pathlib.Path, slug: str) -> Iterator[tuple[pathlib.Path, dict]]:
    root = coordination_root(repo)
    root.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path(repo)
    lock_file.touch(exist_ok=True)

    path = registry_path(repo, slug)
    with lock_file.open("r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        data = load_registry(path, slug)
        try:
            yield path, data
        finally:
            write_registry(path, data)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_registry(path: pathlib.Path, slug: str) -> dict:
    if not path.exists():
        return {"slug": slug, "updated_at": None, "tasks": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    payload.setdefault("slug", slug)
    payload.setdefault("updated_at", None)
    payload.setdefault("tasks", {})
    return payload


def write_registry(path: pathlib.Path, data: dict) -> None:
    data["updated_at"] = isoformat(utc_now())
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def plan_path(repo: pathlib.Path, slug: str) -> pathlib.Path:
    return repo / ".specify" / "specs" / slug / "plan.md"


def parse_plan_tasks(plan_file: pathlib.Path) -> list[dict]:
    tasks: list[dict] = []
    text = plan_file.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = TASK_RE.match(line.strip())
        if not match:
            continue
        mark, task_id, description = match.groups()
        team_match = TEAM_TAG_RE.search(description)
        assigned_team = team_match.group(1).lower() if team_match else None
        tasks.append(
            {
                "task_id": task_id,
                "status": STATUS_MAP.get(mark.lower(), "none"),
                "line_no": line_no,
                "description": description.strip(),
                "assigned_team": assigned_team,
            }
        )
    return tasks


def sync_registry_with_plan(registry: dict, plan_tasks: list[dict]) -> None:
    plan_ids = {task["task_id"] for task in plan_tasks}
    tasks = registry.setdefault("tasks", {})

    for task in plan_tasks:
        record = tasks.setdefault(task["task_id"], {})
        record["assigned_team"] = task["assigned_team"]
        if task["status"] == "full":
            record["state"] = "completed"
            record["lease_until"] = None
            record["team_id"] = None
            record["instance_id"] = None
            record["claimed_by"] = None
        elif task["status"] == "none" and record.get("state") == "completed":
            record["state"] = "available"

    for task_id in list(tasks):
        if task_id not in plan_ids:
            del tasks[task_id]


def claimer_id(team_id: str, instance_id: str | None) -> str:
    return f"{team_id}:{instance_id}" if instance_id else team_id


def default_instance_id(team_id: str) -> str:
    explicit = os.environ.get("AGENT_ALIGN_INSTANCE_ID")
    if explicit:
        return explicit

    tty = "no-tty"
    try:
        tty = os.ttyname(0).replace("/", "_")
    except OSError:
        pass

    host = socket.gethostname() or "localhost"
    try:
        session_id = os.getsid(0)
    except OSError:
        session_id = os.getpid()
    try:
        process_group = os.getpgid(0)
    except OSError:
        process_group = os.getpid()
    fingerprint = f"{team_id}:{host}:{session_id}:{process_group}:{tty}"
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:10]
    return f"{team_id}-{digest}"


def resolve_runtime_identity() -> tuple[str | None, str | None]:
    team_id = os.environ.get("AGENT_ALIGN_TEAM_ID")
    if team_id:
        team_id = team_id.lower()
        return team_id, default_instance_id(team_id)

    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        return "claude", default_instance_id("claude")

    if os.environ.get("CODEX_PLUGIN_ROOT"):
        return "codex", default_instance_id("codex")

    return None, os.environ.get("AGENT_ALIGN_INSTANCE_ID")
