---
layout: default
title: Under the Hood - Technical Details
---

# Under the Hood

How the Solar Proa CAD system works.

[← Back to Home]({{ '/' | relative_url }})

---

## Parametric Design

All vessel designs are created using **parametric CAD modeling** - the geometry is defined by parameters (dimensions, angles, positions) rather than fixed shapes. This means:

- **Change one parameter, update the entire model** - Adjusting the hull length automatically scales masts, crossbeams, and rigging
- **Multiple configurations from one source** - The same base model generates beaching, close-haul, broad reach, and other sailing configurations
- **Design transparency** - Every dimension is traceable to a parameter value

The system uses [FreeCAD](https://www.freecad.org/) (open-source CAD) with Python scripts that read parameter files, build the 3D geometry, and export renders and CAD files.

---

## Build Pipeline

The build process transforms parameter files into website-ready outputs through a series of stages:

<div style="text-align: center; margin: 2em 0;">
  <img src="{{ '/dependency_graph.png' | relative_url }}" alt="Build Pipeline Dependency Graph" style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px; padding: 1em; background: white;">
  <p style="color: #666; font-size: 0.9em; margin-top: 0.5em;">Dependency graph auto-generated from Makefile</p>
</div>

**Stage descriptions:**

| Stage | Input | Output | Description |
|-------|-------|--------|-------------|
| **parameter** | Boat JSON + Configuration JSON | Merged parameters | Combines boat dimensions with sail configuration (shipshape + project plugin) |
| **design** | Parameters | FreeCAD model (.FCStd) | Builds the 3D geometry from parameters |
| **mass** | Design (FreeCAD) | Mass properties JSON | Calculates volumes, masses, and buoyancy (shipshape) |
| **color** | Design (FreeCAD) | Colored design | Applies materials and colors for rendering |
| **buoyancy** | Design (FreeCAD), Mass properties | Buoyancy properties | Finds equilibrium pose using Newton-Raphson iteration (shipshape) |
| **gz** | Design (FreeCAD), Buoyancy | GZ curve JSON + PNG | Computes righting-arm curve over heel angles (shipshape) |
| **render** | Colored design (FreeCAD) | PNG images | Generates isometric, top, front, right views |
| **step** | FreeCAD model | STEP file | Exports universal CAD format |
| **validate** | Parameters, Mass, GZ | Validation JSON | Structural validation: aka, mast, spine, capsize analysis |

---

## Configurations

Each sailing configuration is defined by a JSON file that specifies sail angles, rig rotations, and other dynamic parameters:

```
constant/configuration/
├── beaching.json      # Sails down, on shore
├── beamreach.json     # Cross-wind sailing
├── broadreach.json    # Downwind sailing
├── closehaul.json     # Upwind sailing
├── closehaulreefed.json  # Heavy weather
└── goosewing.json     # Running downwind
```

The build system generates all combinations of boats × configurations automatically.

**Current configurations:**

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; margin: 1em 0;">
{% for config in site.data.configurations %}
  <div style="border: 1px solid #ddd; padding: 1em; border-radius: 4px;">
    <strong>{{ config.display_name }}</strong>
    <p style="font-size: 0.85em; color: #666; margin: 0.5em 0 0 0;">{{ config.description }}</p>
  </div>
{% endfor %}
</div>

---

## Automation

Every push to the main branch triggers a GitHub Actions workflow that:

1. **Builds all FreeCAD models** for each boat × configuration combination
2. **Generates renders** (PNG images from multiple camera angles)
3. **Exports STEP files** for CAD interchange
4. **Calculates mass properties** and validates buoyancy
5. **Builds the Jekyll site** with all generated assets
6. **Deploys to GitHub Pages** at [solarproa.org](https://solarproa.org)

This ensures the website always reflects the current state of the CAD models - renders, specifications, and downloads are never out of sync.

---

## Repository Structure

Design-specific code lives in this repo. Boat-independent analysis (parameter merging, mass, buoyancy, GZ curves) is provided by the [shipshape](https://github.com/shipshape-marine/shipshape) library. Structural validation lives in `src/structural/`.

```
solar-proa/
├── constant/
│   ├── boat/              # Boat parameter files (rp1.json, rp2.json, rp3.json)
│   ├── configuration/     # Sailing configurations
│   └── material/          # Material properties (density, color)
├── src/
│   ├── parameter/         # SolarProa-specific derived parameter calculations
│   ├── design/            # FreeCAD model builders (central, mirror, rotation)
│   ├── color/             # Material and color application
│   ├── render/            # Render generation
│   ├── step/              # STEP export
│   ├── lines/             # Lines plan generation
│   ├── structural/        # Structural validation (aka, mast, spine, capsize)
│   └── buoyancy_design/   # Equilibrium positioning in FreeCAD
├── artifact/              # Generated outputs (models, renders, data)
├── docs/                  # Jekyll website source
└── Makefile               # Build orchestration
```

---

## Tools & Technologies

- **[FreeCAD 1.0](https://www.freecad.org/)** - Open-source parametric CAD
- **Python 3** - Scripting and automation
- **[shipshape](https://github.com/shipshape-marine/shipshape)** - Boat-independent naval engineering library (parameter, mass, buoyancy, GZ)
- **GNU Make** - Build orchestration and dependency tracking
- **Jekyll** - Static site generation
- **GitHub Actions** - CI/CD pipeline
- **Graphviz** - Dependency graph visualization

---

## Open Source

The entire project is open source under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

**GitHub Repository:** [github.com/shipshape-marine/solar-proa](https://github.com/shipshape-marine/solar-proa)

Contributions, feedback, and forks are welcome.

---

[← Back to Home]({{ '/' | relative_url }}) | [View RP1 →]({{ '/rp1.html' | relative_url }}) | [View RP2 →]({{ '/rp2.html' | relative_url }}) | [View RP3 →]({{ '/rp3.html' | relative_url }})
