#!/usr/bin/env python3
"""
Lines Plan Generation for Solar Proa.

Generates a traditional lines plan with:
- Profile view (side elevation)
- Half-breadth view (plan from above)
- Body plan sections at aka positions and midship

Uses FreeCAD TechDraw for proper technical drawings with hatching.

Usage: Set environment variables and run with FreeCAD Python:
    DESIGN_FILE=... PARAMETER_FILE=... OUTPUT_DIR=... freecad-python -m src.lines
"""

import sys
import os
import json
import math

# Check if we're running in FreeCAD
try:
    import FreeCAD as App
    import FreeCADGui as Gui
    import Part
    import TechDraw
except ImportError:
    print("ERROR: This script must be run with freecad-python or FreeCAD")
    sys.exit(1)


def aka_y_position(params, panel_index, aka_index):
    """Calculate the Y position for an aka within a panel."""
    akas_per_panel = params['akas_per_panel']
    panel_start_y = (params['crossdeck_width'] / 2
                     + panel_index * params['panel_width'])

    if akas_per_panel == 1:
        return panel_start_y + params['panel_width'] / 2
    else:
        aka_spacing = ((params['panel_width'] - 2 * params['aka_rim'])
                       / (akas_per_panel - 1))
        return panel_start_y + params['aka_rim'] + aka_index * aka_spacing


def get_section_positions(params):
    """
    Get Y positions for section cuts.
    Returns list of (name, y_position) tuples.
    Includes: midship (Y=0), mast position, and each aka position.
    Uses small offsets to avoid slicing exactly at shape boundaries.
    """
    # Use small offset (1mm) to avoid edge cases
    positions = [("midship", 1.0)]

    # Add mast section
    mast_distance = params.get('mast_distance_from_center', 2200)
    positions.append(("mast", mast_distance + 1.0))

    # Get aka positions (front half only, they're symmetric)
    panels_front = params['panels_longitudinal'] // 2
    akas_per_panel = params['akas_per_panel']

    # The rudder is at the first aka beyond the front half (doesn't go to ama)
    rudder_panel_idx = panels_front

    for panel_idx in range(panels_front * 2):
        for aka_idx in range(akas_per_panel):
            y = aka_y_position(params, panel_idx, aka_idx)
            # Add small offset to avoid cutting exactly at aka edge
            if panel_idx == rudder_panel_idx and aka_idx == 0:
                name = "rudder---raised"
            else:
                name = f"aka_{panel_idx}_{aka_idx}"
            if (panel_idx + 1) * params['panel_width'] < params['vaka_length'] / 2 - 200:
                positions.append((name, y + 1.0))

    # draw the opposing rudder section too
    y = aka_y_position(params, rudder_panel_idx, 0)
    name = f"rudder---lowered"
    positions.append((name, - y - 1.0))

    vaka_length = params['vaka_length']
    aka_width = params['aka_width']
    positions.append(("bow or stern", (vaka_length - aka_width) / 2))

    # Sort by Y position
    positions.sort(key=lambda x: x[1])
    return positions


def init_gui():
    """Initialize FreeCAD GUI for headless operation."""
    import platform
    from PySide import QtGui

    if platform.system() == 'Linux':
        try:
            QtGui.QApplication()
        except RuntimeError:
            pass

        Gui.showMainWindow()
        Gui.getMainWindow().destroy()
        App.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool(
            'SaveThumbnail', False)


def get_horizontal_positions(params):
    """
    Get Z positions for horizontal (plan view) section cuts.
    Returns list of (name, z_position) tuples.
    """
    waterline_z = params.get('lines_plan_waterline_height', 0)
    ama_diameter = params.get('ama_diameter', 370)
    aka_base_level = params.get('aka_base_level', 1400)
    stringer_base_level = params.get('stringer_base_level', 1500)
    stringer_width = params.get('stringer_width', 25.4)
    panel_base_level = params.get('panel_base_level', 1530)
    overhead_base_level = params.get('overhead_base_level', 1403)
    deck_level = params.get('deck_level', 1540)
    gunwale_base_level = params.get('gunwale_base_level', 1350)
    mast_base_level = params.get('mast_base_level', 200)
    mast_step_height = params.get('mast_step_height', 100)
    rudder_vaka_mount_base_level = params.get('rudder_vaka_mount_base_level', 700)

    positions = [
        ("waterline", waterline_z + 1),
        ("ama_centerline", ama_diameter / 2),
        ("mast_step", mast_base_level + mast_step_height / 2),
        ("rudder_mount", rudder_vaka_mount_base_level + 1),
        ("aka", aka_base_level + 51),
        ("stringer", stringer_base_level + stringer_width / 2),
        ("panel", panel_base_level + 3),
        ("deck", deck_level - 2),
        ("overhead", overhead_base_level + 10),
    ]

    # Add gunwale level only if the parameter exists
    if gunwale_base_level:
        positions.append(("gunwale", gunwale_base_level + 25))

    # Sort by Z position
    positions.sort(key=lambda x: x[1])
    return positions


def export_horizontal_section_svgs(shapes, horizontal_positions, output_dir, base_name):
    """Export horizontal (plan view) section cuts as individual SVG files."""

    for name, z_pos in horizontal_positions:
        try:
            print(f"  Slicing at Z={z_pos:.0f} for horizontal section '{name}'...", flush=True)

            plane_normal = App.Vector(0, 0, 1)
            wires = slice_shapes_safely(shapes, plane_normal, z_pos)

            if wires:
                print(f"    Got {len(wires)} wires", flush=True)
                svg_path = os.path.join(output_dir, f"{base_name}.horizontal.{name}.svg")
                export_wires_to_svg(wires, svg_path, view='YX')
                print(f"    Exported: {svg_path}", flush=True)
            else:
                print(f"    Warning: No section found at Z={z_pos}", flush=True)

        except Exception as e:
            import traceback
            print(f"  Error exporting horizontal section '{name}': {e}", flush=True)
            traceback.print_exc()


def slice_shapes_safely(shapes, normal, position):
    """Slice shapes one by one to avoid segfaults with complex compounds."""
    all_wires = []
    for i, shape in enumerate(shapes):
        try:
            wires = shape.slice(normal, position)
            if wires:
                all_wires.extend(wires)
        except Exception as e:
            print(f"      Warning: Could not slice shape {i}: {e}", flush=True)
    return all_wires


def export_section_svgs(shapes, section_positions, output_dir, base_name, params):
    """Export cross-section cuts as SVG files."""

    # Z clipping: show up to 2m above deck level
    deck_level = params.get('deck_level', 1540)
    clip_z = deck_level + 1000

    for name, y_pos in section_positions:
        try:
            print(f"  Slicing at Y={y_pos:.0f} for section '{name}' (clip_z={clip_z:.0f})...", flush=True)

            # Slice each shape individually with a Y-normal plane
            plane_normal = App.Vector(0, 1, 0)
            wires = slice_shapes_safely(shapes, plane_normal, y_pos)

            if wires:
                print(f"    Got {len(wires)} wires", flush=True)
                svg_path = os.path.join(output_dir, f"{base_name}.section.{name}.svg")
                export_wires_to_svg(wires, svg_path, view='XZ', clip_z=clip_z)
                print(f"    Exported: {svg_path}", flush=True)
            else:
                print(f"    Warning: No section found at Y={y_pos}", flush=True)

        except Exception as e:
            import traceback
            print(f"  Error exporting section '{name}': {e}", flush=True)
            traceback.print_exc()


