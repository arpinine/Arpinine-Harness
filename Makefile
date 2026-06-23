PLUGIN_NAME  := arpinine-harness
IMPLEMENTATION ?= claude
PLUGIN_MANIFEST_REL := $(if $(filter $(IMPLEMENTATION),claude),.claude-plugin/plugin.json,$(if $(filter $(IMPLEMENTATION),codex),.codex-plugin/plugin.json,$(if $(filter $(IMPLEMENTATION),copilot),plugin.json,.plugin/plugin.json)))
VERSION      := $(shell python3 -c 'import json; print(json.load(open("src/implementations/$(IMPLEMENTATION)/$(PLUGIN_MANIFEST_REL)"))["version"])')
CORE_DIR     := src/arpinine-harness-core
IMPLEMENTATION_DIR := src/implementations/$(IMPLEMENTATION)
DIST_DIR     := dist/$(IMPLEMENTATION)
PLUGIN_DIST_DIR := $(DIST_DIR)/plugins
BUILD_NAME   := $(PLUGIN_NAME)-$(IMPLEMENTATION)-v$(VERSION)
BUILD_DIR    := $(DIST_DIR)/$(BUILD_NAME)
ZIP_NAME     := $(BUILD_NAME).zip
ZIP_PATH     := $(DIST_DIR)/$(ZIP_NAME)
MARKETPLACE  := arpinine-harness-local
CLAUDE_PLUGIN_DIR := $(PLUGIN_DIST_DIR)/arpinine-harness-claude
CLAUDE_MARKETPLACE_FILE := $(DIST_DIR)/.claude-plugin/marketplace.json
CODEX_PLUGIN_HOME ?= $(HOME)/.agents
CODEX_SYSTEM_PLUGIN_DIR := $(CODEX_PLUGIN_HOME)/plugins/$(PLUGIN_NAME)
CODEX_CACHE_DIR := $(HOME)/.codex/plugins/cache/$(MARKETPLACE)/$(PLUGIN_NAME)
CODEX_CACHE_VERSION_DIR := $(CODEX_CACHE_DIR)/$(VERSION)
CODEX_MARKETPLACE_TEMPLATE := $(IMPLEMENTATION_DIR)/marketplace.json
CODEX_MARKETPLACE_FILE := $(DIST_DIR)/.agents/plugins/marketplace.json
COPILOT_MARKETPLACE_TEMPLATE := $(IMPLEMENTATION_DIR)/marketplace.json
COPILOT_MARKETPLACE_FILE := $(DIST_DIR)/.github/plugin/marketplace.json
COPILOT_PLUGIN_HOME ?= $(HOME)/.copilot
COPILOT_INSTALLED_PLUGIN_DIR := $(COPILOT_PLUGIN_HOME)/installed-plugins/$(MARKETPLACE)/$(PLUGIN_NAME)

.DEFAULT_GOAL := build

STYLE_DIR := tools/style

.PHONY: assemble build clean delivery register validate-structure install uninstall validate help style-paths release release-all release-publish publish-marketplace install-remote

