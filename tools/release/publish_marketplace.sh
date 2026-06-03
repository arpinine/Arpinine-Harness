#!/usr/bin/env bash
# Refresh the COMMITTED, in-repo plugin marketplace so consumers can install with
#   <host> plugin marketplace add arpinine/Arpinine-Harness
# directly from GitHub — no zip download, no build.
#
# Separate from assemble/build/install: it only assembles (read-only reuse) and
# copies the portable assembled trees into the committed `marketplace/` directory,
# then writes the host-specific marketplace manifests. Claude installs directly
# from the repo root. Codex stages a committed Codex-only local marketplace root
# from `marketplace/codex-root/`.
#
# Only portable hosts are eligible: Claude (${CLAUDE_PLUGIN_ROOT}) and Codex
# (plugin-relative hook paths). Copilot bakes machine-absolute hook paths and is
# NOT publishable as a committed marketplace — ship it via `make release` zip.
#
# Usage: tools/release/publish_marketplace.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PLUGIN_NAME="arpinine-harness"
MARKETPLACE="arpinine-harness-local"

assert_portable() { # dir
  if grep -rqI "/Users/\|/home/" "$1" 2>/dev/null; then
    echo "Refusing to publish: machine-absolute path found in $1 (not portable)." >&2
    grep -rnI "/Users/\|/home/" "$1" 2>/dev/null | head >&2
    exit 1
  fi
  # Only config/code carry resolvable placeholders; markdown docs legitimately
  # mention them in prose, so exclude *.md from this check.
  local hits
  hits="$(grep -rlI "__[A-Z_]*PLUGIN_INSTALL_PATH__" "$1" 2>/dev/null | grep -v '\.md$' || true)"
  if [ -n "$hits" ]; then
    echo "Refusing to publish: unresolved install-path placeholder in config/code (would resolve to an invalid path):" >&2
    echo "$hits" >&2
    exit 1
  fi
}

# ---- Claude ----
make assemble IMPLEMENTATION=claude >/dev/null
CLAUDE_SRC="dist/claude/plugins/arpinine-harness-claude"
test -d "$CLAUDE_SRC" || { echo "Missing assembled Claude tree: $CLAUDE_SRC" >&2; exit 1; }
assert_portable "$CLAUDE_SRC"
rm -rf "marketplace/claude"
mkdir -p "marketplace/claude/arpinine-harness-claude"
cp -r "$CLAUDE_SRC/." "marketplace/claude/arpinine-harness-claude/"

CLAUDE_VERSION="$(python3 -c "import json; print(json.load(open('marketplace/claude/arpinine-harness-claude/.claude-plugin/plugin.json'))['version'])")"
python3 - "$PLUGIN_NAME" "$MARKETPLACE" "$CLAUDE_VERSION" <<'PY'
import json, sys
plugin, marketplace, version = sys.argv[1:4]
manifest = {
    "name": marketplace,
    "owner": {"name": "Arpinine"},
    "metadata": {
        "description": "Arpinine Harness Claude Code marketplace (install directly from GitHub)",
        "version": version,
    },
    "plugins": [{
        "name": plugin,
        "description": "Governed product-engineering workflow: ADRs, drift detection, evaluation, compounding rule learning",
        "version": version,
        "source": "./marketplace/claude/arpinine-harness-claude",
    }],
}
open(".claude-plugin/marketplace.json", "w").write(json.dumps(manifest, indent=2) + "\n")
PY

# ---- Codex ----
# Hermetic: codex assemble copies into $(CODEX_SYSTEM_PLUGIN_DIR) = $CODEX_PLUGIN_HOME/plugins/...
# Redirect that to a throwaway dir so packaging never mutates the maintainer's live
# ~/.agents install and works in sandboxed/CI environments.
CODEX_TMP_HOME="$(mktemp -d)"
trap 'rm -rf "$CODEX_TMP_HOME"' EXIT
make assemble IMPLEMENTATION=codex CODEX_PLUGIN_HOME="$CODEX_TMP_HOME" >/dev/null
CODEX_SRC="dist/codex/plugins/arpinine-harness"
test -d "$CODEX_SRC" || { echo "Missing assembled Codex tree: $CODEX_SRC" >&2; exit 1; }
rm -rf "marketplace/codex"
mkdir -p "marketplace/codex/arpinine-harness"
cp -r "$CODEX_SRC/." "marketplace/codex/arpinine-harness/"
# The codex impl ships a marketplace template that cp pulls into the plugin payload.
# It is not a plugin file and carries the unresolved __CODEX_PLUGIN_INSTALL_PATH__
# placeholder; the bundle's authoritative manifest is .agents/plugins/marketplace.json.
rm -f "marketplace/codex/arpinine-harness/marketplace.json"
assert_portable "marketplace/codex/arpinine-harness"

# GitHub-root `codex plugin marketplace add owner/repo` resolves the wrong manifest
# in this multi-host repo, so publish a committed Codex-only marketplace root that
# the installer can sparse-checkout and stage locally.
rm -rf "marketplace/codex-root"
mkdir -p "marketplace/codex-root/plugins/arpinine-harness" "marketplace/codex-root/.agents/plugins"
cp -r "$CODEX_SRC/." "marketplace/codex-root/plugins/arpinine-harness/"
rm -f "marketplace/codex-root/plugins/arpinine-harness/marketplace.json"
assert_portable "marketplace/codex-root/plugins/arpinine-harness"
python3 - "$PLUGIN_NAME" "$MARKETPLACE" <<'PY'
import json, sys
plugin, marketplace = sys.argv[1:3]
manifest = {
    "name": marketplace,
    "interface": {"displayName": "Arpinine Harness"},
    "plugins": [{
        "name": plugin,
        "source": {"source": "local", "path": "./plugins/arpinine-harness"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }],
}
open("marketplace/codex-root/.agents/plugins/marketplace.json", "w").write(json.dumps(manifest, indent=2) + "\n")
PY

echo "Committed marketplace refreshed:"
echo "  Claude: .claude-plugin/marketplace.json -> ./marketplace/claude/arpinine-harness-claude"
echo "  Codex : marketplace/codex-root/.agents/plugins/marketplace.json -> ./plugins/arpinine-harness"
echo "Commit the marketplace/ tree and both manifests. Copilot is zip-only (use 'make release IMPLEMENTATION=copilot')."
