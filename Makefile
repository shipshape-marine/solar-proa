# Makefile-Based Staged Framework for Solar Proa

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
	FILTER_NOISE := 2>&1 | grep -v "3DconnexionNavlib" | grep -v "^$$"
# Conda env with FreeCAD (for geometry modules via shipshape)
	CONDA_PYTHON := /Users/henz/anaconda3/envs/freecad/bin/python
	FREECAD_LIB := /Users/henz/anaconda3/envs/freecad/lib
else
	FREECAD_CMD := xvfb-run -a freecadcmd
	FREECAD_PYTHON := freecad-python
	FILTER_NOISE :=
# On Linux (CI), use freecad-python wrapper directly
	CONDA_PYTHON := $(FREECAD_PYTHON)
	FREECAD_LIB :=
endif

# ==============================================================================
# OVERALL DIRECTORY STRUCTURE
# ==============================================================================

CONST_DIR := constant
BOAT_DIR := $(CONST_DIR)/boat
CONFIGURATION_DIR := $(CONST_DIR)/configuration
MATERIAL_DIR := $(CONST_DIR)/material
SRC_DIR := src

# output directories
ARTIFACT_DIR := artifact
DOCS_DATA_DIR := docs/_data

# create those output directories if they don't exist yet
$(ARTIFACT_DIR) $(DOCS_DATA_DIR):
	@mkdir -p $@

# ==============================================================================
# AUTO-DISCOVERY: Find all boats and configurations
# ==============================================================================

