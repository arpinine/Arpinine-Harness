#!/bin/bash
# Pre-edit task-claim gate.
# Block implementation-path edits unless the current team has an active claim.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 &>/dev/null; then
  exit 0
fi

python3 "$SCRIPT_DIR/check_task_claim.py"
exit $?
