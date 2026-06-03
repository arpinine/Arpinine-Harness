#!/bin/bash
# Pre-edit archetype governance check.
set -euo pipefail

INPUT=$(cat)

if ! command -v python3 &>/dev/null; then
  exit 0
fi

printf '%s' "$INPUT" | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_archetype_governance.py"
