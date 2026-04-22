PLUGIN_NAME := spec-kit-automation
VERSION     := 1.0.0
SRC_DIR     := src/$(PLUGIN_NAME)-v$(VERSION)
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
	@cd $(DIST_DIR) && zip -r $(ZIP_NAME) $(PLUGIN_NAME)-v$(VERSION)/ -x "*/.DS_Store" > /dev/null
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
