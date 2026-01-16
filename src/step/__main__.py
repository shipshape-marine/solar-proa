#!/usr/bin/env python3
"""
Export FreeCAD model to STEP format.
STEP (Standard for the Exchange of Product Data) is an ISO standard
for CAD data exchange, widely supported by CAD software.
"""

import sys
import os
import argparse

# FreeCAD imports
import FreeCAD
import Part
import Import

def export_to_step(input_path: str, output_path: str) -> None:
    """
    Export all visible solid shapes from a FreeCAD document to STEP format.

    Args:
        input_path: Path to input .FCStd file
        output_path: Path to output .step file
    """
    print(f"Loading FreeCAD document: {input_path}")
    doc = FreeCAD.open(input_path)

    # Collect all shapes to export
    shapes_to_export = []

    for obj in doc.Objects:
        # Skip objects without shapes
        if not hasattr(obj, 'Shape'):
            continue

        # Skip invisible objects
        if hasattr(obj, 'Visibility') and not obj.Visibility:
            continue

        # Skip empty shapes
        if obj.Shape.isNull():
            continue

        shapes_to_export.append(obj)

    print(f"Found {len(shapes_to_export)} objects to export")

    if not shapes_to_export:
        print("Warning: No shapes found to export")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    # Export to STEP
    print(f"Exporting to STEP: {output_path}")
    Import.export(shapes_to_export, output_path)

    print(f"STEP export complete: {output_path}")

    FreeCAD.closeDocument(doc.Name)

def main():
    parser = argparse.ArgumentParser(description='Export FreeCAD model to STEP format')
    parser.add_argument('--input', required=True, help='Input FreeCAD file (.FCStd)')
    parser.add_argument('--output', required=True, help='Output STEP file (.step)')

    args = parser.parse_args()

    export_to_step(args.input, args.output)
    print("Done!")

if __name__ == "__main__":
    main()
