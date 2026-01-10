# Color Module

The color module applies material-based color schemes to FreeCAD designs. Colors, transparency, and display modes are defined in JSON files and applied based on material annotations in object labels.

## Overview

**Pipeline**: `design.FCStd` → `color module` → `color.FCStd` → `render module` → `PNG images`

The color module is a separate processing step that:
1. Reads a color scheme from JSON
2. Applies colors, transparency, and display modes to objects based on their materials
3. Saves a colored version of the design (`.color.FCStd`)
4. Generates a JSON artifact with statistics

## Usage

### Apply Colors to a Design

```bash
# Apply default color scheme
make color BOAT=rp2 CONFIGURATION=closehaul

# Apply specific color scheme
make color BOAT=rp2 CONFIGURATION=closehaul COLOR_SCHEME=wiring_view

# Apply colors to all existing designs
make color-all

# Apply specific scheme to all designs
make color-all COLOR_SCHEME=proa
```

### Generated Files

For `rp2.closehaul` with `proa` color scheme:
- `artifacts/rp2.closehaul.color.FCStd` - Colored FreeCAD design
- `artifacts/rp2.closehaul.color.json` - Statistics artifact

## Color Scheme Format

Color schemes are defined in `constants/colors/*.json`:

```json
{
  "scheme_name": "Proa Standard Colors",
  "description": "Default color scheme for solar proa visualizations",
  "version": "1.0",
  "materials": {
    "aluminum": {
      "color": [0.75, 0.75, 0.78],
      "transparency": 0,
      "display_mode": "Shaded",
      "description": "Structural aluminum tubes and profiles"
    },
    "plywood": {
      "color": [0.76, 0.60, 0.42],
      "transparency": 0,
      "display_mode": "Shaded",
      "description": "Marine plywood decking and structure"
    }
  }
}
```

### Color Scheme Properties

- **color**: RGB values from 0.0 to 1.0
- **transparency**: Integer from 0 (opaque) to 100 (fully transparent)
- **display_mode**: FreeCAD display mode (e.g., "Shaded", "Wireframe", "Flat Lines")

## Material Detection

The color module extracts material names from object labels using two formats:

### Format 1: Parentheses (legacy)
```
"Aka_0 (aluminum)" → material: "aluminum"
"Stanchion_2 (steel)" → material: "steel"
```

### Format 2: Double Underscore (preferred)
```
"Deck__plywood_001" → material: "plywood"
"Hull__marine_plywood" → material: "marine_plywood"
```

Both formats are case-insensitive and trailing numbers are stripped.

## Available Color Schemes

### `proa.json` (Default)
Standard color scheme for regular visualization. All materials opaque, realistic colors.

### `wiring_view.json` (Specialized)
Transparent hull view for showing electrical systems:
- Structure (aluminum, plywood): 80% transparent
- Hull exterior: 90% transparent
- Electrical components (wires, batteries, solar panels): Opaque with high-contrast colors

## Creating Custom Color Schemes

1. Create a new JSON file in `constants/colors/`
2. Define materials used in your designs
3. Set appropriate color, transparency, and display mode
4. Use it: `make color COLOR_SCHEME=your_scheme`

### Example: High Contrast Scheme

```json
{
  "scheme_name": "High Contrast",
  "description": "High contrast colors for presentations",
  "version": "1.0",
  "materials": {
    "aluminum": {
      "color": [0.2, 0.2, 0.8],
      "transparency": 0,
      "display_mode": "Shaded"
    },
    "plywood": {
      "color": [0.8, 0.5, 0.1],
      "transparency": 0,
      "display_mode": "Shaded"
    }
  }
}
```

## Platform Differences

### Linux
- Uses `freecad-python` in headless mode
- Colors applied via `color.py` script
- Fast and reliable

### macOS
- Requires GUI mode to persist ViewObject properties
- Uses `color_mac.sh` wrapper script
- Opens FreeCAD, applies colors, saves, quits
- Takes longer but produces identical results

## Integration with Build Pipeline

The color module is integrated into the Makefile dependency chain:

```
parameters.json
    ↓
design.FCStd
    ↓
color.FCStd  ← color scheme JSON
    ↓
render PNGs
```

Renders automatically depend on colored designs. If you run `make render`, it will:
1. Generate parameters (if needed)
2. Generate design (if needed)
3. Apply colors (if needed)
4. Render images

## Statistics Artifact

The `.color.json` artifact contains:

```json
{
  "validator": "color",
  "input_design": "artifacts/rp2.closehaul.design.FCStd",
  "output_design": "artifacts/rp2.closehaul.color.FCStd",
  "color_scheme_file": "constants/colors/proa.json",
  "color_scheme_name": "Proa Standard Colors",
  "statistics": {
    "total_objects": 150,
    "colored_objects": 142,
    "by_material": {
      "aluminum": 45,
      "plywood": 38,
      "steel": 29,
      "solar_panel": 18,
      "canvas": 12
    }
  }
}
```

## Troubleshooting

### No colors appear in renders

Check:
1. Does the object label include material? (e.g., "Aka_0 (aluminum)")
2. Is the material defined in the color scheme JSON?
3. Does the colored FCStd exist? (`artifacts/*.color.FCStd`)
4. Are you rendering the `.color.FCStd` file (not `.design.FCStd`)?

### Some objects not colored

Check the statistics in the `.color.json` artifact to see which materials were found and colored. Objects without material annotations or with undefined materials won't be colored.

### macOS color application hangs

The `color_mac.sh` script has a 30-second timeout. If it hangs:
1. Check if FreeCAD is installed at the expected path
2. Try running FreeCAD manually to verify it works
3. Check for FreeCAD processes that didn't exit cleanly

## Future Enhancements

Potential future features:
- Material-specific transparency for "exploded" views
- Animation support for rotating/transparency transitions
- Color validation (warn if materials in design aren't in scheme)
- Color scheme inheritance (extend base schemes)
- Per-object color overrides for special highlighting
