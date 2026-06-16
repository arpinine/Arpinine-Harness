#!/usr/bin/env bash
# Consumer-side installer for the Copilot release bundle. No build tools required.
#
# GitHub Copilot CLI runs command hooks from the repository-root working directory
# and exposes no plugin-root environment variable, so hook commands must be absolute
# paths to the installed plugin. Copilot installs marketplace plugins under
# ~/.copilot/installed-plugins/<marketplace>/<plugin>. This script bakes that path
# into the bundled hooks.json (resolving the __COPILOT_PLUGIN_INSTALL_PATH__
# placeholder), then registers and installs the plugin.
#
# Run from the extracted bundle directory:  ./install.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_NAME="arpinine-harness"
MARKETPLACE="arpinine-harness-local"
COPILOT_HOME_EFFECTIVE="${COPILOT_HOME:-${COPILOT_PLUGIN_HOME:-$HOME/.copilot}}"
INSTALL_DIR="$COPILOT_HOME_EFFECTIVE/installed-plugins/$MARKETPLACE/$PLUGIN_NAME"

HOOKS="$HERE/plugins/$PLUGIN_NAME/hooks/hooks.json"
test -f "$HOOKS" || { echo "Bundle layout unexpected: missing $HOOKS" >&2; exit 1; }

echo "Resolving Copilot hook paths to $INSTALL_DIR ..."
sed -i.bak "s#__COPILOT_PLUGIN_INSTALL_PATH__#$INSTALL_DIR#g" "$HOOKS"
rm -f "$HOOKS.bak"

if grep -q "__COPILOT_PLUGIN_INSTALL_PATH__" "$HOOKS"; then
  echo "Failed to resolve placeholder in $HOOKS" >&2; exit 1
fi

command -v copilot >/dev/null || { echo "copilot CLI not found on PATH" >&2; exit 1; }
export COPILOT_HOME="$COPILOT_HOME_EFFECTIVE"

echo "Refreshing existing Copilot install state ..."
copilot plugin uninstall "$PLUGIN_NAME@$MARKETPLACE" 2>/dev/null || true
copilot plugin marketplace remove "$MARKETPLACE" --force 2>/dev/null || true

echo "Registering marketplace from $HERE ..."
copilot plugin marketplace add "$HERE"
echo "Installing $PLUGIN_NAME@$MARKETPLACE ..."
copilot plugin install "$PLUGIN_NAME@$MARKETPLACE"
echo "Done. Copilot governance hooks resolve to $INSTALL_DIR."
