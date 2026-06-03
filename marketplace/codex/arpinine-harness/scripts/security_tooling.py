#!/usr/bin/env python3
"""
Shared helpers for security tooling setup, checking, and reporting.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import time
from typing import Any

CACHE_FILE = ".specify/coordination/.security-tooling-cache.json"
CACHE_TTL_SECONDS = 300  # 5 minutes

# Language detection markers
LANGUAGE_MARKERS: dict[str, list[str]] = {
    "python": ["*.py", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"],
    "javascript": ["*.js", "*.jsx", "*.ts", "*.tsx", "package.json"],
    "java": ["*.java", "pom.xml", "build.gradle", "build.gradle.kts"],
    "go": ["*.go", "go.mod"],
    "rust": ["*.rs", "Cargo.toml"],
}

# Config detection for existing tools (detection-then-defaults)
EXISTING_TOOL_CONFIGS: dict[str, list[str]] = {
    "ruff": ["pyproject.toml"],  # check for [tool.ruff] section
    "flake8": [".flake8", "setup.cfg"],
    "eslint": [
        "eslint.config.js", "eslint.config.cjs", "eslint.config.mjs",
        ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml",
    ],
    "prettier": [
        ".prettierrc", ".prettierrc.json", ".prettierrc.yml",
        ".prettierrc.js", "prettier.config.js",
    ],
    "mypy": ["mypy.ini", ".mypy.ini"],  # also check pyproject.toml [tool.mypy]
    "pyright": ["pyrightconfig.json"],
    "pytest": ["pytest.ini", "conftest.py"],  # also check pyproject.toml [tool.pytest]
    "jest": ["jest.config.js", "jest.config.ts", "jest.config.mjs"],
    "vitest": ["vitest.config.js", "vitest.config.ts", "vitest.config.mjs"],
    "checkstyle": ["checkstyle.xml"],
}

# Directories commonly containing source code
_SOURCE_DIRS = ("src", "lib", "app", "packages", "services")

# pyproject.toml section markers for tools that embed config there
_PYPROJECT_SECTIONS: dict[str, str] = {
    "ruff": "[tool.ruff]",
    "mypy": "[tool.mypy]",
    "pytest": "[tool.pytest",  # matches [tool.pytest] and [tool.pytest.ini_options]
}


# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

def find_project_root(start: pathlib.Path) -> pathlib.Path:
    """Walk up from *start* until a ``.specify`` directory is found."""
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / ".specify").exists():
            return candidate
    return pathlib.Path(".").resolve()


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_languages(repo: pathlib.Path) -> list[str]:
    """Scan the repo for language markers and return detected language keys.

    For file extension markers (``*.py`` etc.) we look for matching files in
    common source directories.  For config-file markers (``package.json``
    etc.) we check the repo root.
    """
    detected: list[str] = []
    for language, markers in LANGUAGE_MARKERS.items():
        found = False
        for marker in markers:
            if marker.startswith("*."):
                # Extension-based — search in common source directories
                for source_dir in _SOURCE_DIRS:
                    search_root = repo / source_dir
                    if search_root.is_dir() and any(search_root.rglob(marker)):
                        found = True
                        break
                # Also check repo root (shallow) for top-level files
                if not found and any(repo.glob(marker)):
                    found = True
            else:
                # Config-file marker — check repo root
                if (repo / marker).exists():
                    found = True
            if found:
                break
        if found:
            detected.append(language)
    return detected


# ---------------------------------------------------------------------------
# Tool detection
# ---------------------------------------------------------------------------

def detect_existing_tool(repo: pathlib.Path, tool: str) -> bool:
    """Return ``True`` if configuration files for *tool* already exist."""
    configs = EXISTING_TOOL_CONFIGS.get(tool, [])
    for cfg in configs:
        if cfg == "pyproject.toml":
            # Special handling — check for the tool's section inside pyproject.toml
            section_marker = _PYPROJECT_SECTIONS.get(tool)
            if section_marker and (repo / "pyproject.toml").is_file():
                try:
                    content = (repo / "pyproject.toml").read_text(encoding="utf-8")
                    if section_marker in content:
                        return True
                except OSError:
                    pass
        elif (repo / cfg).exists():
            return True

    # Additional pyproject.toml checks for tools not in configs list
    if tool in _PYPROJECT_SECTIONS and "pyproject.toml" not in configs:
        section_marker = _PYPROJECT_SECTIONS[tool]
        if (repo / "pyproject.toml").is_file():
            try:
                content = (repo / "pyproject.toml").read_text(encoding="utf-8")
                if section_marker in content:
                    return True
            except OSError:
                pass

    return False


# ---------------------------------------------------------------------------
# Tool configuration per language
# ---------------------------------------------------------------------------

def _hook(
    hook_id: str,
    name: str,
    *,
    stages: list[str] | None = None,
    entry: str | None = None,
    language: str | None = None,
    types: list[str] | None = None,
    args: list[str] | None = None,
    pass_filenames: bool | None = None,
) -> dict[str, Any]:
    """Build a single hook dict, omitting ``None`` values."""
    hook: dict[str, Any] = {"id": hook_id, "name": name}
    if stages:
        hook["stages"] = stages
    if entry:
        hook["entry"] = entry
    if language:
        hook["language"] = language
    if types:
        hook["types"] = types
    if args:
        hook["args"] = args
    if pass_filenames is not None:
        hook["pass_filenames"] = pass_filenames
    return hook


def _repo_entry(
    repo_url: str,
    rev: str,
    hooks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a repo entry for .pre-commit-config.yaml."""
    return {"repo": repo_url, "rev": rev, "hooks": hooks}


