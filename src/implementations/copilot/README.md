# Copilot Implementation Plan

This directory owns the GitHub Copilot CLI-specific implementation layer for Arpinine Harness.

The implementation contract is the same abstraction used by the other hosts:
- `assemble`
- `build`
- `delivery`
- `register`
- `validate-structure`

## Current Status

Implemented now:
- root `plugin.json` manifest for GitHub Copilot CLI
- source marketplace template at `src/implementations/copilot/marketplace.json`
- Copilot-native hook wiring at `hooks/hooks.json`
- Copilot skill wrappers for the shared Arpinine Harness commands
- Copilot specialist skill wrappers for the shared agent roles
- hook adapter scripts that normalize Copilot hook payloads before invoking the shared governance checks
- absolute hook-command path resolution: `hooks/hooks.json` ships a `__COPILOT_PLUGIN_INSTALL_PATH__` placeholder that `make assemble` rewrites to the absolute assembled-plugin directory

## Hook path resolution

Copilot command hooks run with the working directory set to the **user's repository root**, and Copilot exposes **no plugin-root environment variable** (unlike Claude's `${CLAUDE_PLUGIN_ROOT}`). A bare relative command such as `./scripts/check.sh` therefore resolves against the user's repo, where the plugin scripts do not exist — so the governance hooks silently never run.

To avoid that, every hook command is stored as `__COPILOT_PLUGIN_INSTALL_PATH__/scripts/<script>` and rewritten at assemble time to the **durable installed-plugin directory** — not the repo-local `dist/` tree. Copilot installs marketplace plugins under `~/.copilot/installed-plugins/<marketplace>/<plugin>` (here `~/.copilot/installed-plugins/arpinine-harness-local/arpinine-harness`) and loads plugin-contributed hooks from that location. Baking that path means the installed plugin keeps working after `make clean`, after the repo moves, and independently of the build tree. This mirrors the Codex `__CODEX_PLUGIN_INSTALL_PATH__` → system-dir approach.

`make validate-structure IMPLEMENTATION=copilot` fails the build if any hook command is non-absolute, points outside the installed-plugin dir, references a script not shipped as an executable in the assembled artifact, or still contains the unresolved placeholder. (Script existence is asserted against the shipped artifact, since the install dir is only populated after `copilot plugin install`.)

Notes:
- `${COPILOT_PLUGIN_DATA}` is a writable per-plugin *data* directory, not the code/scripts directory, so it cannot be used to reach bundled scripts. Copilot exposes no env var pointing at the plugin's own install dir, which is why the absolute install path is baked at assemble time.
- The baked path includes `$HOME`, resolved at assemble time. Assemble on the same machine/user that installs. Override the base with `make ... COPILOT_PLUGIN_HOME=/custom/.copilot` if Copilot's home differs.

## Goal

Add a real Copilot implementation without changing the shared Arpinine Harness core contract and without regressing Claude or Codex.

Copilot is expected to participate in the same multi-team operating model as the other hosts:

- shared governed artifacts under `.specify/`
- shared task leases under `.specify/coordination/`
- shared style standards under `tools/style/`
- no Copilot-specific fork of workflow semantics or governance rules

## Guardrails

- do not move Copilot metadata into `src/arpinine-harness-core/`
- keep shared prompts and workflows identical unless Copilot requires a concrete host adaptation
- host-specific differences belong here: manifest format, marketplace metadata, hook payload adapters, and install flow
