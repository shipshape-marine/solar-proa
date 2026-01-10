#!/usr/bin/env python3
"""
Generate downloads.yml for Jekyll from available configurations
"""

import os
import sys
import json

def generate_downloads_yaml(boat, config_dir, artifacts_dir, output_path):
    """Generate YAML file listing available configurations"""
    
    # Get all configuration files from constants/configurations
    configs = []
    
    for f in os.listdir(config_dir):
        if f.endswith('.json') and not f.startswith('_'):
            config_name = f.replace('.json', '')
            # Convert to proper case (beaching -> Beaching, closehaul -> CloseHaul, etc.)
            config_display = config_name.title().replace('haul', 'Haul').replace('wing', 'Wing')
            configs.append({
                'name': config_display,
                'key': config_name
            })
    
    # Sort configs by key
    configs.sort(key=lambda x: x['key'])
    
    # Generate YAML
    yaml_lines = [
        f"# Auto-generated download links for {boat}",
        f"boat: {boat}",
        "configurations:"
    ]
    
    for config in configs:
        yaml_lines.append(f"  - name: {config['name']}")
        # Check if FCStd file exists in artifacts
        fcstd_filename = f"{boat.lower()}.{config['key']}.design.FCStd"
        yaml_lines.append(f"    filename: {fcstd_filename}")
        
        # Add friendly description
        descriptions = {
            'beaching': 'Rigging stowed, solar deployed',
            'beamreach': 'Crosswind, optimal speed',
            'broadreach': 'Downwind angle',
            'closehaul': 'Upwind sailing, tight angle',
            'closehaulreefed': 'Reduced sail in strong winds',
            'goosewing': 'Running downwind'
        }
        if config['key'] in descriptions:
            yaml_lines.append(f"    description: {descriptions[config['key']]}")
    
    # Write file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(yaml_lines))
    
    print(f"✓ Generated {output_path} ({len(configs)} configurations)")

if __name__ == "__main__":
    # Determine paths relative to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.join(script_dir, '..')
    config_dir = os.path.join(repo_root, 'constants', 'configurations')
    artifacts_dir = os.path.join(repo_root, 'artifacts')
    
    # Check if config directory exists
    if not os.path.exists(config_dir):
        print(f"ERROR: Configuration directory not found: {config_dir}")
        print(f"Script dir: {script_dir}")
        print(f"Repo root: {repo_root}")
        sys.exit(1)
    
    # Generate for all boats
    boats = ['rp1', 'rp2', 'rp3']
    
    for boat in boats:
        output = os.path.join(repo_root, 'docs', '_data', f'{boat}_downloads.yml')
        generate_downloads_yaml(boat.upper(), config_dir, artifacts_dir, output)
    
    print("All downloads YAML files generated!")
