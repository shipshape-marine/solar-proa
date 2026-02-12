#!/usr/bin/env python3
"""
CAD Generation wrapper - loads parameters from JSON and generates FreeCAD model.
This wraps the existing SolarProa.FCMacro with JSON-based parameter loading.

Arguments can be passed via:
1. Command line: freecad script.py <params.json> <output.FCStd>
2. Environment variables: PARAMS_PATH and OUTPUT_PATH (for Linux freecadcmd)
"""

import sys
import os
import json
import math

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Support both command-line args and environment variables
# On Mac: args come through sys.argv
# On Linux freecadcmd: args must come through environment variables
if os.environ.get('PARAMS_PATH') and os.environ.get('OUTPUT_PATH'):
    params_path = os.environ['PARAMS_PATH']
    output_path = os.environ['OUTPUT_PATH']
elif len(sys.argv) >= 5:
    params_path = sys.argv[3]
    output_path = sys.argv[4]
elif len(sys.argv) >= 3:
    # Direct invocation: python main.py params.json output.FCStd
    params_path = sys.argv[1]
    output_path = sys.argv[2]
else:
    print("ERROR: No parameters provided", file=sys.stderr)
    print("Usage: Set PARAMS_PATH and OUTPUT_PATH environment variables", file=sys.stderr)
    print("   Or: freecad main.py <params.json> <output.FCStd>", file=sys.stderr)
    sys.exit(1)

print(f"Loading parameters: {params_path}")
print(f"Output design: {output_path}")

# Load parameters
with open(params_path, 'r') as p:
        params = json.load(p)

print("Parameters loaded successfully")
boat = params.get('boat_name', 'unknown')
print(f"  Boat: {boat}")
configuration = params.get('configuration_name', 'unknown')
print(f"  Configuration: {configuration}")
print(f"  Total parameters: {len(params)}")

# Now import and run the existing FreeCAD generation code
# This would import from the original SolarProa.FCMacro modules
print("\nImporting FreeCAD modules...")

try:
    import FreeCAD as App
    import Part
    from FreeCAD import Base
    print(f"FreeCAD version = {App.Version()}")
    print(f"FreeCAD.GuiUp = {App.GuiUp}")
    
    # Import FreeCADGui even in console mode to enable ViewObject properties
    # This doesn't open a GUI, it just makes ViewObject attributes available
    try:
        import FreeCADGui
        print("FreeCADGui imported (for ViewObject support)")
    except ImportError:
        print("Warning: FreeCADGui not available, ViewObject visibility may not work")
        
except ImportError as e:
    print(f"ERROR: Could not import FreeCAD: {e}")
    print("This script must be run with FreeCAD's Python")
    sys.exit(1)

# Import the shape-building modules

print("Importing shapes...")
if 'shapes' in sys.modules: del sys.modules['shapes']
from shapes import *

print("Importing central...")
if 'central' in sys.modules: del sys.modules['central']
from central import *

print("Importing rotating...")
if 'rotating' in sys.modules: del sys.modules['rotating']
from rotating import *

print("Importing mirror...")
if 'mirror' in sys.modules: del sys.modules['mirror']
from mirror import *

print("All imports complete")

# Initialize headless GUI (Linux only) - MUST be done before creating document
# This is the same approach used in render.py
import platform
if platform.system() == 'Linux' and not App.GuiUp:
    print("Initializing headless GUI (Linux) before document creation...")
    try:
        from PySide import QtGui
        try:
            QtGui.QApplication()
        except RuntimeError:
            pass  # QApplication already exists
        
        import FreeCADGui as Gui
        Gui.showMainWindow()
        Gui.getMainWindow().destroy()
        App.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool('SaveThumbnail', False)
        print("[ok] Headless GUI initialized")
    except Exception as e:
        print(f"Warning: Could not initialize headless GUI: {e}")
        print("ViewObject visibility may not work")

# Close all open documents
for doc_name in App.listDocuments():
    App.closeDocument(doc_name)

# The actual model generation would happen here
# by calling the appropriate functions from the imported modules
# For now, this is a placeholder that shows the structure

print(f"\nGenerating design...")
print(f"Output will be saved to: {output_path}")

doc_name = f"Solar Proa {boat} {configuration}"