def tool_config_for_languages(
    languages: list[str],
    repo: pathlib.Path,
) -> dict[str, list[dict]]:
    """Return pre-commit and pre-push tool configurations for *languages*.

    Uses detection-then-defaults: if a tool's config already exists in the
    repo we reference it as-is; otherwise we supply sensible defaults.
    """
    has_python = "python" in languages
    has_js = "javascript" in languages
    has_java = "java" in languages

    pre_commit: list[dict[str, Any]] = []
    pre_push: list[dict[str, Any]] = []

    # -- Pre-commit stage ---------------------------------------------------

    # gitleaks — always included
    pre_commit.append(
        _repo_entry(
            "https://github.com/gitleaks/gitleaks",
            "latest",
            [_hook("gitleaks", "Detect secrets with gitleaks")],
        )
    )

    if has_python:
        # ruff lint + format check
        pre_commit.append(
            _repo_entry(
                "https://github.com/astral-sh/ruff-pre-commit",
                "latest",
                [
                    _hook("ruff", "Ruff lint", args=["--fix"]),
                    _hook("ruff-format", "Ruff format check"),
                ],
            )
        )

    if has_js:
        # eslint — local hook using npx
        pre_commit.append(
            _repo_entry(
                "local",
                "latest",
                [
                    _hook(
                        "eslint",
                        "ESLint",
                        entry="npx eslint",
                        language="system",
                        types=["file"],
                        args=["--fix"],
                    ),
                ],
            )
        )
        # prettier
        pre_commit.append(
            _repo_entry(
                "https://github.com/pre-commit/mirrors-prettier",
                "latest",
                [_hook("prettier", "Prettier")],
            )
        )

    if has_java:
        # checkstyle — local
        pre_commit.append(
            _repo_entry(
                "local",
                "latest",
                [
                    _hook(
                        "checkstyle",
                        "Checkstyle",
                        entry="checkstyle",
                        language="system",
                        types=["java"],
                    ),
                ],
            )
        )

    # -- Pre-push stage -----------------------------------------------------

    if has_python:
        # mypy
        pre_push.append(
            _repo_entry(
                "https://github.com/pre-commit/mirrors-mypy",
                "latest",
                [_hook("mypy", "mypy type checking", stages=["pre-push"])],
            )
        )
        # pytest — local
        pre_push.append(
            _repo_entry(
                "local",
                "latest",
                [
                    _hook(
                        "pytest",
                        "Run pytest",
                        entry="pytest",
                        language="system",
                        stages=["pre-push"],
                        pass_filenames=False,
                    ),
                ],
            )
        )
        # pip-audit — local
        pre_push.append(
            _repo_entry(
                "local",
                "latest",
                [
                    _hook(
                        "pip-audit",
                        "pip-audit dependency check",
                        entry="pip-audit",
                        language="system",
                        stages=["pre-push"],
                        pass_filenames=False,
                    ),
                ],
            )
        )
        # bandit
        pre_push.append(
            _repo_entry(
                "https://github.com/PyCQA/bandit",
                "latest",
                [_hook("bandit", "Bandit security linter", stages=["pre-push"], args=["-r"])],
            )
        )

    if has_js:
        # tsc — local
        pre_push.append(
            _repo_entry(
                "local",
                "latest",
                [
                    _hook(
                        "tsc",
                        "TypeScript type check",
                        entry="npx tsc --noEmit",
                        language="system",
                        stages=["pre-push"],
                        pass_filenames=False,
                    ),
                ],
            )
        )
        # vitest / jest — pick based on detection
        if detect_existing_tool(repo, "vitest"):
            test_entry = "npx vitest run"
            test_id = "vitest"
            test_name = "Run vitest"
        elif detect_existing_tool(repo, "jest"):
            test_entry = "npx jest"
            test_id = "jest"
            test_name = "Run jest"
        else:
            # Default to vitest when neither is detected
            test_entry = "npx vitest run"
            test_id = "vitest"
            test_name = "Run vitest"
        pre_push.append(
            _repo_entry(
                "local",
                "latest",
                [
                    _hook(
                        test_id,
                        test_name,
                        entry=test_entry,
                        language="system",
                        stages=["pre-push"],
                        pass_filenames=False,
                    ),
                ],
            )
        )
        # npm audit — local
        pre_push.append(
            _repo_entry(
                "local",
                "latest",
                [
                    _hook(
                        "npm-audit",
                        "npm audit",
                        entry="npm audit --audit-level=moderate",
                        language="system",
                        stages=["pre-push"],
                        pass_filenames=False,
                    ),
                ],
            )
        )

    return {"pre-commit": pre_commit, "pre-push": pre_push}


