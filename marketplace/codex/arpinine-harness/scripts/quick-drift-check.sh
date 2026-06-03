#!/bin/bash
# Quick post-edit drift check: fires on every file write via PostToolUse hook.
# Lightweight by design: file references, endpoint mismatch hints, and stale eval hints.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 &>/dev/null; then
  exit 0
fi

python3 "$SCRIPT_DIR/quick_drift_check.py" || true
# Intentionally advisory — drift warnings are non-blocking.
# Drift findings are surfaced as prominent warnings for the user to review,
# but do not block edit operations. See security review item H2.
exit 0
