#!/usr/bin/env python3
"""
Buoyancy design - creates a design with the boat at its equilibrium waterline.

Takes a design FCStd and buoyancy.json, outputs a new FCStd with:
1. Boat positioned at equilibrium (z-offset, pitch, roll)
2. Semi-transparent water surface at z=0
3. Waterline clearly visible

Usage:
    python -m src.buoyancy_design \
        --design artifact/boat.design.FCStd \
        --buoyancy artifact/boat.buoyancy.json \
        --materials constant/material/proa.json \
        --output artifact/boat.buoyancy_design.FCStd
"""

import sys
import os
import json
import argparse
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    import FreeCAD as App
    import Part
    from FreeCAD import Base
except ImportError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("This script must be run with FreeCAD's Python", file=sys.stderr)
    sys.exit(1)


def load_colors(materials_path: str) -> dict:
    """Load material colors from materials JSON file."""
    with open(materials_path) as f:
        materials = json.load(f)

    colors = {}
    for name, props in materials.get('materials', {}).items():
        if 'color' in props:
            color = props['color']
            # Convert hex color to RGB tuple (0-1 range)
            if isinstance(color, str) and color.startswith('#'):
                r = int(color[1:3], 16) / 255.0
                g = int(color[3:5], 16) / 255.0
                b = int(color[5:7], 16) / 255.0
                colors[name] = (r, g, b)
    return colors


def apply_colors(doc, materials_path: str):
    """Apply colors to objects based on material labels."""
    colors = load_colors(materials_path)

    for obj in doc.Objects:
        if not hasattr(obj, 'Label'):
            continue
        if not hasattr(obj, 'ViewObject') or obj.ViewObject is None:
            continue

        label = obj.Label
        # Extract material from label (format: "ComponentName__material_name")
        if '__' in label:
            material = label.split('__')[-1].strip('()')
            if material in colors:
                try:
                    obj.ViewObject.ShapeColor = colors[material]
                except Exception:
                    pass  # GUI not available in console mode


def make_rotation_matrix(pitch_deg: float, roll_deg: float) -> Base.Matrix:
    """
    Create rotation matrix for pitch and roll.

    Pitch: rotation about X axis (positive = bow up)
    Roll: rotation about Y axis (positive = starboard down)

    R = Ry(roll) * Rx(pitch)
    """
    pitch_rad = math.radians(pitch_deg)
    roll_rad = math.radians(roll_deg)

    cos_p = math.cos(pitch_rad)
    sin_p = math.sin(pitch_rad)
    cos_r = math.cos(roll_rad)
    sin_r = math.sin(roll_rad)

    # Combined rotation matrix: R = Ry(roll) * Rx(pitch)
    matrix = Base.Matrix(
        cos_r,              sin_r * sin_p,      sin_r * cos_p,      0,
        0,                  cos_p,              -sin_p,             0,
        -sin_r,             cos_r * sin_p,      cos_r * cos_p,      0,
        0,                  0,                  0,                  1
    )

    return matrix


def transform_object(obj, z_offset: float, pitch_deg: float, roll_deg: float,
                     rotation_center: Base.Vector):
    """
    Transform an object by the equilibrium pose.

    1. Translate to rotation center
    2. Apply rotation
    3. Translate back
    4. Apply z offset
    """
    if not hasattr(obj, 'Shape') or obj.Shape.isNull():
        return

    # Skip container objects (App::Part, etc.) that have read-only Shape
    if obj.TypeId in ('App::Part', 'App::Origin', 'App::Line', 'App::Plane'):
        return

    # Only process Part::Feature objects that have writable shapes
    if not obj.TypeId.startswith('Part::'):
        return

    shape = obj.Shape.copy()

    # Only transform if there's actual rotation or displacement
    if abs(pitch_deg) > 1e-6 or abs(roll_deg) > 1e-6 or abs(z_offset) > 1e-6:
        # Translate to rotation center
        shape.translate(Base.Vector(-rotation_center.x, -rotation_center.y, -rotation_center.z))

        # Apply rotation
        if abs(pitch_deg) > 1e-6 or abs(roll_deg) > 1e-6:
            rot_matrix = make_rotation_matrix(pitch_deg, roll_deg)
            shape = shape.transformGeometry(rot_matrix)

        # Translate back and apply z offset
        shape.translate(Base.Vector(rotation_center.x, rotation_center.y,
                                    rotation_center.z + z_offset))

        obj.Shape = shape


def compute_rotation_center(doc) -> Base.Vector:
    """
    Compute the rotation center (centroid of all shapes).
    This should match what the buoyancy solver uses.
    """
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
            # Skip shapes that can't compute center of gravity (lines, curves, etc.)
            continue

    if total_volume > 0:
        return Base.Vector(
            weighted_center.x / total_volume,
            weighted_center.y / total_volume,
            weighted_center.z / total_volume
        )
    return Base.Vector(0, 0, 0)


