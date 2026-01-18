#!/usr/bin/env python3
"""
Generate a dependency graph by parsing the Makefile.
Automatically extracts stages and their dependencies.
"""

import re
import subprocess
import sys
import os


def parse_makefile(makefile_path):
    """Parse the Makefile to extract stages and dependencies."""

    with open(makefile_path, 'r') as f:
        content = f.read()

    # First, extract variable definitions
    variables = {}
    for match in re.finditer(r'^([A-Z_]+)\s*:=\s*(.+)$', content, re.MULTILINE):
        var_name = match.group(1)
        var_value = match.group(2).strip()
        variables[var_name] = var_value

    # Find all *_ARTIFACT definitions to identify stages
    stages = {}
    artifact_pattern = re.compile(r'^([A-Z][A-Z_]*)_ARTIFACT\s*:=\s*(.+)$', re.MULTILINE)

    for match in artifact_pattern.finditer(content):
        stage_name = match.group(1).lower().replace('_', '-')
        artifact_pattern_str = match.group(2).strip()
        stages[stage_name] = {
            'name': stage_name,
            'artifact': artifact_pattern_str,
            'depends_on': []
        }

    # Find dependency rules for each artifact
    # Pattern: $(STAGE_ARTIFACT): dep1 dep2 dep3
    rule_pattern = re.compile(
        r'^\$\(([A-Z][A-Z_]*)_ARTIFACT\)\s*:\s*(.+?)(?:\s*\||\s*$)',
        re.MULTILINE
    )

    for match in rule_pattern.finditer(content):
        stage_name = match.group(1).lower().replace('_', '-')
        deps_str = match.group(2).strip()

        if stage_name not in stages:
            continue

        # Parse dependencies
        deps = []
        for dep in deps_str.split():
            dep = dep.strip()
            if not dep:
                continue

            # Check if it's another stage artifact
            artifact_match = re.match(r'\$\(([A-Z][A-Z_]*)_ARTIFACT\)', dep)
            if artifact_match:
                dep_stage = artifact_match.group(1).lower().replace('_', '-')
                deps.append(dep_stage)
            # Check if it's a file reference
            elif re.match(r'\$\(([A-Z]+)_FILE\)', dep):
                file_match = re.match(r'\$\(([A-Z]+)_FILE\)', dep)
                file_type = file_match.group(1).lower()
                deps.append(f'{file_type}.json')
            # Check if it's a source reference (skip these for the graph)
            elif '_SOURCE' in dep:
                continue

        stages[stage_name]['depends_on'] = deps

    # Find input file definitions (BOAT_FILE, CONFIGURATION_FILE, etc)
    inputs = {}
    file_pattern = re.compile(r'^([A-Z]+)_FILE\s*:=\s*\$\(([A-Z_]+)\)/\$\(([A-Z]+)\)\.json', re.MULTILINE)
    for match in file_pattern.finditer(content):
        file_type = match.group(1).lower()
        dir_var = match.group(2)
        # Get the directory path
        if dir_var in variables:
            dir_path = variables[dir_var]
            # Expand nested variables
            for var, val in variables.items():
                dir_path = dir_path.replace(f'$({var})', val)
            inputs[f'{file_type}.json'] = f'{dir_path}/*.json'

    # Special case: render is a phony target without *_ARTIFACT
    # It depends on color and produces multiple PNGs
    if 'render' not in stages:
        stages['render'] = {
            'name': 'render',
            'artifact': '{boat}.{config}.render.*.png',
            'depends_on': ['color']
        }

    # Special case: buoyancy-render is a phony target without *_ARTIFACT
    # It depends on buoyancy-design and produces multiple PNGs
    if 'buoyancy-render' not in stages:
        stages['buoyancy-render'] = {
            'name': 'buoyancy-render',
            'artifact': '{boat}.{config}.buoyancy_design.render.*.png',
            'depends_on': ['buoyancy-design']
        }

    return stages, inputs


def generate_dot(stages, inputs):
    """Generate DOT graph representation."""

    # Color palette
    colors = ['#a8e6cf', '#dcedc1', '#ffd3b6', '#ffaaa5', '#ff8b94', '#b5ead7', '#c7ceea', '#e2f0cb']
    input_color = '#c7ceea'

    lines = [
        'digraph MakefileDependencies {',
        '    rankdir=LR;',
        '    node [shape=box, style="rounded,filled", fontname="Helvetica"];',
        '    edge [fontname="Helvetica", fontsize=10];',
        '',
        '    // Input files (constants)',
        '    subgraph cluster_inputs {',
        '        label="Constants";',
        '        style=dashed;',
        '        color=gray;',
    ]

    # Add input nodes
    for inp_name, inp_path in sorted(inputs.items()):
        node_id = inp_name.replace('.', '_')
        lines.append(f'        {node_id} [label="{inp_path}", fillcolor="{input_color}"];')

    lines.extend([
        '    }',
        '',
        '    // Processing stages',
        '    subgraph cluster_stages {',
        '        label="Stages (src/*)";',
        '        style=dashed;',
        '        color=gray;',
    ])

    # Add stage nodes
    for i, (stage_name, stage_info) in enumerate(sorted(stages.items())):
        color = colors[i % len(colors)]
        # Simplify artifact pattern for display
        artifact = stage_info['artifact']
        # Replace variable references with placeholders
        artifact = re.sub(r'\$\([A-Z_]+\)/', '', artifact)
        artifact = artifact.replace('$(BOAT)', '{boat}')
        artifact = artifact.replace('$(CONFIGURATION)', '{config}')
        label = f"{stage_name}\\n{artifact}"
        node_id = stage_name.replace('-', '_')
        lines.append(f'        {node_id} [label="{label}", fillcolor="{color}"];')

    lines.extend([
        '    }',
        '',
        '    // Dependencies',
    ])

    # Add edges
    for stage_name, stage_info in stages.items():
        stage_node = stage_name.replace('-', '_')
        for dep in stage_info['depends_on']:
            dep_node = dep.replace('.', '_').replace('-', '_')
            lines.append(f'    {dep_node} -> {stage_node};')

    lines.append('}')

    return '\n'.join(lines)


def main():
    # Find Makefile
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.join(script_dir, '..')
    makefile_path = os.path.join(repo_root, 'Makefile')

    if not os.path.exists(makefile_path):
        print(f"Error: Makefile not found at {makefile_path}", file=sys.stderr)
        sys.exit(1)

    # Parse Makefile
    stages, inputs = parse_makefile(makefile_path)

    if not stages:
        print("Error: No stages found in Makefile", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(stages)} stages: {', '.join(sorted(stages.keys()))}")
    print(f"Found {len(inputs)} inputs: {', '.join(sorted(inputs.keys()))}")

    # Generate DOT
    dot_content = generate_dot(stages, inputs)

    if len(sys.argv) > 1 and sys.argv[1] == '--dot':
        # Output DOT format only
        print(dot_content)
    else:
        # Try to generate PNG
        output_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(repo_root, 'docs', 'dependency_graph.png')

        try:
            result = subprocess.run(
                ['dot', '-Tpng', '-o', output_file],
                input=dot_content,
                text=True,
                capture_output=True
            )
            if result.returncode == 0:
                print(f"✓ Generated {output_file}")
            else:
                print(f"Error running dot: {result.stderr}", file=sys.stderr)
                sys.exit(1)
        except FileNotFoundError:
            print("Error: 'dot' (graphviz) not found. Install with:", file=sys.stderr)
            print("  brew install graphviz  # macOS", file=sys.stderr)
            print("  apt install graphviz   # Linux", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
