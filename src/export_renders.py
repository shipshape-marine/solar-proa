#!/usr/bin/env python3
"""
Export renders from FreeCAD files.
Usage: freecadcmd export_renders.py <input.FCStd> <output_dir>
"""

import sys
import os

# Check if we're running in FreeCAD
try:
    import FreeCAD as App
    import FreeCADGui as Gui
except ImportError:
    print("ERROR: This script must be run with freecadcmd or FreeCAD")
    sys.exit(1)

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
                        print(f"  Colored {obj.Label} as {mat_key}")
                    except Exception as e:
                        print(f"  Warning: Could not color {obj.Label}: {e}")
            
            # Recurse into groups
            if hasattr(obj, 'Group'):
                process_objects(obj.Group)
    
    process_objects(doc.Objects)


def export_renders(fcstd_path, output_dir):
    """Export multiple views from an FCStd file as PNG images"""
    
    if not os.path.exists(fcstd_path):
        print(f"ERROR: File not found: {fcstd_path}")
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Import Qt for headless rendering
    from PySide import QtGui
    import platform
    
    # Initialize headless GUI (only on Linux)
    if platform.system() == 'Linux':
        try:
            QtGui.QApplication()
        except RuntimeError:
            pass
        
        Gui.showMainWindow()
        Gui.getMainWindow().destroy()
        App.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool('SaveThumbnail', False)
    
    # Open the document
    print(f"Opening {fcstd_path}...")
    doc = App.openDocument(fcstd_path)
    
    # Apply material-based colors
    print("Applying material colors...")
    apply_colors_to_objects(doc)
    doc.recompute()
    
    # Create GUI document - this is essential for rendering
    print("Creating GUI document...")
    Gui.getDocument(doc.Name)
    
    # Create a new 3D view for rendering
    print("Creating 3D view for rendering...")
    from pivy import coin
    
    # Try to get active view, or create one
    view = Gui.activeDocument().activeView()
    if not view:
        # Create a view manually
        Gui.activeDocument().addAnnotation("TempView", "")
        Gui.SendMsgToActiveView("ViewFit")
        view = Gui.activeDocument().activeView()
    
    if not view:
        # Last resort - try creating through the document
        print("Attempting alternative view creation...")
        import FreeCADGui
        view = FreeCADGui.ActiveDocument.ActiveView
        
    if not view:
        print("ERROR: Could not create view")
        App.closeDocument(doc.Name)
        return False
    
    print(f"View created successfully: {type(view)}")
    
    # Get base name for output files
    base_name = os.path.splitext(os.path.basename(fcstd_path))[0]
    
    # Make all objects visible and set proper display modes
    print("Setting objects visible...")
    for obj in doc.Objects:
        if hasattr(obj, 'ViewObject') and obj.ViewObject:
            try:
                if 'Origin' not in obj.Name and obj.TypeId != 'App::Origin':
                    obj.ViewObject.Visibility = True
                    # Set display mode to Shaded for better renders
                    if hasattr(obj.ViewObject, 'DisplayMode'):
                        obj.ViewObject.DisplayMode = "Shaded"
            except Exception as e:
                print(f"Warning: Could not set visibility for {obj.Name}: {e}")
    
    # Recompute to ensure everything is updated
    doc.recompute()
    
    # Define views to export
    views = [
        ('Isometric', 'viewIsometric'),
        ('Front', 'viewFront'),
        ('Top', 'viewTop'),
        ('Right', 'viewRight'),
    ]
    
    # Disable animation for faster rendering
    try:
        view.setAnimationEnabled(False)
    except:
        pass
    
    # Export each view
    for view_name, view_method in views:
        print(f"Exporting {view_name} view...")
        
        # Set the view
        getattr(view, view_method)()
        view.fitAll()
        
        # Export as PNG
        output_path = os.path.join(output_dir, f"{base_name}_{view_name}.png")
        view.saveImage(output_path, 1920, 1080, 'White')
        
        # Crop white borders using ImageMagick (more robust than PIL)
        try:
            import subprocess
            
            # ImageMagick's trim removes matching border color
            # -fuzz allows slight color variations
            # -trim removes borders
            # +repage resets the canvas size
            # -bordercolor white -border 20 adds back a small white border (padding)
            result = subprocess.run([
                'convert',
                output_path,
                '-fuzz', '1%',
                '-trim',
                '+repage',
                '-bordercolor', 'white',
                '-border', '20',
                output_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  Cropped and saved: {output_path}")
            else:
                print(f"  Saved (ImageMagick crop failed): {output_path}")
                if result.stderr:
                    print(f"    Error: {result.stderr.strip()}")
        except FileNotFoundError:
            print(f"  Saved (ImageMagick not available): {output_path}")
        except Exception as e:
            print(f"  Saved (crop error: {e}): {output_path}")
    
    # Close document
    App.closeDocument(doc.Name)
    
    print(f"Exported {len(views)} views from {fcstd_path}")
    return True

if __name__ == "__main__":
    # Get arguments from environment variables (passed by Makefile)
    fcstd_path = os.environ.get('FCSTD_FILE')
    output_dir = os.environ.get('OUTPUT_DIR')
    
    if not fcstd_path or not output_dir:
        print("ERROR: FCSTD_FILE and OUTPUT_DIR environment variables must be set")
        print(f"FCSTD_FILE={fcstd_path}")
        print(f"OUTPUT_DIR={output_dir}")
        sys.exit(1)
    
    print(f"Input file: {fcstd_path}")
    print(f"Output dir: {output_dir}")
    
    success = export_renders(fcstd_path, output_dir)
    
    # Exit cleanly
    import os as _os
    _os._exit(0 if success else 1)