def export_wire_groups_to_svg(wire_groups, svg_path, view='XZ', target_size=800, stroke_width=1.0, clip_z=None):
    """Export multiple groups of wires to an SVG file with different colors.

    Args:
        wire_groups: List of (wires, color) tuples, drawn in order (last is on top)
        svg_path: Output file path
        view: Which plane to project to ('XZ', 'XY', 'YZ', 'YX')
        target_size: Target size for the larger dimension in SVG units
        stroke_width: Line width in SVG
        clip_z: Maximum Z value to include (clips tall elements like masts)
    """
    # Collect all points from all wire groups for bounds calculation
    all_points = []
    for wires, color in wire_groups:
        for wire in wires:
            for edge in wire.Edges:
                points = edge.discretize(50)
                if clip_z is not None:
                    points = [p for p in points if p.z <= clip_z]
                all_points.extend(points)

    if not all_points:
        return

    # Map coordinates based on view
    def map_point(p):
        if view == 'XZ':
            return (p.x, -p.z)
        elif view == 'XY':
            return (p.x, -p.y)
        elif view == 'YX':
            # Y to horizontal (fore-aft), X to vertical (beam) - traditional breadth plan
            return (p.y, -p.x)
        elif view == 'YZ':
            return (p.y, -p.z)
        return (p.x, -p.y)

    # Find bounds
    mapped = [map_point(p) for p in all_points]
    min_x = min(p[0] for p in mapped)
    max_x = max(p[0] for p in mapped)
    min_y = min(p[1] for p in mapped)
    max_y = max(p[1] for p in mapped)

    # Calculate scale to fit target size
    extent_x = max_x - min_x
    extent_y = max_y - min_y
    if extent_x < 0.1:
        extent_x = 0.1
    if extent_y < 0.1:
        extent_y = 0.1

    scale = target_size / max(extent_x, extent_y)
    margin = 40
    scale_bar_height = 30

    width = extent_x * scale + 2 * margin
    height = extent_y * scale + 2 * margin + scale_bar_height
    offset_x = -min_x * scale + margin
    offset_y = -min_y * scale + margin

    # Build SVG content
    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{width:.1f}" height="{height:.1f}" '
        f'viewBox="0 0 {width:.1f} {height:.1f}">'
    ]

    # Draw each wire group with its color (order matters - last is on top)
    for wires, color in wire_groups:
        svg_lines.append(f'<g fill="none" stroke="{color}" stroke-width="{stroke_width}">')
        for wire in wires:
            for edge in wire.Edges:
                points = edge.discretize(50)
                if clip_z is not None:
                    points = [p for p in points if p.z <= clip_z]
                if len(points) >= 2:
                    path_data = []
                    for i, p in enumerate(points):
                        x, y = map_point(p)
                        sx = x * scale + offset_x
                        sy = y * scale + offset_y
                        if i == 0:
                            path_data.append(f"M {sx:.2f} {sy:.2f}")
                        else:
                            path_data.append(f"L {sx:.2f} {sy:.2f}")
                    svg_lines.append(f'<path d="{" ".join(path_data)}"/>')
        svg_lines.append('</g>')

    # Add scale bar
    max_extent_mm = max(extent_x, extent_y)
    if max_extent_mm > 5000:
        bar_length_mm = 1000
        bar_label = "1 m"
    elif max_extent_mm > 2000:
        bar_length_mm = 500
        bar_label = "0.5 m"
    elif max_extent_mm > 500:
        bar_length_mm = 200
        bar_label = "200 mm"
    else:
        bar_length_mm = 100
        bar_label = "100 mm"

    bar_length_svg = bar_length_mm * scale
    bar_x = margin
    bar_y = height - 15

    svg_lines.append(f'<g stroke="black" stroke-width="1" fill="black">')
    svg_lines.append(f'<line x1="{bar_x:.1f}" y1="{bar_y:.1f}" x2="{bar_x + bar_length_svg:.1f}" y2="{bar_y:.1f}"/>')
    svg_lines.append(f'<line x1="{bar_x:.1f}" y1="{bar_y - 5:.1f}" x2="{bar_x:.1f}" y2="{bar_y + 5:.1f}"/>')
    svg_lines.append(f'<line x1="{bar_x + bar_length_svg:.1f}" y1="{bar_y - 5:.1f}" x2="{bar_x + bar_length_svg:.1f}" y2="{bar_y + 5:.1f}"/>')
    svg_lines.append(f'<text x="{bar_x + bar_length_svg / 2:.1f}" y="{bar_y - 8:.1f}" '
                     f'text-anchor="middle" font-family="sans-serif" font-size="10">{bar_label}</text>')
    svg_lines.append('</g>')

    svg_lines.append('</svg>')

    with open(svg_path, 'w') as f:
        f.write('\n'.join(svg_lines))


def export_wires_to_svg(wires, svg_path, view='XZ', target_size=800, stroke_width=1.0, clip_z=None):
    """Export a list of wires to an SVG file with scale bar.

    Args:
        wires: List of Part.Wire objects
        svg_path: Output file path
        view: Which plane to project to ('XZ', 'XY', 'YZ', 'YX')
        target_size: Target size for the larger dimension in SVG units
        stroke_width: Line width in SVG
        clip_z: Maximum Z value to include (clips tall elements like masts)
    """
    # Collect all points from wires, applying Z clipping if specified
    all_points = []
    for wire in wires:
        for edge in wire.Edges:
            # Discretize the edge into points
            points = edge.discretize(50)  # 50 points per edge
            if clip_z is not None:
                points = [p for p in points if p.z <= clip_z]
            all_points.extend(points)

    if not all_points:
        return

    # Map coordinates based on view (which plane the slice is in)
    # For a slice perpendicular to axis A, the result is in the plane of the other two axes
    def map_point(p):
        if view == 'XZ':
            # Slice perpendicular to Y - result is in XZ plane
            # Map X to horizontal, Z to vertical (flipped for SVG Y-down)
            return (p.x, -p.z)
        elif view == 'XY':
            # Slice perpendicular to Z - result is in XY plane
            # Map X to horizontal, Y to vertical (flipped)
            return (p.x, -p.y)
        elif view == 'YX':
            # Slice perpendicular to Z - result is in XY plane
            # Map Y to horizontal (fore-aft), X to vertical (beam) - traditional breadth plan
            return (p.y, -p.x)
        elif view == 'YZ':
            # Slice perpendicular to X - result is in YZ plane
            # Map Y to horizontal, Z to vertical (flipped)
            return (p.y, -p.z)
        return (p.x, -p.y)

    # Find bounds
    mapped = [map_point(p) for p in all_points]
    min_x = min(p[0] for p in mapped)
    max_x = max(p[0] for p in mapped)
    min_y = min(p[1] for p in mapped)
    max_y = max(p[1] for p in mapped)

    # Calculate scale to fit target size
    extent_x = max_x - min_x
    extent_y = max_y - min_y
    if extent_x < 0.1:
        extent_x = 0.1
    if extent_y < 0.1:
        extent_y = 0.1

    scale = target_size / max(extent_x, extent_y)
    margin = 40  # Increased margin for scale bar
    scale_bar_height = 30  # Space for scale bar at bottom

    width = extent_x * scale + 2 * margin
    height = extent_y * scale + 2 * margin + scale_bar_height
    offset_x = -min_x * scale + margin
    offset_y = -min_y * scale + margin

    # Build SVG content
    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{width:.1f}" height="{height:.1f}" '
        f'viewBox="0 0 {width:.1f} {height:.1f}">',
        f'<g fill="none" stroke="black" stroke-width="{stroke_width}">'
    ]

    # Draw each wire (with Z clipping if specified)
    for wire in wires:
        for edge in wire.Edges:
            points = edge.discretize(50)
            if clip_z is not None:
                points = [p for p in points if p.z <= clip_z]
            if len(points) >= 2:
                path_data = []
                for i, p in enumerate(points):
                    x, y = map_point(p)
                    sx = x * scale + offset_x
                    sy = y * scale + offset_y
                    if i == 0:
                        path_data.append(f"M {sx:.2f} {sy:.2f}")
                    else:
                        path_data.append(f"L {sx:.2f} {sy:.2f}")
                svg_lines.append(f'<path d="{" ".join(path_data)}"/>')

    svg_lines.append('</g>')

    # Add scale bar at bottom
    # Determine a nice round scale bar length (1m or 0.5m depending on drawing size)
    max_extent_mm = max(extent_x, extent_y)
    if max_extent_mm > 5000:
        bar_length_mm = 1000  # 1 meter
        bar_label = "1 m"
    elif max_extent_mm > 2000:
        bar_length_mm = 500  # 0.5 meter
        bar_label = "0.5 m"
    elif max_extent_mm > 500:
        bar_length_mm = 200  # 20 cm
        bar_label = "200 mm"
    else:
        bar_length_mm = 100  # 10 cm
        bar_label = "100 mm"

    bar_length_svg = bar_length_mm * scale
    bar_x = margin
    bar_y = height - 15

    # Draw scale bar with end ticks
    svg_lines.append(f'<g stroke="black" stroke-width="1" fill="black">')
    # Main bar
    svg_lines.append(f'<line x1="{bar_x:.1f}" y1="{bar_y:.1f}" x2="{bar_x + bar_length_svg:.1f}" y2="{bar_y:.1f}"/>')
    # End ticks
    svg_lines.append(f'<line x1="{bar_x:.1f}" y1="{bar_y - 5:.1f}" x2="{bar_x:.1f}" y2="{bar_y + 5:.1f}"/>')
    svg_lines.append(f'<line x1="{bar_x + bar_length_svg:.1f}" y1="{bar_y - 5:.1f}" x2="{bar_x + bar_length_svg:.1f}" y2="{bar_y + 5:.1f}"/>')
    # Label
    svg_lines.append(f'<text x="{bar_x + bar_length_svg / 2:.1f}" y="{bar_y - 8:.1f}" '
                     f'text-anchor="middle" font-family="sans-serif" font-size="10">{bar_label}</text>')
    svg_lines.append('</g>')

    svg_lines.append('</svg>')

    with open(svg_path, 'w') as f:
        f.write('\n'.join(svg_lines))


