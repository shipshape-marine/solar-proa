#!/usr/bin/env python3
"""
CAD Generation wrapper - loads parameters from JSON and generates FreeCAD model.
This wraps the existing SolarProa.FCMacro with JSON-based parameter loading.
"""

import sys
import os
import json

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

params_path = sys.argv[3]
output_path = sys.argv[4]

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

print("Importing rotating...")
if 'rotating' in sys.modules: del sys.modules['rotating']
from rotating import *

print("Importing mirror...")
if 'mirror' in sys.modules: del sys.modules['mirror']
from mirror import *

print("Importing central...")
if 'central' in sys.modules: del sys.modules['central']
from central import *

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
        print("✓ Headless GUI initialized")
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
    reefing_percentage=params['reefing_percentage_biru'])
rig_biru.Placement = FreeCAD.Placement(
    Base.Vector(params['vaka_x_offset'],
                params['mast_distance_from_center'],
                params['sole_thickness']),
    FreeCAD.Rotation(Base.Vector(0, 0, 1),
                     params['rig_rotation_biru']))

# rig_kuning with specified rotation and camber
rig_kuning = doc.addObject("App::Part", "Rig Kuning")
rig(rig_kuning, params, sail_angle=params['sail_angle_kuning'],
    sail_camber=params['sail_camber_kuning'],
    reefing_percentage=params['reefing_percentage_kuning'])
rig_kuning.Placement = FreeCAD.Placement(
    Base.Vector(params['vaka_x_offset'], - params['mast_distance_from_center'], params['sole_thickness']),
    FreeCAD.Rotation(Base.Vector(0, 0, 1), params['rig_rotation_kuning']))

# rudder: each rudder (biru and kuning) is
# constructed at origin in rotating.py,
# then rotated, then translated in x and y-direction

# rudder_biru with rudder_rotation_biru

# Calculate last aka Y position for rudder placement
last_panel_index = params['panels_longitudinal'] // 2 - 1
last_aka_index = params['akas_per_panel'] - 1
last_aka_y = aka_y_position(params, last_panel_index, last_aka_index)

rudder_biru = doc.addObject("App::Part", "Rudder Biru")
rudder(rudder_biru, params, params['rudder_raised_biru'])
rudder_biru.Placement = FreeCAD.Placement(
    Base.Vector(params['vaka_x_offset'] - params['vaka_width'] / 2
                - params['rudder_distance_from_vaka'],
                last_aka_y,
                0),
    FreeCAD.Rotation(Base.Vector(0, 0, 1), params['rudder_rotation_biru']))

# rudder_kuning with rudder_rotation_kuning

rudder_kuning = doc.addObject("App::Part", "Rudder Kuning")
rudder(rudder_kuning, params, params['rudder_raised_kuning'])
rudder_kuning.Placement = FreeCAD.Placement(
    Base.Vector(params['vaka_x_offset'] - params['vaka_width'] / 2
                - params['rudder_distance_from_vaka'],
                - last_aka_y,
                0),
    FreeCAD.Rotation(Base.Vector(0, 0, 1), params['rudder_rotation_kuning']))

# boat: central unmirrored components: hull, sole, etc

vessel = doc.addObject("App::Part", "Vessel Central")
central(vessel, params)

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
        print(f"✓ Visibility set for {len(doc.Objects)} objects")
    except Exception as e:
        print(f"Warning: Could not set visibility: {e}")

# Save the document
doc.saveAs(output_path)
print(f"Saved document to {output_path}")
if platform.system() == 'Darwin':
    print("Note: Visibility will be fixed by post-processing on macOS")
elif platform.system() == 'Linux':
    print("✓ Objects should be visible when opening")


# GUI-only code - skip in console mode
if FreeCAD.GuiUp:
    if 'view' in sys.modules:
        del sys.modules['view']
    from view import * 

    # set preferred view
    view = FreeCAD.Gui.ActiveDocument.ActiveView
    view.viewIsometric()
    view.fitAll()

    set_sail_view()

#set_interior_view()
#set_mast_view()
#set_cockpit_view()
#set_below_view()

# Exit console mode cleanly (but not GUI mode)
# Note: After destroying the GUI window, we need to exit carefully to avoid segfault
if not FreeCAD.GuiUp:
    # Close the document before exiting
    FreeCAD.closeDocument(doc.Name)
    # Use os._exit instead of sys.exit to avoid cleanup issues
    import os
    os._exit(0)

