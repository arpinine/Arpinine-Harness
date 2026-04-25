PLUGIN_NAME  := agent-align
VERSION      := 1.4.0
IMPLEMENTATION ?= claude
CORE_DIR     := src/agent-align-core
IMPLEMENTATION_DIR := src/implementations/$(IMPLEMENTATION)
DIST_DIR     := dist
BUILD_NAME   := $(PLUGIN_NAME)-$(IMPLEMENTATION)-v$(VERSION)
BUILD_DIR    := $(DIST_DIR)/$(BUILD_NAME)
ZIP_NAME     := $(BUILD_NAME).zip
ZIP_PATH     := $(DIST_DIR)/$(ZIP_NAME)
MARKETPLACE  := agent-align-local
CODEX_PLUGIN_DIR := plugins/agent-align-codex
CODEX_MARKETPLACE_FILE := .agents/plugins/marketplace.json

.DEFAULT_GOAL := build

.PHONY: assemble build clean install uninstall validate help

assemble: clean
	@set -e; \
	trap 'rm -rf "$(BUILD_DIR)"' EXIT INT TERM; \
	test -d $(CORE_DIR) || (echo "Missing shared core directory: $(CORE_DIR)" && exit 1); \
	test -d $(IMPLEMENTATION_DIR) || (echo "Missing implementation directory: $(IMPLEMENTATION_DIR)" && exit 1); \
	echo "Assembling $(PLUGIN_NAME) v$(VERSION) for $(IMPLEMENTATION)..."; \
	mkdir -p $(BUILD_DIR); \
	cp -r $(CORE_DIR)/. $(BUILD_DIR)/; \
	cp -r $(IMPLEMENTATION_DIR)/. $(BUILD_DIR)/; \
	chmod +x $(BUILD_DIR)/scripts/*.sh 2>/dev/null || true; \
	find $(BUILD_DIR) -type d -name "__pycache__" -prune -exec rm -rf {} +; \
	find $(BUILD_DIR) -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete; \
	find $(BUILD_DIR) -depth -type d -empty -delete; \
	if [ "$(IMPLEMENTATION)" = "codex" ]; then \
		echo "Warning: Codex currently wires 4/11 workflows: at-init, at-new, at-review, at-plan."; \
		mkdir -p .agents/plugins plugins; \
		rm -rf $(CODEX_PLUGIN_DIR); \
		cp -r $(BUILD_DIR) $(CODEX_PLUGIN_DIR); \
	fi; \
	trap - EXIT

## Build deployable plugin zip
build: assemble
	@echo "Packaging $(BUILD_NAME)..."
	@cd $(DIST_DIR) && zip -r $(ZIP_NAME) $(BUILD_NAME)/ -x "*/.DS_Store" -x "*/__pycache__/*" -x "*.pyc" > /dev/null
	@rm -rf $(BUILD_DIR)
	@echo "✅ $(ZIP_PATH) ($$(du -h $(ZIP_PATH) | cut -f1))"

## Remove dist/
clean:
	@rm -rf $(DIST_DIR) $(CODEX_PLUGIN_DIR)

## Build + install plugin into Claude Code
install:
	@set -e; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		$(MAKE) build IMPLEMENTATION=claude; \
		claude plugin marketplace add ./; \
		claude plugin install $(PLUGIN_NAME)@$(MARKETPLACE); \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		$(MAKE) assemble IMPLEMENTATION=codex; \
		echo "Codex CLI install flow is not yet verified."; \
		echo "Prepared local Codex plugin at $(CODEX_PLUGIN_DIR) and repo marketplace at $(CODEX_MARKETPLACE_FILE)."; \
		echo "If your Codex version supports it, try manually: codex plugin marketplace add ./"; \
	else \
		echo "install target is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Uninstall plugin and remove marketplace from Claude Code
uninstall:
	@set -e; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		claude plugin uninstall $(PLUGIN_NAME); \
		claude plugin marketplace remove $(MARKETPLACE); \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		echo "Codex CLI uninstall flow is not yet verified."; \
		echo "Remove marketplace '$(MARKETPLACE)' manually if your Codex version supports marketplace removal."; \
	else \
		echo "uninstall target is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Validate plugin structure (requires Claude Code CLI)
validate: assemble
	@set -e; \
	trap 'rm -rf "$(BUILD_DIR)"' EXIT INT TERM; \
	if [ "$(IMPLEMENTATION)" = "claude" ]; then \
		claude plugin validate $(BUILD_DIR); \
	elif [ "$(IMPLEMENTATION)" = "codex" ]; then \
		test -f $(BUILD_DIR)/.codex-plugin/plugin.json || (echo "Missing .codex-plugin/plugin.json" && exit 1); \
		test -d $(BUILD_DIR)/skills || (echo "Missing skills directory" && exit 1); \
		echo "Codex plugin structure looks valid."; \
	else \
		echo "validate target is not implemented for IMPLEMENTATION=$(IMPLEMENTATION)"; \
		exit 1; \
	fi

## Show available targets
help:
	@grep -E '^##' Makefile | sed 's/## //'
	@echo ""
	@echo "Targets: build (default), clean, install, uninstall, validate"
	@echo "Variables: IMPLEMENTATION=claude (default)"