def export_fullbreadth_with_hatching(wires, solar_wires_even, solar_wires_odd, svg_path, view='YX', target_size=800, stroke_width=1.0):
    """Export full breadth plan with hatched solar panels.

    Args:
        wires: List of Part.Wire objects for the main structure
        solar_wires_even: List of Part.Wire objects for solar panels (i+j) % 2 == 0
        solar_wires_odd: List of Part.Wire objects for solar panels (i+j) % 2 == 1
        svg_path: Output file path
        view: Which plane to project to ('YX' for breadth plan)
        target_size: Target size for the larger dimension in SVG units
        stroke_width: Line width in SVG
    """
    # Collect all points for bounds calculation
    all_points = []
    for wire in wires:
        for edge in wire.Edges:
            points = edge.discretize(50)
            all_points.extend(points)

    if not all_points:
        return

    # Map coordinates based on view
    def map_point(p):
        if view == 'YX':
            return (p.y, -p.x)
        elif view == 'XZ':
            return (p.x, -p.z)
        elif view == 'XY':
            return (p.x, -p.y)
        elif view == 'YZ':
            return (p.y, -p.z)
        return (p.x, -p.y)

    def wire_to_path(wire, scale, offset_x, offset_y):
        """Convert a wire to an SVG path using ordered vertices."""
        # Use OrderedVertexes to get vertices in proper order around the wire
        if hasattr(wire, 'OrderedVertexes'):
            vertices = wire.OrderedVertexes
        else:
            vertices = wire.Vertexes

        if len(vertices) < 3:
            return None

        path_data = []
        for i, v in enumerate(vertices):
            x, y = map_point(v.Point)
            sx = x * scale + offset_x
            sy = y * scale + offset_y
            if i == 0:
                path_data.append(f"M {sx:.2f} {sy:.2f}")
            else:
                path_data.append(f"L {sx:.2f} {sy:.2f}")

        if wire.isClosed():
            path_data.append("Z")

        return " ".join(path_data)

    # Find bounds
    mapped = [map_point(p) for p in all_points]
    min_x = min(p[0] for p in mapped)
    max_x = max(p[0] for p in mapped)
    min_y = min(p[1] for p in mapped)
    max_y = max(p[1] for p in mapped)

    # Calculate scale
    extent_x = max_x - min_x
    extent_y = max_y - min_y
    if extent_x < 0.1:
        extent_x = 0.1
    if extent_y < 0.1:
        extent_y = 0.1

    scale = target_size / max(extent_x, extent_y)
    margin = 40
    scale_bar_height = 30

    width = extent_x * scale + 2 * margin
    height = extent_y * scale + 2 * margin + scale_bar_height
    offset_x = -min_x * scale + margin
    offset_y = -min_y * scale + margin

    # Build SVG content with two hatch patterns (45° and -45°)
    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{width:.1f}" height="{height:.1f}" '
        f'viewBox="0 0 {width:.1f} {height:.1f}">',
        '<defs>',
        '  <pattern id="hatch45" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">',
        '    <line x1="0" y1="0" x2="0" y2="6" stroke="#555555" stroke-width="0.8"/>',
        '  </pattern>',
        '  <pattern id="hatch135" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(-45)">',
        '    <line x1="0" y1="0" x2="0" y2="6" stroke="#555555" stroke-width="0.8"/>',
        '  </pattern>',
        '</defs>'
    ]

    # Draw hatched solar panels (even panels with 45° hatch)
    if solar_wires_even:
        svg_lines.append('<g fill="url(#hatch45)" stroke="#666666" stroke-width="0.5">')
        for wire in solar_wires_even:
            path_d = wire_to_path(wire, scale, offset_x, offset_y)
            if path_d:
                svg_lines.append(f'<path d="{path_d}"/>')
        svg_lines.append('</g>')

    # Draw hatched solar panels (odd panels with -45° hatch)
    if solar_wires_odd:
        svg_lines.append('<g fill="url(#hatch135)" stroke="#666666" stroke-width="0.5">')
        for wire in solar_wires_odd:
            path_d = wire_to_path(wire, scale, offset_x, offset_y)
            if path_d:
                svg_lines.append(f'<path d="{path_d}"/>')
        svg_lines.append('</g>')

    # Draw main structure wires (foreground)
    svg_lines.append(f'<g fill="none" stroke="black" stroke-width="{stroke_width}">')
    for wire in wires:
        for edge in wire.Edges:
            points = edge.discretize(50)
            if len(points) >= 2:
                path_data = []
                for i, p in enumerate(points):
                    x, y = map_point(p)
                    sx = x * scale + offset_x
                    sy = y * scale + offset_y
                    if i == 0:
                        path_data.append(f"M {sx:.2f} {sy:.2f}")
                    else:
                        path_data.append(f"L {sx:.2f} {sy:.2f}")
                svg_lines.append(f'<path d="{" ".join(path_data)}"/>')
    svg_lines.append('</g>')

    # Add scale bar
    max_extent_mm = max(extent_x, extent_y)
    if max_extent_mm > 5000:
        bar_length_mm = 1000
        bar_label = "1 m"
    elif max_extent_mm > 2000:
        bar_length_mm = 500
        bar_label = "0.5 m"
    elif max_extent_mm > 500:
        bar_length_mm = 200
        bar_label = "200 mm"
    else:
        bar_length_mm = 100
        bar_label = "100 mm"

    bar_length_svg = bar_length_mm * scale
    bar_x = margin
    bar_y = height - 15

    svg_lines.append('<g stroke="black" stroke-width="1" fill="black">')
    svg_lines.append(f'<line x1="{bar_x:.1f}" y1="{bar_y:.1f}" x2="{bar_x + bar_length_svg:.1f}" y2="{bar_y:.1f}"/>')
    svg_lines.append(f'<line x1="{bar_x:.1f}" y1="{bar_y - 5:.1f}" x2="{bar_x:.1f}" y2="{bar_y + 5:.1f}"/>')
    svg_lines.append(f'<line x1="{bar_x + bar_length_svg:.1f}" y1="{bar_y - 5:.1f}" x2="{bar_x + bar_length_svg:.1f}" y2="{bar_y + 5:.1f}"/>')
    svg_lines.append(f'<text x="{bar_x + bar_length_svg / 2:.1f}" y="{bar_y - 8:.1f}" '
                     f'text-anchor="middle" font-family="sans-serif" font-size="10">{bar_label}</text>')
    svg_lines.append('</g>')

    svg_lines.append('</svg>')

    with open(svg_path, 'w') as f:
        f.write('\n'.join(svg_lines))


