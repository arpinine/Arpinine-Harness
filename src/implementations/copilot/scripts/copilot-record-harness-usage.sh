#!/bin/bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 &>/dev/null; then
  exit 0
fi

python3 "$SCRIPT_DIR/copilot_record_harness_usage.py" || true
exit 0
