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

# Create temp files for script and config
TEMP_SCRIPT=$(mktemp /tmp/freecad_render.XXXXXX)
mv "$TEMP_SCRIPT" "${TEMP_SCRIPT}.py"
TEMP_SCRIPT="${TEMP_SCRIPT}.py"

TEMP_CONFIG=$(mktemp /tmp/freecad_render_config.XXXXXX)
mv "$TEMP_CONFIG" "${TEMP_CONFIG}.txt"
TEMP_CONFIG="${TEMP_CONFIG}.txt"

# Write config to temp file (avoid passing as FreeCAD args)
echo "$OUTPUT_DIR" > "$TEMP_CONFIG"
echo "$BASENAME" >> "$TEMP_CONFIG"

cat > "$TEMP_SCRIPT" << 'EOF'
import FreeCAD
import FreeCADGui
import sys
import os

# Get arguments from command line
filepath = sys.argv[-2]
config_path = sys.argv[-1]

# Read config from temp file
with open(config_path) as f:
    lines = f.read().strip().split('\n')
    output_dir = lines[0]
    base_name = lines[1]

background = '#C6D2FF'

# Views are embedded to avoid FreeCAD trying to open JSON file
views = [
    ('front', 'viewFront'),
    ('isometric', 'viewIsometric'),
    ('right', 'viewRight'),
    ('top', 'viewTop'),
]

print(f"Opening {filepath}...")
doc = FreeCAD.openDocument(filepath)

# Note: Colors should already be applied by the color module
# The input FCStd file is expected to be a *.color.FCStd file
doc.recompute()

print(f"Rendering {len(views)} views: {[v[0] for v in views]}")

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

# Close document and exit
FreeCAD.closeDocument(doc.Name)
os._exit(0)
EOF

# Get view.json path
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VIEWS_JSON="$SCRIPT_DIR/../../constant/view.json"

# Count expected renders from view.json
if [ -f "$VIEWS_JSON" ]; then
    EXPECTED_RENDERS=$(python3 -c "import json; print(len(json.load(open('$VIEWS_JSON'))))")
else
    EXPECTED_RENDERS=4
fi

# Run FreeCAD with the script
echo "Rendering $FCSTD_FILE..."
"$FREECAD" "$TEMP_SCRIPT" "$FCSTD_FILE" "$TEMP_CONFIG" &
FREECAD_PID=$!

# Wait up to 120 seconds for completion
for i in {1..240}; do
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

# Check if renders were created
ACTUAL_RENDERS=$(ls "$OUTPUT_DIR"/${BASENAME}.render.*.png 2>/dev/null | wc -l | tr -d ' ')

if [ "$ACTUAL_RENDERS" -ge "$EXPECTED_RENDERS" ]; then
    echo "Render complete for $BASENAME ($ACTUAL_RENDERS images created)"
    # Clean up
    rm -f "$TEMP_SCRIPT" "$TEMP_CONFIG"
    exit 0
else
    echo "WARNING: Only $ACTUAL_RENDERS of $EXPECTED_RENDERS images created"
    # Clean up
    rm -f "$TEMP_SCRIPT" "$TEMP_CONFIG"
    exit 0  # Don't fail the build
fi

