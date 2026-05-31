#!/bin/bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NORMALIZED="$(python3 "$SCRIPT_DIR/copilot_normalize_hook_input.py")"

if ! command -v python3 &>/dev/null; then
  exit 0
fi

printf '%s' "$NORMALIZED" | python3 "$SCRIPT_DIR/update_backlog.py"
exit 0