#BOATS := $(basename $(notdir $(wildcard $(BOAT_DIR)/*.json)))
BOATS := rp2
CONFIGURATIONS := $(basename $(notdir $(wildcard $(CONFIGURATION_DIR)/*.json)))

# Filter out any backup or temp files
BOATS := $(filter-out %~,$(BOATS))
CONFIGURATIONS := $(filter-out %~,$(CONFIGURATIONS))

# ==============================================================================
# DEFAULTS AND VARIABLES
# ==============================================================================

# Default boat and configuration
# (can be overridden, e.g.:
#  make design BOAT=rp3 CONFIGURATION=broadreach MATERIAL=wiring)
BOAT ?= rp2
CONFIGURATION ?= closehaul
MATERIAL ?= proa

# Computed file paths
BOAT_FILE := $(BOAT_DIR)/$(BOAT).json
CONFIGURATION_FILE := $(CONFIGURATION_DIR)/$(CONFIGURATION).json
MATERIAL_FILE := $(MATERIAL_DIR)/$(MATERIAL).json

# ==============================================================================
# MAIN TARGETS
# ==============================================================================

.DEFAULT_GOAL := all

.PHONY: all
all: required-all

# "required" target: look in the appropriate configuration file what stages
# need to run and run them
.PHONY: required
required:
	@echo "Running required stages for $(BOAT).$(CONFIGURATION)..."
	@required_stages=$$(python3 -c "import json; config = json.load(open('$(CONFIGURATION_FILE)')); print(' '.join(config.get('required', [])))"); \
	for stage in $$required_stages; do \
		echo "Running stage: $$stage"; \
		$(MAKE) $$stage BOAT=$(BOAT) CONFIGURATION=$(CONFIGURATION) MATERIAL=$(MATERIAL) || true; \
	done; \
	echo "✓ Required stages complete for $(BOAT).$(CONFIGURATION)"

# Apply "required" stages to all designs
.PHONY: required-all
required-all:
	@echo "run required stages..."
	@for boat in $(BOATS); do \
		for configuration in $(CONFIGURATIONS); do \
			echo ""; \
			$(MAKE) required BOAT=$$boat CONFIGURATION=$$configuration || true; \
		done \
	done
	@echo ""
	@echo "✓ All required stages complete!"

.PHONY: help
help:
	@echo "Solar Proa Makefile-Based Staged Framework"
	@echo ""
	@echo "Platform: $(UNAME)"
	@echo "Discovered boats: $(BOATS)"
	@echo "Discovered configurations: $(CONFIGURATIONS)"
	@echo ""
	@echo "Main Targets:"
	@echo "  make                        - Same as 'make all' and 'make required-all'"
	@echo "  make required-all           - Run all required stages for all boats and configurations"
	@echo "                                Required stages are specified in constants/configurations"
	@echo "  make design                 - Generate single design (BOAT=$(BOAT) CONFIGURATION=$(CONFIGURATION))"
	@echo "  make cables                 - Add power cables to design"
	@echo "  make color                  - Apply color scheme to design (MATERIAL=$(MATERIAL))"
	@echo "  make step                   - Export design to STEP format (geometry only)"
	@echo "  make render                 - Render images (applies colors then renders)"
	@echo "  make buoyancy               - Run buoyancy equilibrium analysis"
	@echo "  make gz                     - Compute GZ righting arm curve (JSON + PNG)"
	@echo "  make buoyancy-design        - Position boat at equilibrium with water surface"
	@echo "  make buoyancy-render        - Render images of boat at equilibrium"
	@echo "  make validate-structure     - Validate structural integrity (all load cases)"
	@echo "  make lines                  - Generate lines plan (TechDraw with sections)"
	@echo "  make lines-pdf              - Compile lines plan LaTeX to PDF"
	@echo ""
	@echo "Parameter Targets:"
	@echo "  make parameter              - Compute and save parameter to artifacts/"
	@echo ""
	@echo "Utility Targets:"
	@echo "  make clean                  - Remove all generated files"
	@echo "  make check                  - Check FreeCAD installation"
	@echo "  make graph                  - Generate dependency graph (docs/dependency_graph.png)"
	@echo "  make help                   - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make parameter BOAT=rp1"
	@echo "  make design BOAT=rp2 CONFIGURATION=closehaul"
	@echo "  make color BOAT=rp3 CONFIGURATION=closehaul MATERIAL=proa"
	@echo "  make render BOAT=rp2 CONFIGURATION=closehaul"
	@echo ""
	@echo "FreeCAD: $(FREECAD)"

# remove all generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	@rm -rf $(ARTIFACT_DIR)
	@rm -rf $(DOCS_DATA_DIR)
	@echo "Removing backup files..."
	@find . -name '*~' -delete
	@echo "Removing Python cache..."
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete
	@find . -name '*.pyo' -delete
	@echo "✓ Clean complete!"

# check if FreeCAD and Python are properly installed
.PHONY: check
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

# copy artifacts to docs folders for local preview
.PHONY: sync-docs
sync-docs:
	@echo "Syncing artifacts to docs folders..."
	@mkdir -p docs/_data docs/renders docs/downloads docs/lines
	@# Copy JSON files with dots→underscores renaming
	@for file in artifact/*.json; do \
		if [ -f "$$file" ]; then \
			basename=$$(basename "$$file" .json); \
			newname=$$(echo "$$basename" | tr '.' '_'); \
			cp "$$file" "docs/_data/$${newname}.json"; \
		fi \
	done
	@echo "  Copied $$(ls artifact/*.json 2>/dev/null | wc -l | tr -d ' ') JSON files to docs/_data/"
	@# Copy PNG renders
	@if ls artifact/*.png 1>/dev/null 2>&1; then \
		cp artifact/*.png docs/renders/; \
		echo "  Copied $$(ls artifact/*.png | wc -l | tr -d ' ') PNG files to docs/renders/"; \
	fi
	@# Copy lines plan SVGs
	@if ls artifact/*.svg 1>/dev/null 2>&1; then \
		cp artifact/*.svg docs/lines/; \
		echo "  Copied $$(ls artifact/*.svg | wc -l | tr -d ' ') SVG files to docs/lines/"; \
	fi
	@# Copy lines plan PDFs
	@if ls artifact/*.pdf 1>/dev/null 2>&1; then \
		cp artifact/*.pdf docs/lines/; \
		echo "  Copied $$(ls artifact/*.pdf | wc -l | tr -d ' ') PDF files to docs/lines/"; \
	fi
	@# Copy downloads
	@if ls artifact/*.FCStd 1>/dev/null 2>&1; then \
		cp artifact/*.FCStd docs/downloads/; \
		echo "  Copied $$(ls artifact/*.FCStd | wc -l | tr -d ' ') FCStd files to docs/downloads/"; \
	fi
	@if ls artifact/*.step.step 1>/dev/null 2>&1; then \
		cp artifact/*.step.step docs/downloads/; \
		echo "  Copied $$(ls artifact/*.step.step | wc -l | tr -d ' ') STEP files to docs/downloads/"; \
	fi
	@# Generate YAML files if scripts exist
	@if [ -f docs/generate_downloads_yaml.py ]; then python3 docs/generate_downloads_yaml.py; fi
	@if [ -f docs/generate_configurations_yaml.py ]; then python3 docs/generate_configurations_yaml.py; fi
	@echo "✓ Docs sync complete"

# make diagrams
.PHONY: diagrams
diagrams: 
	@echo "making all diagrams..."
	python3 -m shipshape.validate_structure.diagrams

# serve website locally
.PHONY: localhost
localhost: sync-docs diagrams
	@echo "Serving website in localhost..."
	cd docs; bundle exec jekyll serve

# make zip file with just the newest versions of the git files
.PHONY: zip
zip:	clean
	@echo "Make zip file with current working directory"
	@rm -f ../CAD-clean.zip
	git ls-files | zip -@ ../CAD-clean.zip

# generate dependency graph
.PHONY: graph
graph:
	@python3 docs/generate_dependency_graph.py docs/dependency_graph.png

# ==============================================================================
# STAGES
# ==============================================================================

# ==============================================================================
# PARAMETER COMPUTATION
# ==============================================================================

PARAMETER_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).parameter.json

$(PARAMETER_ARTIFACT): $(BOAT_FILE) $(CONFIGURATION_FILE)
	@echo "Computing parameters for $(BOAT) and $(CONFIGURATION)..."
	@mkdir -p $(ARTIFACT_DIR)
	@PYTHONPATH=$(PWD) python3 -m shipshape.parameter \
		--compute src.parameter.compute \
		--boat $(BOAT_FILE) \
		--configuration $(CONFIGURATION_FILE) \
		--output $@
	@echo "✓ Computed parameters saved to $@"

.PHONY: parameter
parameter: $(PARAMETER_ARTIFACT)

# ==============================================================================
# DESIGN GENERATION
# ==============================================================================

DESIGN_DIR := $(SRC_DIR)/design
DESIGN_SOURCE := $(wildcard $(DESIGN_DIR)/*.py)
DESIGN_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).design.FCStd

$(DESIGN_ARTIFACT): $(PARAMETER_ARTIFACT) $(DESIGN_SOURCE) | $(DESIGN_DIR)
	@echo "Generating design: $(BOAT).$(CONFIGURATION)"
	@echo "  Parameters: $(PARAMETER_ARTIFACT)"
	@PARAMS_PATH=$(PARAMETER_ARTIFACT) OUTPUT_PATH=$(DESIGN_ARTIFACT) $(FREECAD_CMD) $(DESIGN_DIR)/main.py $(FILTER_NOISE) || true
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

.PHONY: design
design: $(DESIGN_ARTIFACT)

# ==============================================================================
# ADD POWER CABLES
# ==============================================================================

CABLES_DIR := $(SRC_DIR)/power_cables
CABLES_SOURCE := $(wildcard $(CABLES_DIR)/*.py)
CABLES_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).cables.FCStd

$(CABLES_ARTIFACT): $(DESIGN_ARTIFACT) $(CABLES_SOURCE) $(PARAMETER_ARTIFACT) | $(ARTIFACT_DIR)
	@echo "Adding power cables to: $(BOAT).$(CONFIGURATION)"
	@if [ "$(UNAME)" = "Darwin" ]; then \
		bash $(CABLES_DIR)/power_cables_mac.sh \
			--design "$(DESIGN_ARTIFACT)" \
			--params "$(PARAMETER_ARTIFACT)" \
			--outputdesign "$(CABLES_ARTIFACT)"; \
	else \
		$(FREECAD_PYTHON) -m src.power_cables \
			--design "$(DESIGN_ARTIFACT)" \
			--params "$(PARAMETER_ARTIFACT)" \
			--outputdesign "$(CABLES_ARTIFACT)"; \
	fi
	@echo "✓ Cables added: $(CABLES_ARTIFACT)"

.PHONY: cables
cables: $(CABLES_ARTIFACT)

# ==============================================================================
# COLOR THE DESIGNS
# ==============================================================================

COLOR_DIR := $(SRC_DIR)/color
COLOR_SOURCE := $(wildcard $(COLOR_DIR)/*.py)
COLOR_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).color.FCStd

$(COLOR_ARTIFACT): $(DESIGN_ARTIFACT) $(MATERIAL_FILE) $(COLOR_SOURCE) | $(COLOR_DIR)
	@echo "Applying color scheme '$(MATERIAL)' to $(BOAT).$(CONFIGURATION)..."
	@if [ ! -f "$(MATERIAL_FILE)" ]; then \
		echo "ERROR: Color scheme not found: $(MATERIAL_FILE)"; \
		echo "Available schemes: $(notdir $(wildcard $(MATERIAL_DIR)/*.json))"; \
		exit 1; \
	fi
	@if [ "$(UNAME)" = "Darwin" ]; then \
		bash $(COLOR_DIR)/color_mac.sh \
			"$(DESIGN_ARTIFACT)" \
			"$(MATERIAL_FILE)" \
			"$(COLOR_ARTIFACT)" \
			"$(FREECAD_APP)"; \
	else \
		freecad-python -m src.color \
			--design "$(DESIGN_ARTIFACT)" \
			--color "$(MATERIAL_FILE)" \
			--outputdesign "$(COLOR_ARTIFACT)"; \
	fi
	@echo "✓ Colored design: $(COLOR_ARTIFACT)"

.PHONY: color
color: $(COLOR_ARTIFACT)
	@echo "✓ Color scheme '$(MATERIAL)' applied to $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# FIND THE MASS OF THE PARTS AND COMPUTE THE TOTAL MASS
# ==============================================================================

MASS_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).mass.json

$(MASS_ARTIFACT): $(DESIGN_ARTIFACT) $(MATERIAL_FILE) | $(ARTIFACT_DIR)
	@echo "Running mass analysis: $(BOAT).$(CONFIGURATION)"
	@PYTHONPATH=$(FREECAD_LIB):$(PWD) $(CONDA_PYTHON) -m shipshape.mass \
		--design $(DESIGN_ARTIFACT) --materials $(MATERIAL_FILE) --output $@

.PHONY: mass
mass: $(MASS_ARTIFACT)
	@echo "✓ mass calculation applied to $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# RENDER THE COLORED DESIGNS
# ==============================================================================

RENDER_DIR := $(SRC_DIR)/render
RENDER_SOURCE := $(wildcard $(RENDER_DIR)/*.py)

.PHONY: render
render: $(COLOR_ARTIFACT) $(RENDER_SOURCE)
	@echo "Rendering images from $(COLOR_ARTIFACT)..."
	@if [ "$(UNAME)" = "Darwin" ]; then \
		$(RENDER_DIR)/render_mac.sh "$(COLOR_ARTIFACT)" "$(ARTIFACT_DIR)" "$(FREECAD_APP)"; \
	else \
		FCSTD_FILE="$(COLOR_ARTIFACT)" IMAGE_DIR="$(ARTIFACT_DIR)" freecad-python -m src.render; \
	fi
	@echo "Cropping images with ImageMagick..."
	@if command -v convert >/dev/null 2>&1; then \
		for img in $(ARTIFACT_DIR)/*.png; do \
			if [ -f "$$img" ]; then \
				convert "$$img" -fuzz 1% -trim +repage -bordercolor \#C6D2FF -border 25 "$$img" || true; \
			fi \
		done; \
		echo "Cropping complete!"; \
	else \
		echo "ImageMagick not found, skipping crop"; \
	fi
	@echo "Render complete!"

# ==============================================================================
# EXPORT DESIGNS TO STEP FORMAT
# ==============================================================================

STEP_DIR := $(SRC_DIR)/step
STEP_SOURCE := $(wildcard $(STEP_DIR)/*.py) $(wildcard $(STEP_DIR)/*.sh)
STEP_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).step.step

$(STEP_ARTIFACT): $(DESIGN_ARTIFACT) $(STEP_SOURCE) | $(ARTIFACT_DIR)
	@echo "Exporting STEP: $(BOAT).$(CONFIGURATION)"
	@if [ "$(UNAME)" = "Darwin" ]; then \
		bash $(STEP_DIR)/step_mac.sh \
			"$(DESIGN_ARTIFACT)" \
			"$(STEP_ARTIFACT)" \
			"$(FREECAD_APP)"; \
	else \
		$(FREECAD_PYTHON) -m src.step \
			--input "$(DESIGN_ARTIFACT)" \
			--output "$(STEP_ARTIFACT)"; \
	fi
	@echo "✓ STEP export: $(STEP_ARTIFACT)"

.PHONY: step
step: $(STEP_ARTIFACT)
	@echo "✓ STEP export complete for $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# BUOYANCY EQUILIBRIUM ANALYSIS
# ==============================================================================

BUOYANCY_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).buoyancy.json

$(BUOYANCY_ARTIFACT): $(DESIGN_ARTIFACT) $(MASS_ARTIFACT) $(MATERIAL_FILE) | $(ARTIFACT_DIR)
	@echo "Running buoyancy analysis: $(BOAT).$(CONFIGURATION)"
	@PYTHONPATH=$(FREECAD_LIB):$(PWD) $(CONDA_PYTHON) -m shipshape.buoyancy \
		--design $(DESIGN_ARTIFACT) \
		--mass $(MASS_ARTIFACT) \
		--materials $(MATERIAL_FILE) \
		--output $@

.PHONY: buoyancy
buoyancy: $(BUOYANCY_ARTIFACT)
	@echo "✓ Buoyancy analysis complete for $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# GZ CURVE (RIGHTING ARM) ANALYSIS
# ==============================================================================

GZ_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).gz.json
GZ_PNG := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).gz.png

$(GZ_ARTIFACT): $(BUOYANCY_ARTIFACT) $(DESIGN_ARTIFACT) $(PARAMETER_ARTIFACT) | $(ARTIFACT_DIR)
	@echo "Computing GZ curve: $(BOAT).$(CONFIGURATION)"
	@PYTHONPATH=$(FREECAD_LIB):$(PWD) $(CONDA_PYTHON) -m shipshape.gz \
		--design $(DESIGN_ARTIFACT) \
		--buoyancy $(BUOYANCY_ARTIFACT) \
		--parameters $(PARAMETER_ARTIFACT) \
		--output $@ \
		--output-png $(GZ_PNG)

.PHONY: gz
gz: $(GZ_ARTIFACT)
	@echo "✓ GZ curve analysis complete for $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# BUOYANCY DESIGN - POSITION BOAT AT EQUILIBRIUM WITH WATER SURFACE
# ==============================================================================

BUOYANCY_DESIGN_DIR := $(SRC_DIR)/buoyancy_design
BUOYANCY_DESIGN_SOURCE := $(wildcard $(BUOYANCY_DESIGN_DIR)/*.py)
BUOYANCY_DESIGN_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).buoyancy_design.FCStd

$(BUOYANCY_DESIGN_ARTIFACT): $(DESIGN_ARTIFACT) $(BUOYANCY_ARTIFACT) $(MATERIAL_FILE) $(BUOYANCY_DESIGN_SOURCE) | $(ARTIFACT_DIR)
	@echo "Creating buoyancy design: $(BOAT).$(CONFIGURATION)"
	@if [ "$(UNAME)" = "Darwin" ]; then \
		bash $(BUOYANCY_DESIGN_DIR)/buoyancy_design_mac.sh \
			"$(DESIGN_ARTIFACT)" \
			"$(BUOYANCY_ARTIFACT)" \
			"$(MATERIAL_FILE)" \
			"$@" \
			"$(FREECAD_APP)"; \
	else \
		PYTHONPATH=$(PWD) $(FREECAD_PYTHON) -m src.buoyancy_design \
			--design $(DESIGN_ARTIFACT) \
			--buoyancy $(BUOYANCY_ARTIFACT) \
			--materials $(MATERIAL_FILE) \
			--output $@; \
	fi

.PHONY: buoyancy-design
buoyancy-design: $(BUOYANCY_DESIGN_ARTIFACT)
	@echo "✓ Buoyancy design complete for $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# BUOYANCY RENDER - RENDER IMAGES OF BOAT AT EQUILIBRIUM
# ==============================================================================

.PHONY: buoyancy-render
buoyancy-render: $(BUOYANCY_DESIGN_ARTIFACT) $(RENDER_SOURCE)
	@echo "Rendering buoyancy images from $(BUOYANCY_DESIGN_ARTIFACT)..."
	@if [ "$(UNAME)" = "Darwin" ]; then \
		$(RENDER_DIR)/render_mac.sh "$(BUOYANCY_DESIGN_ARTIFACT)" "$(ARTIFACT_DIR)" "$(FREECAD_APP)"; \
	else \
		FCSTD_FILE="$(BUOYANCY_DESIGN_ARTIFACT)" IMAGE_DIR="$(ARTIFACT_DIR)" freecad-python -m src.render; \
	fi
	@echo "Cropping images with ImageMagick..."
	@if command -v convert >/dev/null 2>&1; then \
		for img in $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).buoyancy_design.render.*.png; do \
			if [ -f "$$img" ]; then \
				convert "$$img" -fuzz 1% -trim +repage -bordercolor \#C6D2FF -border 25 "$$img" || true; \
			fi \
		done; \
		echo "Cropping complete!"; \
	else \
		echo "ImageMagick not found, skipping crop"; \
	fi
	@echo "✓ Buoyancy render complete for $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# STRUCTURAL VALIDATION
# ==============================================================================

VALIDATE_STRUCTURE_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).validate_structure.json

$(VALIDATE_STRUCTURE_ARTIFACT): $(PARAMETER_ARTIFACT) $(MASS_ARTIFACT) $(GZ_ARTIFACT) | $(ARTIFACT_DIR)
	@echo "Running structural validation: $(BOAT).$(CONFIGURATION)"
	@python3 -m shipshape.validate_structure \
		--parameters $(PARAMETER_ARTIFACT) \
		--mass $(MASS_ARTIFACT) \
		--gz $(GZ_ARTIFACT) \
		--output $@

.PHONY: validate-structure
validate-structure: $(VALIDATE_STRUCTURE_ARTIFACT)
	@echo "✓ Structural validation complete for $(BOAT).$(CONFIGURATION)"

# ==============================================================================
# LINES PLAN - TRADITIONAL NAVAL ARCHITECTURE DRAWINGS
# ==============================================================================

LINES_DIR := $(SRC_DIR)/lines
LINES_SOURCE := $(wildcard $(LINES_DIR)/*.py)
LINES_ARTIFACT := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).lines.FCStd
LINES_TEX := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).lines.tex
LINES_PDF := $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).lines.pdf

$(LINES_ARTIFACT) $(LINES_TEX): $(DESIGN_ARTIFACT) $(PARAMETER_ARTIFACT) $(LINES_SOURCE) | $(ARTIFACT_DIR)
	@echo "Generating lines plan: $(BOAT).$(CONFIGURATION)"
	@if [ "$(UNAME)" = "Darwin" ]; then \
		bash $(LINES_DIR)/lines_mac.sh \
			"$(DESIGN_ARTIFACT)" \
			"$(PARAMETER_ARTIFACT)" \
			"$(ARTIFACT_DIR)" \
			"$(FREECAD_APP)"; \
	else \
		PYTHONPATH=$(PWD) \
		DESIGN_FILE=$(DESIGN_ARTIFACT) \
		PARAMETER_FILE=$(PARAMETER_ARTIFACT) \
		OUTPUT_DIR=$(ARTIFACT_DIR) \
		$(FREECAD_PYTHON) -m src.lines; \
	fi

.PHONY: lines
lines: $(LINES_ARTIFACT)
	@echo "✓ Lines plan complete for $(BOAT).$(CONFIGURATION)"

$(LINES_PDF): $(LINES_TEX)
	@echo "Converting SVGs to PDF for LaTeX inclusion..."
	@for svg in $(ARTIFACT_DIR)/$(BOAT).$(CONFIGURATION).lines.*.svg; do \
		if [ -f "$$svg" ]; then \
			pdf=$${svg%.svg}.pdf; \
			if command -v rsvg-convert >/dev/null 2>&1; then \
				rsvg-convert -f pdf -o "$$pdf" "$$svg" 2>/dev/null || true; \
			elif command -v inkscape >/dev/null 2>&1; then \
				inkscape "$$svg" --export-filename="$$pdf" 2>/dev/null || true; \
			fi; \
		fi; \
	done
	@echo "Compiling lines plan LaTeX: $(BOAT).$(CONFIGURATION)"
	@cd $(ARTIFACT_DIR) && pdflatex -interaction=nonstopmode $(notdir $(LINES_TEX)) || true
	@cd $(ARTIFACT_DIR) && pdflatex -interaction=nonstopmode $(notdir $(LINES_TEX)) || true
	@if [ -f "$(LINES_PDF)" ]; then \
		echo "✓ Lines plan PDF: $(LINES_PDF)"; \
	else \
		echo "Warning: PDF generation failed (pdflatex may not be installed)"; \
	fi

.PHONY: lines-pdf
lines-pdf: $(LINES_PDF)
	@echo "✓ Lines plan PDF complete for $(BOAT).$(CONFIGURATION)"
