#!/usr/bin/env python3

# FreeCAD Worker
# Adapted from design and color modules
import json

import sys
import os
import math

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
design_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "design")
)
sys.path.insert(0, design_dir)



#TODO: change output_path to output_dir
if os.environ.get('PARAMS_PATH') and os.environ.get('OUTPUT_DIR'):
    params_path = os.environ['PARAMS_PATH']
    output_dir = os.environ['OUTPUT_DIR']
elif len(sys.argv) >= 2:
    # Direct invocation: python main.py params.json output.FCStd
    params_path = sys.argv[-2]
    output_dir = sys.argv[-1]
else:
    print(
        "Usage: freecadcmd build.py <params.json> <output_dir>",
        file=sys.stderr,
    )
    sys.exit(1)

# TODO: fix output paths for the generated files, 
# Generated files will be located inside output_dir


print(f"Loading parameters: {params_path}")
print(f"Output directory: {output_dir}")

# Load parameters
with open(params_path, 'r') as p:
        params = json.load(p)

print("Parameters loaded successfully")
boat = params.get('boat_name', 'unknown')
print(f"  Boat: {boat}")
configuration = params.get('configuration_name', 'unknown')
print(f"  Configuration: {configuration}")
print(f"  Total parameters: {len(params)}")

fcstd_output_path = os.path.join(
    output_dir,
    f"{boat}.{configuration}.design.FCStd",
)
glb_output_path = os.path.join(
    output_dir,
    f"{boat}.{configuration}.glb",
)
npz_output_path = os.path.join(
    output_dir,
    f"{boat}.{configuration}.npz",
)

# This section is copied from design.main
# TODO: change print statements to logging statements
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
# Note: Do not import helpers from design.main, 
# it will run the whole design.main file

print("Importing shapes...")
if 'shapes' in sys.modules: del sys.modules['shapes']
from shapes import direction_arrow

print("Importing central...")
if 'central' in sys.modules: del sys.modules['central']
from central import central

print("Importing rotating...")
if 'rotating' in sys.modules: del sys.modules['rotating']
from rotating import rig, rudder

print("Importing mirror...")
if 'mirror' in sys.modules: del sys.modules['mirror']
from mirror import mirror

print("All imports complete")


# NOTE: This might be able to be skipped because we are setting colors directly in glb
# # Initialize headless GUI (Linux only) - MUST be done before creating document
# # This is the same approach used in render.py
# import platform
# if platform.system() == 'Linux' and not App.GuiUp:
#     print("Initializing headless GUI (Linux) before document creation...")
#     try:
#         from PySide import QtGui
#         try:
#             QtGui.QApplication()
#         except RuntimeError:
#             pass  # QApplication already exists
        
#         import FreeCADGui as Gui
#         Gui.showMainWindow()
#         Gui.getMainWindow().destroy()
#         App.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool('SaveThumbnail', False)
#         print("[ok] Headless GUI initialized")
#     except Exception as e:
#         print(f"Warning: Could not initialize headless GUI: {e}")
#         print("ViewObject visibility may not work")

# Close all open documents
for doc_name in App.listDocuments():
    App.closeDocument(doc_name)



# Generate Freecad Model
print(f"\nGenerating freecad model...")
print(f"FCStd output will be saved to: {fcstd_output_path}")

doc_name = f"Solar Proa {boat} {configuration}"

# Close all open documents first
for d in App.listDocuments().values():
    App.closeDocument(d.Name)

try:
    doc = App.newDocument(doc_name)
    print(f"Created document, doc = {doc}")
    print(f"Document name: {doc.Name}")
    
    App.setActiveDocument(doc.Name)  # Use actual doc name, not the label
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

# Calculate last aka Y position for rudder placement
last_aka_y = (params['akas_per_panel'] * params['panels_longitudinal'] / 2 + 1) * params['panel_width']

# rudder_biru with rudder_rotation_biru
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

#TODO: boat direction currently always points outwards from biru side, 
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
    boat_arrow.Placement = App.Placement(
        Base.Vector(boat_arrow_x, boat_arrow_y, boat_arrow_z),
        App.Rotation(Base.Vector(1, 0, 0), -90))


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

    rot1 = App.Rotation(App.Vector(0, 1, 0), 90)
    rot2 = App.Rotation(App.Vector(0, 0, 1),
                            - 90 + params['wind_direction'])
    combined = rot2.multiply(rot1)
    wind_arrow.Placement = App.Placement(
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

# Save the .FCStd document
doc.saveAs(fcstd_output_path)

print(f"Saved FreeCAD model: {fcstd_output_path}")


from geometry import extract_display_geometry, extract_shadow_casters, extract_panel_boundaries
from numpy import savez_compressed
extracted_display_mesh = extract_display_geometry(doc, 100)
extracted_shadow_casters = extract_shadow_casters(doc, 25)
panel_boundaries = extract_panel_boundaries(doc)
savez_compressed(
    npz_output_path,
    display_vertices=extracted_display_mesh["vertices"],
    display_faces=extracted_display_mesh["faces"],
    shadow_caster_vertices=extracted_shadow_casters["vertices"],
    shadow_caster_faces=extracted_shadow_casters["faces"],
    panel_corners=panel_boundaries["corners"],
    panel_names=panel_boundaries["names"]
)



sys.stdout.flush()
sys.stderr.flush()
App.closeDocument(doc.Name)
import os as _os
_os._exit(0)