def export_projection_svgs(shapes, solar_panel_shapes_even, solar_panel_shapes_odd, output_dir, base_name, bbox, params):
    """Export profile views as SVG - longitudinal sections through vaka and ama."""

    # Profile cuts are longitudinal sections (X-normal planes)
    # showing the side view (Y-Z projection)

    # Vaka centerline is offset in X
    vaka_x = params.get('vaka_x_offset', 4500)
    vaka_width = params.get('vaka_width', 1150)

    # Ama centerline is at X=0
    ama_x = 0

    # Rudder centerline is offset from vaka by rudder_distance_from_vaka + 0.5 * vaka_width
    rudder_distance = params.get('rudder_distance_from_vaka', 250)
    rudder_x = vaka_x - rudder_distance - 0.5 * vaka_width

    # Z clipping: show up to 2m above deck level to include mast base but not full height
    deck_level = params.get('deck_level', 1540)
    clip_z = deck_level + 1000  # 2 meters above deck

    normal = App.Vector(1, 0, 0)

    # 1. Vaka centerline profile (showing cockpit area)
    try:
        print(f"  Slicing at X={vaka_x:.0f} for vaka profile (clip_z={clip_z:.0f})...", flush=True)
        svg_path = os.path.join(output_dir, f"{base_name}.profile.vaka.svg")

        wires = slice_shapes_safely(shapes, normal, vaka_x)
        if wires:
            print(f"    Got {len(wires)} wires", flush=True)
            export_wires_to_svg(wires, svg_path, view='YZ', clip_z=clip_z)
            print(f"    Exported vaka profile: {svg_path}", flush=True)
        else:
            print(f"    Warning: No wires for vaka profile", flush=True)

    except Exception as e:
        import traceback
        print(f"  Error exporting vaka profile: {e}", flush=True)
        traceback.print_exc()

    # 2. Combined vaka + rudder profile (vaka in grey, rudder in black on top)
    try:
        print(f"  Creating combined vaka+rudder profile (clip_z={clip_z:.0f})...", flush=True)
        svg_path = os.path.join(output_dir, f"{base_name}.profile.vaka_rudder.svg")

        wire_groups = []

        # Slice at vaka centerline (grey, drawn first/background)
        vaka_wires = slice_shapes_safely(shapes, normal, vaka_x)
        if vaka_wires:
            print(f"    Vaka (X={vaka_x:.0f}): {len(vaka_wires)} wires (grey)", flush=True)
            wire_groups.append((vaka_wires, '#888888'))

        # Slice at rudder centerline (black, drawn last/foreground)
        rudder_wires = slice_shapes_safely(shapes, normal, rudder_x)
        if rudder_wires:
            print(f"    Rudder (X={rudder_x:.0f}): {len(rudder_wires)} wires (black)", flush=True)
            wire_groups.append((rudder_wires, 'black'))

        if wire_groups:
            export_wire_groups_to_svg(wire_groups, svg_path, view='YZ', clip_z=clip_z)
            print(f"    Exported combined vaka+rudder profile: {svg_path}", flush=True)
        else:
            print(f"    Warning: No wires for combined profile", flush=True)

    except Exception as e:
        import traceback
        print(f"  Error exporting combined profile: {e}", flush=True)
        traceback.print_exc()

    # 3. Ama centerline profile
    try:
        print(f"  Slicing at X={ama_x:.0f} for ama profile (clip_z={clip_z:.0f})...", flush=True)
        svg_path = os.path.join(output_dir, f"{base_name}.profile.ama.svg")

        wires = slice_shapes_safely(shapes, normal, ama_x)
        if wires:
            print(f"    Got {len(wires)} wires", flush=True)
            export_wires_to_svg(wires, svg_path, view='YZ', clip_z=clip_z)
            print(f"    Exported ama profile: {svg_path}", flush=True)
        else:
            print(f"    Warning: No wires for ama profile", flush=True)

    except Exception as e:
        import traceback
        print(f"  Error exporting ama profile: {e}", flush=True)
        traceback.print_exc()

    # Full breadth plan: top-down view with slices at key structural levels
    horizontal_positions = get_horizontal_positions(params)
    z_levels = [z for _, z in horizontal_positions]
    panel_base_level = params.get('panel_base_level', 1530)

    try:
        print(f"  Creating full breadth plan with {len(z_levels)} waterlines...", flush=True)
        svg_path = os.path.join(output_dir, f"{base_name}.fullbreadth.svg")

        all_wires = []
        for z in z_levels:
            normal = App.Vector(0, 0, 1)
            wires = slice_shapes_safely(shapes, normal, z)
            if wires:
                print(f"    Z={z:.0f}: {len(wires)} wires", flush=True)
                all_wires.extend(wires)

        # Slice solar panels at panel surface level for hatching
        solar_wires_even = []
        solar_wires_odd = []
        solar_z = panel_base_level + 3  # Same level as panels
        normal = App.Vector(0, 0, 1)
        if solar_panel_shapes_even:
            solar_wires_even = slice_shapes_safely(solar_panel_shapes_even, normal, solar_z)
            print(f"    Solar panels (even) at Z={solar_z:.0f}: {len(solar_wires_even)} wires", flush=True)
        if solar_panel_shapes_odd:
            solar_wires_odd = slice_shapes_safely(solar_panel_shapes_odd, normal, solar_z)
            print(f"    Solar panels (odd) at Z={solar_z:.0f}: {len(solar_wires_odd)} wires", flush=True)

        if all_wires:
            # Use 'YX' view for traditional orientation: fore-aft horizontal, beam vertical
            export_fullbreadth_with_hatching(all_wires, solar_wires_even, solar_wires_odd, svg_path, view='YX')
            print(f"    Exported full breadth plan: {svg_path}", flush=True)
        else:
            print(f"    Warning: No sections found for full breadth plan", flush=True)

    except Exception as e:
        import traceback
        print(f"  Error exporting full breadth plan: {e}", flush=True)
        traceback.print_exc()


