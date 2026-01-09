# Makefile-Based Validation Framework for Solar Proa
# Three-tier architecture:
# Boat + Configuration constants (JSON)
# → Parameters (Make + Python)
# → Design generation (Make + Python)
# → Validation (Make + Python)

# ==============================================================================
# PLATFORM DETECTION AND FREECAD CONFIGURATION
# ==============================================================================

UNAME := $(shell uname)

# Detect FreeCAD command (different on different systems)
FREECAD_APP := /Applications/FreeCAD.app/Contents/MacOS/FreeCAD
FREECAD_BUNDLE := /Applications/FreeCAD.app
FREECAD := $(shell which freecad 2>/dev/null || \
                   which freecadcmd 2>/dev/null || \
                   (test -f $(FREECAD_APP) && echo $(FREECAD_APP)) || \
                   echo "freecad")

# On macOS use GUI app, on Linux use headless
ifeq ($(UNAME),Darwin)
	FREECAD_CMD := $(FREECAD_APP) --console
	FREECAD_PYTHON := $(FREECAD_BUNDLE)/Contents/Resources/bin/python
else
	FREECAD_CMD := xvfb-run -a freecadcmd
	FREECAD_PYTHON := freecad-python
endif

# ==============================================================================
# DIRECTORY STRUCTURE
# ==============================================================================

CONST_DIR := constants
BOATS_DIR := $(CONST_DIR)/boats
CONFIGURATIONS_DIR := $(CONST_DIR)/configurations
SRC_DIR := src
ARTIFACTS_DIR := artifacts
DOCS_DATA_DIR := docs/_data

# Validator source directories
PARAMETERS_DIR := $(SRC_DIR)/parameters
DESIGN_DIR := $(SRC_DIR)/design
MASS_DIR := $(SRC_DIR)/mass
BUOYANCY_DIR := $(SRC_DIR)/buoyancy
STABILITY_DIR := $(SRC_DIR)/stability
RENDER_DIR := $(SRC_DIR)/render

# ==============================================================================
# AUTO-DISCOVERY: Find all boats and configurations
# ==============================================================================

