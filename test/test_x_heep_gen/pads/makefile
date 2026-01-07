ROOT_DIR := $(shell git rev-parse --show-toplevel)

# Determine Python interpreter (matches main Makefile logic)
ifeq ($(wildcard $(ROOT_DIR)/.venv/.*),)
PYTHON := $(shell which python)
else
PYTHON := $(ROOT_DIR)/.venv/python
endif

GENERATE_SCRIPT := $(ROOT_DIR)/test/test_x_heep_gen/pads/generate_goldens.py

# User targets

## Generate golden reference files from current branch
## Usage:
##   make golden                              # Generate all scenarios
##   make golden SCENARIO=minimal_pads        # Generate only minimal_pads scenario
.PHONY: golden
golden:
	$(PYTHON) $(GENERATE_SCRIPT) $(if $(SCENARIO),--scenario $(SCENARIO))

## Generate golden references from main branch (safe - returns to original branch)
.PHONY: golden-from-main
golden-from-main:
	$(PYTHON) $(GENERATE_SCRIPT) --from-main --verify

## Verify existing golden reference files are valid
.PHONY: golden-verify
golden-verify:
	$(PYTHON) $(GENERATE_SCRIPT) --verify --dry-run

## Generate golden references from hjson configs only (skip python configs)
## Use this when Python config support is not yet available on current branch
.PHONY: golden-hjson
golden-hjson:
	$(PYTHON) $(GENERATE_SCRIPT) --hjson-only $(if $(SCENARIO),--scenario $(SCENARIO))