def create_water_surface(doc, bounds: dict, water_level: float = 0.0):
    """
    Create a semi-transparent water surface plane.

    Args:
        doc: FreeCAD document
        bounds: Dictionary with xmin, xmax, ymin, ymax from boat bounding box
        water_level: Z coordinate of water surface (default 0)
    """
    # Extend water surface beyond boat bounds
    margin = 1000  # mm
    width = bounds['xmax'] - bounds['xmin'] + 2 * margin
    length = bounds['ymax'] - bounds['ymin'] + 2 * margin
    thickness = 25  # Slab thickness for visible waterline edge

    # Validate dimensions
    if width <= 0 or length <= 0 or math.isinf(width) or math.isinf(length):
        print(f"Warning: Invalid bounds for water surface: {bounds}")
        # Use default large water surface
        width = 15000
        length = 15000
        x_start = -5000
        y_start = -5000
    else:
        x_start = bounds['xmin'] - margin
        y_start = bounds['ymin'] - margin

    print(f"  Water surface: width={width:.0f}, length={length:.0f}, x_start={x_start:.0f}, y_start={y_start:.0f}")

    # Create water as a thin box just below water level
    water_shape = Part.makeBox(
        float(width), float(length), float(thickness),
        Base.Vector(float(x_start), float(y_start), float(water_level - thickness))
    )

    water_obj = doc.addObject("Part::Feature", "Water_Surface__water")
    water_obj.Shape = water_shape

    # Set visual properties (only if GUI is available)
    if hasattr(water_obj, 'ViewObject') and water_obj.ViewObject is not None:
        try:
            water_obj.ViewObject.ShapeColor = (0.2, 0.5, 0.8)  # Ocean blue
            water_obj.ViewObject.Transparency = 60
            water_obj.ViewObject.DisplayMode = "Shaded"
        except Exception:
            pass  # GUI not available in console mode

    return water_obj


def get_boat_bounds(doc) -> dict:
    """Get the bounding box of hull objects near the waterline.

    Only considers objects that intersect the waterline zone (z between
    -2000 and +2000mm), so masts, rigging, and other above-deck structures
    don't inflate the water surface dimensions.
    """
    xmin = ymin = zmin = float('inf')
    xmax = ymax = zmax = float('-inf')

    waterline_zone_min = -2000  # mm
    waterline_zone_max = 2000   # mm

    for obj in doc.Objects:
        if not hasattr(obj, 'Shape') or obj.Shape.isNull():
            continue

        # Skip non-geometric objects
        if not obj.TypeId.startswith('Part::'):
            continue

        # Skip indicator objects (direction arrows) from bounds
        name = obj.Label or obj.Name
        if '_indicator' in name:
            continue

        bbox = obj.Shape.BoundBox
        if not bbox.isValid():
            continue

        # Only include objects that intersect the waterline zone
        if bbox.ZMin > waterline_zone_max or bbox.ZMax < waterline_zone_min:
            continue

        xmin = min(xmin, bbox.XMin)
        xmax = max(xmax, bbox.XMax)
        ymin = min(ymin, bbox.YMin)
        ymax = max(ymax, bbox.YMax)
        zmin = min(zmin, bbox.ZMin)
        zmax = max(zmax, bbox.ZMax)

    # Return default bounds if no valid shapes found
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


def create_buoyancy_design(design_path: str, buoyancy_path: str,
                           materials_path: str, output_path: str,
                           verbose: bool = True):
    """
    Create a buoyancy design with boat at equilibrium.

    Args:
        design_path: Path to input FCStd design file
        buoyancy_path: Path to buoyancy.json with equilibrium data
        materials_path: Path to materials JSON for coloring
        output_path: Path for output FCStd file
        verbose: Print progress information
    """
    # Load buoyancy data
    with open(buoyancy_path) as f:
        buoyancy = json.load(f)

    eq = buoyancy['equilibrium']
    z_offset = eq['z_offset_mm']
    pitch_deg = eq['pitch_deg']
    roll_deg = eq['roll_deg']

    if verbose:
        print(f"Equilibrium pose: z={z_offset:.1f}mm, pitch={pitch_deg:.2f}°, roll={roll_deg:.2f}°")

    # Open design document
    if verbose:
        print(f"Opening design: {design_path}")
    doc = App.openDocument(design_path)

    # Compute rotation center (must match buoyancy solver)
    rotation_center = compute_rotation_center(doc)
    if verbose:
        print(f"Rotation center: ({rotation_center.x:.1f}, {rotation_center.y:.1f}, {rotation_center.z:.1f})")

    # Transform all objects to equilibrium pose
    if verbose:
        print("Transforming boat to equilibrium pose...")

    objects_to_transform = [obj for obj in doc.Objects
                           if hasattr(obj, 'Shape') and not obj.Shape.isNull()]

    for obj in objects_to_transform:
        transform_object(obj, z_offset, pitch_deg, roll_deg, rotation_center)

    # Get bounds after transformation
    bounds = get_boat_bounds(doc)
    if verbose:
        print(f"Boat bounds: x=[{bounds['xmin']:.0f}, {bounds['xmax']:.0f}], "
              f"y=[{bounds['ymin']:.0f}, {bounds['ymax']:.0f}], "
              f"z=[{bounds['zmin']:.0f}, {bounds['zmax']:.0f}]")

    # Create water surface at z=0
    if verbose:
        print("Creating water surface...")
    create_water_surface(doc, bounds, water_level=0.0)

    # Apply colors from materials
    if verbose:
        print("Applying colors...")
    apply_colors(doc, materials_path)

    # Recompute document
    doc.recompute()

    # Save output
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    doc.saveAs(output_path)

    if verbose:
        print(f"✓ Buoyancy design saved to {output_path}")

    App.closeDocument(doc.Name)


def main():
    parser = argparse.ArgumentParser(
        description='Create buoyancy design with boat at equilibrium',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--design', required=True,
                        help='Path to input FCStd design file')
    parser.add_argument('--buoyancy', required=True,
                        help='Path to buoyancy.json artifact')
    parser.add_argument('--materials', required=True,
                        help='Path to materials JSON file')
    parser.add_argument('--output', required=True,
                        help='Path to output FCStd file')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress progress output')

    args = parser.parse_args()

    for path, name in [(args.design, 'Design'), (args.buoyancy, 'Buoyancy'),
                       (args.materials, 'Materials')]:
        if not os.path.exists(path):
            print(f"ERROR: {name} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    create_buoyancy_design(
        args.design,
        args.buoyancy,
        args.materials,
        args.output,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
