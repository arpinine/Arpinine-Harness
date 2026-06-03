#!/usr/bin/env python3
"""Shared helpers for archetype scaffolding and governance."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any


ARCHETYPE_METADATA_REL = pathlib.Path(".specify") / "archetype.json"
CONSTITUTION_CANDIDATES = (
    pathlib.Path("CONSTITUTION.md"),
    pathlib.Path(".specify") / "constitution.md",
    pathlib.Path(".specify") / "memory" / "constitution.md",
    pathlib.Path("constitution.md"),
)
CONSTITUTION_TITLE = "# Project Constitution"


def archetypes_dir(script_dir: pathlib.Path) -> pathlib.Path:
    return script_dir.parent / "archetypes"


def list_archetypes(root: pathlib.Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_dir())


def load_manifest(root: pathlib.Path, archetype_name: str) -> dict[str, Any]:
    archetype_dir = root / archetype_name
    manifest_path = archetype_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest.json for archetype {archetype_name!r}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def metadata_path(repo: pathlib.Path) -> pathlib.Path:
    return repo / ARCHETYPE_METADATA_REL


def write_metadata(repo: pathlib.Path, archetype_name: str) -> pathlib.Path:
    path = metadata_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "archetype": archetype_name,
        "selected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "scaffold_archetype.py",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_selected_archetype(repo: pathlib.Path) -> str:
    path = metadata_path(repo)
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    value = payload.get("archetype", "")
    return str(value).strip()


def find_constitution_path(repo: pathlib.Path) -> pathlib.Path | None:
    for candidate in CONSTITUTION_CANDIDATES:
        path = repo / candidate
        if path.exists():
            return path

    for candidate in repo.rglob("*.md"):
        if ".git" in candidate.parts or "dist" in candidate.parts:
            continue
        try:
            first_line = candidate.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        except Exception:
            continue
        if first_line and first_line[0].strip() == CONSTITUTION_TITLE:
            return candidate
    return None
