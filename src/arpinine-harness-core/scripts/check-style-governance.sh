#!/bin/bash
# Pre-edit style governance gate.
# Block code edits when the repo has no declared style standard for that language.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 &>/dev/null; then
  exit 0
fi

export PYTHONPATH="$SCRIPT_DIR"
python3 "$SCRIPT_DIR/check_style_governance.py"
exit $?