def export_summary_svgs(shapes, section_positions, output_dir, base_name, params):
    """Export summary views for the one-page overview (no Z clipping, full mast)."""

    vaka_x = params.get('vaka_x_offset', 4500)
    vaka_width = params.get('vaka_width', 1150)
    ama_x = 0
    rudder_distance = params.get('rudder_distance_from_vaka', 250)
    rudder_x = vaka_x - rudder_distance - 0.5 * vaka_width

    # 1. Combined profile: vaka + ama + rudder overlayed (no clipping)
    try:
        print(f"  Creating summary profile (all sections, no clip)...", flush=True)
        svg_path = os.path.join(output_dir, f"{base_name}.summary.profile.svg")

        normal = App.Vector(1, 0, 0)
        wire_groups = []

        # Ama in light grey (background)
        ama_wires = slice_shapes_safely(shapes, normal, ama_x)
        if ama_wires:
            wire_groups.append((ama_wires, '#CCCCCC'))

        # Vaka in medium grey
        vaka_wires = slice_shapes_safely(shapes, normal, vaka_x)
        if vaka_wires:
            wire_groups.append((vaka_wires, '#666666'))

        # Rudder in black (foreground)
        rudder_wires = slice_shapes_safely(shapes, normal, rudder_x)
        if rudder_wires:
            wire_groups.append((rudder_wires, 'black'))

        if wire_groups:
            export_wire_groups_to_svg(wire_groups, svg_path, view='YZ', target_size=600)
            print(f"    Exported summary profile: {svg_path}", flush=True)

    except Exception as e:
        import traceback
        print(f"  Error exporting summary profile: {e}", flush=True)
        traceback.print_exc()

    # 2. Combined body plan: all sections overlayed (no clipping)
    try:
        print(f"  Creating summary body plan (all sections overlayed)...", flush=True)
        svg_path = os.path.join(output_dir, f"{base_name}.summary.bodyplan.svg")

        normal = App.Vector(0, 1, 0)
        wire_groups = []

        # Use different grey levels for each section
        num_sections = len(section_positions)
        for i, (name, y_pos) in enumerate(section_positions):
            wires = slice_shapes_safely(shapes, normal, y_pos)
            if wires:
                # Gradient from light grey to black
                grey_level = int(200 - (180 * i / max(num_sections - 1, 1)))
                color = f'#{grey_level:02x}{grey_level:02x}{grey_level:02x}'
                wire_groups.append((wires, color))
                print(f"    Section {name} (Y={y_pos:.0f}): {len(wires)} wires", flush=True)

        if wire_groups:
            export_wire_groups_to_svg(wire_groups, svg_path, view='XZ', target_size=400)
            print(f"    Exported summary body plan: {svg_path}", flush=True)

    except Exception as e:
        import traceback
        print(f"  Error exporting summary body plan: {e}", flush=True)
        traceback.print_exc()

    # Note: Full breadth summary reuses the detailed fullbreadth.svg


