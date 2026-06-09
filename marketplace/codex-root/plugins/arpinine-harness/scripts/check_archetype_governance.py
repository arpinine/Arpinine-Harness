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
FRONTEND_PATH_RE = re.compile(r"(^|/)(src/)?frontend(/|$)", re.IGNORECASE)
DB_PATH_RE = re.compile(r"(^|/)(src/)?db(/|$)", re.IGNORECASE)
INFRA_PATH_RE = re.compile(r"(^|/)infra(/|$)", re.IGNORECASE)
AGENT_APP_FORBIDDEN_IMPORT_RE = re.compile(
    r"\b(fastapi|flask|django|express|nestjs|sqlalchemy|sequelize|typeorm|prisma|requests|httpx|psycopg|sqlite3|openharness|langgraph|pydantic_ai|semantic_kernel)\b",
    re.IGNORECASE,
)
ML_DOMAIN_FORBIDDEN_IMPORT_RE = re.compile(
    r"\b(sklearn|torch|tensorflow|xgboost|lightgbm|catboost|pandas|numpy)\b",
    re.IGNORECASE,
)
NOTEBOOK_IMPORT_RE = re.compile(r"\bfrom\s+notebooks\b|\bimport\s+notebooks\b|\.\./notebooks\b", re.IGNORECASE)
# Technology-agnostic fullstack-app: framework names are illustrative examples of the
# stack a product might pick, not an allow/deny list. The boundary, not the framework,
# is what is enforced.
FULLSTACK_DOMAIN_FORBIDDEN_IMPORT_RE = re.compile(
    r"\b(fastapi|flask|django|express|nestjs|sqlalchemy|sequelize|typeorm|prisma|"
    r"requests|httpx|psycopg|sqlite3|react|react-dom|vue|svelte|sveltekit|vite|next|axios)\b",
    re.IGNORECASE,
)
PERSISTENCE_IMPORT_RE = re.compile(
    r"\b(sqlalchemy|sequelize|typeorm|prisma|psycopg|psycopg2|asyncpg|sqlite3|"
    r"pymongo|mongoose|knex|mysql|mysql2|pg)\b",
    re.IGNORECASE,
)
IAC_IMPORT_RE = re.compile(r"\b(aws_cdk|aws-cdk-lib|constructs|pulumi|cdktf|troposphere)\b", re.IGNORECASE)
# Frontend reaching into backend/domain/db internals instead of the API boundary.
APP_INTERNAL_IMPORT_RE = re.compile(
    r"(from|import|require)\b[^\n]*\b(src[\\/.])?(backend|domain|db)\b", re.IGNORECASE
)
# Infrastructure code importing application business logic.
APP_LOGIC_FROM_INFRA_RE = re.compile(r"\b(src[\\/.])(domain|backend)\b", re.IGNORECASE)
# Stack-specific fullstack-react-fastapi layout (frontend/ + backend/ + iac/ at repo root).
BACKEND_PATH_RE = re.compile(r"(^|/)backend(/|$)", re.IGNORECASE)
BACKEND_API_PATH_RE = re.compile(r"(^|/)backend/api(/|$)", re.IGNORECASE)
STORES_PATH_RE = re.compile(r"(^|/)stores(/|$)", re.IGNORECASE)
IAC_PATH_RE = re.compile(r"(^|/)(iac|infra)(/|$)", re.IGNORECASE)
SERVER_STATE_RE = re.compile(
    r"\b(axios|react-query|@tanstack/react-query|useQuery|useMutation|useInfiniteQuery)\b|\bfetch\s*\(",
    re.IGNORECASE,
)
IAC_APP_IMPORT_RE = re.compile(
    r"(from|import|require)\b[^\n]*\bbackend[\\/.](core|api)\b", re.IGNORECASE
)


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

    if archetype == "fullstack-app":
        # 1. domain stays free of framework, transport, persistence, and frontend imports
        if DOMAIN_PATH_RE.search(rel) and FULLSTACK_DOMAIN_FORBIDDEN_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-app domain layer cannot import web frameworks, transport, persistence, or frontend libraries.")
            print("Keep src/domain/ pure; move framework code into src/backend/, src/db/, or src/frontend/.")
            return 1
        # 2. database drivers / ORM confined to src/db/
        if SRC_PATH_RE.search(rel) and not DB_PATH_RE.search(rel) and PERSISTENCE_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-app database drivers and ORM imports are confined to src/db/.")
            print("Depend on the repository abstractions exposed by src/db/ instead of importing the driver/ORM directly.")
            return 1
        # 3. frontend talks to the backend only through the published API boundary
        if FRONTEND_PATH_RE.search(rel) and APP_INTERNAL_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-app frontend cannot import src/backend/, src/domain/, or src/db/.")
            print("Call the backend over the published HTTP/API boundary and depend only on shared contract types.")
            return 1
        # 4a. application code under src/ must not import infrastructure-as-code constructs
        if SRC_PATH_RE.search(rel) and IAC_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-app application code cannot import infrastructure-as-code constructs.")
            print("Keep IaC (CDK, Pulumi, Terraform, ...) inside infra/.")
            return 1
        # 4b. infrastructure code must not import application business logic
        if INFRA_PATH_RE.search(rel) and APP_LOGIC_FROM_INFRA_RE.search(pending):
            print("VIOLATION: fullstack-app infrastructure code cannot import application business logic from src/.")
            print("Infra communicates with the app through configuration and environment, not shared imports.")
            return 1

    if archetype == "fullstack-react-fastapi":
        # frontend talks to the backend only through the HTTP API boundary
        if FRONTEND_PATH_RE.search(rel) and APP_INTERNAL_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-react-fastapi frontend cannot import from backend/.")
            print("Call the FastAPI endpoints over HTTP (Axios) and depend only on shared contract types (Zod).")
            return 1
        # route handlers in backend/api/ are thin wrappers — no persistence/ORM access
        if BACKEND_API_PATH_RE.search(rel) and PERSISTENCE_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-react-fastapi route handlers in backend/api/ cannot access the database/ORM directly.")
            print("Keep handlers thin; move data access and business logic into backend/core/.")
            return 1
        # server state belongs in React Query, not Zustand stores
        if STORES_PATH_RE.search(rel) and SERVER_STATE_RE.search(pending):
            print("VIOLATION: fullstack-react-fastapi Zustand stores cannot hold server state (no axios/fetch/React Query).")
            print("Use React Query for server state; keep stores for UI-only state.")
            return 1
        # AWS CDK confined to iac/ — application code must not import it
        if (FRONTEND_PATH_RE.search(rel) or BACKEND_PATH_RE.search(rel)) and IAC_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-react-fastapi application code cannot import AWS CDK / infrastructure constructs.")
            print("Keep CDK inside iac/cdk/.")
            return 1
        # infrastructure code must not import application business logic
        if IAC_PATH_RE.search(rel) and IAC_APP_IMPORT_RE.search(pending):
            print("VIOLATION: fullstack-react-fastapi infrastructure code cannot import application business logic from backend/.")
            print("Infra communicates with the app through configuration and environment, not shared imports.")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
