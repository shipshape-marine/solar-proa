#!/usr/bin/env python3
"""
Export renders from FreeCAD files.
Usage: freecadcmd export_renders.py <input.FCStd> <output_render>
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

def export_renders(fcstd_path, output_render):
    """Export multiple views from an FCStd file as PNG images"""
    
    if not os.path.exists(fcstd_path):
        print(f"ERROR: File not found: {fcstd_path}")
        return False
    
    # Create output directory
    os.makedirs(output_render, exist_ok=True)
    
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
    
    # Note: Colors should already be applied by the color module
    # The input FCStd file is expected to be a *.color.FCStd file
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
        ('isometric', 'viewIsometric'),
        ('front', 'viewFront'),
        ('top', 'viewTop'),
        ('right', 'viewRight'),
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
        clean_name = base_name.replace('.design', '')
        output_path = os.path.join(output_render, f"{clean_name}.render.{view_name}.png")
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
    render_dir = os.environ.get('IMAGE_DIR')
    
    if not fcstd_path or not render_dir:
        print("ERROR: FCSTD_FILE and RENDER_DIR environment variables must be set")
        print(f"FCSTD_FILE={fcstd_path}")
        print(f"RENDER_DIR={render_dir}")
        sys.exit(1)
    
    print(f"Input file: {fcstd_path}")
    print(f"Output dir: {render_dir}")
    
    success = export_renders(fcstd_path, render_dir)
    
    # Exit cleanly
    import os as _os
    _os._exit(0 if success else 1)