assemble: clean
	@set -e; \
	trap 'rm -rf "$(BUILD_DIR)"' EXIT INT TERM; \
	test -d $(CORE_DIR) || (echo "Missing shared core directory: $(CORE_DIR)" && exit 1); \
	test -d $(IMPLEMENTATION_DIR) || (echo "Missing implementation directory: $(IMPLEMENTATION_DIR)" && exit 1); \
	echo "Assembling $(PLUGIN_NAME) v$(VERSION) for $(IMPLEMENTATION)..."; \
	find $(CORE_DIR) $(IMPLEMENTATION_DIR) -type d -name "__pycache__" -prune -exec rm -rf {} +; \
	find $(CORE_DIR) $(IMPLEMENTATION_DIR) -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete; \
	mkdir -p $(BUILD_DIR); \
	cp -r $(CORE_DIR)/. $(BUILD_DIR)/; \
	cp -r $(IMPLEMENTATION_DIR)/. $(BUILD_DIR)/; \
	python3 $(BUILD_DIR)/scripts/scaffold_compression_setup.py --target-dir $(BUILD_DIR) > /dev/null; \
	chmod +x $(BUILD_DIR)/scripts/*.sh 2>/dev/null || true; \
	find $(BUILD_DIR) -type d -name tests -prune -exec rm -rf {} +; \
	find $(BUILD_DIR) -type d -name "__pycache__" -prune -exec rm -rf {} +; \
	find $(BUILD_DIR) -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete; \
	find $(BUILD_DIR) -depth -type d -empty -delete; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		mkdir -p $(PLUGIN_DIST_DIR) $(DIST_DIR)/.claude-plugin; \
		rm -rf $(CLAUDE_PLUGIN_DIR); \
		cp -r $(BUILD_DIR) $(CLAUDE_PLUGIN_DIR); \
		python3 -c "import json; m=json.load(open('.claude-plugin/marketplace.json')); m['plugins'][0]['source']='./plugins/arpinine-harness-claude'; open('$(CLAUDE_MARKETPLACE_FILE)','w').write(json.dumps(m, indent=2)+chr(10))"; \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		echo "Rewriting CLAUDE_PLUGIN_ROOT references for Codex plugin layout..."; \
		find $(BUILD_DIR) -type f \( -name "*.md" -o -name "*.json" -o -name "*.sh" -o -name "*.py" \) -print0 \
			| xargs -0 sed -i.bak -e 's#"\$${CLAUDE_PLUGIN_ROOT}/scripts/#"scripts/#g' \
				-e 's#`\$${CLAUDE_PLUGIN_ROOT}/scripts/#`scripts/#g' \
				-e 's#\$${CLAUDE_PLUGIN_ROOT}/scripts/#scripts/#g'; \
		find $(BUILD_DIR) -type f -name "*.bak" -delete; \
		echo "Rewriting facade skill-invocation names for Codex (strip arpinine-harness: namespace)..."; \
		find $(BUILD_DIR)/commands -type f -name "*.md" -print0 \
			| xargs -0 sed -i.bak -e 's#`arpinine-harness:at-#`at-#g'; \
		find $(BUILD_DIR) -type f -name "*.bak" -delete; \
		mkdir -p $(PLUGIN_DIST_DIR) $(DIST_DIR)/.agents/plugins $(CODEX_PLUGIN_HOME)/plugins; \
		rm -rf $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME) $(CODEX_SYSTEM_PLUGIN_DIR); \
		cp -r $(BUILD_DIR) $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME); \
		cp -r $(BUILD_DIR) $(CODEX_SYSTEM_PLUGIN_DIR); \
		sed "s#__CODEX_PLUGIN_INSTALL_PATH__#$(CODEX_SYSTEM_PLUGIN_DIR)#g" $(CODEX_MARKETPLACE_TEMPLATE) > $(CODEX_MARKETPLACE_FILE); \
		echo "Codex plugin installed to $(CODEX_SYSTEM_PLUGIN_DIR) (marketplace points here absolutely)"; \
	elif [ "$(IMPLEMENTATION)" = "copilot" ]; then \
		echo "Rewriting CLAUDE_PLUGIN_ROOT references for Copilot plugin layout..."; \
		find $(BUILD_DIR) -type f \( -name "*.md" -o -name "*.json" -o -name "*.sh" -o -name "*.py" \) -print0 \
			| xargs -0 sed -i.bak -e 's#"\$${CLAUDE_PLUGIN_ROOT}/scripts/#"scripts/#g' \
				-e 's#`\$${CLAUDE_PLUGIN_ROOT}/scripts/#`scripts/#g' \
				-e 's#\$${CLAUDE_PLUGIN_ROOT}/scripts/#scripts/#g'; \
		find $(BUILD_DIR) -type f -name "*.bak" -delete; \
		echo "Rewriting facade skill-invocation names for Copilot (strip arpinine-harness: namespace)..."; \
		find $(BUILD_DIR)/commands -type f -name "*.md" -print0 \
			| xargs -0 sed -i.bak -e 's#`arpinine-harness:at-#`at-#g'; \
		find $(BUILD_DIR) -type f -name "*.bak" -delete; \
		echo "Resolving __COPILOT_PLUGIN_INSTALL_PATH__ in Copilot hooks to the durable installed-plugin dir $(COPILOT_INSTALLED_PLUGIN_DIR) (Copilot copies marketplace plugins there on install; no plugin-root env var, hooks run from repo-root cwd)..."; \
		sed -i.bak "s#__COPILOT_PLUGIN_INSTALL_PATH__#$(COPILOT_INSTALLED_PLUGIN_DIR)#g" $(BUILD_DIR)/hooks/hooks.json; \
		rm -f $(BUILD_DIR)/hooks/hooks.json.bak; \
		mkdir -p $(PLUGIN_DIST_DIR) $(DIST_DIR)/.github/plugin; \
		rm -rf $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME); \
		cp -r $(BUILD_DIR) $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME); \
		cp $(COPILOT_MARKETPLACE_TEMPLATE) $(COPILOT_MARKETPLACE_FILE); \
		echo "Copilot plugin assembled at $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME)"; \
	fi; \
	trap - EXIT

## Build deployable plugin zip
build: assemble
	@echo "Packaging $(BUILD_NAME)..."
	@cd $(DIST_DIR) && zip -r $(ZIP_NAME) $(BUILD_NAME)/ -x "*/.DS_Store" -x "*/__pycache__/*" -x "*.pyc" > /dev/null
	@rm -rf $(BUILD_DIR)
	@echo "✅ $(ZIP_PATH) ($$(du -h $(ZIP_PATH) | cut -f1))"

## Package a GitHub-distributable, marketplace-addable bundle (separate from assemble/build)
release:
	@tools/release/package_release.sh $(IMPLEMENTATION)

## Package bundles for ALL implementations (no upload)
release-all:
	@for impl in claude codex copilot; do tools/release/package_release.sh $$impl; done

## Build all bundles and publish them to a GitHub Release (requires authenticated gh CLI)
## Override the tag with TAG=vX.Y.Z; set DRAFT=1 for a draft release.
release-publish:
	@TAG="$(TAG)" DRAFT="$(DRAFT)" tools/release/publish_release.sh $(TAG)

## Refresh committed marketplace artifacts for no-build GitHub install.
## Claude installs directly from repo root; Codex stages the committed Codex tree locally.
publish-marketplace:
	@tools/release/publish_marketplace.sh

## No-build GitHub install.
## Claude installs from the repo-root marketplace; Codex stages a Codex-only local root first.
## Vars: REMOTE_REPO (default arpinine/Arpinine-Harness), REMOTE_REF (optional branch/tag/sha).
REMOTE_REPO ?= arpinine/Arpinine-Harness
REMOTE_SOURCE := $(REMOTE_REPO)$(if $(REMOTE_REF),@$(REMOTE_REF),)
install-remote:
	@if [ "$(IMPLEMENTATION)" = "claude" ]; then HOST=claude; ADD=install; RM=uninstall; \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		REMOTE_REPO="$(REMOTE_REPO)" REMOTE_REF="$(REMOTE_REF)" bash tools/release/install_codex_remote.sh; \
		exit $$?; \
	else echo "install-remote supports IMPLEMENTATION=claude|codex only (Copilot is zip-only)"; exit 1; fi; \
	command -v $$HOST >/dev/null || { echo "$$HOST CLI not found on PATH"; exit 1; }; \
	echo "Removing any existing local install..."; \
	$$HOST plugin $$RM $(PLUGIN_NAME) 2>/dev/null || true; \
	$$HOST plugin marketplace remove $(MARKETPLACE) 2>/dev/null || true; \
	echo "Adding remote marketplace: $(REMOTE_SOURCE)"; \
	$$HOST plugin marketplace add "$(REMOTE_SOURCE)"; \
	echo "Installing $(PLUGIN_NAME)@$(MARKETPLACE) from remote..."; \
	$$HOST plugin $$ADD $(PLUGIN_NAME)@$(MARKETPLACE); \
	$$HOST plugin list | grep -A4 "$(PLUGIN_NAME)" || true; \
	echo "Done. Restart $$HOST to load commands."

## Remove generated build outputs
clean:
	@rm -rf $(DIST_DIR)

## Regenerate .specify/delivery.md from plan task status
delivery:
	@python3 $(CORE_DIR)/scripts/update_backlog.py

## Register the assembled plugin marketplace entry for the selected implementation
register:
	@set -e; \
	$(MAKE) assemble IMPLEMENTATION=$(IMPLEMENTATION); \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		claude plugin marketplace add ./$(DIST_DIR); \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		codex plugin marketplace add ./$(DIST_DIR); \
		echo "Codex marketplace registered from $(CODEX_MARKETPLACE_FILE)."; \
		echo "Enable $(PLUGIN_NAME) from the Codex marketplace UI if your Codex client requires a separate confirmation step."; \
	elif [ "$(IMPLEMENTATION)" = "copilot" ]; then \
		copilot plugin marketplace add ./$(DIST_DIR); \
		echo "Copilot marketplace registered from $(COPILOT_MARKETPLACE_FILE)."; \
	else \
		echo "register target is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Validate assembled plugin structure for the selected implementation
validate-structure: assemble
	@set -e; \
	trap 'rm -rf "$(BUILD_DIR)"' EXIT INT TERM; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		test -f $(BUILD_DIR)/.claude-plugin/plugin.json || (echo "Missing .claude-plugin/plugin.json" && exit 1); \
		grep -q '"skills"[[:space:]]*:[[:space:]]*"./skills/"' $(BUILD_DIR)/.claude-plugin/plugin.json || (echo "Claude plugin manifest must declare skills at ./skills/" && exit 1); \
		! grep -q '"hooks"' $(BUILD_DIR)/.claude-plugin/plugin.json || (echo "Claude plugin manifest must NOT declare hooks: Claude auto-loads hooks/hooks.json, and a manifest reference causes a duplicate-load failure" && exit 1); \
		test -f $(BUILD_DIR)/hooks/hooks.json || (echo "Missing hooks/hooks.json (auto-loaded by Claude)" && exit 1); \
		test -d $(BUILD_DIR)/context_compression || (echo "Missing scaffolded context_compression package" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/__init__.py || (echo "Missing context_compression/__init__.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/context_compression_provider.py || (echo "Missing context_compression/context_compression_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/noop_provider.py || (echo "Missing context_compression/noop_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/headroom_provider.py || (echo "Missing context_compression/headroom_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/host_wiring.py || (echo "Missing context_compression/host_wiring.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/security.py || (echo "Missing context_compression/security.py" && exit 1); \
		test -f $(BUILD_DIR)/scripts/run_compressed_session.py || (echo "Missing compression launcher scripts/run_compressed_session.py" && exit 1); \
		test -d $(BUILD_DIR)/commands || (echo "Missing commands directory" && exit 1); \
		test -d $(BUILD_DIR)/scripts || (echo "Missing scripts directory" && exit 1); \
		test -d $(BUILD_DIR)/skills || (echo "Missing skills directory" && exit 1); \
		echo "Claude plugin structure looks valid."; \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		test -f $(BUILD_DIR)/.codex-plugin/plugin.json || (echo "Missing .codex-plugin/plugin.json" && exit 1); \
		grep -q '"hooks"[[:space:]]*:[[:space:]]*"./hooks/hooks.json"' $(BUILD_DIR)/.codex-plugin/plugin.json || (echo "Codex plugin manifest must declare hooks at ./hooks/hooks.json" && exit 1); \
		test -f $(BUILD_DIR)/hooks/hooks.json || (echo "Missing hooks/hooks.json" && exit 1); \
		test -d $(BUILD_DIR)/context_compression || (echo "Missing scaffolded context_compression package" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/__init__.py || (echo "Missing context_compression/__init__.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/context_compression_provider.py || (echo "Missing context_compression/context_compression_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/noop_provider.py || (echo "Missing context_compression/noop_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/headroom_provider.py || (echo "Missing context_compression/headroom_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/host_wiring.py || (echo "Missing context_compression/host_wiring.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/security.py || (echo "Missing context_compression/security.py" && exit 1); \
		test -f $(BUILD_DIR)/scripts/run_compressed_session.py || (echo "Missing compression launcher scripts/run_compressed_session.py" && exit 1); \
		for agent in product-owner tech-architect security-reviewer ai-engineer devops data-engineer tdd-guide domain-linguist; do \
			test -f "$(BUILD_DIR)/skills/$$agent/SKILL.md" || (echo "Missing Codex specialist wrapper: $$agent" && exit 1); \
		done; \
		test -d $(BUILD_DIR)/skills || (echo "Missing skills directory" && exit 1); \
		for skill in $$(ls $(CORE_DIR)/commands/ | sed 's/\.md$$//'); do \
			test -f "$(BUILD_DIR)/skills/$$skill/SKILL.md" || (echo "Missing Codex workflow wrapper: $$skill" && exit 1); \
		done; \
		test -d $(CODEX_SYSTEM_PLUGIN_DIR) || (echo "Missing Codex system plugin dir: $(CODEX_SYSTEM_PLUGIN_DIR)" && exit 1); \
		test -f "$(CODEX_SYSTEM_PLUGIN_DIR)/hooks/hooks.json" || (echo "Missing hooks in system plugin dir" && exit 1); \
		test -f $(CODEX_MARKETPLACE_FILE) || (echo "Missing generated Codex marketplace manifest: $(CODEX_MARKETPLACE_FILE)" && exit 1); \
		grep -q "\"path\": \"$(CODEX_SYSTEM_PLUGIN_DIR)\"" $(CODEX_MARKETPLACE_FILE) || (echo "Codex marketplace manifest does not point at $(CODEX_SYSTEM_PLUGIN_DIR). Source.path field must match the durable system install dir, not repo-local dist/." && exit 1); \
		grep -q "__CODEX_PLUGIN_INSTALL_PATH__" $(CODEX_MARKETPLACE_FILE) && (echo "Codex marketplace manifest still contains unresolved __CODEX_PLUGIN_INSTALL_PATH__ placeholder" && exit 1) || true; \
		echo "Codex plugin structure looks valid. Installed at $(CODEX_SYSTEM_PLUGIN_DIR). Marketplace resolves to that path."; \
	elif [ "$(IMPLEMENTATION)" = "copilot" ]; then \
		test -f $(BUILD_DIR)/plugin.json || (echo "Missing plugin.json" && exit 1); \
		grep -q '"skills"[[:space:]]*:[[:space:]]*"./skills/"' $(BUILD_DIR)/plugin.json || (echo "Copilot plugin manifest must declare skills at ./skills/" && exit 1); \
		grep -q '"hooks"[[:space:]]*:[[:space:]]*"./hooks/hooks.json"' $(BUILD_DIR)/plugin.json || (echo "Copilot plugin manifest must declare hooks at ./hooks/hooks.json" && exit 1); \
		test -f $(BUILD_DIR)/hooks/hooks.json || (echo "Missing hooks/hooks.json" && exit 1); \
		test -d $(BUILD_DIR)/context_compression || (echo "Missing scaffolded context_compression package" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/__init__.py || (echo "Missing context_compression/__init__.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/context_compression_provider.py || (echo "Missing context_compression/context_compression_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/noop_provider.py || (echo "Missing context_compression/noop_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/headroom_provider.py || (echo "Missing context_compression/headroom_provider.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/host_wiring.py || (echo "Missing context_compression/host_wiring.py" && exit 1); \
		test -f $(BUILD_DIR)/context_compression/security.py || (echo "Missing context_compression/security.py" && exit 1); \
		test -f $(BUILD_DIR)/scripts/run_compressed_session.py || (echo "Missing compression launcher scripts/run_compressed_session.py" && exit 1); \
		for agent in product-owner tech-architect security-reviewer ai-engineer devops data-engineer tdd-guide domain-linguist; do \
			test -f "$(BUILD_DIR)/skills/$$agent/SKILL.md" || (echo "Missing Copilot specialist wrapper: $$agent" && exit 1); \
		done; \
		test -d $(BUILD_DIR)/skills || (echo "Missing skills directory" && exit 1); \
		for skill in $$(ls $(CORE_DIR)/commands/ | sed 's/\.md$$//'); do \
			test -f "$(BUILD_DIR)/skills/$$skill/SKILL.md" || (echo "Missing Copilot workflow wrapper: $$skill" && exit 1); \
		done; \
		test -f $(COPILOT_MARKETPLACE_FILE) || (echo "Missing generated Copilot marketplace manifest: $(COPILOT_MARKETPLACE_FILE)" && exit 1); \
		grep -q '"source"[[:space:]]*:[[:space:]]*"\./plugins/$(PLUGIN_NAME)"' $(COPILOT_MARKETPLACE_FILE) || (echo "Copilot marketplace manifest must point at ./plugins/$(PLUGIN_NAME)" && exit 1); \
		test -f $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME)/hooks/hooks.json || (echo "Missing assembled Copilot hooks manifest" && exit 1); \
		! grep -q "__COPILOT_PLUGIN_INSTALL_PATH__" $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME)/hooks/hooks.json || (echo "Copilot hooks.json still contains unresolved __COPILOT_PLUGIN_INSTALL_PATH__ placeholder; assemble did not rewrite it" && exit 1); \
		ARTIFACT_DIR="$(abspath $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME))" INSTALL_DIR="$(COPILOT_INSTALLED_PLUGIN_DIR)" python3 -c 'import json,os,sys; \
artifact=os.environ["ARTIFACT_DIR"]; install=os.environ["INSTALL_DIR"]; \
m=json.load(open(os.path.join(artifact,"hooks","hooks.json"))); \
cmds=[h["bash"] for ph in m["hooks"].values() for h in ph if "bash" in h]; \
prefix=install+"/scripts/"; \
bad=[c for c in cmds if not os.path.isabs(c)]; \
offtree=[c for c in cmds if os.path.isabs(c) and not c.startswith(prefix)]; \
shipped=[c for c in cmds if c.startswith(prefix) and not (lambda p: os.path.isfile(p) and os.access(p, os.X_OK))(os.path.join(artifact,"scripts",c[len(prefix):]))]; \
sys.exit("Copilot hook commands must be absolute (Copilot resolves cwd against repo root, exposes no plugin-root env var): "+str(bad)) if bad else None; \
sys.exit("Copilot hook commands must point at the durable installed-plugin dir "+install+": "+str(offtree)) if offtree else None; \
sys.exit("Copilot hook scripts missing/not-executable in the shipped artifact (will be absent after install): "+str(shipped)) if shipped else None; \
print("Copilot hooks: %d command(s) point at %s and ship as executable scripts" % (len(cmds), install))' || exit 1; \
		echo "Copilot plugin structure looks valid. Marketplace resolves via $(COPILOT_MARKETPLACE_FILE). Hooks resolve to the durable installed-plugin dir $(COPILOT_INSTALLED_PLUGIN_DIR)."; \
	else \
		echo "validate-structure target is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Build + install plugin (Claude Code for claude, Codex system dir for codex)
install:
	@set -e; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		$(MAKE) register IMPLEMENTATION=claude; \
		claude plugin install $(PLUGIN_NAME)@$(MARKETPLACE); \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		$(MAKE) register IMPLEMENTATION=codex; \
		rm -rf $(CODEX_CACHE_DIR); \
		mkdir -p $(CODEX_CACHE_VERSION_DIR); \
		cp -r $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME)/. $(CODEX_CACHE_VERSION_DIR)/; \
		echo "Cache hydrated at $(CODEX_CACHE_VERSION_DIR)"; \
	elif [ "$(IMPLEMENTATION)" = "copilot" ]; then \
		$(MAKE) register IMPLEMENTATION=copilot; \
		copilot plugin install $(PLUGIN_NAME)@$(MARKETPLACE); \
	else \
		echo "install is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Remove plugin and deregister marketplace entry (Claude Code for claude, Codex for codex)
uninstall:
	@set -e; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		claude plugin uninstall $(PLUGIN_NAME); \
		claude plugin marketplace remove $(MARKETPLACE); \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		rm -rf $(CODEX_SYSTEM_PLUGIN_DIR); \
		echo "Removed $(CODEX_SYSTEM_PLUGIN_DIR)"; \
		rm -rf $(CODEX_CACHE_DIR); \
		echo "Cleared cache $(CODEX_CACHE_DIR)"; \
		codex plugin marketplace remove $(MARKETPLACE) 2>/dev/null && echo "Marketplace entry removed" || echo "No marketplace entry found (may need manual removal)"; \
	elif [ "$(IMPLEMENTATION)" = "copilot" ]; then \
		copilot plugin uninstall $(PLUGIN_NAME) 2>/dev/null || echo "Plugin was not installed"; \
		copilot plugin marketplace remove $(MARKETPLACE) 2>/dev/null && echo "Marketplace entry removed" || echo "No marketplace entry found"; \
	else \
		echo "uninstall is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Run native host validation when supported (Claude-only)
validate:
	@set -e; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		$(MAKE) assemble IMPLEMENTATION=claude; \
		trap 'rm -rf "$(BUILD_DIR)"' EXIT INT TERM; \
		claude plugin validate $(BUILD_DIR); \
	else \
		echo "Native validate is Claude-only. Use 'make validate-structure IMPLEMENTATION=$(IMPLEMENTATION)' for the common cross-implementation flow."; \
		exit 1; \
	fi

## Show available targets
help:
	@grep -E '^##' Makefile | sed 's/## //'
	@echo ""
	@echo "Targets: build (default), clean, delivery, register, validate-structure, install, uninstall, validate, release, release-all, release-publish"
	@echo "         release         -> one GitHub-distributable bundle (dist/<impl>/release/); separate from build"
	@echo "         release-all     -> bundles for all implementations (no upload)"
	@echo "         release-publish -> build all bundles + upload to a GitHub Release (needs authenticated gh; TAG=vX.Y.Z, DRAFT=1 optional)"
	@echo "         publish-marketplace -> refresh committed marketplace artifacts (Claude direct; Codex staged local root)"
	@echo "         install-remote -> no-build GitHub install (Claude direct; Codex stages a Codex-only local root)"
	@echo "Variables: IMPLEMENTATION=claude|codex|copilot (default: claude)"
	@echo "           CODEX_PLUGIN_HOME=<path> (default: $(HOME)/.agents)"
	@echo "Claude-only: validate (uses claude plugin validate)"

## Show canonical style config locations
style-paths:
	@echo "Python: $(STYLE_DIR)/python/pyproject.toml"
	@echo "Frontend: $(STYLE_DIR)/frontend/eslint.config.cjs"
	@echo "Frontend: $(STYLE_DIR)/frontend/.prettierrc.json"
	@echo "Java: $(STYLE_DIR)/java/checkstyle.xml"
	@echo "Rust: $(STYLE_DIR)/rust/rustfmt.toml"
	@echo "Shared: $(STYLE_DIR)/shared/.editorconfig"
