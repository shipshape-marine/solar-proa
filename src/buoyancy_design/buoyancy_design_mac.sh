#!/bin/bash
# Create buoyancy design with boat at equilibrium (macOS - GUI mode required)
#
# macOS requires GUI mode to properly persist ViewObject properties.
# This script opens the design in FreeCAD GUI, transforms it, adds water, saves, and quits.

if [ $# -lt 5 ]; then
    echo "Usage: $0 <design.FCStd> <buoyancy.json> <materials.json> <output.FCStd> [freecad_path]"
    exit 1
fi

DESIGN_FCSTD="$1"
BUOYANCY_JSON="$2"
MATERIALS_JSON="$3"
OUTPUT_FCSTD="$4"
FREECAD="${5:-/Applications/FreeCAD.app/Contents/MacOS/FreeCAD}"

if [ ! -f "$DESIGN_FCSTD" ]; then
    echo "ERROR: Design file not found: $DESIGN_FCSTD"
    exit 1
fi

if [ ! -f "$BUOYANCY_JSON" ]; then
    echo "ERROR: Buoyancy file not found: $BUOYANCY_JSON"
    exit 1
fi

if [ ! -f "$MATERIALS_JSON" ]; then
    echo "ERROR: Materials file not found: $MATERIALS_JSON"
    exit 1
fi

# Create temporary Python script
TEMP_SCRIPT=$(mktemp /tmp/freecad_buoyancy_design_XXXXXX.py)

cat > "$TEMP_SCRIPT" << 'EOFPYTHON'
import FreeCAD as App
import FreeCADGui as Gui
import Part
from FreeCAD import Base
import sys
import os
import json
import math


def load_colors(materials_path):
    """Load material colors from materials JSON file."""
    with open(materials_path) as f:
        materials = json.load(f)

    colors = {}
    for name, props in materials.get('materials', {}).items():
        if 'color' in props:
            color = props['color']
            if isinstance(color, str) and color.startswith('#'):
                r = int(color[1:3], 16) / 255.0
                g = int(color[3:5], 16) / 255.0
                b = int(color[5:7], 16) / 255.0
                colors[name] = (r, g, b)
    return colors


def apply_colors(doc, materials_path):
    """Apply colors to objects based on material labels."""
    colors = load_colors(materials_path)

    for obj in doc.Objects:
        if not hasattr(obj, 'Label'):
            continue
        if not hasattr(obj, 'ViewObject') or obj.ViewObject is None:
            continue

        label = obj.Label
        if '__' in label:
            material = label.split('__')[-1].strip('()')
            if material in colors:
                try:
                    obj.ViewObject.ShapeColor = colors[material]
                except Exception:
                    pass


def make_rotation_matrix(pitch_deg, roll_deg):
    """Create rotation matrix for pitch and roll."""
    pitch_rad = math.radians(pitch_deg)
    roll_rad = math.radians(roll_deg)

    cos_p = math.cos(pitch_rad)
    sin_p = math.sin(pitch_rad)
    cos_r = math.cos(roll_rad)
    sin_r = math.sin(roll_rad)

    matrix = Base.Matrix(
        cos_r,              sin_r * sin_p,      sin_r * cos_p,      0,
        0,                  cos_p,              -sin_p,             0,
        -sin_r,             cos_r * sin_p,      cos_r * cos_p,      0,
        0,                  0,                  0,                  1
    )
    return matrix


def transform_object(obj, z_offset, pitch_deg, roll_deg, rotation_center):
    """Transform an object by the equilibrium pose."""
    if not hasattr(obj, 'Shape') or obj.Shape.isNull():
        return

    if obj.TypeId in ('App::Part', 'App::Origin', 'App::Line', 'App::Plane'):
        return

    if not obj.TypeId.startswith('Part::'):
        return

    shape = obj.Shape.copy()

    if abs(pitch_deg) > 1e-6 or abs(roll_deg) > 1e-6 or abs(z_offset) > 1e-6:
        shape.translate(Base.Vector(-rotation_center.x, -rotation_center.y, -rotation_center.z))

        if abs(pitch_deg) > 1e-6 or abs(roll_deg) > 1e-6:
            rot_matrix = make_rotation_matrix(pitch_deg, roll_deg)
            shape = shape.transformGeometry(rot_matrix)

        shape.translate(Base.Vector(rotation_center.x, rotation_center.y,
                                    rotation_center.z + z_offset))

        obj.Shape = shape


def compute_rotation_center(doc):
    """Compute the rotation center (centroid of all shapes)."""
    total_volume = 0.0
    weighted_center = Base.Vector(0, 0, 0)

    for obj in doc.Objects:
        if not hasattr(obj, 'Shape') or obj.Shape.isNull():
            continue
        try:
            vol = obj.Shape.Volume
            if vol < 1e-6:
                continue
            cog = obj.Shape.CenterOfGravity
            total_volume += vol
            weighted_center += Base.Vector(cog.x * vol, cog.y * vol, cog.z * vol)
        except RuntimeError:
            continue

    if total_volume > 0:
        return Base.Vector(
            weighted_center.x / total_volume,
            weighted_center.y / total_volume,
            weighted_center.z / total_volume
        )
    return Base.Vector(0, 0, 0)


def get_boat_bounds(doc):
    """Get the bounding box of all objects in the document."""
    xmin = ymin = zmin = float('inf')
    xmax = ymax = zmax = float('-inf')

    for obj in doc.Objects:
        if not hasattr(obj, 'Shape') or obj.Shape.isNull():
            continue
        if not obj.TypeId.startswith('Part::'):
            continue

        bbox = obj.Shape.BoundBox
        if not bbox.isValid():
            continue

        xmin = min(xmin, bbox.XMin)
        xmax = max(xmax, bbox.XMax)
        ymin = min(ymin, bbox.YMin)
        ymax = max(ymax, bbox.YMax)
        zmin = min(zmin, bbox.ZMin)
        zmax = max(zmax, bbox.ZMax)

    if xmin == float('inf'):
        return {
            'xmin': -5000, 'xmax': 5000,
            'ymin': -5000, 'ymax': 5000,
            'zmin': -1000, 'zmax': 1000
        }

    return {
        'xmin': xmin, 'xmax': xmax,
        'ymin': ymin, 'ymax': ymax,
        'zmin': zmin, 'zmax': zmax
    }


def create_water_surface(doc, bounds, water_level=0.0):
    """Create a semi-transparent water surface plane."""
    margin = 1000
    width = bounds['xmax'] - bounds['xmin'] + 2 * margin
    length = bounds['ymax'] - bounds['ymin'] + 2 * margin
    thickness = 10

    if width <= 0 or length <= 0 or math.isinf(width) or math.isinf(length):
        width = 15000
        length = 15000
        x_start = -5000
        y_start = -5000
    else:
        x_start = bounds['xmin'] - margin
        y_start = bounds['ymin'] - margin

    print(f"  Water surface: width={width:.0f}, length={length:.0f}")

    water_shape = Part.makeBox(
        float(width), float(length), float(thickness),
        Base.Vector(float(x_start), float(y_start), float(water_level - thickness))
    )

    water_obj = doc.addObject("Part::Feature", "Water_Surface__water")
    water_obj.Shape = water_shape

    if hasattr(water_obj, 'ViewObject') and water_obj.ViewObject is not None:
        try:
            water_obj.ViewObject.ShapeColor = (0.2, 0.5, 0.8)
            water_obj.ViewObject.Transparency = 60
            water_obj.ViewObject.DisplayMode = "Shaded"
        except Exception:
            pass

    return water_obj


# Get arguments
design_path = sys.argv[-4]
buoyancy_path = sys.argv[-3]
materials_path = sys.argv[-2]
output_path = sys.argv[-1]

# Load buoyancy data
print(f"Loading buoyancy data: {buoyancy_path}")
with open(buoyancy_path) as f:
    buoyancy = json.load(f)

eq = buoyancy['equilibrium']
z_offset = eq['z_offset_mm']
pitch_deg = eq['pitch_deg']
roll_deg = eq['roll_deg']

print(f"Equilibrium pose: z={z_offset:.1f}mm, pitch={pitch_deg:.2f}, roll={roll_deg:.2f}")

# Open design
print(f"Opening design: {design_path}")
doc = App.openDocument(design_path)

# Compute rotation center
rotation_center = compute_rotation_center(doc)
print(f"Rotation center: ({rotation_center.x:.1f}, {rotation_center.y:.1f}, {rotation_center.z:.1f})")

# Transform all objects
print("Transforming boat to equilibrium pose...")
objects_to_transform = [obj for obj in doc.Objects
                       if hasattr(obj, 'Shape') and not obj.Shape.isNull()]

for obj in objects_to_transform:
    transform_object(obj, z_offset, pitch_deg, roll_deg, rotation_center)

# Get bounds after transformation
bounds = get_boat_bounds(doc)
print(f"Boat bounds: x=[{bounds['xmin']:.0f}, {bounds['xmax']:.0f}], "
      f"y=[{bounds['ymin']:.0f}, {bounds['ymax']:.0f}], "
      f"z=[{bounds['zmin']:.0f}, {bounds['zmax']:.0f}]")

# Create water surface
print("Creating water surface...")
create_water_surface(doc, bounds, water_level=0.0)

# Apply colors
print("Applying colors...")
apply_colors(doc, materials_path)

# Recompute
doc.recompute()

# Save
print(f"Saving buoyancy design: {output_path}")
doc.saveAs(output_path)

print(f"Buoyancy design saved to {output_path}")

# Close and quit
App.closeDocument(doc.Name)
os._exit(0)
EOFPYTHON

# Run FreeCAD with the script
echo "Running FreeCAD to create buoyancy design..."
"$FREECAD" "$TEMP_SCRIPT" "$DESIGN_FCSTD" "$BUOYANCY_JSON" "$MATERIALS_JSON" "$OUTPUT_FCSTD" &
FREECAD_PID=$!

# Wait up to 60 seconds for completion
for i in {1..120}; do
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
    echo "ERROR: Buoyancy design was not created"
    exit 1
fi

echo "Buoyancy design complete"