# Close all open documents first
for d in FreeCAD.listDocuments().values():
    FreeCAD.closeDocument(d.Name)

# Create new document
try:
    doc = FreeCAD.newDocument(doc_name)
    print(f"Created document, doc = {doc}")
    print(f"Document name: {doc.Name}")
    
    FreeCAD.setActiveDocument(doc.Name)  # Use actual doc name, not the label
    print(f"Set active document")
    
    doc.recompute()
    print(f"Recomputed document")

except Exception as e:
    print(f"ERROR creating document: {e}")
    import traceback
    traceback.print_exc()
    raise

# boat: central unmirrored components: hull, sole, etc

vessel = doc.addObject("App::Part", "Vessel Central")
central(vessel, params)

# mirrored parts: Biru (blue) side is on the right as seen
# standing on the vaka facing the ama

biru = doc.addObject("App::Part", "Mirrored Biru")
mirror(biru, params)

kuning = doc.addObject("App::Part", "Mirrored Kuning")
for obj in biru.Group:
    mirrored_obj = kuning.newObject("Part::Feature", obj.Name)
    
    # Get the shape with its placement applied
    shape = obj.Shape.copy()
    
    # Mirror the shape across the XZ plane (Y=0)
    mirror_matrix = Base.Matrix()
    mirror_matrix.scale(Base.Vector(1, -1, 1))  # Negate Y
    shape = shape.transformGeometry(mirror_matrix)
    
    mirrored_obj.Shape = shape
    mirrored_obj.Placement = obj.Placement  # Copy the placement too
    
# rig: each rig (biru and kuning) is
# constructed at origin in rotating.py,
# then rotated, then translated in x and y-direction

# rig_biru with specified rotation and camber

rig_biru = doc.addObject("App::Part", "Rig Biru")
rig(rig_biru, params, sail_angle=params['sail_angle_biru'],
    sail_camber=params['sail_camber_biru'],
    reefing_percentage=params['reefing_percentage_biru'],
    x_offset=params['vaka_x_offset'],
    y_offset=params['mast_distance_from_center'],
    z_rotation=params['rig_rotation_biru'])

# rig_kuning with specified rotation and camber
rig_kuning = doc.addObject("App::Part", "Rig Kuning")
rig(rig_kuning, params, sail_angle=params['sail_angle_kuning'],
    sail_camber=params['sail_camber_kuning'],
    reefing_percentage=params['reefing_percentage_kuning'],
    x_offset=params['vaka_x_offset'],
    y_offset=- params['mast_distance_from_center'],
    z_rotation=params['rig_rotation_kuning'])

# rudder: each rudder (biru and kuning) is
# constructed at origin in rotating.py,
# then rotated, then translated in x and y-direction

# rudder_biru with rudder_rotation_biru

# Calculate last aka Y position for rudder placement

last_aka_y = (params['akas_per_panel'] * params['panels_longitudinal'] / 2 + 1) * params['panel_width']

rudder_biru = doc.addObject("App::Part", "Rudder Biru")
rudder(rudder_biru, params, params['rudder_raised_biru'],
       x_offset=params['vaka_x_offset'] - params['vaka_width'] / 2
                - params['rudder_distance_from_vaka'],
       y_offset=last_aka_y,
       z_rotation=params['rudder_rotation_biru'])

# rudder_kuning with rudder_rotation_kuning

rudder_kuning = doc.addObject("App::Part", "Rudder Kuning")
rudder(rudder_kuning, params, params['rudder_raised_kuning'],
       x_offset=params['vaka_x_offset'] - params['vaka_width'] / 2
                - params['rudder_distance_from_vaka'],
       y_offset=- last_aka_y,
       z_rotation=params['rudder_rotation_kuning'])

arrows = doc.addObject("App::Part", "Direction Arrows")

