#!/usr/bin/env python3
"""
Generate YAML statistics files for Jekyll from FreeCAD models
Uses the existing stats.py module

Usage: 
  python generate_stats_yaml.py <fcstd_file> <output_yaml>
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    import FreeCAD as App
    import stats
    from material import material
except ImportError as e:
    print(f"ERROR: {e}")
    print("This script must be run with FreeCAD's Python")
    sys.exit(1)

def boat_name_from_file(filename):
    """Extract boat name: RotiProa_RP2_Config.FCStd -> RP2"""
    base = os.path.basename(filename).replace('.FCStd', '')
    parts = base.split('_')
    return parts[1] if len(parts) >= 2 else 'Unknown'

def config_from_file(filename):
    """Extract configuration: RotiProa_RP2_CloseHaul.FCStd -> CloseHaul"""
    base = os.path.basename(filename).replace('.FCStd', '')
    parts = base.split('_')
    return parts[2] if len(parts) >= 3 else 'Default'

def generate_yaml(fcstd_path, output_path):
    """Generate YAML stats file using stats.py logic"""
    
    print(f"Opening {fcstd_path}...")
    doc = App.openDocument(fcstd_path)
    
    boat = boat_name_from_file(fcstd_path)
    config = config_from_file(fcstd_path)
    
    # Collect statistics using same logic as stats.py
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
        
        # Look for material name
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
                'mass_kg': weight_kg,
                'volume_liters': volume_liters,
                'material': mat['Name']
            })
            
            processed_labels.add(obj.Label)
    
    total_mass = sum(material_weights.values())
    total_volume = sum(material_volumes.values())
    
    # Create YAML content
    yaml_lines = [
        f"# Auto-generated statistics for {boat} - {config}",
        f"boat: {boat}",
        f"configuration: {config}",
        f"total_mass_kg: {total_mass:.2f}",
        f"total_volume_liters: {total_volume:.2f}",
        f"displacement_saltwater_kg: {total_volume * 1.025:.2f}",
        "",
        "materials:"
    ]
    
    # Add materials
    for mat_name in sorted(material_weights.keys()):
        yaml_lines.append(f"  {mat_name}:")
        yaml_lines.append(f"    mass_kg: {material_weights[mat_name]:.2f}")
        yaml_lines.append(f"    volume_liters: {material_volumes[mat_name]:.2f}")
    
    yaml_lines.append("")
    yaml_lines.append("top_components:")
    
    # Sort by mass and take top 10
    sorted_components = sorted(all_components, key=lambda x: x['mass_kg'], reverse=True)[:10]
    for comp in sorted_components:
        yaml_lines.append(f"  - name: \"{comp['name']}\"")
        yaml_lines.append(f"    mass_kg: {comp['mass_kg']:.2f}")
        yaml_lines.append(f"    volume_liters: {comp['volume_liters']:.2f}")
        yaml_lines.append(f"    material: {comp['material']}")
    
    yaml_lines.append("")
    yaml_lines.append(f"component_count: {len(all_components)}")
    
    # Write file
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(yaml_lines))
    
    print(f"✓ Generated {output_path}")
    print(f"  Total mass: {total_mass:.2f} kg")
    print(f"  Materials: {len(material_weights)}")
    print(f"  Components: {len(all_components)}")
    
    App.closeDocument(doc.Name)

if __name__ == "__main__":
    # Try environment variables first (Linux CI/CD), then command line args (Mac)
    fcstd = os.environ.get('FCSTD_FILE')
    output = os.environ.get('OUTPUT_YAML')
    
    if not fcstd and len(sys.argv) >= 3:
        # Mac fallback - command line args
        fcstd = sys.argv[1]
        output = sys.argv[2]
    
    if not fcstd or not output:
        print("Usage: generate_stats_yaml.py <fcstd_file> <output_yaml>")
        print("Or set FCSTD_FILE and OUTPUT_YAML environment variables")
        sys.exit(1)
    
    if not os.path.exists(fcstd):
        print(f"ERROR: {fcstd} not found")
        sys.exit(1)
    
    generate_yaml(fcstd, output)