def create_lines_plan(design_path, params, output_dir, boat_name, config_name):
    """
    Create lines plan drawings using TechDraw.

    Args:
        design_path: Path to the FCStd design file
        params: Parameter dictionary
        output_dir: Directory for output files
        boat_name: Name of the boat (e.g., 'rp2')
        config_name: Configuration name (e.g., 'closehaul')
    """
    print(f"Opening design: {design_path}")
    design_doc = App.openDocument(design_path)
    design_doc.recompute()

    # Create a new document for the lines plan
    lines_doc = App.newDocument("LinesPlan")

    # Get all visible solid shapes from the design
    print("Collecting shapes from design...")

    # Patterns to exclude from lines plan (case-insensitive)
    exclude_patterns = [
        'origin', 'indicator', 'arrow',  # UI elements
        'load',                           # Test loads
        'air',                            # Internal air volumes (buoyancy calc)
        'plane',                          # Reference planes
        'sail',                           # Sails
        'yard',                           # Yard spars
        'boom',                           # Boom spars
    ]

    # Type IDs to exclude
    exclude_types = [
        'App::Origin',
        'App::Line',
        'App::Plane',
    ]

    # Build a map of object -> parent App::Part for placement transformation
    parent_part_map = {}
    for obj in design_doc.Objects:
        if obj.TypeId == 'App::Part':
            if hasattr(obj, 'Group'):
                for child in obj.Group:
                    parent_part_map[child.Name] = obj
                    # Also check nested groups
                    if hasattr(child, 'Group'):
                        for grandchild in child.Group:
                            parent_part_map[grandchild.Name] = obj

    def get_parent_placement(obj):
        """Get the placement of the parent App::Part container."""
        if obj.Name in parent_part_map:
            return parent_part_map[obj.Name].Placement
        return App.Placement()

    shapes = []
    solar_panel_shapes_even = []  # Solar panels where (i+j) % 2 == 0
    solar_panel_shapes_odd = []   # Solar panels where (i+j) % 2 == 1
    for obj in design_doc.Objects:
        if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
            # Skip by type
            if obj.TypeId in exclude_types:
                continue
            # Skip App::Part containers themselves
            if obj.TypeId == 'App::Part':
                continue
            # Skip by name pattern
            name_lower = obj.Name.lower()
            if any(pattern in name_lower for pattern in exclude_patterns):
                print(f"  Skipped: {obj.Name}")
                continue

            # Get shape and apply parent placement for objects inside App::Part
            shape = obj.Shape.copy()
            parent_placement = get_parent_placement(obj)
            if not parent_placement.isIdentity():
                shape = shape.transformed(parent_placement.toMatrix())

            # Only include solid shapes with reasonable volume (> 1 mm³)
            if shape.Volume > 1:
                shapes.append(shape)
                # Track solar panels separately for hatching, using (i+j) % 2 pattern
                if 'solar' in name_lower:
                    # Parse panel indices from name like "Panel_0_1__solar_"
                    import re
                    match = re.search(r'panel_(\d+)_(\d+)', name_lower)
                    if match:
                        i, j = int(match.group(1)), int(match.group(2))
                        if (i + j) % 2 == 0:
                            solar_panel_shapes_even.append(shape)
                            print(f"  Added: {obj.Name} (Volume: {shape.Volume:.0f} mm³) [SOLAR EVEN]")
                        else:
                            solar_panel_shapes_odd.append(shape)
                            print(f"  Added: {obj.Name} (Volume: {shape.Volume:.0f} mm³) [SOLAR ODD]")
                    else:
                        solar_panel_shapes_even.append(shape)
                        print(f"  Added: {obj.Name} (Volume: {shape.Volume:.0f} mm³) [SOLAR]")
                else:
                    print(f"  Added: {obj.Name} (Volume: {shape.Volume:.0f} mm³)")

    if not shapes:
        print("ERROR: No shapes found in design")
        return False

    print(f"Total shapes collected: {len(shapes)}")

    # Create a compound of all shapes for sectioning
    print(f"Creating compound from {len(shapes)} shapes...")
    compound = Part.makeCompound(shapes)
    vessel = lines_doc.addObject("Part::Feature", "Vessel")
    vessel.Shape = compound

    # Recompute to ensure compound is ready
    lines_doc.recompute()

    # Get bounding box for scaling calculations
    bbox = compound.BoundBox
    print(f"Vessel bounds: X=[{bbox.XMin:.0f}, {bbox.XMax:.0f}], "
          f"Y=[{bbox.YMin:.0f}, {bbox.YMax:.0f}], "
          f"Z=[{bbox.ZMin:.0f}, {bbox.ZMax:.0f}]")

    # Vessel dimensions in mm (use params as fallback if bbox is empty or too small)
    vessel_length = bbox.YMax - bbox.YMin
    vessel_width = bbox.XMax - bbox.XMin
    vessel_height = bbox.ZMax - bbox.ZMin

    # Use params as fallback for reasonable minimums
    if vessel_length < 100:
        vessel_length = params.get('vaka_length', 9000)
    if vessel_width < 100:
        vessel_width = params.get('beam', 5000)
    if vessel_height < 100:
        vessel_height = params.get('mast_height', 8500)

    print(f"Vessel dimensions: L={vessel_length:.0f}mm, W={vessel_width:.0f}mm, H={vessel_height:.0f}mm")

    # Create TechDraw page with A3 landscape template
    print("Creating TechDraw page...")
    page = lines_doc.addObject('TechDraw::DrawPage', 'LinesPlan')

    # Use built-in A3 landscape template
    template = lines_doc.addObject('TechDraw::DrawSVGTemplate', 'Template')
    # FreeCAD includes templates in its installation
    template_paths = [
        '/Applications/FreeCAD.app/Contents/Resources/share/Mod/TechDraw/Templates/A3_Landscape_blank.svg',
        '/Applications/FreeCAD.app/Contents/Resources/Mod/TechDraw/Templates/A3_Landscape_blank.svg',
        '/usr/share/freecad/Mod/TechDraw/Templates/A3_Landscape_blank.svg',
        '/usr/share/freecad-daily/Mod/TechDraw/Templates/A3_Landscape_blank.svg',
    ]

    template_found = False
    for tp in template_paths:
        if os.path.exists(tp):
            template.Template = tp
            template_found = True
            print(f"Using template: {tp}")
            break

    if not template_found:
        # Create a simple blank template
        print("No template found, using default page size")

    page.Template = template

    # Calculate scale to fit A3 (420x297mm) landscape
    # Leave margins for title block etc
    available_width = 380  # mm
    available_height = 250  # mm

    # Calculate scales for different views (using dimensions computed above)
    profile_scale = min(available_width / vessel_length,
                        (available_height * 0.4) / vessel_height)
    halfbreadth_scale = min(available_width / vessel_length,
                            (available_height * 0.3) / vessel_width)
    section_scale = min((available_width * 0.3) / vessel_width,
                        (available_height * 0.5) / vessel_height)

    # Use a common scale (smallest) for consistency
    # Ensure scale is reasonable (between 1:10 and 1:1000)
    common_scale = min(profile_scale, halfbreadth_scale, section_scale) * 0.8
    common_scale = max(0.001, min(0.1, common_scale))  # Clamp to reasonable range

    print(f"  Profile scale: {profile_scale:.6f}")
    print(f"  Half-breadth scale: {halfbreadth_scale:.6f}")
    print(f"  Section scale: {section_scale:.6f}")
    print(f"Using scale: 1:{1/common_scale:.0f} (scale factor: {common_scale:.6f})")

    # =========================================================================
    # Create Profile View (side elevation, looking from +X toward -X)
    # =========================================================================
    print("Creating profile view...")
    profile_view = lines_doc.addObject('TechDraw::DrawViewPart', 'Profile')
    page.addView(profile_view)
    profile_view.Source = [vessel]
    profile_view.Direction = App.Vector(1, 0, 0)  # Looking from starboard
    profile_view.Scale = common_scale
    profile_view.X = 150  # Position on page (mm from left)
    profile_view.Y = 220  # Position on page (mm from bottom)
    profile_view.Caption = "Profile (sheer plan)"

    # =========================================================================
    # Create Half-Breadth View (plan view, looking from +Z toward -Z)
    # =========================================================================
    print("Creating half-breadth view...")
    halfbreadth_view = lines_doc.addObject('TechDraw::DrawViewPart', 'HalfBreadth')
    page.addView(halfbreadth_view)
    halfbreadth_view.Source = [vessel]
    halfbreadth_view.Direction = App.Vector(0, 0, 1)  # Looking from above
    halfbreadth_view.Scale = common_scale
    halfbreadth_view.X = 150
    halfbreadth_view.Y = 100
    halfbreadth_view.Caption = "Half-Breadth Plan"

    # =========================================================================
    # Create Section Views (body plan)
    # =========================================================================
    section_positions = get_section_positions(params)
    print(f"Creating {len(section_positions)} section views...")

    # Position sections on the right side of the page
    section_start_x = 320
    section_start_y = 200
    section_spacing = 40  # Vertical spacing between sections

    sections_created = []
    for i, (name, y_pos) in enumerate(section_positions):
        print(f"  Section '{name}' at Y={y_pos:.0f}mm")

        section = lines_doc.addObject('TechDraw::DrawViewSection', f'Section_{name}')
        page.addView(section)
        section.Source = [vessel]
        section.BaseView = profile_view

        # Section cut perpendicular to Y axis (longitudinal)
        section.SectionNormal = App.Vector(0, 1, 0)  # Cut plane normal
        section.SectionOrigin = App.Vector(0, y_pos, 0)  # Cut position
        section.Direction = App.Vector(0, -1, 0)  # Looking from bow toward stern

        section.Scale = common_scale * 1.5  # Slightly larger for detail
        section.X = section_start_x
        section.Y = section_start_y - i * section_spacing
        section.SectionSymbol = name.upper()[:3]

        # Configure hatching for cut surfaces
        section.CutSurfaceDisplay = 'SvgHatch'  # Traditional hatching

        sections_created.append((name, section))

    # Add waterline if specified
    waterline_height = params.get('lines_plan_waterline_height', 0)
    if waterline_height != 0:
        print(f"Adding waterline at Z={waterline_height}mm")
        # Could add a line annotation here

    # Recompute to generate all views
    print("Recomputing document...")
    lines_doc.recompute()

    # =========================================================================
    # Export views to SVG
    # =========================================================================
    base_name = f"{boat_name}.{config_name}.lines"

    print("Exporting drawings...")

    # Export DXF (works in headless mode)
    dxf_path = os.path.join(output_dir, f"{base_name}.dxf")
    try:
        TechDraw.writeDXFPage(page, dxf_path)
        print(f"Exported DXF: {dxf_path}")
    except Exception as e:
        print(f"DXF export failed: {e}")

    # Export section cuts as SVG using Part operations (works headless)
    print("Exporting section SVGs...", flush=True)
    try:
        export_section_svgs(shapes, section_positions, output_dir, base_name, params)
    except Exception as e:
        import traceback
        print(f"Section SVG export failed: {e}", flush=True)
        traceback.print_exc()

    # Export individual horizontal section SVGs
    print("Exporting horizontal section SVGs...", flush=True)
    try:
        horizontal_positions = get_horizontal_positions(params)
        export_horizontal_section_svgs(shapes, horizontal_positions, output_dir, base_name)
    except Exception as e:
        import traceback
        print(f"Horizontal section SVG export failed: {e}", flush=True)
        traceback.print_exc()

    # Export profile and half-breadth projections
    print("Exporting projection SVGs...", flush=True)
    try:
        export_projection_svgs(shapes, solar_panel_shapes_even, solar_panel_shapes_odd, output_dir, base_name, bbox, params)
    except Exception as e:
        import traceback
        print(f"Projection SVG export failed: {e}", flush=True)
        traceback.print_exc()

    # Export summary views for one-page overview
    print("Exporting summary SVGs...", flush=True)
    try:
        export_summary_svgs(shapes, section_positions, output_dir, base_name, params)
    except Exception as e:
        import traceback
        print(f"Summary SVG export failed: {e}", flush=True)
        traceback.print_exc()

    # Save the FreeCAD document
    fcstd_path = os.path.join(output_dir, f"{base_name}.FCStd")
    lines_doc.saveAs(fcstd_path)
    print(f"Saved lines plan document: {fcstd_path}")

    # =========================================================================
    # Generate LaTeX document
    # =========================================================================
    print("Generating LaTeX document...")
    latex_path = os.path.join(output_dir, f"{base_name}.tex")

    latex_content = generate_latex(
        boat_name, config_name, params,
        section_positions, horizontal_positions, common_scale,
        base_name, output_dir
    )

    with open(latex_path, 'w') as f:
        f.write(latex_content)
    print(f"Generated LaTeX: {latex_path}")

    # Cleanup - close documents safely
    try:
        App.closeDocument(design_doc.Name)
    except Exception as e:
        print(f"Note: Could not close design doc: {e}")

    try:
        App.closeDocument(lines_doc.Name)
    except Exception as e:
        print(f"Note: Could not close lines doc: {e}")

    return True


