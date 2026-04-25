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

.DEFAULT_GOAL := build

.PHONY: assemble build clean install uninstall validate help

assemble: clean
	@test -d $(CORE_DIR) || (echo "Missing shared core directory: $(CORE_DIR)" && exit 1)
	@test -d $(IMPLEMENTATION_DIR) || (echo "Missing implementation directory: $(IMPLEMENTATION_DIR)" && exit 1)
	@echo "Assembling $(PLUGIN_NAME) v$(VERSION) for $(IMPLEMENTATION)..."
	@mkdir -p $(DIST_DIR)
	@cp -r $(CORE_DIR) $(BUILD_DIR)
	@cp -r $(IMPLEMENTATION_DIR)/. $(BUILD_DIR)/
	@chmod +x $(BUILD_DIR)/scripts/*.sh
	@find $(BUILD_DIR) -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find $(BUILD_DIR) -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	@find $(BUILD_DIR) -depth -type d -empty -delete

## Build deployable plugin zip
build: assemble
	@echo "Packaging $(BUILD_NAME)..."
	@cd $(DIST_DIR) && zip -r $(ZIP_NAME) $(BUILD_NAME)/ -x "*/.DS_Store" -x "*/__pycache__/*" -x "*.pyc" > /dev/null
	@rm -rf $(BUILD_DIR)
	@echo "✅ $(ZIP_PATH) ($$(du -h $(ZIP_PATH) | cut -f1))"

## Remove dist/
clean:
	@rm -rf $(DIST_DIR)

## Build + install plugin into Claude Code
install: build
	@if [ "$(IMPLEMENTATION)" != "claude" ]; then echo "install target currently supports IMPLEMENTATION=claude only"; exit 1; fi
	claude plugin marketplace add ./
	claude plugin install $(PLUGIN_NAME)@$(MARKETPLACE)

## Uninstall plugin and remove marketplace from Claude Code
uninstall:
	claude plugin uninstall $(PLUGIN_NAME)
	claude plugin marketplace remove $(MARKETPLACE)

## Validate plugin structure (requires Claude Code CLI)
validate: assemble
	@if [ "$(IMPLEMENTATION)" != "claude" ]; then echo "validate target currently supports IMPLEMENTATION=claude only"; rm -rf $(BUILD_DIR); exit 1; fi
	claude plugin validate $(BUILD_DIR)
	@rm -rf $(BUILD_DIR)

## Show available targets
help:
	@grep -E '^##' Makefile | sed 's/## //'
	@echo ""
	@echo "Targets: build (default), clean, install, uninstall, validate"
	@echo "Variables: IMPLEMENTATION=claude (default)"