# ---------------------------------------------------------------------------
# Pre-commit config generation
# ---------------------------------------------------------------------------

def _yaml_scalar(value: Any, indent: int = 0) -> str:
    """Format a single YAML scalar value."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        # Quote strings that could be misinterpreted
        if any(c in value for c in ":{}\n#[]") or value in ("true", "false", "null"):
            return f'"{value}"'
        return value
    return str(value)


def _yaml_list_inline(items: list[str]) -> str:
    """Format a short list as inline YAML: [a, b, c]."""
    return "[" + ", ".join(items) + "]"


def _render_hook(hook: dict[str, Any], indent: str = "      ") -> str:
    """Render a single hook entry as YAML lines."""
    lines: list[str] = []
    lines.append(f"{indent}- id: {_yaml_scalar(hook['id'])}")
    if "name" in hook:
        lines.append(f"{indent}  name: {_yaml_scalar(hook['name'])}")
    if "entry" in hook:
        lines.append(f"{indent}  entry: {_yaml_scalar(hook['entry'])}")
    if "language" in hook:
        lines.append(f"{indent}  language: {_yaml_scalar(hook['language'])}")
    if "stages" in hook:
        lines.append(f"{indent}  stages: {_yaml_list_inline(hook['stages'])}")
    if "types" in hook:
        lines.append(f"{indent}  types: {_yaml_list_inline(hook['types'])}")
    if "args" in hook:
        lines.append(f"{indent}  args: {_yaml_list_inline(hook['args'])}")
    if "pass_filenames" in hook:
        lines.append(f"{indent}  pass_filenames: {_yaml_scalar(hook['pass_filenames'])}")
    return "\n".join(lines)


def _render_repo(repo_entry: dict[str, Any]) -> str:
    """Render a single repo entry as YAML lines."""
    lines: list[str] = []
    lines.append(f"  - repo: {_yaml_scalar(repo_entry['repo'])}")
    lines.append(f"    rev: {_yaml_scalar(repo_entry['rev'])}")
    lines.append("    hooks:")
    for hook in repo_entry.get("hooks", []):
        lines.append(_render_hook(hook))
    return "\n".join(lines)


def generate_precommit_config(tools: dict[str, list[dict]]) -> str:
    """Generate YAML content for ``.pre-commit-config.yaml``.

    Uses string formatting — no YAML library required.
    """
    all_repos = tools.get("pre-commit", []) + tools.get("pre-push", [])
    if not all_repos:
        return "repos: []\n"

    lines: list[str] = ["repos:"]
    for repo_entry in all_repos:
        lines.append(_render_repo(repo_entry))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Merge with existing config
# ---------------------------------------------------------------------------

def merge_precommit_config(existing_path: pathlib.Path, new_repos: list[dict]) -> str:
    """Merge *new_repos* into an existing ``.pre-commit-config.yaml``.

    New repos are appended only if their ``repo`` URL is not already present
    in the file.  If parsing fails the original content is preserved and new
    repos are appended with a comment.
    """
    try:
        existing_content = existing_path.read_text(encoding="utf-8")
    except OSError:
        existing_content = ""

    if not existing_content.strip():
        return generate_precommit_config({"pre-commit": new_repos, "pre-push": []})

    # Extract existing repo URLs (simple line-based scan)
    existing_urls: set[str] = set()
    for line in existing_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- repo:"):
            url = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            existing_urls.add(url)

    repos_to_add = [r for r in new_repos if r["repo"] not in existing_urls]
    if not repos_to_add:
        return existing_content

    # Append new repos
    addition_lines: list[str] = [
        "  # --- Added by Arpinine Harness security tooling ---",
    ]
    for repo_entry in repos_to_add:
        addition_lines.append(_render_repo(repo_entry))

    # Ensure the file ends with a newline before appending
    merged = existing_content.rstrip("\n") + "\n" + "\n".join(addition_lines) + "\n"
    return merged


# ---------------------------------------------------------------------------
# Pre-commit framework checks
# ---------------------------------------------------------------------------

def check_precommit_installed() -> bool:
    """Return ``True`` if the ``pre-commit`` CLI is on ``$PATH``."""
    return shutil.which("pre-commit") is not None


def check_hooks_active(repo: pathlib.Path) -> dict[str, bool]:
    """Check whether pre-commit/pre-push hooks are installed in the repo.

    Returns a dict with ``pre_commit`` and ``pre_push`` booleans indicating
    whether the corresponding git hook file exists and is managed by the
    pre-commit framework (contains the string ``pre-commit``).
    """
    hooks_dir = repo / ".git" / "hooks"
    result: dict[str, bool] = {"pre_commit": False, "pre_push": False}

    for stage, key in [("pre-commit", "pre_commit"), ("pre-push", "pre_push")]:
        hook_file = hooks_dir / stage
        if hook_file.is_file():
            try:
                content = hook_file.read_text(encoding="utf-8", errors="replace")
                result[key] = "pre-commit" in content
            except OSError:
                pass

    return result


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

def _cache_path(repo: pathlib.Path) -> pathlib.Path:
    return repo / CACHE_FILE


def read_cache(repo: pathlib.Path) -> dict | None:
    """Read the security-tooling cache.  Return ``None`` on any error."""
    path = _cache_path(repo)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_cache(repo: pathlib.Path, status: dict) -> None:
    """Write *status* to the cache file with a timestamp."""
    path = _cache_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**status, "_cached_at": time.time()}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_cache_stale(cache: dict | None, ttl: int = CACHE_TTL_SECONDS) -> bool:
    """Return ``True`` if *cache* is absent, missing a timestamp, or expired."""
    if cache is None:
        return True
    cached_at = cache.get("_cached_at")
    if cached_at is None:
        return True
    try:
        return (time.time() - float(cached_at)) > ttl
    except (TypeError, ValueError):
        return True


# ---------------------------------------------------------------------------
# Installation instructions
# ---------------------------------------------------------------------------

_INSTALL_INSTRUCTIONS: dict[str, list[str]] = {
    "pre-commit": [
        "pip install pre-commit",
        "brew install pre-commit",
    ],
    "gitleaks": [
        "brew install gitleaks",
        "go install github.com/gitleaks/gitleaks/v8@latest",
    ],
    "pip-audit": [
        "pip install pip-audit",
    ],
    "bandit": [
        "pip install bandit",
    ],
    "mypy": [
        "pip install mypy",
    ],
    "npm": [
        "Install Node.js from nodejs.org or use nvm",
    ],
    "npx": [
        "Install Node.js from nodejs.org or use nvm",
    ],
}


def installation_instructions(missing: list[str]) -> list[str]:
    """Return human-readable install instructions for each missing tool."""
    instructions: list[str] = []
    for tool in missing:
        commands = _INSTALL_INSTRUCTIONS.get(tool)
        if commands:
            options = " or ".join(f"`{c}`" for c in commands)
            instructions.append(f"{tool}: {options}")
        else:
            instructions.append(f"{tool}: install manually (no known install command)")
    return instructions


# ---------------------------------------------------------------------------
# Status report
# ---------------------------------------------------------------------------

def format_status_report(repo: pathlib.Path) -> str:
    """Generate a formatted security health report for *repo*."""
    lines: list[str] = []
    lines.append("Security Tooling Status")
    lines.append("=" * 40)

    # Pre-commit installed?
    pc_installed = check_precommit_installed()
    lines.append(f"pre-commit installed: {'yes' if pc_installed else 'no'}")

    # Hooks active?
    hooks = check_hooks_active(repo)
    lines.append(f"pre-commit hook active: {'yes' if hooks['pre_commit'] else 'no'}")
    lines.append(f"pre-push hook active: {'yes' if hooks['pre_push'] else 'no'}")

    # Detected languages
    languages = detect_languages(repo)
    lines.append("")
    lines.append(f"Detected languages: {', '.join(languages) if languages else 'none'}")

    # Configured tools
    tools = tool_config_for_languages(languages, repo)
    pre_commit_tools = [
        hook["id"]
        for repo_entry in tools.get("pre-commit", [])
        for hook in repo_entry.get("hooks", [])
    ]
    pre_push_tools = [
        hook["id"]
        for repo_entry in tools.get("pre-push", [])
        for hook in repo_entry.get("hooks", [])
    ]
    lines.append("")
    lines.append("Configured tools (pre-commit stage):")
    for tool_id in pre_commit_tools:
        lines.append(f"  - {tool_id}")
    if not pre_commit_tools:
        lines.append("  (none)")

    lines.append("Configured tools (pre-push stage):")
    for tool_id in pre_push_tools:
        lines.append(f"  - {tool_id}")
    if not pre_push_tools:
        lines.append("  (none)")

    # Missing tools
    missing: list[str] = []
    if not pc_installed:
        missing.append("pre-commit")
    for tool_id in pre_commit_tools + pre_push_tools:
        if tool_id in _INSTALL_INSTRUCTIONS and shutil.which(tool_id) is None:
            if tool_id not in missing:
                missing.append(tool_id)

    if missing:
        lines.append("")
        lines.append("Missing tools:")
        for instruction in installation_instructions(missing):
            lines.append(f"  {instruction}")
    else:
        lines.append("")
        lines.append("All tools available.")

    return "\n".join(lines) + "\n"
