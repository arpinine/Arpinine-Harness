#!/usr/bin/env python3
"""Executable archetype-specific pre-edit checks."""

from __future__ import annotations

import json
import pathlib
import re
import sys

from archetype_support import load_selected_archetype
from spec_provider import find_project_root


DOMAIN_PATH_RE = re.compile(r"(^|/)(src/)?domain(/|$)", re.IGNORECASE)
SRC_PATH_RE = re.compile(r"(^|/)(src|lib|app)/", re.IGNORECASE)
AGENT_APP_FORBIDDEN_IMPORT_RE = re.compile(
    r"\b(fastapi|flask|django|express|nestjs|sqlalchemy|sequelize|typeorm|prisma|requests|httpx|psycopg|sqlite3|openharness|langgraph|pydantic_ai|semantic_kernel)\b",
    re.IGNORECASE,
)
ML_DOMAIN_FORBIDDEN_IMPORT_RE = re.compile(
    r"\b(sklearn|torch|tensorflow|xgboost|lightgbm|catboost|pandas|numpy)\b",
    re.IGNORECASE,
)
NOTEBOOK_IMPORT_RE = re.compile(r"\bfrom\s+notebooks\b|\bimport\s+notebooks\b|\.\./notebooks\b", re.IGNORECASE)


def read_payload() -> tuple[str, str]:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return "", ""

    tool_input = payload.get("tool_input", {})
    file_path = str(tool_input.get("file_path", "") or "")
    content = tool_input.get("content")
    new_string = tool_input.get("new_string")
    if isinstance(content, str):
        return file_path, content
    if isinstance(new_string, str):
        return file_path, new_string
    return file_path, ""


def main() -> int:
    repo = find_project_root(pathlib.Path.cwd()) or pathlib.Path.cwd()
    archetype = load_selected_archetype(repo)
    if not archetype:
        return 0

    file_path, pending = read_payload()
    if not file_path:
        return 0

    rel_path = pathlib.Path(file_path).resolve()
    try:
        rel = rel_path.relative_to(repo.resolve()).as_posix()
    except Exception:
        rel = pathlib.Path(file_path).as_posix()

    if archetype == "agent-app":
        if DOMAIN_PATH_RE.search(rel) and AGENT_APP_FORBIDDEN_IMPORT_RE.search(pending):
            print("VIOLATION: agent-app domain layer cannot import framework, runtime, transport, or persistence packages.")
            print("Move infrastructure code into tools/adapters and keep domain modules pure.")
            return 1

    if archetype == "ml-pipeline":
        if rel.startswith("data/raw/"):
            print("VIOLATION: ml-pipeline raw data is immutable after ingest.")
            print("Write derived artifacts under data/processed/ instead of editing data/raw/.")
            return 1
        if SRC_PATH_RE.search(rel) and NOTEBOOK_IMPORT_RE.search(pending):
            print("VIOLATION: production code cannot import from notebooks in the ml-pipeline archetype.")
            print("Move reusable logic into src/ and keep notebooks exploratory only.")
            return 1
        if DOMAIN_PATH_RE.search(rel) and ML_DOMAIN_FORBIDDEN_IMPORT_RE.search(pending):
            print("VIOLATION: ml-pipeline domain modules cannot import ML/dataframe frameworks directly.")
            print("Keep domain logic framework-independent; move ML-specific code into features, models, or pipelines.")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