def generate_latex(boat_name, config_name, params, sections, horizontal_sections, scale, base_name, output_dir):
    """Generate LaTeX document for lines plan."""

    # Get vessel dimensions from params - Principal Dimensions
    vaka_length = params.get('vaka_length', 9000)
    ama_length = params.get('ama_length', 9300)
    vaka_width = params.get('vaka_width', 1150)
    ama_diameter = params.get('ama_diameter', 370)
    crossdeck_width = params.get('crossdeck_width', 1540)
    beam = params.get('beam', 5600)
    waterline = params.get('lines_plan_waterline_height', 0)
    vaka_x_offset = params.get('vaka_x_offset', 4500)
    rudder_distance_from_vaka = params.get('rudder_distance_from_vaka', 250)
    rudder_x = vaka_x_offset - rudder_distance_from_vaka
    deck_level = params.get('deck_level', 1540)
    freeboard = params.get('freeboard', 1200)
    mast_height = params.get('mast_height', 8500)
    sail_area = params.get('sail_area_m2', 60)

    # LOA is the longer of vaka or ama
    loa = max(vaka_length, ama_length)

    # Calculate human-readable scale (e.g., 1:50)
    scale_ratio = int(round(1.0 / scale)) if scale > 0 else 100
    scale_ratio = max(10, min(1000, scale_ratio))  # Clamp to reasonable range

    # Calculate station spacing
    if len(sections) >= 2:
        station_spacing = sections[1][1] - sections[0][1]
    else:
        station_spacing = 0

    # Section list for the table (escape underscores for LaTeX)
    def escape_latex(s):
        return s.replace('_', r'\_')

    section_rows = "\n".join([
        f"        {escape_latex(name)} & {y_pos:.0f} \\\\"
        for name, y_pos in sections
    ])

    horizontal_rows = "\n".join([
        f"        {escape_latex(name)} & {z_pos:.0f} \\\\"
        for name, z_pos in horizontal_sections
    ])

    # Generate section pages for LaTeX - each section on its own page
    section_pages = [f"\\section*{{Body Plan}}"]
    for name, y_pos in sections:
        svg_name = f"{base_name}.section.{name}"
        section_pages.append(
            f"%% ===== SECTION: {name} =====\n"
            f"\\begin{{figure}}[H]\n"
            f"\\centering\n"
            f"\\IfFileExists{{{svg_name}.pdf}}{{%\n"
            f"    \\includegraphics[width=0.95\\textwidth,height=0.85\\textheight,keepaspectratio]{{{svg_name}.pdf}}\n"
            f"}}{{%\n"
            f"    \\textit{{(Section {escape_latex(name)}: see {escape_latex(base_name)}.FCStd)}}\n"
            f"}}\n"
            f"\\caption{{Body Plan---Section at {escape_latex(name)} (Y={y_pos:.0f}mm)}}\n"
            f"\\end{{figure}}"
        )
    section_figures = "\n\n".join(section_pages)

    # Generate horizontal section pages for LaTeX
    horizontal_pages = [f"\\section*{{Horizontal Sections (Plan View)}}"]
    for name, z_pos in horizontal_sections:
        svg_name = f"{base_name}.horizontal.{name}"
        horizontal_pages.append(
            f"%% ===== HORIZONTAL: {name} =====\n"
            f"\\begin{{figure}}[H]\n"
            f"\\centering\n"
            f"\\IfFileExists{{{svg_name}.pdf}}{{%\n"
            f"    \\includegraphics[width=0.95\\textwidth,height=0.85\\textheight,keepaspectratio]{{{svg_name}.pdf}}\n"
            f"}}{{%\n"
            f"    \\textit{{(Horizontal section {escape_latex(name)}: see {escape_latex(base_name)}.FCStd)}}\n"
            f"}}\n"
            f"\\caption{{Horizontal Section---{escape_latex(name)} (Z={z_pos:.0f}mm)}}\n"
            f"\\end{{figure}}"
        )
    horizontal_figures = "\n\n".join(horizontal_pages)

    # Compute page numbers dynamically
    # Page 1: Summary
    # Pages 2-4: Profile (vaka, vaka+rudder, ama)
    # Body plan: one page per section, starting at page 5
    # Full breadth: one page after body plan
    # Horizontal sections: one page per section after full breadth
    profile_start = 2
    profile_end = 4
    body_start = profile_end + 1
    body_end = body_start + len(sections) - 1
    breadth_page = body_end + 1
    horiz_start = breadth_page + 1
    horiz_end = horiz_start + len(horizontal_sections) - 1

    latex = f"""\\documentclass[a3paper,landscape]{{article}}
\\usepackage[margin=20mm]{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{float}}
\\usepackage{{caption}}

\\title{{Lines Plan: {boat_name.upper()} - {config_name.title()}}}
%\\author{{Generated by Solar Proa CAD System}}
%\\date{{\\today}}

\\begin{{document}}

%\\maketitle

%% ===== SUMMARY PAGE - Traditional Lines Plan Layout =====
\\vspace{{0.5cm}}

\\section*{{Lines Plan of Roti Proa II}}

%\\vspace{{0.3cm}}
%% Profile at top (full width)
\\noindent
\\begin{{minipage}}[t]{{0.30\\textwidth}}
\\subsection*{{Profile (vaka, rudder and ama sections)}}
\\noindent
\\IfFileExists{{{base_name}.summary.profile.pdf}}{{%
\\noindent
\\hspace{{-2.0\\baselineskip}}
\\includegraphics[trim=0 0 0 0,width=1.4\\textwidth,height=1.4\\textheight,keepaspectratio]{{{base_name}.summary.profile.pdf}}
}}{{%
    \\textit{{(Summary profile: see {escape_latex(base_name)}.FCStd)}}
}}
\\end{{minipage}}
\\hspace{{25mm}}
\\begin{{minipage}}[t]{{0.20\\textwidth}}
\\subsection*{{Body Plan (all sections)}}
\\IfFileExists{{{base_name}.summary.bodyplan.pdf}}{{%
\\noindent
\\vspace{{-30mm}}
\\hspace{{-2.0\\baselineskip}}
\\includegraphics[trim=0 0 0 0,width=1.45\\textwidth,height=1.4\\textheight,keepaspectratio]{{{base_name}.summary.bodyplan.pdf}}
}}{{%
    \\textit{{(Summary body plan)}}
}}
\\end{{minipage}}
\\hspace{{13mm}}
%% Full breadth plan in middle and body plan on right
\\begin{{minipage}}[t]{{0.45\\textwidth}}
\\subsection*{{\\hspace{{20mm}}Full Breadth Plan}}
\\noindent
\\IfFileExists{{{base_name}.fullbreadth.pdf}}{{%
\\noindent
\\vspace{{-7mm}}
\\hspace{{-2.0\\baselineskip}}
\\includegraphics[angle=-90,trim=0 0 0 0,width=0.7\\textwidth,height=0.5\\textheight,keepaspectratio]{{{base_name}.fullbreadth.pdf}}
}}{{%
    \\textit{{(Full breadth plan)}}
}}
\\end{{minipage}}

\\vspace{{0mm}}
\\noindent
\\begin{{minipage}}[t]{{0.18\\textwidth}}
\\subsection*{{Proa Terminology}}

    \\begin{{description}} 
    \\item[Vaka:] main hull of the proa \\vspace{{-2mm}}
    \\item[Ama:] outrigger hull         \\vspace{{-2mm}}
    \\item[Aka:] cross-beam connecting vaka with ama
    \\end{{description}}
\\vspace{{-5mm}}
    
\\subsection*{{Section Stations}}
\\begin{{tabular}}{{lr}}
\\toprule
Station & Y Position \\\\
\\midrule
{section_rows}
\\bottomrule
\\end{{tabular}}
\\end{{minipage}}
%
\\hfill
%
\\begin{{minipage}}[t]{{0.14\\textwidth}}
\\subsection*{{Horizontal Stations}}
\\begin{{tabular}}{{lr}}
\\toprule
Station & Z Position \\\\
\\midrule
{horizontal_rows}
\\bottomrule
\\end{{tabular}}
\\end{{minipage}}
%
\hfill
%
\\begin{{minipage}}[t]{{0.14\\textwidth}}
\\subsection*{{Principal Dimensions}}
\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Parameter}} & \\textbf{{Value}} \\\\
\\midrule
\\multicolumn{{2}}{{l}}{{\\textit{{Hull Dimensions}}}} \\\\
Length Overall (LOA) & {loa/1000:.2f} m \\\\
Beam (Overall) & {beam/1000:.2f} m \\\\
Vaka Length & {vaka_length/1000:.2f} m \\\\
Vaka Beam & {vaka_width/1000:.2f} m \\\\
Ama Length & {ama_length/1000:.2f} m \\\\
Ama Diameter & {ama_diameter/1000:.2f} m \\\\
\\midrule
\\multicolumn{{2}}{{l}}{{\\textit{{Vertical Dimensions}}}} \\\\
Freeboard & {freeboard/1000:.2f} m \\\\
Deck Height & {deck_level/1000:.2f} m \\\\
Design Waterline & {waterline/1000:.2f} m \\\\
\\bottomrule
\\end{{tabular}}
\\end{{minipage}}
%
\\hfill    
%
\\begin{{minipage}}[t]{{0.15\\textwidth}}
\\subsection*{{Rig}}
\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Parameter}} & \\textbf{{Value}} \\\\
\\midrule
Mast Height & {mast_height/1000:.2f} m \\\\
Sail Area & {sail_area:.1f} m\\textsuperscript{{2}} \\\\
\\bottomrule
\\end{{tabular}}
\\vspace{{2mm}}
    
\\subsection*{{Electric Propulsion System}}
\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Parameter}} & \\textbf{{Value}} \\\\
\\midrule
Number of solar panels & 8 \\\\
Maximal power (each) & 500 W \\\\
Electric motor power & 4 kW \\\\
Onboard battery capacity & 8 kWh \\\\
\\bottomrule
\\end{{tabular}}
\\end{{minipage}}    
%
\\hspace{{8mm}}
%
\\begin{{minipage}}[t]{{0.30\\textwidth}}
\\subsection*{{Notes}}
Pages {profile_start}--{horiz_end} show the detailed lines plan
    of the {boat_name.upper()} solar-electric proa
    in the {config_name} configuration (front rudder raised).

\\subsubsection*{{Views}}
\\begin{{itemize}}
    \\item \\textbf{{Profile (Sheer Plan)}} (pages {profile_start}--{profile_end})
    \\item \\textbf{{Body Plan}} (pages {body_start}--{body_end})
    \\item \\textbf{{Full Breadth Plan}} (page {breadth_page})
    \\item \\textbf{{Horizontal Sections}} (pages {horiz_start}--{horiz_end})
\\end{{itemize}}

\\textbf{{Section Locations:}}
Sections are taken at midship (Y=0), at each aka, and at mast  position.
The asymmetric proa design requires showing the full beam rather
than the traditional half-sections used for symmetric hulls.
\\end{{minipage}}
    
%\\vfill

%\\begin{{center}}
%\\textit{{{boat_name.upper()}}}
%% (removed  - {config_name.title()} Configuration    
%\\end{{center}}

%\\vfill

%\\begin{{center}}
%\\textit{{Lines plan generated from parametric CAD model.}}

%\\textit{{Drawing reference: {escape_latex(base_name)}}}
%\\end{{center}}

%% ===== PROFILE - VAKA =====
\\newpage

\\section*{{Profile}}
    
\\begin{{figure}}[H]
\\centering
\\IfFileExists{{{base_name}.profile.vaka.pdf}}{{%
    \\includegraphics[width=0.95\\textwidth,height=0.85\\textheight,keepaspectratio]{{{base_name}.profile.vaka.pdf}}
}}{{%
    \\textit{{(Vaka profile: see {escape_latex(base_name)}.FCStd)}}
}}
\\caption{{Profile---Vaka centerline section (X={vaka_x_offset:.0f}mm)}}
\\end{{figure}}

%% ===== PROFILE - VAKA + RUDDER =====
\\newpage
\\begin{{figure}}[H]
\\centering
\\IfFileExists{{{base_name}.profile.vaka_rudder.pdf}}{{%
    \\includegraphics[width=0.95\\textwidth,height=0.85\\textheight,keepaspectratio]{{{base_name}.profile.vaka_rudder.pdf}}
}}{{%
    \\textit{{(Combined profile: see {escape_latex(base_name)}.FCStd)}}
}}
\\caption{{Profile---Rudder and vaka sections (rudder X={rudder_x:.0f}mm in black, vaka X={vaka_x_offset:.0f}mm in grey; forward rudder raised)}}
\\end{{figure}}

%% ===== PROFILE - AMA =====
\\newpage
\\begin{{figure}}[H]
\\centering
\\IfFileExists{{{base_name}.profile.ama.pdf}}{{%
    \\includegraphics[width=0.95\\textwidth,height=0.85\\textheight,keepaspectratio]{{{base_name}.profile.ama.pdf}}
}}{{%
    \\textit{{(Ama profile: see {escape_latex(base_name)}.FCStd)}}
}}
\\caption{{Profile---Ama centerline section (X=0)}}
\\end{{figure}}

%% ===== BODY PLAN SECTIONS =====
{section_figures}

%% ===== FULL BREADTH PLAN =====
\\newpage

\\section*{{Full Breadth Plan}}
    
\\begin{{figure}}[H]
\\centering
\\IfFileExists{{{base_name}.fullbreadth.pdf}}{{%
    \\includegraphics[width=0.95\\textwidth,height=0.85\\textheight,keepaspectratio]{{{base_name}.fullbreadth.pdf}}
}}{{%
    \\textit{{(Full breadth plan: see {escape_latex(base_name)}.FCStd)}}
}}
\\caption{{Full breadth plan---View from above (solar panels hatched)}}
\\end{{figure}}
    
%% ===== HORIZONTAL SECTIONS =====
\\newpage
{horizontal_figures}

\\end{{document}}
"""
    return latex


if __name__ == "__main__":
    # Get arguments from environment variables
    design_path = os.environ.get('DESIGN_FILE')
    parameter_path = os.environ.get('PARAMETER_FILE')
    output_dir = os.environ.get('OUTPUT_DIR')

    if not design_path or not parameter_path or not output_dir:
        print("ERROR: Required environment variables not set")
        print(f"  DESIGN_FILE={design_path}")
        print(f"  PARAMETER_FILE={parameter_path}")
        print(f"  OUTPUT_DIR={output_dir}")
        sys.exit(1)

    print(f"Design file: {design_path}")
    print(f"Parameter file: {parameter_path}")
    print(f"Output directory: {output_dir}")

    # Load parameters
    with open(parameter_path) as f:
        params = json.load(f)

    boat_name = params.get('boat_name', 'unknown')
    config_name = params.get('configuration_name', 'unknown')

    # Initialize GUI for TechDraw
    init_gui()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate lines plan
    success = create_lines_plan(
        design_path, params, output_dir,
        boat_name, config_name
    )

    # Exit cleanly
    import os as _os
    _os._exit(0 if success else 1)
