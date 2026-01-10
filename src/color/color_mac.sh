#!/bin/bash
# Apply color scheme to FreeCAD design (macOS - GUI mode required)
#
# macOS requires GUI mode to properly persist ViewObject properties.
# This script opens the design in FreeCAD GUI, applies colors, saves, and quits.

if [ $# -lt 4 ]; then
    echo "Usage: $0 <input.FCStd> <colors.json> <output.FCStd> <output.json> [freecad_path]"
    exit 1
fi

INPUT_FCSTD="$1"
COLOR_JSON="$2"
OUTPUT_FCSTD="$3"
OUTPUT_JSON="$4"
FREECAD="${5:-/Applications/FreeCAD.app/Contents/MacOS/FreeCAD}"

if [ ! -f "$INPUT_FCSTD" ]; then
    echo "ERROR: Input file not found: $INPUT_FCSTD"
    exit 1
fi

if [ ! -f "$COLOR_JSON" ]; then
    echo "ERROR: Color scheme file not found: $COLOR_JSON"
    exit 1
fi

# Create temporary Python script
TEMP_SCRIPT=$(mktemp /tmp/freecad_color_XXXXXX.py)

cat > "$TEMP_SCRIPT" << 'EOFPYTHON'
import FreeCAD
import FreeCADGui
import sys
import os
import json

def get_material_from_label(label):
    """
    Extract material from object label.
    
    Supports two formats:
    - Parentheses: "Aka_0 (aluminum)" -> "aluminum"
    - Double underscore: "Deck__plywood_001" -> "plywood"
    """
    label_lower = label.lower()
    
    # Format 1: "Component (material)"
    if '(' in label_lower:
        return label_lower.split('(')[1].rstrip(')').strip()
    
    # Format 2: "Component__material"
    if '__' in label_lower:
        parts = label_lower.split('__')
        if len(parts) >= 2:
            return parts[1].rstrip('_0123456789').strip()
    
    return None

def apply_colors(doc, color_scheme):
    """Apply color scheme to all objects"""
    materials_def = color_scheme.get('materials', {})
    stats = {
        'total_objects': 0,
        'colored_objects': 0,
        'by_material': {}
    }
    
    def process_objects(obj_list):
        for obj in obj_list:
            stats['total_objects'] += 1
            
            if hasattr(obj, 'ViewObject') and obj.ViewObject:
                mat_key = get_material_from_label(obj.Label)
                
                if mat_key and mat_key in materials_def:
                    mat_def = materials_def[mat_key]
                    
                    try:
                        # Apply color
                        if 'color' in mat_def:
                            obj.ViewObject.ShapeColor = tuple(mat_def['color'])
                        
                        # Apply transparency
                        if 'transparency' in mat_def:
                            obj.ViewObject.Transparency = mat_def['transparency']
                        
                        # Apply display mode
                        if 'display_mode' in mat_def:
                            if hasattr(obj.ViewObject, 'DisplayMode'):
                                obj.ViewObject.DisplayMode = mat_def['display_mode']
                        
                        stats['colored_objects'] += 1
                        stats['by_material'][mat_key] = stats['by_material'].get(mat_key, 0) + 1
                        
                    except Exception as e:
                        print(f"Warning: Could not color {obj.Label}: {e}")
            
            # Recurse into groups
            if hasattr(obj, 'Group'):
                process_objects(obj.Group)
    
    process_objects(doc.Objects)
    return stats

# Get arguments
input_fcstd = sys.argv[-3]
color_json = sys.argv[-2]
output_fcstd = sys.argv[-1]

# Load color scheme
print(f"Loading color scheme: {color_json}")
with open(color_json, 'r') as f:
    color_scheme = json.load(f)

scheme_name = color_scheme.get('scheme_name', 'Unknown')
print(f"  Scheme: {scheme_name}")
print(f"  Materials defined: {len(color_scheme.get('materials', {}))}")

# Open design
print(f"Opening design: {input_fcstd}")
doc = FreeCAD.openDocument(input_fcstd)

# Apply colors
print("Applying colors...")
stats = apply_colors(doc, color_scheme)
doc.recompute()

# Save colored design
print(f"Saving colored design: {output_fcstd}")
doc.saveAs(output_fcstd)

print(f"✓ Color application complete")
print(f"  Total objects: {stats['total_objects']}")
print(f"  Colored objects: {stats['colored_objects']}")
print(f"  Materials used: {len(stats['by_material'])}")
for mat, count in sorted(stats['by_material'].items()):
    print(f"    {mat}: {count}")

# Close and quit
FreeCAD.closeDocument(doc.Name)
os._exit(0)
EOFPYTHON

# Run FreeCAD with the script
echo "Running FreeCAD to apply colors..."
"$FREECAD" "$TEMP_SCRIPT" "$INPUT_FCSTD" "$COLOR_JSON" "$OUTPUT_FCSTD" &
FREECAD_PID=$!

# Wait up to 30 seconds for completion
for i in {1..60}; do
    if ! kill -0 $FREECAD_PID 2>/dev/null; then
        break
    fi
    sleep 0.5
done

# Force kill if still running
if kill -0 $FREECAD_PID 2>/dev/null; then
    echo "Warning: FreeCAD did not exit cleanly, forcing..."
    kill -9 $FREECAD_PID 2>/dev/null
fi

# Clean up
rm -f "$TEMP_SCRIPT"

# Verify output was created
if [ ! -f "$OUTPUT_FCSTD" ]; then
    echo "ERROR: Colored design was not created"
    exit 1
fi

echo "✓ Color application complete"
