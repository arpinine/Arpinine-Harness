#!/bin/bash
# Pre-edit constitution check: fires before every Edit/Write via PreToolUse hook.
# Validate the pending content from stdin, not only the file currently on disk.

INPUT=$(cat)

if ! command -v python3 &>/dev/null; then
  exit 0
fi

RESULT=$(
  printf '%s' "$INPUT" | python3 -c '
import json
import pathlib
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    print("")
    raise SystemExit(0)

tool_input = payload.get("tool_input", {})
file_path = tool_input.get("file_path", "")
content = tool_input.get("content")
new_string = tool_input.get("new_string")
old_string = tool_input.get("old_string")
append = tool_input.get("append")

candidate = None
if isinstance(content, str):
    candidate = content
elif isinstance(new_string, str):
    existing = ""
    if file_path:
        try:
            existing = pathlib.Path(file_path).read_text()
        except Exception:
            existing = ""
    if isinstance(old_string, str) and old_string:
        if old_string in existing:
            candidate = existing.replace(old_string, new_string, 1)
        else:
            candidate = existing + new_string
    elif append and isinstance(existing, str):
        candidate = existing + new_string
    else:
        candidate = new_string if not existing else existing + "\n" + new_string
elif file_path:
    try:
        candidate = pathlib.Path(file_path).read_text()
    except Exception:
        candidate = ""

if candidate is None:
    candidate = ""

print(file_path)
print("<<<CONTENT>>>")
print(candidate)
' 2>/dev/null
)

FILE_PATH=$(printf '%s\n' "$RESULT" | awk 'BEGIN{seen=0} /^<<<CONTENT>>>$/{seen=1; exit} !seen {print}')
PENDING_CONTENT=$(printf '%s\n' "$RESULT" | awk 'BEGIN{seen=0} /^<<<CONTENT>>>$/{seen=1; next} seen {print}')

[[ -z "$FILE_PATH" ]] && exit 0

TECH_PATTERN='FastAPI|Django|Flask|Rails|Spring|Laravel|NestJS|Express|'
TECH_PATTERN+='React|Vue|Angular|Svelte|NextJS|'
TECH_PATTERN+='PostgreSQL|MySQL|SQLite|MongoDB|DynamoDB|Firestore|Redis|Kafka|RabbitMQ|'
TECH_PATTERN+='JWT|OAuth|SAML|OpenID|'
TECH_PATTERN+='Docker|Kubernetes|Terraform|AWS|GCP|Azure|Vercel|'
TECH_PATTERN+='Prisma|SQLAlchemy|TypeORM|Sequelize|Hibernate|'
TECH_PATTERN+='gRPC|GraphQL|REST|WebSocket'

if [[ "$FILE_PATH" == *"spec.md" ]] && printf '%s' "$PENDING_CONTENT" | grep -q -E "$TECH_PATTERN"; then
  echo "VIOLATION: spec.md contains implementation details"
  echo "spec.md must stay product-facing. Move tech choices to plan.md or ADRs."
  exit 1
fi

if printf '%s' "$PENDING_CONTENT" | grep -q -iE \
  "(api_key|api_secret|secret|password|passwd|token|auth_token|access_key|private_key)[[:space:]]*[:=][[:space:]]*['\"][^'\"]{3,}"; then
  echo "VIOLATION: Hardcoded secret detected in pending changes for $FILE_PATH"
  echo "Use environment variables or a secret manager reference."
  exit 1
fi

exit 0
