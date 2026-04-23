PLUGIN_NAME := agent-align
VERSION     := 1.4.0
SRC_DIR     := src/$(PLUGIN_NAME)-v1.0.0
DIST_DIR    := dist
ZIP_NAME    := $(PLUGIN_NAME)-v$(VERSION).zip
ZIP_PATH    := $(DIST_DIR)/$(ZIP_NAME)

.DEFAULT_GOAL := build

.PHONY: build clean install validate help

## Build deployable plugin zip
build: clean
	@echo "Building $(PLUGIN_NAME) v$(VERSION)..."
	@mkdir -p $(DIST_DIR)
	@cp -r $(SRC_DIR) $(DIST_DIR)/$(PLUGIN_NAME)-v$(VERSION)
	@chmod +x $(DIST_DIR)/$(PLUGIN_NAME)-v$(VERSION)/scripts/*.sh
	@find $(DIST_DIR)/$(PLUGIN_NAME)-v$(VERSION) -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find $(DIST_DIR)/$(PLUGIN_NAME)-v$(VERSION) -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	@find $(DIST_DIR)/$(PLUGIN_NAME)-v$(VERSION) -depth -type d -empty -delete
	@cd $(DIST_DIR) && zip -r $(ZIP_NAME) $(PLUGIN_NAME)-v$(VERSION)/ -x "*/.DS_Store" -x "*/__pycache__/*" -x "*.pyc" > /dev/null
	@rm -rf $(DIST_DIR)/$(PLUGIN_NAME)-v$(VERSION)
	@echo "✅ $(ZIP_PATH) ($$(du -h $(ZIP_PATH) | cut -f1))"

## Remove dist/
clean:
	@rm -rf $(DIST_DIR)

## Build + install plugin into Claude Code
install: build
	claude plugin install $(ZIP_PATH)

## Validate plugin structure (requires Claude Code CLI)
validate:
	claude plugin validate $(SRC_DIR)

## Show available targets
help:
	@grep -E '^##' Makefile | sed 's/## //'
	@echo ""
	@echo "Targets: build (default), clean, install, validate"
