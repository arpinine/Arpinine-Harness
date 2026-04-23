#!/bin/bash
# Validate runtime dependencies for AgentAlign.
# This script reports readiness; it does not install tools automatically.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "MISSING Python (python3 not found) [required]"
  exit 1
fi

python3 "$SCRIPT_DIR/check_dependencies.py" "$@"
