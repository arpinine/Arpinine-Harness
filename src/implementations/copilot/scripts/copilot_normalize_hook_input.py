#!/usr/bin/env python3
"""Normalize GitHub Copilot hook payloads to the shared Claude-shaped edit payload."""

from __future__ import annotations

import json
import sys
from typing import Any


def _as_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _first(args: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in args and args[key] is not None:
            return args[key]
    return None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        json.dump({}, sys.stdout)
        return 0

    try:
        payload = json.loads(raw)
    except Exception:
        json.dump({}, sys.stdout)
        return 0

    tool_name = str(payload.get("toolName") or payload.get("tool_name") or "").lower()
    tool_args = _as_object(payload.get("toolArgs") or payload.get("tool_args"))

    file_path = _first(tool_args, "filePath", "file_path", "path", "targetFile", "target_file", "filename")
    content = _first(tool_args, "content", "fileContents", "file_contents", "text")
    new_string = _first(tool_args, "newString", "new_string", "replacement", "replaceWith", "replace_with")
    old_string = _first(tool_args, "oldString", "old_string", "search", "searchText", "search_text")
    append = bool(_first(tool_args, "append", "isAppend", "is_append"))

    updated_content = _first(tool_args, "updatedContent", "updated_content")
    if tool_name == "create" and content is None and isinstance(new_string, str):
        content = new_string
    if tool_name == "edit" and content is None and isinstance(updated_content, str):
        content = updated_content

    normalized = {
        "tool_input": {
            "file_path": file_path or "",
            "content": content if isinstance(content, str) else None,
            "new_string": new_string if isinstance(new_string, str) else None,
            "old_string": old_string if isinstance(old_string, str) else None,
            "append": append,
        }
    }
    json.dump(normalized, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
