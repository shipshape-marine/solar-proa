#!/usr/bin/env python3
"""
Apply color scheme to FreeCAD design (Linux - headless mode)

This script loads a color scheme from JSON and applies colors, transparency,
and display modes to all objects in a FreeCAD design based on their material.
"""

import sys
import json
import argparse
import os
import platform

try:
    import FreeCAD as App
except ImportError:
    print("ERROR: Must run with FreeCAD Python", file=sys.stderr)
    sys.exit(1)


# Initialize headless GUI (Linux only) - MUST be done BEFORE opening document
# This enables ViewObject properties in console mode
if platform.system() == 'Linux' and not App.GuiUp:
    print("Initializing headless GUI for ViewObject support...")
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
        print(f"Warning: Could not initialize headless GUI: {e}", file=sys.stderr)
        print("ViewObject properties may not work", file=sys.stderr)

def get_material_from_label(label):
    """
    Extract material from object label.
    
    Supports two formats:
    - Parentheses: "Aka_0 (aluminum)" -> "aluminum"
    - Double underscore: "Deck__plywood_001" -> "plywood"
    
    Args:
        label: Object label string
        
    Returns:
        Material name (lowercase) or None if no material found
    """
    label_lower = label.lower()
    
    # Format 1: "Component (material)"
    if '(' in label_lower:
        material = label_lower.split('(')[1].rstrip(')').strip()
        return material
    
    # Format 2: "Component__material"
    if '__' in label_lower:
        parts = label_lower.split('__')
        if len(parts) >= 2:
            # Strip trailing numbers: "plywood_001" -> "plywood"
            material = parts[1].rstrip('_0123456789').strip()
            return material
    
    return None


def apply_colors(doc, color_scheme):
    """
    Apply color scheme to all objects in document based on material.
    
    Args:
        doc: FreeCAD document
        color_scheme: Dict with 'materials' key containing material definitions
    
    Returns:
        Dict with statistics about colored objects
    """
    materials_def = color_scheme.get('materials', {})
    stats = {
        'total_objects': 0,
        'colored_objects': 0,
        'by_material': {}
    }
    
    def process_objects(obj_list):
        for obj in obj_list:
            stats['total_objects'] += 1
            
            if hasattr(obj, 'ViewObject') and obj.ViewObject:
                mat_key = get_material_from_label(obj.Label)
                
                if mat_key and mat_key in materials_def:
                    mat_def = materials_def[mat_key]
                    
                    try:
                        # Apply color
                        if 'color' in mat_def:
                            obj.ViewObject.ShapeColor = tuple(mat_def['color'])
                        
                        # Apply transparency (0-100)
                        if 'transparency' in mat_def:
                            obj.ViewObject.Transparency = mat_def['transparency']
                        
                        # Apply display mode
                        if 'display_mode' in mat_def:
                            if hasattr(obj.ViewObject, 'DisplayMode'):
                                obj.ViewObject.DisplayMode = mat_def['display_mode']
                        
                        stats['colored_objects'] += 1
                        stats['by_material'][mat_key] = stats['by_material'].get(mat_key, 0) + 1
                        
                    except Exception as e:
                        print(f"Warning: Could not color {obj.Label}: {e}", file=sys.stderr)
            
            # Recurse into groups
            if hasattr(obj, 'Group'):
                process_objects(obj.Group)
    
    process_objects(doc.Objects)
    return stats

def main():
    parser = argparse.ArgumentParser(
        description='Apply color scheme to FreeCAD design'
    )
    parser.add_argument('--design', required=True, 
                       help='Input FCStd design file')
    parser.add_argument('--colors', required=True,
                       help='Color scheme JSON file')
    parser.add_argument('--outputdesign', required=True,
                       help='Output colored FCStd file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.design):
        print(f"ERROR: Design file not found: {args.design}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(args.colors):
        print(f"ERROR: Color scheme file not found: {args.colors}", file=sys.stderr)
        sys.exit(1)
    
    # Load color scheme
    print(f"Loading color scheme: {args.colors}")
    with open(args.colors, 'r') as f:
        color_scheme = json.load(f)
    
    scheme_name = color_scheme.get('scheme_name', 'Unknown')
    print(f"  Scheme: {scheme_name}")
    print(f"  Materials defined: {len(color_scheme.get('materials', {}))}")
    
    # Open design
    print(f"Opening design: {args.design}")
    doc = App.openDocument(args.design)
    
    # Create GUI document to ensure ViewObject is available
    if platform.system() == 'Linux':
        try:
            import FreeCADGui as Gui
            Gui.getDocument(doc.Name)
            print("✓ GUI document created")
        except Exception as e:
            print(f"Warning: Could not create GUI document: {e}", file=sys.stderr)
    
    # Apply colors
    print("Applying colors...")
    stats = apply_colors(doc, color_scheme)
    doc.recompute()
    
    # Ensure visibility is preserved/set correctly
    print("Setting visibility...")
    def make_all_visible(obj_list):
        """Recursively make all objects visible (except Origin helpers)"""
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
            if hasattr(obj, 'Group'):
                make_all_visible(obj.Group)
    
    make_all_visible(doc.Objects)
    
    # Save colored design
    print(f"Saving colored design: {args.outputdesign}")
    doc.saveAs(args.outputdesign)
    
    print(f"✓ Color application complete")
    print(f"  Total objects: {stats['total_objects']}")
    print(f"  Colored objects: {stats['colored_objects']}")
    print(f"  Materials used: {len(stats['by_material'])}")
    for mat, count in sorted(stats['by_material'].items()):
        print(f"    {mat}: {count}")
    
    App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
