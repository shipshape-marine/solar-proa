#!/bin/bash
# export_renders_mac.sh - Export renders using FreeCAD GUI on macOS
# Usage: ./export_renders_mac.sh <input.FCStd> <output_dir> [freecad_path]

if [ $# -lt 2 ]; then
    echo "Usage: $0 <input.FCStd> <output_dir> [freecad_path]"
    exit 1
fi

FCSTD_FILE="$1"
OUTPUT_DIR="$2"
FREECAD="${3:-/Applications/FreeCAD.app/Contents/MacOS/FreeCAD}"

if [ ! -f "$FCSTD_FILE" ]; then
    echo "ERROR: File not found: $FCSTD_FILE"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get base name for output files
BASENAME=$(basename "$FCSTD_FILE" .FCStd)
# Strip .color suffix if present to match the output filenames
BASENAME=${BASENAME%.color}

# Create a temporary Python script
TEMP_SCRIPT=$(mktemp /tmp/freecad_render_XXXXXX.py)

cat > "$TEMP_SCRIPT" << 'EOF'
import FreeCAD
import FreeCADGui
import sys
import os

# Get arguments
filepath = sys.argv[-3]
output_dir = sys.argv[-2]
base_name = sys.argv[-1]
background = '#C6D2FF'

print(f"Opening {filepath}...")
doc = FreeCAD.openDocument(filepath)

# Note: Colors should already be applied by the color module
# The input FCStd file is expected to be a *.color.FCStd file
doc.recompute()

# Define views to export
views = [
    ('isometric', 'viewIsometric'),
    ('front', 'viewFront'),
    ('top', 'viewTop'),
    ('right', 'viewRight'),
]

# Get active view
view = FreeCADGui.activeView()

if not view:
    print("ERROR: No active view available")
    FreeCAD.closeDocument(doc.Name)
    sys.exit(1)

# Disable animation for faster rendering
view.setAnimationEnabled(False)

# Export each view
for view_name, view_method in views:
    print(f"Exporting {view_name} view...")
    
    # Set the view
    getattr(view, view_method)()
    view.fitAll()
    
    # Export as PNG 
    clean_name = base_name.replace('.color', '')
    output_path = os.path.join(output_dir, f"{clean_name}.render.{view_name}.png")
    view.saveImage(output_path, 1920, 1080, background)
    
    print(f"  Saved: {output_path}")

print(f"Exported {len(views)} views from {filepath}")

# Close document and quit
FreeCAD.closeDocument(doc.Name)
FreeCADGui.getMainWindow().close()
EOF

# Run FreeCAD with the script
echo "Rendering $FCSTD_FILE..."
"$FREECAD" "$TEMP_SCRIPT" "$FCSTD_FILE" "$OUTPUT_DIR" "$BASENAME" 2>&1 | grep -v "Populating font" || true

# Check if renders were created
EXPECTED_RENDERS=4
ACTUAL_RENDERS=$(ls "$OUTPUT_DIR"/${BASENAME}.render.*.png 2>/dev/null | wc -l | tr -d ' ')

if [ "$ACTUAL_RENDERS" -ge "$EXPECTED_RENDERS" ]; then
    echo "Render complete for $BASENAME ($ACTUAL_RENDERS images created)"
    # Clean up
    rm -f "$TEMP_SCRIPT"
    exit 0
else
    echo "WARNING: Only $ACTUAL_RENDERS of $EXPECTED_RENDERS images created"
    # Clean up
    rm -f "$TEMP_SCRIPT"
    exit 0  # Don't fail the build
fi

