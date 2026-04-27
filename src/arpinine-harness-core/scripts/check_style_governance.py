#!/usr/bin/env python3
"""
Pre-edit gate: require repository-defined style standards for edited languages.
"""

from __future__ import annotations

import json
import pathlib
import sys

CODE_PREFIXES = ("src/", "lib/", "app/", "packages/", "services/", "internal/", "cmd/", "tests/")
STYLE_ROOT = "tools/style"

LANGUAGE_RULES: dict[str, dict[str, object]] = {
    ".py": {
        "language": "Python",
        "configs": [f"{STYLE_ROOT}/python/pyproject.toml"],
    },
    ".js": {
        "language": "JavaScript/TypeScript",
        "configs": [
            f"{STYLE_ROOT}/frontend/eslint.config.cjs",
            f"{STYLE_ROOT}/frontend/.prettierrc.json",
        ],
    },
    ".jsx": {
        "language": "JavaScript/TypeScript",
        "configs": [
            f"{STYLE_ROOT}/frontend/eslint.config.cjs",
            f"{STYLE_ROOT}/frontend/.prettierrc.json",
        ],
    },
    ".ts": {
        "language": "JavaScript/TypeScript",
        "configs": [
            f"{STYLE_ROOT}/frontend/eslint.config.cjs",
            f"{STYLE_ROOT}/frontend/.prettierrc.json",
        ],
    },
    ".tsx": {
        "language": "JavaScript/TypeScript",
        "configs": [
            f"{STYLE_ROOT}/frontend/eslint.config.cjs",
            f"{STYLE_ROOT}/frontend/.prettierrc.json",
        ],
    },
    ".go": {
        "language": "Go",
        "configs": ["go.mod", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".java": {
        "language": "Java",
        "configs": [f"{STYLE_ROOT}/java/checkstyle.xml", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".rs": {
        "language": "Rust",
        "configs": [f"{STYLE_ROOT}/rust/rustfmt.toml", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".swift": {
        "language": "Swift",
        "configs": [f"{STYLE_ROOT}/swift/.swift-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".sh": {
        "language": "Shell",
        "configs": [f"{STYLE_ROOT}/shared/.editorconfig", ".shfmt.conf"],
    },
    ".bash": {
        "language": "Shell",
        "configs": [f"{STYLE_ROOT}/shared/.editorconfig", ".shfmt.conf"],
    },
    ".zsh": {
        "language": "Shell",
        "configs": [f"{STYLE_ROOT}/shared/.editorconfig", ".shfmt.conf"],
    },
    ".lua": {
        "language": "Lua",
        "configs": [f"{STYLE_ROOT}/lua/stylua.toml", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".c": {
        "language": "C/C++",
        "configs": [f"{STYLE_ROOT}/cpp/.clang-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".m": {
        "language": "Objective-C",
        "configs": [f"{STYLE_ROOT}/cpp/.clang-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".mm": {
        "language": "Objective-C",
        "configs": [f"{STYLE_ROOT}/cpp/.clang-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".cc": {
        "language": "C/C++",
        "configs": [f"{STYLE_ROOT}/cpp/.clang-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".cpp": {
        "language": "C/C++",
        "configs": [f"{STYLE_ROOT}/cpp/.clang-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".h": {
        "language": "C/C++",
        "configs": [f"{STYLE_ROOT}/cpp/.clang-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".hpp": {
        "language": "C/C++",
        "configs": [f"{STYLE_ROOT}/cpp/.clang-format", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".erl": {
        "language": "Erlang",
        "configs": [f"{STYLE_ROOT}/erlang/elvis.config", f"{STYLE_ROOT}/erlang/rebar.config", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
    ".hrl": {
        "language": "Erlang",
        "configs": [f"{STYLE_ROOT}/erlang/elvis.config", f"{STYLE_ROOT}/erlang/rebar.config", f"{STYLE_ROOT}/shared/.editorconfig"],
    },
}

STYLE_CONFIG_EDIT_PATHS = {
    ".specify/CONSTITUTION.md",
    f"{STYLE_ROOT}/README.md",
    f"{STYLE_ROOT}/python/pyproject.toml",
    f"{STYLE_ROOT}/frontend/eslint.config.cjs",
    f"{STYLE_ROOT}/frontend/.prettierrc.json",
    f"{STYLE_ROOT}/shared/.editorconfig",
    f"{STYLE_ROOT}/java/checkstyle.xml",
    "go.mod",
    "Cargo.toml",
    f"{STYLE_ROOT}/rust/rustfmt.toml",
    f"{STYLE_ROOT}/swift/.swift-format",
    ".shfmt.conf",
    f"{STYLE_ROOT}/lua/stylua.toml",
    f"{STYLE_ROOT}/cpp/.clang-format",
    f"{STYLE_ROOT}/erlang/elvis.config",
    f"{STYLE_ROOT}/erlang/rebar.config",
}


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def find_project_root(start: pathlib.Path) -> pathlib.Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / ".specify").exists():
            return candidate
    return pathlib.Path(".").resolve()


def main() -> int:
    payload = load_payload()
    tool_input = payload.get("tool_input", {})
    file_path = str(tool_input.get("file_path", ""))
    if not file_path:
        return 0

    normalized = pathlib.Path(file_path).as_posix()
    if normalized in STYLE_CONFIG_EDIT_PATHS:
        return 0

    if not normalized.startswith(CODE_PREFIXES):
        return 0

    ext = pathlib.Path(normalized).suffix.lower()
    rule = LANGUAGE_RULES.get(ext)
    if not rule:
        return 0

    repo = find_project_root(pathlib.Path.cwd())
    configs = [repo / name for name in rule["configs"]]
    if any(path.exists() for path in configs):
        return 0

    language = rule["language"]
    config_list = ", ".join(f"`{name}`" for name in rule["configs"])
    print(f"VIOLATION: no repository-defined style standard found for {language}")
    print(f"Pending edit: {normalized}")
    print(
        "The constitution requires one shared style standard per language across all teams and plugins."
    )
    print(
        f"Add a checked-in style config before editing {language} files. Accepted markers for this language: {config_list}."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
