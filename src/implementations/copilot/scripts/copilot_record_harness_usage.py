#!/usr/bin/env python3
"""Record one GitHub Copilot hook event into the harness-usage ledger.

This is intentionally fail-open. Copilot hook payloads do not consistently expose
model/token/cost telemetry today, so the recorder stores whatever the host
provides and marks the rest as absent. Reports then surface these runs as
incomplete instead of inventing cost.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import Any

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
CORE_SCRIPT_DIR = SCRIPT_DIR.parents[2] / "arpinine-harness-core" / "scripts"
if CORE_SCRIPT_DIR.exists() and str(CORE_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_SCRIPT_DIR))

from measurement_artifacts import write_harness_usage_run


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


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


def _lookup(obj: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def infer_spec_slug(file_path: str | None) -> str | None:
    if not file_path:
        return None
    normalized = file_path.replace("\\", "/")
    patterns = (
        r"/?\.specify/specs/([^/]+)/",
        r"/?\.specify/evals/([^/]+)/",
        r"/?\.specify/observations/([^/]+)/",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return match.group(1)
    return None


def build_usage_record(payload: dict[str, Any]) -> tuple[dict, str | None]:
    tool_name = str(payload.get("toolName") or payload.get("tool_name") or "unknown").lower()
    tool_args = _as_object(payload.get("toolArgs") or payload.get("tool_args"))
    usage = _as_object(payload.get("usage"))
    billing = _as_object(payload.get("billing"))
    model = _as_object(payload.get("model"))

    file_path = _lookup(tool_args, "filePath", "file_path", "path", "targetFile", "target_file", "filename")
    spec_slug = infer_spec_slug(file_path if isinstance(file_path, str) else None)
    session_id = _lookup(payload, "sessionId", "session_id")

    token_in = _lookup(
        usage,
        "inputTokens",
        "input_tokens",
        "promptTokens",
        "prompt_tokens",
        "input",
    )
    token_out = _lookup(
        usage,
        "outputTokens",
        "output_tokens",
        "completionTokens",
        "completion_tokens",
        "output",
    )
    cost_usd = _lookup(billing, "costUsd", "cost_usd", "usd")
    model_name = _lookup(model, "name", "model_name", "id") or _lookup(payload, "modelName", "model_name")
    model_version = _lookup(model, "version", "model_version") or _lookup(payload, "modelVersion", "model_version")

    host = os.environ.get("ARPININE_HARNESS_TEAM_ID") or "copilot"
    record = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": f"copilot:{tool_name}",
        "spec_slug": spec_slug,
        "session_id": str(session_id) if session_id else None,
        "host": host,
        "model_name": model_name,
        "model_version": model_version,
        "token_count_input": _to_float(token_in),
        "token_count_output": _to_float(token_out),
        "cost_usd": _to_float(cost_usd),
        "outcome": "RECORDED",
        "source_file_path": file_path if isinstance(file_path, str) else None,
    }
    return record, (str(session_id) if session_id else None)


def main() -> int:
    repo = find_project_root(pathlib.Path.cwd())
    if repo is None:
        return 0

    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0

    record, session_id = build_usage_record(payload)
    write_harness_usage_run(repo, record, session_id=session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
