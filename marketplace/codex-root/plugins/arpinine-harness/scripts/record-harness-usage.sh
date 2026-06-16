#!/bin/bash
set -uo pipefail

INPUT=$(cat)

if ! command -v python3 &>/dev/null; then
  exit 0
fi

printf '%s' "$INPUT" | python3 "scripts/record_harness_usage_from_hook.py" || true
exit 0
