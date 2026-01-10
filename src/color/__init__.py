"""
Color module - applies material-based color schemes to FreeCAD designs

This module reads color scheme definitions from JSON files and applies them to 
FreeCAD designs based on material annotations in object labels.

Supported label formats:
- Parentheses: "ComponentName (material)"
- Double underscore: "ComponentName__material"

Color schemes can specify:
- RGB color values (0.0-1.0)
- Transparency (0-100)
- Display mode (e.g., "Shaded", "Wireframe")
"""