# boat arrow indicating boat movement direction (positive Y)
# positioned outside the vaka hull on the outer side (negative X from vaka)
if 'boat_speed_kt' in params:
    boat_arrow_length = params['vaka_length'] / 3
    boat_arrow_shaft_radius = params['vaka_length'] / 200
    boat_arrow_shape = direction_arrow(boat_arrow_length,
                                       shaft_radius=boat_arrow_shaft_radius)
    boat_arrow = arrows.newObject("Part::Feature", "Boat_Arrow__boat_indicator")
    boat_arrow.Shape = boat_arrow_shape
    boat_arrow_x = params['vaka_x_offset']
    boat_arrow_y = params['vaka_length'] / 2 + 200
    boat_arrow_z = params['deck_base_level']
    boat_arrow.Placement = FreeCAD.Placement(
        Base.Vector(boat_arrow_x, boat_arrow_y, boat_arrow_z),
        FreeCAD.Rotation(Base.Vector(1, 0, 0), -90))

# wind arrows indicating wind movement direction
# positioned so arrow tips form a square grid in plane perpendicular to wind
def wind_arrows(y_offset, z_offset, h_offset):
    wind_arrow_length = params['wind_speed_kt'] * params['vaka_length'] / 50
    wind_arrow_shaft_radius = params['vaka_length'] / 200
    wind_arrow_shape = direction_arrow(wind_arrow_length,
                                       shaft_radius=wind_arrow_shaft_radius)
    wind_arrow = arrows.newObject("Part::Feature", "Wind_Arrow__wind_indicator")
    wind_arrow.Shape = wind_arrow_shape

    wind_dir_rad = math.radians(params['wind_direction'])

    # Step 1: Calculate tip position (in plane at mast, perpendicular to wind)
    # Start at mast position, then apply perpendicular horizontal offset
    # Arrow direction is (sin(wind_dir), -cos(wind_dir), 0) due to -90+wind_dir rotation
    # Perpendicular direction is (cos(wind_dir), sin(wind_dir), 0)
    tip_x = params['vaka_x_offset'] + h_offset * math.cos(wind_dir_rad)
    tip_y = y_offset + h_offset * math.sin(wind_dir_rad)
    tip_z = params['mast_height'] - z_offset

    # Step 2: Calculate base position by moving back from tip along arrow direction
    # Arrow points in direction (sin(wind_dir), -cos(wind_dir), 0)
    wind_arrow_x = tip_x - wind_arrow_length * math.sin(wind_dir_rad)
    wind_arrow_y = tip_y + wind_arrow_length * math.cos(wind_dir_rad)
    wind_arrow_z = tip_z

    rot1 = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
    rot2 = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1),
                            - 90 + params['wind_direction'])
    combined = rot2.multiply(rot1)
    wind_arrow.Placement = FreeCAD.Placement(
        Base.Vector(wind_arrow_x, wind_arrow_y, wind_arrow_z),
        combined)

if 'wind_speed_kt' in params:
    spacing = params['vaka_length'] / 10
    for i in range(0, 4):
        for j in range(0, 4):
            h_off = (j - 1.5) * spacing 
            wind_arrows(params['mast_distance_from_center'],
                        i * spacing, h_off)
            wind_arrows(- params['mast_distance_from_center'],
                        i * spacing, h_off)
    
# recompute before stats and rendering
doc.recompute()

# Set visibility for all objects (works because GUI was initialized early)
if platform.system() == 'Linux':
    print("Setting object visibility...")
    def make_all_visible(obj_list):
        """Recursively make all objects visible"""
        for obj in obj_list:
            try:
                if hasattr(obj, 'ViewObject') and obj.ViewObject:
                    # Hide Origin objects (coordinate helpers)
                    if 'Origin' in obj.Name or obj.TypeId == 'App::Origin':
                        obj.ViewObject.Visibility = False
                    else:
                        obj.ViewObject.Visibility = True
            except Exception as e:
                pass
            # Recurse into groups
            if hasattr(obj, 'Group') and obj.Group:
                make_all_visible(obj.Group)
    
    try:
        make_all_visible(doc.Objects)
        print(f"[ok] Visibility set for {len(doc.Objects)} objects")
    except Exception as e:
        print(f"Warning: Could not set visibility: {e}")

# Save the document
doc.saveAs(output_path)
print(f"Saved document to {output_path}")
print("Design generation complete")

# Flush output and exit immediately to prevent FreeCAD from entering interactive mode
sys.stdout.flush()
sys.stderr.flush()
FreeCAD.closeDocument(doc.Name)
import os as _os
_os._exit(0)

