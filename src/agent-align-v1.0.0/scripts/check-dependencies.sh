#!/bin/bash
# Validate runtime dependencies for AgentAlign.
# This script reports readiness; it does not install tools automatically.

set -euo pipefail

echo "AGENTALIGN DEPENDENCY CHECK"
echo "---------------------------"

check_cmd() {
  local label="$1"
  local cmd="$2"
  local required="${3:-no}"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "OK     $label ($cmd found)"
    return 0
  fi

  if [[ "$required" == "yes" ]]; then
    echo "MISSING $label ($cmd not found) [required]"
  else
    echo "MISSING $label ($cmd not found) [optional]"
  fi
}

check_cmd "spec-kit CLI" "specify" "yes"
check_cmd "Python" "python3" "yes"
check_cmd "uv/uvx" "uvx" "no"
check_cmd "Node.js" "node" "no"
check_cmd "npm" "npm" "no"
check_cmd "OpenHarness-ready JS toolchain" "npx" "no"

if [[ -d ".specify/specs" ]]; then
  echo
  echo "SPEC-SCOPED CHECKS"
  echo "------------------"
  while IFS= read -r plan; do
    slug="$(basename "$(dirname "$plan")")"
    echo "Spec: $slug"

    if grep -qi "## Harness Strategy" "$plan"; then
      if grep -qi "openharness" "$plan"; then
        check_cmd "Node.js for OpenHarness workflows" "node" "no"
        check_cmd "npm for OpenHarness workflows" "npm" "no"
      fi
    fi

    eval_plan=".specify/evals/$slug/eval-plan.md"
    if [[ -f "$eval_plan" ]]; then
      framework="$(grep -iE '^- Framework:' "$eval_plan" | head -1 | sed 's/^- Framework:[[:space:]]*//')"
      if [[ -n "$framework" ]]; then
        echo "Eval framework declared: $framework"
      fi
      if grep -qi "deepeval" "$eval_plan"; then
        check_cmd "DeepEval CLI/runtime" "deepeval" "no"
      fi
      if grep -qi "pytest" "$eval_plan"; then
        check_cmd "pytest" "pytest" "no"
      fi
    fi
  done < <(find .specify/specs -name "plan.md" -type f 2>/dev/null | sort)
fi

echo
echo "Guidance:"
echo "- spec-kit is required for automated /spec-* generation flows."
echo "- Harness and eval dependencies are required only if selected in plan/eval artifacts."
echo "- AgentAlign validates dependencies; it does not install them during plugin installation."
