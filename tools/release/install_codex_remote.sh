#!/usr/bin/env bash
set -euo pipefail

PLUGIN_NAME="arpinine-harness"
MARKETPLACE="arpinine-harness-local"
REMOTE_REPO="${REMOTE_REPO:-arpinine/Arpinine-Harness}"
REMOTE_REF="${REMOTE_REF:-}"
GIT_REMOTE_URL="${GIT_REMOTE_URL:-https://github.com/${REMOTE_REPO}.git}"
INSTALL_BASE="${INSTALL_BASE:-$HOME/.codex/marketplaces}"
INSTALL_ROOT="${INSTALL_ROOT:-$INSTALL_BASE/${MARKETPLACE}-codex}"
STAGING_ROOT="${INSTALL_ROOT}.staging.$$"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd git
require_cmd codex

mkdir -p "$INSTALL_BASE"
rm -rf "$STAGING_ROOT"

echo "Cloning Codex marketplace payload from $GIT_REMOTE_URL ..."
git clone --depth 1 --filter=blob:none --sparse "$GIT_REMOTE_URL" "$STAGING_ROOT" >/dev/null
git -C "$STAGING_ROOT" sparse-checkout set marketplace/codex-root
git -C "$STAGING_ROOT" checkout --force >/dev/null

if [ -n "$REMOTE_REF" ]; then
  echo "Checking out $REMOTE_REF ..."
  git -C "$STAGING_ROOT" fetch --depth 1 origin "$REMOTE_REF" >/dev/null
  git -C "$STAGING_ROOT" checkout --detach FETCH_HEAD >/dev/null
  git -C "$STAGING_ROOT" checkout --force >/dev/null
fi

MARKETPLACE_ROOT="$STAGING_ROOT/marketplace/codex-root"

test -f "$MARKETPLACE_ROOT/.agents/plugins/marketplace.json" || {
  echo "Missing Codex marketplace manifest in cloned repo root" >&2
  exit 1
}
test -f "$MARKETPLACE_ROOT/plugins/$PLUGIN_NAME/.codex-plugin/plugin.json" || {
  echo "Missing Codex plugin payload under marketplace/codex-root/plugins/$PLUGIN_NAME" >&2
  exit 1
}

# Codex resolves local marketplace entries relative to a durable root path,
# so stage the sparse checkout into a stable user-local directory.
rm -rf "$INSTALL_ROOT"
mv "$MARKETPLACE_ROOT" "$INSTALL_ROOT"
rm -rf "$STAGING_ROOT"

echo "Removing any previous Codex install for $PLUGIN_NAME ..."
codex plugin remove "$PLUGIN_NAME" 2>/dev/null || true
codex plugin marketplace remove "$MARKETPLACE" 2>/dev/null || true

echo "Adding staged Codex marketplace root: $INSTALL_ROOT"
codex plugin marketplace add "$INSTALL_ROOT"

echo "Installing $PLUGIN_NAME@$MARKETPLACE ..."
codex plugin add "$PLUGIN_NAME@$MARKETPLACE"

echo "Installed. Fully restart Codex to load the plugin."
echo "Staged marketplace root: $INSTALL_ROOT"
