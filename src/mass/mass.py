#!/usr/bin/env python3
"""
Mass analysis validator - computes mass, volume, and component breakdown from FreeCAD model.
Outputs JSON artifact for downstream validators.
"""

import sys
import os
import json
import argparse

# Add src to path for FreeCAD imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

try:
    import FreeCAD as App
    from design.material import material
except ImportError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("This script must be run with FreeCAD's Python", file=sys.stderr)
    sys.exit(1)


def analyze_mass(fcstd_path: str) -> dict:
    """
    Analyze mass properties of a FreeCAD model.
    
    Returns:
        Dictionary with mass analysis results
    """
    doc = App.openDocument(fcstd_path)
    
    material_weights = {}
    material_volumes = {}
    processed_labels = set()
    all_components = []
    
    def get_all_objects(obj_list):
        """Recursively get all objects including those in groups"""
        all_objs = []
        for obj in obj_list:
            all_objs.append(obj)
            if hasattr(obj, 'Group'):
                all_objs.extend(get_all_objects(obj.Group))
        return all_objs
    
    all_objects = get_all_objects(doc.Objects)
    
    for obj in all_objects:
        if not hasattr(obj, 'Shape'):
            continue
        
        if obj.Label in processed_labels:
            continue
        
        # Look for material name in label (format: ComponentName__material_name)
        label = obj.Label
        label_lower = label.lower()
        mat_key = None
        
        if '__' in label_lower:
            parts = label_lower.split('__')
            if len(parts) >= 2:
                mat_key = parts[1].rstrip('_0123456789').strip()
        
        if mat_key and mat_key in material:
            mat = material[mat_key]
            volume_m3 = obj.Shape.Volume / 1e9
            volume_liters = volume_m3 * 1000
            weight_kg = volume_m3 * mat['Density']
            
            # Track by material
            if mat['Name'] not in material_weights:
                material_weights[mat['Name']] = 0
                material_volumes[mat['Name']] = 0
            material_weights[mat['Name']] += weight_kg
            material_volumes[mat['Name']] += volume_liters
            
            # Track individual component
            all_components.append({
                'name': obj.Label,
                'mass_kg': round(weight_kg, 2),
                'volume_liters': round(volume_liters, 2),
                'material': mat['Name']
            })
            
            processed_labels.add(obj.Label)
    
    total_mass = sum(material_weights.values())
    total_volume = sum(material_volumes.values())
    
    # Build result
    result = {
        'validator': 'mass',
        'total_mass_kg': round(total_mass, 2),
        'total_volume_liters': round(total_volume, 2),
        'displacement_saltwater_kg': round(total_volume * 1.025, 2),
        'materials': {},
        'components': sorted(all_components, key=lambda x: x['mass_kg'], reverse=True),
        'component_count': len(all_components)
    }
    
    # Add material breakdown
    for mat_name in sorted(material_weights.keys()):
        result['materials'][mat_name] = {
            'mass_kg': round(material_weights[mat_name], 2),
            'volume_liters': round(material_volumes[mat_name], 2)
        }
    
    App.closeDocument(doc.Name)
    return result


def main():
    parser = argparse.ArgumentParser(description='Analyze mass properties of FreeCAD model')
    parser.add_argument('--design', required=True, help='Path to FCStd design file')
    parser.add_argument('--output', required=True, help='Path to output JSON artifact')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.design):
        print(f"ERROR: Design file not found: {args.design}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing mass properties: {args.design}")
    result = analyze_mass(args.design)
    
    # Write JSON output
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✓ Mass analysis complete")
    print(f"  Total mass: {result['total_mass_kg']:.2f} kg")
    print(f"  Components: {result['component_count']}")
    print(f"  Output: {args.output}")


if __name__ == "__main__":
    main()
