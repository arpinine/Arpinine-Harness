#!/bin/bash
# Regenerate .specify/delivery.md from .specify/specs/*/plan.md data.

INPUT=$(cat)

if ! command -v python3 &>/dev/null; then
  exit 0
fi

printf '%s' "$INPUT" | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update_backlog.py"
exit 0
