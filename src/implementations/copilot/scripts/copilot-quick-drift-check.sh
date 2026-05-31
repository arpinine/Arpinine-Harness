#!/bin/bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 &>/dev/null; then
  exit 0
fi

NORMALIZED="$(python3 "$SCRIPT_DIR/copilot_normalize_hook_input.py")"

printf '%s' "$NORMALIZED" | "$SCRIPT_DIR/quick-drift-check.sh" || true
# Intentionally advisory — drift warnings are non-blocking (mirrors core quick-drift-check.sh).
exit 0
