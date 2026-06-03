#!/usr/bin/env bash
# Package a GitHub-distributable plugin bundle for one implementation.
#
# This is SEPARATE from `make assemble` / `make build` / `make install` and does
# not change their behavior. It consumes the assembled plugin tree and restages it
# as a self-contained, marketplace-addable bundle whose marketplace source path is
# RELATIVE to the extracted directory, so a consumer can install without building.
#
# Usage: tools/release/package_release.sh <claude|codex|copilot>
#
# Output: dist/<impl>/release/arpinine-harness-<impl>-v<version>.zip
set -euo pipefail

IMPL="${1:-}"
case "$IMPL" in
  claude|codex|copilot) ;;
  *) echo "Usage: $0 <claude|codex|copilot>" >&2; exit 2 ;;
esac

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PLUGIN_NAME="arpinine-harness"
MARKETPLACE="arpinine-harness-local"

# Assemble first (reuses the existing, unchanged make target).
# For codex, redirect the system-dir copy to a throwaway home so packaging never
# mutates the maintainer's live ~/.agents install and works in sandboxed/CI runs.
if [ "$IMPL" = "codex" ]; then
  CODEX_TMP_HOME="$(mktemp -d)"
  trap 'rm -rf "$CODEX_TMP_HOME"' EXIT
  make assemble IMPLEMENTATION=codex CODEX_PLUGIN_HOME="$CODEX_TMP_HOME" >/dev/null
else
  make assemble IMPLEMENTATION="$IMPL" >/dev/null
fi

case "$IMPL" in
  claude)
    PLUGIN_DIRNAME="arpinine-harness-claude"
    MANIFEST_REL=".claude-plugin/marketplace.json"
    ;;
  codex)
    PLUGIN_DIRNAME="$PLUGIN_NAME"
    MANIFEST_REL=".agents/plugins/marketplace.json"
    ;;
  copilot)
    PLUGIN_DIRNAME="$PLUGIN_NAME"
    MANIFEST_REL=".github/plugin/marketplace.json"
    ;;
esac

SRC_PLUGIN="dist/$IMPL/plugins/$PLUGIN_DIRNAME"
test -d "$SRC_PLUGIN" || { echo "Assembled plugin not found: $SRC_PLUGIN" >&2; exit 1; }

VERSION="$(python3 -c "import json,glob,sys;
mp=[p for p in ['$SRC_PLUGIN/.claude-plugin/plugin.json','$SRC_PLUGIN/.codex-plugin/plugin.json','$SRC_PLUGIN/plugin.json'] if __import__('os').path.isfile(p)];
print(json.load(open(mp[0]))['version'])")"

BUNDLE_NAME="$PLUGIN_NAME-$IMPL-v$VERSION"
RELEASE_DIR="dist/$IMPL/release"
STAGE="$RELEASE_DIR/$BUNDLE_NAME"
ZIP="$RELEASE_DIR/$BUNDLE_NAME.zip"

rm -rf "$STAGE" "$ZIP"
mkdir -p "$STAGE/plugins/$PLUGIN_DIRNAME" "$STAGE/$(dirname "$MANIFEST_REL")"

# Copy the assembled plugin tree into the bundle.
cp -r "$SRC_PLUGIN/." "$STAGE/plugins/$PLUGIN_DIRNAME/"

# The codex impl ships a marketplace template that cp pulls into the plugin payload.
# It is not a plugin file and carries the unresolved __CODEX_PLUGIN_INSTALL_PATH__
# placeholder; the bundle's authoritative manifest is written below. Strip the stray.
if [ "$IMPL" = "codex" ]; then
  rm -f "$STAGE/plugins/$PLUGIN_DIRNAME/marketplace.json"
fi

# Write a bundle-relative marketplace manifest (source points inside the bundle).
RELSOURCE="./plugins/$PLUGIN_DIRNAME"
python3 - "$STAGE/$MANIFEST_REL" "$PLUGIN_NAME" "$MARKETPLACE" "$RELSOURCE" "$VERSION" "$IMPL" <<'PY'
import json, sys
out, plugin, marketplace, source, version, impl = sys.argv[1:7]
manifest = {
    "name": marketplace,
    "owner": {"name": "Arpinine"},
    "metadata": {
        "description": f"Arpinine Harness {impl} plugin bundle (GitHub release)",
        "version": version,
    },
    "plugins": [
        {
            "name": plugin,
            "description": "Governed product-engineering workflow: ADRs, drift detection, evaluation, compounding rule learning",
            "version": version,
            "source": source,
        }
    ],
}
open(out, "w").write(json.dumps(manifest, indent=2) + "\n")
PY

# Copilot bakes an absolute install path at assemble time, which is machine-specific
# and not portable in a zip. Restore the relocatable placeholder in the bundle and
# ship a one-command installer that resolves it on the consumer's machine.
if [ "$IMPL" = "copilot" ]; then
  cp "src/implementations/copilot/hooks/hooks.json" "$STAGE/plugins/$PLUGIN_DIRNAME/hooks/hooks.json"
  cp "tools/release/copilot-bundle-install.sh" "$STAGE/install.sh"
  chmod +x "$STAGE/install.sh"
fi

( cd "$RELEASE_DIR" && zip -r "$BUNDLE_NAME.zip" "$BUNDLE_NAME/" \
    -x "*/.DS_Store" -x "*/__pycache__/*" -x "*.pyc" >/dev/null )
rm -rf "$STAGE"

echo "Release bundle: $ZIP ($(du -h "$ZIP" | cut -f1))"
echo "Upload this asset to a GitHub Release. Consumer procedure: see README 'Install from a GitHub Release'."
