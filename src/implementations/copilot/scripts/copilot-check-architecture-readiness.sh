#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NORMALIZED="$(python3 "$SCRIPT_DIR/copilot_normalize_hook_input.py")"

printf '%s' "$NORMALIZED" | "$SCRIPT_DIR/check-architecture-readiness.sh"
