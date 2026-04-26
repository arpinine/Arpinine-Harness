#!/bin/bash
# Pre-edit security setup check: verify pre-commit hooks are installed and active.
# Uses a cache with 5-minute TTL to avoid checking on every edit.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 &>/dev/null; then
  echo "AgentAlign security check failed: Python (python3) not found."
  echo "Ensure your environment is set up correctly:"
  echo "  - Activate your virtual environment: source .venv/bin/activate"
  echo "  - Install dependencies: uv sync (or pip install -r requirements.txt)"
  exit 1
fi

export PYTHONPATH="$SCRIPT_DIR"
python3 "$SCRIPT_DIR/check_security_setup.py"
exit $?
