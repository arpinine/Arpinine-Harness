#!/bin/bash
# Pre-edit constitution check: fires before every Edit/Write via PreToolUse hook.
# Tool input arrives as JSON on stdin — extract file_path from it.

INPUT=$(cat)

# Parse file_path from stdin JSON (prefer python3, fall back to grep)
if command -v python3 &>/dev/null; then
  FILE_PATH=$(printf '%s' "$INPUT" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" \
    2>/dev/null)
else
  FILE_PATH=$(printf '%s' "$INPUT" \
    | grep -o '"file_path" *: *"[^"]*"' \
    | sed 's/.*: *"//;s/"//')
fi

[[ -z "$FILE_PATH" ]] && exit 0

# --- Rule 1: No tech details in spec.md ---
if [[ "$FILE_PATH" == *"spec.md" ]]; then
  TECH_PATTERN='FastAPI|Django|Flask|Rails|Spring|Laravel|NestJS|Express|'
  TECH_PATTERN+='React|Vue|Angular|Svelte|NextJS|'
  TECH_PATTERN+='PostgreSQL|MySQL|SQLite|MongoDB|DynamoDB|Firestore|Redis|Kafka|RabbitMQ|'
  TECH_PATTERN+='JWT|OAuth|SAML|OpenID|'
  TECH_PATTERN+='Docker|Kubernetes|Terraform|AWS|GCP|Azure|Vercel|'
  TECH_PATTERN+='Prisma|SQLAlchemy|TypeORM|Sequelize|Hibernate|'
  TECH_PATTERN+='gRPC|GraphQL|REST|WebSocket'

  if grep -q -E "$TECH_PATTERN" "$FILE_PATH" 2>/dev/null; then
    echo "❌ VIOLATION: spec.md contains implementation details"
    echo "   spec.md = WHAT/WHY (product). Move tech choices to plan.md."
    exit 1
  fi
fi

# --- Rule 2: No hardcoded secrets (case-insensitive key names) ---
if grep -q -iE \
  "(api_key|api_secret|secret|password|passwd|token|auth_token|access_key|private_key)[[:space:]]*=[[:space:]]*['\"][^'\"]{3,}" \
  "$FILE_PATH" 2>/dev/null; then
  echo "❌ VIOLATION: Hardcoded secret detected in $FILE_PATH"
  echo "   Use environment variables. No secrets in source files."
  exit 1
fi

exit 0
