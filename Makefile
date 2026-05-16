PLUGIN_NAME  := arpinine-harness
IMPLEMENTATION ?= claude
VERSION      := $(shell python3 -c 'import json; print(json.load(open("src/implementations/$(IMPLEMENTATION)/.$(IMPLEMENTATION)-plugin/plugin.json"))["version"])')
CORE_DIR     := src/arpinine-harness-core
IMPLEMENTATION_DIR := src/implementations/$(IMPLEMENTATION)
DIST_DIR     := dist
PLUGIN_DIST_DIR := $(DIST_DIR)/plugins
BUILD_NAME   := $(PLUGIN_NAME)-$(IMPLEMENTATION)-v$(VERSION)
BUILD_DIR    := $(DIST_DIR)/$(BUILD_NAME)
ZIP_NAME     := $(BUILD_NAME).zip
ZIP_PATH     := $(DIST_DIR)/$(ZIP_NAME)
MARKETPLACE  := arpinine-harness-local
CLAUDE_PLUGIN_DIR := $(PLUGIN_DIST_DIR)/arpinine-harness-claude
CODEX_PLUGIN_DIR := $(PLUGIN_DIST_DIR)/$(PLUGIN_NAME)
CLAUDE_MARKETPLACE_FILE := $(DIST_DIR)/.claude-plugin/marketplace.json
CODEX_MARKETPLACE_TEMPLATE := $(IMPLEMENTATION_DIR)/marketplace.json
CODEX_MARKETPLACE_FILE := $(DIST_DIR)/.agents/plugins/marketplace.json

.DEFAULT_GOAL := build

STYLE_DIR := tools/style

.PHONY: assemble build clean delivery register validate-structure install uninstall validate help style-paths

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
	chmod +x $(BUILD_DIR)/scripts/*.sh 2>/dev/null || true; \
	find $(BUILD_DIR) -type d -name tests -prune -exec rm -rf {} +; \
	find $(BUILD_DIR) -type d -name "__pycache__" -prune -exec rm -rf {} +; \
	find $(BUILD_DIR) -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete; \
	find $(BUILD_DIR) -depth -type d -empty -delete; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		mkdir -p $(PLUGIN_DIST_DIR) $(DIST_DIR)/.claude-plugin; \
		rm -rf $(CLAUDE_PLUGIN_DIR); \
		cp -r $(BUILD_DIR) $(CLAUDE_PLUGIN_DIR); \
		cat .claude-plugin/marketplace.json | sed 's#\./dist/plugins/#./plugins/#g' > $(CLAUDE_MARKETPLACE_FILE); \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		mkdir -p $(PLUGIN_DIST_DIR) $(DIST_DIR)/.agents/plugins; \
		rm -rf $(CODEX_PLUGIN_DIR); \
		cp -r $(BUILD_DIR) $(CODEX_PLUGIN_DIR); \
		cat $(CODEX_MARKETPLACE_TEMPLATE) | sed 's#\./dist/plugins/#./plugins/#g' > $(CODEX_MARKETPLACE_FILE); \
	fi; \
	trap - EXIT

## Build deployable plugin zip
build: assemble
	@echo "Packaging $(BUILD_NAME)..."
	@cd $(DIST_DIR) && zip -r $(ZIP_NAME) $(BUILD_NAME)/ -x "*/.DS_Store" -x "*/__pycache__/*" -x "*.pyc" > /dev/null
	@rm -rf $(BUILD_DIR)
	@echo "✅ $(ZIP_PATH) ($$(du -h $(ZIP_PATH) | cut -f1))"

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
		claude plugin marketplace add ./dist; \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		codex plugin marketplace add ./dist; \
		echo "Codex marketplace registered from $(CODEX_MARKETPLACE_FILE)."; \
		echo "Enable $(PLUGIN_NAME) from the Codex marketplace UI if your Codex client requires a separate confirmation step."; \
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
		grep -q '"hooks"[[:space:]]*:[[:space:]]*"./hooks/hooks.json"' $(BUILD_DIR)/.claude-plugin/plugin.json || (echo "Claude plugin manifest must declare hooks at ./hooks/hooks.json" && exit 1); \
		test -f $(BUILD_DIR)/hooks/hooks.json || (echo "Missing hooks/hooks.json" && exit 1); \
		test -d $(BUILD_DIR)/commands || (echo "Missing commands directory" && exit 1); \
		test -d $(BUILD_DIR)/scripts || (echo "Missing scripts directory" && exit 1); \
		test -d $(BUILD_DIR)/skills || (echo "Missing skills directory" && exit 1); \
		echo "Claude plugin structure looks valid."; \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		test -f $(BUILD_DIR)/.codex-plugin/plugin.json || (echo "Missing .codex-plugin/plugin.json" && exit 1); \
		grep -q '"hooks"[[:space:]]*:[[:space:]]*"./hooks/hooks.json"' $(BUILD_DIR)/.codex-plugin/plugin.json || (echo "Codex plugin manifest must declare hooks at ./hooks/hooks.json" && exit 1); \
		test -f $(BUILD_DIR)/hooks/hooks.json || (echo "Missing hooks/hooks.json" && exit 1); \
		test -d $(BUILD_DIR)/skills || (echo "Missing skills directory" && exit 1); \
		for skill in $$(ls $(CORE_DIR)/commands/ | sed 's/\.md$$//'); do \
			test -f "$(BUILD_DIR)/skills/$$skill/SKILL.md" || (echo "Missing Codex workflow wrapper: $$skill" && exit 1); \
		done; \
		echo "Codex plugin structure looks valid."; \
	else \
		echo "validate-structure target is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Build + install plugin into Claude Code (Claude-only convenience target)
install:
	@set -e; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		$(MAKE) register IMPLEMENTATION=claude; \
		claude plugin install $(PLUGIN_NAME)@$(MARKETPLACE); \
	else \
		echo "install is Claude-only. Use 'make register IMPLEMENTATION=$(IMPLEMENTATION)' for the common cross-implementation flow."; \
		exit 1; \
	fi

## Uninstall plugin and remove marketplace from Claude Code (Claude-only convenience target)
uninstall:
	@set -e; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		claude plugin uninstall $(PLUGIN_NAME); \
		claude plugin marketplace remove $(MARKETPLACE); \
	else \
		echo "uninstall is Claude-only. No common cross-implementation uninstall abstraction is available."; \
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
	@echo "Targets: build (default), clean, delivery, register, validate-structure, install, uninstall, validate"
	@echo "Variables: IMPLEMENTATION=claude (default)"

## Show canonical style config locations
style-paths:
	@echo "Python: $(STYLE_DIR)/python/pyproject.toml"
	@echo "Frontend: $(STYLE_DIR)/frontend/eslint.config.cjs"
	@echo "Frontend: $(STYLE_DIR)/frontend/.prettierrc.json"
	@echo "Java: $(STYLE_DIR)/java/checkstyle.xml"
	@echo "Rust: $(STYLE_DIR)/rust/rustfmt.toml"
	@echo "Shared: $(STYLE_DIR)/shared/.editorconfig"
