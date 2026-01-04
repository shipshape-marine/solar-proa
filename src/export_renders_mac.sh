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

# Create a temporary Python script
TEMP_SCRIPT=$(mktemp /tmp/freecad_render_XXXXXX.py)

cat > "$TEMP_SCRIPT" << 'EOF'
import FreeCAD
import FreeCADGui
import sys
import os

# Material color mapping (RGB 0-1 scale)
MATERIAL_COLORS = {
    'aluminum': (0.75, 0.75, 0.75),          # Light gray
    'plywood': (0.82, 0.71, 0.55),           # Wood tan
    'marine_plywood': (0.82, 0.71, 0.55),    # Wood tan
    'foam': (1.0, 0.85, 0.0),                # Safety yellow
    'solar_panels': (0.1, 0.1, 0.35),        # Dark blue
    'stainless_steel': (0.85, 0.85, 0.87),   # Bright metallic
    'steel': (0.6, 0.6, 0.62),               # Dark metallic
    'pvc': (0.95, 0.95, 0.95),               # Off-white
    'rope': (0.9, 0.8, 0.5),                 # Tan/beige
    'canvas': (0.95, 0.92, 0.85),            # Off-white/cream
}

def get_material_from_label(label):
    """Extract material name from object label like 'Deck__plywood_001'"""
    label_lower = label.lower()
    if '__' in label_lower:
        parts = label_lower.split('__')
        if len(parts) >= 2:
            # Handle cases like "Deck__plywood_001" - extract just "plywood"
            mat_key = parts[1].rstrip('_0123456789').strip()
            return mat_key
    return None

def apply_colors_to_objects(doc):
    """Apply material-based colors to all objects"""
    
    def process_objects(obj_list):
        for obj in obj_list:
            # Color this object
            if hasattr(obj, 'ViewObject') and obj.ViewObject:
                mat_key = get_material_from_label(obj.Label)
                if mat_key and mat_key in MATERIAL_COLORS:
                    try:
                        obj.ViewObject.ShapeColor = MATERIAL_COLORS[mat_key]
                        obj.ViewObject.Transparency = 0
                        # Use Shaded mode for better rendering
                        if hasattr(obj.ViewObject, 'DisplayMode'):
                            obj.ViewObject.DisplayMode = "Shaded"
                        print(f"  Colored {obj.Label} as {mat_key}: {MATERIAL_COLORS[mat_key]}")
                    except Exception as e:
                        print(f"  Warning: Could not color {obj.Label}: {e}")
            
            # Recurse into groups
            if hasattr(obj, 'Group'):
                process_objects(obj.Group)
    
    process_objects(doc.Objects)

# Get arguments
filepath = sys.argv[-3]
output_dir = sys.argv[-2]
base_name = sys.argv[-1]

print(f"Opening {filepath}...")
doc = FreeCAD.openDocument(filepath)

# Apply material-based colors
print("Applying material colors...")
apply_colors_to_objects(doc)
doc.recompute()

# Define views to export
views = [
    ('Isometric', 'viewIsometric'),
    ('Front', 'viewFront'),
    ('Top', 'viewTop'),
    ('Right', 'viewRight'),
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
    output_path = os.path.join(output_dir, f"{base_name}_{view_name}.png")
    view.saveImage(output_path, 1920, 1080, 'White')
    
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
ACTUAL_RENDERS=$(ls "$OUTPUT_DIR"/${BASENAME}_*.png 2>/dev/null | wc -l | tr -d ' ')

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

