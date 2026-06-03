#!/usr/bin/env python3
"""Inspect Arpinine Harness governance state and emit normalized JSON to stdout.

Contract defined in: src/arpinine-harness-core/state-inspector.md
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
STATE_RE = re.compile(r"^state:\s*(.+?)\s*$", re.MULTILINE)
DRIFT_RE = re.compile(
    r"(CRITICAL\s+unresolved|Remaining:\s*[1-9]\d*|[1-9]\d*\s+OPEN\b)",
    re.IGNORECASE,
)

ACTIVE_MAP_STATES: frozenset[str] = frozenset({
    "needs-clarification",
    "backlog-ready-awaiting-selection",
    "promoting-features",
})
COMPLETED_MAP_STATES: frozenset[str] = frozenset({"completed"})

ACTIVE_DISCOVERY_STATES: frozenset[str] = frozenset({
    "needs-clarification",
    "spec-ready-awaiting-confirmation",
})
COMPLETED_DISCOVERY_STATES: frozenset[str] = frozenset({"promoted-to-spec"})

SOURCE_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".go", ".rs", ".java", ".rb", ".php",
    ".cs", ".cpp", ".c",
})
PROJECT_MARKERS: frozenset[str] = frozenset({
    "package.json", "pyproject.toml", "go.mod",
    "Cargo.toml", "pom.xml", "Gemfile", "composer.json",
})
SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "__pycache__",
    ".venv", "venv", "dist", "build",
})

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / ".specify").exists() or (candidate / ".git").exists():
            return candidate
    return None


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def read_frontmatter_state(path: pathlib.Path) -> str | None:
    text = read_text(path)
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    sm = STATE_RE.search(m.group(1))
    return sm.group(1).strip() if sm else None


def scan_sessions(
    directory: pathlib.Path,
    filename: str,
    active_states: frozenset[str],
    completed_states: frozenset[str],
    warnings: list[str],
) -> tuple[list[str], list[str]]:
    active: list[str] = []
    completed: list[str] = []
    if not directory.exists():
        return active, completed
    try:
        entries = sorted(directory.iterdir())
    except OSError as exc:
        warnings.append(f"Cannot read {directory}: {exc}")
        return active, completed
    for session_dir in entries:
        if not session_dir.is_dir():
            continue
        md = session_dir / filename
        if not md.is_file():
            continue
        state = read_frontmatter_state(md)
        if state in active_states:
            active.append(session_dir.name)
        elif state in completed_states:
            completed.append(session_dir.name)
    return active, completed


def has_source_files(repo: pathlib.Path, specify_dir: pathlib.Path) -> bool:
    for marker in PROJECT_MARKERS:
        if (repo / marker).exists():
            return True
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        # Skip .specify/ tree
        try:
            path.relative_to(specify_dir)
            continue
        except ValueError:
            pass
        # Skip unwanted directories
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in SOURCE_EXTENSIONS:
            return True
    return False


def scan_specs(
    spec_root: pathlib.Path,
    eval_root: pathlib.Path,
    obs_root: pathlib.Path,
    warnings: list[str],
) -> dict[str, list[str]]:
    without_plan: list[str] = []
    with_plan: list[str] = []
    open_drift: list[str] = []
    eval_gaps: list[str] = []
    observation_gaps: list[str] = []

    if not spec_root.exists():
        return {
            "specs_without_plan": without_plan,
            "specs_with_plan": with_plan,
            "specs_with_open_drift": open_drift,
            "eval_gaps": eval_gaps,
            "observation_gaps": observation_gaps,
            "spec_count": 0,
        }

    try:
        entries = sorted(spec_root.iterdir())
    except OSError as exc:
        warnings.append(f"Cannot read {spec_root}: {exc}")
        return {
            "specs_without_plan": without_plan,
            "specs_with_plan": with_plan,
            "specs_with_open_drift": open_drift,
            "eval_gaps": eval_gaps,
            "observation_gaps": observation_gaps,
            "spec_count": 0,
        }

    count = 0
    for spec_dir in entries:
        if not spec_dir.is_dir():
            continue
        if not (spec_dir / "spec.md").exists():
            continue
        slug = spec_dir.name
        count += 1
        has_plan = (spec_dir / "plan.md").exists()
        eval_dir = eval_root / slug
        has_eval = (eval_dir / "eval-plan.md").exists()
        obs_dir = obs_root / slug
        has_obs = (obs_dir / "latest-observation.md").exists()

        if not has_plan:
            without_plan.append(slug)
        else:
            with_plan.append(slug)
            if not has_eval:
                eval_gaps.append(slug)
            elif not has_obs:
                observation_gaps.append(slug)

        # Drift: heuristic scan of canonical drift report
        drift_report = spec_dir / "drift-report.md"
        if drift_report.exists() and DRIFT_RE.search(read_text(drift_report)):
            open_drift.append(slug)

    return {
        "specs_without_plan": without_plan,
        "specs_with_plan": with_plan,
        "specs_with_open_drift": open_drift,
        "eval_gaps": eval_gaps,
        "observation_gaps": observation_gaps,
        "spec_count": count,
    }


# ---------------------------------------------------------------------------
# Main inspector
# ---------------------------------------------------------------------------

def inspect(repo_root: pathlib.Path) -> dict[str, Any]:
    warnings: list[str] = []
    incomplete_state = False
    specify = repo_root / ".specify"
    governed = specify.is_dir()

    spec_data = scan_specs(
        specify / "specs",
        specify / "evals",
        specify / "observations",
        warnings,
    )

    active_map, completed_map = scan_sessions(
        specify / "map", "map.md",
        ACTIVE_MAP_STATES, COMPLETED_MAP_STATES,
        warnings,
    )
    active_discovery, completed_discovery = scan_sessions(
        specify / "discovery", "discovery.md",
        ACTIVE_DISCOVERY_STATES, COMPLETED_DISCOVERY_STATES,
        warnings,
    )

    try:
        has_existing = has_source_files(repo_root, specify)
    except Exception as exc:
        warnings.append(f"Codebase scan failed: {exc}")
        has_existing = False
    if warnings:
        incomplete_state = True

    spec_count: int = spec_data["spec_count"]
    bootstrap_candidate = has_existing and (not governed or spec_count == 0)

    return {
        "repo_root": str(repo_root),
        "governed": governed,
        "has_specs": spec_count > 0,
        "spec_count": spec_count,
        "active_map_sessions": active_map,
        "completed_map_sessions": completed_map,
        "active_discovery_sessions": active_discovery,
        "completed_discovery_sessions": completed_discovery,
        "specs_without_plan": spec_data["specs_without_plan"],
        "specs_with_plan": spec_data["specs_with_plan"],
        "specs_with_open_drift": spec_data["specs_with_open_drift"],
        "eval_gaps": spec_data["eval_gaps"],
        "observation_gaps": spec_data["observation_gaps"],
        "has_existing_codebase": has_existing,
        "bootstrap_candidate": bootstrap_candidate,
        "incomplete_state": incomplete_state,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect Arpinine Harness governance state. Emits JSON to stdout.",
    )
    parser.add_argument(
        "--repo",
        type=pathlib.Path,
        default=None,
        help="Project root path (auto-detected from CWD if omitted)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent width; use 0 for compact output (default: 2)",
    )
    args = parser.parse_args()

    repo = args.repo.resolve() if args.repo else find_project_root(pathlib.Path.cwd())
    if repo is None:
        print(json.dumps(
            {
                "repo_root": None,
                "governed": False,
                "has_specs": False,
                "spec_count": 0,
                "active_map_sessions": [],
                "completed_map_sessions": [],
                "active_discovery_sessions": [],
                "completed_discovery_sessions": [],
                "specs_without_plan": [],
                "specs_with_plan": [],
                "specs_with_open_drift": [],
                "eval_gaps": [],
                "observation_gaps": [],
                "has_existing_codebase": False,
                "bootstrap_candidate": False,
                "incomplete_state": True,
                "warnings": ["Could not determine project root: no .specify/ or .git/ found."],
            },
            indent=args.indent or None,
        ))
        sys.exit(0)

    result = inspect(repo)
    print(json.dumps(result, indent=args.indent or None))


if __name__ == "__main__":
    main()
