# Compiler Optimization Gallery - Makefile
#
# Copyright (c) 2026 Larry H <l.gr [at] dartmouth [dot] edu>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Developed for COSC-69.16: Basics of Reverse Engineering
# Dartmouth College, Winter 2026
#
# Usage:
#   make install    - Install Python dependencies
#   make compile    - Run Compiler Explorer batch processing
#   make book       - Generate MkDocs documentation
#   make serve      - Serve MkDocs locally for preview
#   make build      - Build static site
#   make all        - Full pipeline: compile + book
#   make clean      - Remove generated outputs
#   make clean-all  - Remove outputs and book

.PHONY: all install compile book serve build clean clean-all help check-deps rebuild

# Configuration
PYTHON      ?= python3
PIP         ?= pip
CONFIG      ?= docs/config.yaml
SRC_DIR     ?= src
OUTPUT_DIR  ?= output
BOOK_DIR    ?= book
TEMPLATES   ?= templates

# MkDocs
MKDOCS      ?= mkdocs

# Default target
all: compile book

# Help
help:
	@echo "Compiler Optimization Gallery"
	@echo ""
	@echo "Targets:"
	@echo "  install     Install Python dependencies (jinja2, pyyaml, requests, mkdocs-material)"
	@echo "  compile     Run Compiler Explorer batch processing"
	@echo "  book        Generate MkDocs documentation from compiler output"
	@echo "  serve       Serve MkDocs locally at http://127.0.0.1:8000"
	@echo "  build       Build static HTML site in $(BOOK_DIR)/site/"
	@echo "  all         Full pipeline: compile + book (default)"
	@echo "  clean       Remove compiler output directory"
	@echo "  clean-all   Remove both output and book directories"
	@echo "  rebuild     Clean everything and rebuild from scratch"
	@echo ""
	@echo "Configuration (override with VAR=value):"
	@echo "  CONFIG=$(CONFIG)"
	@echo "  SRC_DIR=$(SRC_DIR)"
	@echo "  OUTPUT_DIR=$(OUTPUT_DIR)"
	@echo "  BOOK_DIR=$(BOOK_DIR)"
	@echo "  TEMPLATES=$(TEMPLATES)"

# Install dependencies
install:
	$(PIP) install --quiet requests pyyaml jinja2 mkdocs-material

# Check dependencies exist
check-deps:
	@$(PYTHON) -c "import requests, yaml, jinja2" 2>/dev/null || \
		(echo "Error: Missing dependencies. Run: make install" && exit 1)

# Compile sources with Compiler Explorer
compile: check-deps
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON) ce_batch.py \
		--yaml $(CONFIG) \
		--src $(SRC_DIR) \
		--out $(OUTPUT_DIR)

# Generate MkDocs book
book: check-deps
	@mkdir -p $(BOOK_DIR)
	$(PYTHON) build_book.py \
		--input $(OUTPUT_DIR) \
		--output $(BOOK_DIR) \
		--config $(CONFIG) \
		--templates $(TEMPLATES)

# Serve MkDocs locally
serve: book
	cd $(BOOK_DIR) && $(MKDOCS) serve

# Build static site
build: book
	cd $(BOOK_DIR) && $(MKDOCS) build

# Clean compiler output
clean:
	rm -rf $(OUTPUT_DIR)

# Clean everything
clean-all: clean
	rm -rf $(BOOK_DIR)

# Rebuild from scratch
rebuild: clean-all all
