#!/bin/bash
# Fix visibility in a FreeCAD file by opening and saving in GUI mode

if [ $# -lt 1 ]; then
    echo "Usage: $0 <file.FCStd>"
    exit 1
fi

FCSTD_FILE="$1"
FREECAD="${2:-/Applications/FreeCAD.app/Contents/MacOS/FreeCAD}"

# Create a temporary Python script
TEMP_SCRIPT=$(mktemp /tmp/freecad_fix_XXXXX.py)

cat > "$TEMP_SCRIPT" << 'EOF'
import FreeCAD
import FreeCADGui
import sys

filepath = sys.argv[-1]
print(f"Opening {filepath}...")

doc = FreeCAD.openDocument(filepath)

def make_visible(obj_list):
    """Recursively make all objects visible"""
    for obj in obj_list:
        try:
            if hasattr(obj, 'ViewObject') and obj.ViewObject:
                obj.ViewObject.Visibility = True
        except:
            pass
        # Recurse into groups
        if hasattr(obj, 'Group') and obj.Group:
            make_visible(obj.Group)

print("Setting visibility...")
make_visible(doc.Objects)

print("Saving...")
doc.save()

print("Done!")
FreeCAD.closeDocument(doc.Name)
EOF

# Run FreeCAD with the script
"$FREECAD" "$TEMP_SCRIPT" "$FCSTD_FILE"

# Clean up
rm -f "$TEMP_SCRIPT"
