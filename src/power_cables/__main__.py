#!/usr/bin/env python3
"""
Apply power cables to FreeCAD design (Linux - headless mode)

This script loads a FreeCAD design and adds power cables to the solar panels.
"""

import sys
import argparse
import os
import platform
import json

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    import FreeCAD as App
    import FreeCADGui as Gui
except ImportError:
    print("ERROR: Must run with FreeCAD Python", file=sys.stderr)
    sys.exit(1)

from wiring import wire_solar_panels

# Initialize headless GUI (Linux only) - MUST be done BEFORE opening document
if platform.system() == 'Linux' and not App.GuiUp:
    print("Initializing headless GUI for ViewObject support...")
    try:
        from PySide import QtGui
        try:
            QtGui.QApplication()
        except RuntimeError:
            pass  # QApplication already exists
        
        Gui.showMainWindow()
        Gui.getMainWindow().destroy()
        App.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool('SaveThumbnail', False)
        print("✓ Headless GUI initialized")
    except Exception as e:
        print(f"Warning: Could not initialize headless GUI: {e}", file=sys.stderr)
        print("ViewObject properties may not work", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description='Add power cables to FreeCAD design'
    )
    parser.add_argument('--design', required=True, 
                       help='Input FCStd design file')
    parser.add_argument('--params', required=False,
                       help='Path to parameters artifact JSON file')
    parser.add_argument('--outputdesign', required=True,
                       help='Output FCStd file with power cables')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.design):
        print(f"ERROR: Design file not found: {args.design}", file=sys.stderr)
        sys.exit(1)

    params = {}
    if args.params:
        if not os.path.exists(args.params):
             print(f"ERROR: Parameter file not found: {args.params}", file=sys.stderr)
             sys.exit(1)
        print(f"Loading parameters from: {args.params}")
        with open(args.params, 'r') as f:
            params = json.load(f)
    
    # Open design
    print(f"Opening design: {args.design}")
    doc = App.openDocument(args.design)
    
    print(doc, doc.Name)

    # Create GUI document to ensure ViewObject is available
    if platform.system() == 'Linux':
        try:
            Gui.getDocument(doc.Name)
            print("✓ GUI document created")
        except Exception as e:
            print(f"Warning: Could not create GUI document: {e}", file=sys.stderr)
    
    # Apply wiring
    print("Adding power cables...")
    
    
    # Calling wiring function
    wire_solar_panels(doc, params=params)
    
    doc.recompute()
    
    # Save design
    print(f"Saving design with cables: {args.outputdesign}")
    doc.saveAs(args.outputdesign)
    
    print(f"✓ Power cables application complete")
    
    App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