BOATS := $(basename $(notdir $(wildcard $(BOATS_DIR)/*.json)))
CONFIGURATIONS := $(basename $(notdir $(wildcard $(CONFIGURATIONS_DIR)/*.json)))

# Filter out any backup or temp files
BOATS := $(filter-out %~,$(BOATS))
CONFIGURATIONS := $(filter-out %~,$(CONFIGURATIONS))

# ==============================================================================
# DEFAULTS AND VARIABLES
# ==============================================================================

# Default boat and configuration (can be overridden: make design BOAT=rp2 CONFIGURATION=closehaul)
BOAT ?= rp2
CONFIGURATION ?= closehaul

# Computed file paths using dot-separated naming convention
BOAT_FILE := $(BOATS_DIR)/$(BOAT).json
CONFIGURATION_FILE := $(CONFIGURATIONS_DIR)/$(CONFIGURATION).json

# Artifact paths
PARAMETERS_ARTIFACT := $(ARTIFACTS_DIR)/$(BOAT).$(CONFIGURATION).parameters.json
DESIGN_ARTIFACT := $(ARTIFACTS_DIR)/$(BOAT).$(CONFIGURATION).design.FCStd
MASS_ARTIFACT := $(ARTIFACTS_DIR)/$(BOAT).$(CONFIGURATION).mass.json
BUOYANCY_ARTIFACT := $(ARTIFACTS_DIR)/$(BOAT).$(CONFIGURATION).buoyancy.json
STABILITY_ARTIFACT := $(ARTIFACTS_DIR)/$(BOAT).$(CONFIGURATION).stability.json
AGGREGATE_ARTIFACT := $(ARTIFACTS_DIR)/$(BOAT).$(CONFIGURATION).aggregate.json
JEKYLL_DATA := $(DOCS_DATA_DIR)/$(BOAT).$(CONFIGURATION).json

# ==============================================================================
# PHONY TARGETS
# ==============================================================================

.PHONY: all help clean check
.PHONY: jekyll validate design-all validate-all parameters-all

# ==============================================================================
# MAIN TARGETS
# ==============================================================================

all: design-all validate-all

help:
	@echo "Solar Proa Makefile-Based Validation Framework"
	@echo ""
	@echo "Platform: $(UNAME)"
	@echo "Discovered boats: $(BOATS)"
	@echo "Discovered configurations: $(CONFIGURATIONS)"
	@echo ""
	@echo "Main Targets:"
	@echo "  make all                    - Build and validate all boats with all configurations"
	@echo "  make design                 - Generate single design (BOAT=$(BOAT) CONFIGURATION=$(CONFIGURATION))"
	@echo "  make design-all             - Generate all boat+configuration combinations"
	@echo "  make validate               - Run validators for single design (BOAT=$(BOAT) CONFIGURATION=$(CONFIGURATION))"
	@echo "  make validate-all           - Run validators for all existing designs"
	@echo ""
	@echo "Parameter Targets:"
	@echo "  make parameters             - Compute and save parameters to artifacts/"
	@echo "  make parameters-all         - Generate all boat+configuration parameters"
	@echo ""
	@echo "Utility Targets:"
	@echo "  make clean                  - Remove all generated files"
	@echo "  make check                  - Check FreeCAD installation"
	@echo "  make help                   - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make design BOAT=rp2 CONFIGURATION=closehaul"
	@echo "  make validate BOAT=rp2 CONFIGURATION=closehaul"
	@echo "  make parameters BOAT=rp2"
	@echo ""
	@echo "FreeCAD: $(FREECAD)"

# ==============================================================================
# PARAMETER COMPUTATION
# ==============================================================================

# Compute and save parameters to artifacts directory
$(PARAMETERS_ARTIFACT): $(BOAT_FILE) $(CONFIGURATION_FILE) $(PARAMETERS_DIR)/parameters.py
	@echo "Computing parameters for $(BOAT) and $(CONFIGURATION)..."
	@mkdir -p $(ARTIFACTS_DIR)
	@python3 $(PARAMETERS_DIR)/parameters.py \
		--boat $(BOAT_FILE) \
		--configuration $(CONFIGURATION_FILE) \
		--output $@
	@echo "✓ Computed parameters saved to $@"

parameters: $(PARAMETERS_ARTIFACT)

# Compute and save parameters for all boat+configuration combinations
parameters-all:
	@echo "Generating all parameter files..."
	@for boat in $(BOATS); do \
		for configuration in $(CONFIGURATIONS); do \
			echo ""; \
			$(MAKE) parameters BOAT=$$boat CONFIGURATION=$$configuration || true; \
		done \
	done
	@echo ""
	@echo "✓ All designs complete!"

# ==============================================================================
# DESIGN GENERATION
# ==============================================================================

# Create output directories
$(ARTIFACTS_DIR) $(DOCS_DATA_DIR):
	@mkdir -p $@

# Generate a single design
$(DESIGN_ARTIFACT): $(PARAMETERS_ARTIFACT) $(DESIGN_DIR)/design.FCMacro | $(DESIGN_DIR)
	@echo "Generating design: $(BOAT).$(CONFIGURATION)"
	@echo "  Parameters: $(PARAMETERS_ARTIFACT)"
	@$(FREECAD_CMD) $(DESIGN_DIR)/design.FCMacro $(PARAMETERS_ARTIFACT) $(DESIGN_ARTIFACT) || true
	@if [ -f "$(DESIGN_ARTIFACT)" ]; then \
		echo "✓ Design complete: $(DESIGN_ARTIFACT)"; \
		if [ "$(UNAME)" = "Darwin" ]; then \
			echo "Fixing visibility on macOS..."; \
			bash $(DESIGN_DIR)/fix_visibility.sh "$(DESIGN_ARTIFACT)" "$(FREECAD_APP)"; \
		fi; \
	else \
		echo "ERROR: Design failed - no design file created"; \
		exit 1; \
	fi

design: $(DESIGN_ARTIFACT)

# Generate the designs for all boat+configuration combinations
design-all:
	@echo "Generating all designs..."
	@for boat in $(BOATS); do \
		for configuration in $(CONFIGURATIONS); do \
			echo ""; \
			$(MAKE) design BOAT=$$boat CONFIGURATION=$$configuration || true; \
		done \
	done
	@echo ""
	@echo "✓ All designs complete!"

# ==============================================================================
# VALIDATION PIPELINE (DAG-based dependency resolution)
# ==============================================================================

# Mass analysis (depends on design)
$(MASS_ARTIFACT): $(DESIGN_ARTIFACT) $(MASS_DIR)/mass.py | $(ARTIFACTS_DIR)
	@echo "Running mass analysis: $(BOAT).$(CONFIGURATION)"
	@if [ "$(UNAME)" = "Darwin" ]; then \
		PYTHONPATH=$(FREECAD_BUNDLE)/Contents/Resources/lib:$(FREECAD_BUNDLE)/Contents/Resources/Mod:$(PWD) \
		DYLD_LIBRARY_PATH=$(FREECAD_BUNDLE)/Contents/Frameworks:$(FREECAD_BUNDLE)/Contents/Resources/lib \
		$(FREECAD_PYTHON) $(MASS_DIR)/mass.py --design $(DESIGN_ARTIFACT) --output $@; \
	else \
		PYTHONPATH=$(PWD):$(PWD)/src/design $(FREECAD_PYTHON) $(MASS_DIR)/mass.py --design $(DESIGN_ARTIFACT) --output $@; \
	fi

# Buoyancy analysis (depends on mass)
$(BUOYANCY_ARTIFACT): $(MASS_ARTIFACT) $(PARAMETERS_ARTIFACT) $(BUOYANCY_DIR)/buoyancy.py | $(ARTIFACTS_DIR)
	@echo "Running buoyancy analysis: $(BOAT).$(CONFIGURATION)"
	@$(MAKE) parameters BOAT=$(BOAT) CONFIGURATION=$(CONFIGURATION)
	@python3 $(BUOYANCY_DIR)/buoyancy.py \
		--mass $(MASS_ARTIFACT) \
		--parameters $(PARAMETERS_ARTIFACT) \
		--output $@
	@echo "✓ Buoyancy analyis saved to $@"

# Stability analysis (depends on mass and buoyancy)
$(STABILITY_ARTIFACT): $(MASS_ARTIFACT) $(BUOYANCY_ARTIFACT) $(PARAMETERS_ARTIFACT) $(CONFIGURATION_FILE) $(STABILITY_DIR)/stability.py | $(ARTIFACTS_DIR)
	@echo "Running stability analysis: $(BOAT).$(CONFIGURATION)"
	@python3 $(STABILITY_DIR)/stability.py \
		--mass $(MASS_ARTIFACT) \
		--buoyancy $(BUOYANCY_ARTIFACT) \
		--parameters $(PARAMETERS_ARTIFACT) \
		--configuration $(CONFIGURATION_FILE) \
		--output $@

# Aggregate all artifacts into a single JSON for Jekyll
$(AGGREGATE_ARTIFACT): $(PARAMETERS_ARTIFACT) $(MASS_ARTIFACT) | $(DOCS_DATA_DIR) 
	@echo "Aggregating artifacts: $(BOAT).$(CONFIGURATION)"
	@mkdir -p $(DOCS_DATA_DIR)
	@python3 -c "import json; \
		boat='$(BOAT)'; configuration='$(CONFIGURATION)'; \
		parameters = json.load(open('$(PARAMETERS_ARTIFACT)')); \
		mass = json.load(open('$(MASS_ARTIFACT)')); \
		result = {'boat': boat, 'configuration': configuration, 'parameters': parameters, 'mass': mass}; \
		json.dump(result, open('$@', 'w'), indent=2)"
	@echo "✓ Aggregated artifact: $@"

# $(BUOYANCY_ARTIFACT) $(STABILITY_ARTIFACT) 
#	, 'buoyancy': buoyancy, 'stability': stability
#	buoyancy = json.load(open('$(BUOYANCY_ARTIFACT)')); \
#	stability = json.load(open('$(STABILITY_ARTIFACT)')); \


# Validate a single design (runs all validators based on configuration)
validate: 
	@if make -q $(AGGREGATE_ARTIFACT) 2>/dev/null; then \
		echo "✓ Validation already up to date"; \
	else \
		$(MAKE) $(AGGREGATE_ARTIFACT); \
		echo "✓ Validation rebuilt"; \
	fi

# Validate all boat+configuration combinations (matches design-all)
validate-all:
	@echo "Validating all designs..."
	@for boat in $(BOATS); do \
		for configuration in $(CONFIGURATIONS); do \
			echo ""; \
			$(MAKE) validate BOAT=$$boat CONFIGURATION=$$configuration || true; \
		done \
	done
	@echo ""
	@echo "✓ All validations complete!"

# Validate only designs that already have .FCStd files
validate-existing:
	@echo "Validating existing designs..."
	@for design in $(ARTIFACTS_DIR)/*.design.FCStd; do \
		if [ -f "$$design" ]; then \
			base=$$(basename "$$design" .design.FCStd); \
			boat=$$(echo "$$base" | cut -d'.' -f1); \
			configuration=$$(echo "$$base" | cut -d'.' -f2); \
			echo ""; \
			$(MAKE) validate BOAT=$$boat CONFIGURATION=$$configuration || true; \
		fi \
	done
	@echo ""
	@echo "✓ All existing designs validated!"

# Render images from single FCStd file (assumes FCSTD exists)
.PHONY: render-only
render-only: $(RENDER_DIR)
	@echo "Rendering images from $(DESIGN_ARTIFACT)..."
	@if [ ! -f "$(DESIGN_ARTIFACT)" ]; then \
		echo "ERROR: $(DESIGN_ARTIFACT) not found. Run 'make design' first."; \
		exit 1; \
	fi
	@if [ "$(UNAME)" = "Darwin" ]; then \
		$(RENDER_DIR)/render_mac.sh "$(DESIGN_ARTIFACT)" "$(ARTIFACTS_DIR)" "$(FREECAD_APP)"; \
	else \
		FCSTD_FILE="$(DESIGN_ARTIFACT)" IMAGE_DIR="$(ARTIFACTS_DIR)" freecad-python $(RENDER_DIR)/render_linux.py; \
	fi
	@echo "Cropping images with ImageMagick..."
	@if command -v convert >/dev/null 2>&1; then \
		for img in $(ARTIFACTS_DIR)/*.png; do \
			if [ -f "$$img" ]; then \
				convert "$$img" -fuzz 1% -trim +repage -bordercolor white -border 20 "$$img" || true; \
			fi \
		done; \
		echo "Cropping complete!"; \
	else \
		echo "ImageMagick not found, skipping crop"; \
	fi
	@echo "Render complete!"

# Render with auto-build
.PHONY: render
render: design render-only

# Render images from all existing FCStd files
.PHONY: render-all
render-all: $(RENDER_DIR)
	@echo "Rendering images from all existing designs..."
	@for fcstd in $(ARTIFACTS_DIR)/*.FCStd; do \
		if [ -f "$$fcstd" ]; then \
			base=$$(basename "$$fcstd" .FCStd); \
			boat=$$(echo "$$base" | cut -d'.' -f1); \
			config=$$(echo "$$base" | cut -d'.' -f2); \
			echo "Processing $$boat $$config..."; \
			$(MAKE) render-only BOAT=$$boat CONFIGURATION=$$config || true; \
		fi \
	done
	@echo "All renders complete!"

# ==============================================================================
# CONFIGURATION-DRIVEN VALIDATION (read required_validators from configuration)
# ==============================================================================

# This is a more advanced target that reads the configuration file to determine
# which validators to run. For now, we run all validators by default.
# Future enhancement: parse JSON and conditionally run validators.

# ==============================================================================
# PARALLEL EXECUTION
# ==============================================================================

# To run validations in parallel (for independent designs):
#   make validate-all -j4

# To run a single validation pipeline in parallel (not useful since it's sequential):
#   Dependencies ensure correct order automatically

# ==============================================================================
# CLEANUP
# ==============================================================================

clean:
	@echo "Cleaning generated files..."
	@rm -rf $(ARTIFACTS_DIR)
	@rm -rf $(DOCS_DATA_DIR)
	@echo "Removing backup files..."
	@find . -name '*~' -delete
	@echo "Removing Python cache..."
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete
	@find . -name '*.pyo' -delete
	@echo "✓ Clean complete!"

# ==============================================================================
# DIAGNOSTICS
# ==============================================================================

check:
	@echo "Checking for FreeCAD..."
	@$(FREECAD) --version || (echo "FreeCAD not found!" && exit 1)
	@echo "✓ FreeCAD found: $(FREECAD)"
	@echo ""
	@echo "Checking Python..."
	@python3 --version
	@echo ""
	@echo "Discovered boats: $(BOATS)"
	@echo "Discovered configurations: $(CONFIGURATIONS)"
	@echo ""
	@echo "System ready!"

# Serve website locally
.PHONY: localhost
localhost:
	@echo "Serving website in localhost..."
	cd docs; bundle exec jekyll serve

# Make zip file with just the newest versions of the git files
.PHONY: zip
zip:	clean
	@echo "Make zip file with current working directory"
	@rm -f ../CAD-clean.zip
	git ls-files | zip -@ ../CAD-clean.zip
