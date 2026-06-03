#!/usr/bin/env bash
# Build every implementation's release bundle and publish them to a GitHub Release.
# Separate from assemble/build/install — only packages + uploads.
#
# Usage: tools/release/publish_release.sh [tag]
#   tag defaults to v<version> read from the Claude plugin manifest (all impls share one version).
#
# Requires: gh CLI authenticated (`gh auth login`). Set DRAFT=1 for a draft release.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

IMPLS="claude codex copilot"

VERSION="$(python3 -c "import json; print(json.load(open('src/implementations/claude/.claude-plugin/plugin.json'))['version'])")"
TAG="${1:-v$VERSION}"

command -v gh >/dev/null || { echo "gh CLI not found. Install it or run 'make release-all' to only build the zips." >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh is not authenticated. Run 'gh auth login' first." >&2; exit 1; }

# Build all bundles.
ASSETS=()
for impl in $IMPLS; do
  tools/release/package_release.sh "$impl"
  zip="dist/$impl/release/arpinine-harness-$impl-v$VERSION.zip"
  test -f "$zip" || { echo "Expected bundle missing: $zip" >&2; exit 1; }
  ASSETS+=("$zip")
done

NOTES="Arpinine Harness $TAG — plugin bundles for Claude Code, Codex, and GitHub Copilot CLI.

Install without building: download the bundle for your assistant and follow the
\"Install from a GitHub Release\" section of the README.
- Claude / Codex: extract, then \`marketplace add <dir>\` + install.
- Copilot: extract, then run \`./install.sh\` (resolves machine-specific hook paths)."

DRAFT_FLAG=""
[ "${DRAFT:-0}" = "1" ] && DRAFT_FLAG="--draft"

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "Release $TAG exists — uploading assets (clobbering existing)..."
  gh release upload "$TAG" "${ASSETS[@]}" --clobber
else
  echo "Creating release $TAG ..."
  gh release create "$TAG" "${ASSETS[@]}" --title "Arpinine Harness $TAG" --notes "$NOTES" $DRAFT_FLAG
fi

echo "Published $TAG with: ${ASSETS[*]}"
