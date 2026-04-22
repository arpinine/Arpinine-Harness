#!/bin/bash
# Quick post-edit drift check: fires on every file write via PostToolUse hook.
# Lightweight — full analysis is /spec-audit.

# Find most recently modified spec (sort by mtime, not arbitrary head -1)
LATEST_SPEC=$(find .specify/specs -name "spec.md" -type f 2>/dev/null \
  | xargs ls -t 2>/dev/null \
  | head -1)

[[ -z "$LATEST_SPEC" ]] && exit 0

# Match file references across common project layouts
MISSING_FILES=$(grep -oE \
  '(src|lib|app|packages|services|internal|cmd)/[a-zA-Z0-9_/.-]+\.(py|js|ts|go|rs|java|rb|kt|swift)' \
  "$LATEST_SPEC" 2>/dev/null \
  | sort -u \
  | while read -r file; do
      [[ ! -f "$file" ]] && echo "   ⚠️  $file (in spec, not found on disk)"
    done)

if [[ -n "$MISSING_FILES" ]]; then
  echo "📋 Quick Drift Check ($(basename "$(dirname "$LATEST_SPEC")/spec.md")):"
  echo "$MISSING_FILES"
  echo "   Run /spec-audit for full analysis and ADR resolution."
fi
