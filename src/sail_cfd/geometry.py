"""
Sail surface geometry for CFD, as a zero-thickness STL.

Rebuilds the sail exactly as src/design/rotating.py does - a strip of a
cylinder of radius sail_camber, yard_length long, hung below the yard pivot,
then tilted by sail_angle about the yard-spar (x) axis - but in pure Python,
so it doesn't need FreeCAD. The surface is written without thickness:
snappyHexMesh turns it into a two-sided baffle (see case.py), which avoids
having to resolve the real 2 mm cloth. Optionally (chord_camber_pct) the
CAD strip is swapped for a sail with chordwise camber - see sail_surface.

CFD frame (metres): z=0 is the sea surface (capsize_analysis.heeling_axis_level_mm),
the yard pivot sits on the z axis, the chord (yard direction) runs along y,
and the sail bulges toward +x - the leeward side, so wind comes from -x.
Only the sail is modelled: no mast, spars, hull or the second rig.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from src.structural.capsize_analysis import heeling_axis_level_mm
from src.structural.mast_analysis import calculate_sail_levels

Vec = Tuple[float, float, float]


def sail_surface(params: Dict[str, Any], reefing_percentage: float,
                 sail_camber_mm: float, sail_angle_deg: float,
                 n_arc: int = 48, n_span: int = 24,
                 chord_camber_pct: Optional[float] = None) -> Dict[str, Any]:
    """
    Triangulated sail surface in the CFD frame.

    By default the sail is the CAD strip: a cylinder of radius
    sail_camber_mm, curved only between yard and boom. Giving
    chord_camber_pct replaces it (sail_camber_mm is then unused) with a
    doubly curved sail that is flat along the yard, boom, luff and leech
    and deepest at the centre, its mid-height section a parabola with depth
    chord_camber_pct % of the chord - camber in the usual sailing sense.
    The deepest point is at mid-chord, so the sail is the same from either
    end, as a shunting proa's sail must be.

    Returns a dict with 'triangles' (list of 3-vertex tuples, metres) and
    the reference values post-processing needs: the area the structural
    checks use (sail_width x effective height, so C x A reproduces their
    force), the pivot height, and the geometric CE height.
    """
    levels = calculate_sail_levels(params, reefing_percentage, sail_angle_deg)
    h = levels['effective_sail_height_mm']
    if h <= 0:
        raise ValueError("fully reefed sail has no surface to simulate")
    if chord_camber_pct is None and sail_camber_mm < h / 2:
        raise ValueError(f"sail_camber {sail_camber_mm} mm is smaller than half the sail "
                         f"height ({h / 2:.0f} mm) - no such arc")
    if chord_camber_pct is not None and not 0 <= chord_camber_pct <= 25:
        raise ValueError(f"chord_camber_pct must be within 0-25, got {chord_camber_pct}")

    length = params['yard_length']
    waterline = heeling_axis_level_mm(params)
    pivot_z = levels['pivot_level_mm'] - waterline

    theta = math.radians(sail_angle_deg)

    if chord_camber_pct is None:
        # Arc in the x-z plane, as rotating.py: circle centred at (cx, -h/2),
        # passing through (0, 0) and (0, -h), bulging toward +x
        cx = -math.sqrt(sail_camber_mm**2 - (h / 2)**2)

        def bulge(y: float, z: float) -> float:
            return cx + math.sqrt(sail_camber_mm**2 - (z + h / 2)**2)
    else:
        depth = chord_camber_pct / 100 * length

        def bulge(y: float, z: float) -> float:
            return depth * (1 - (2 * y / length)**2) * (1 - (2 * z / h + 1)**2)

    def point(y: float, z: float) -> Vec:
        x = bulge(y, z)
        # Tilt about the x axis by sail_angle, then lift to pivot height
        y_r = y * math.cos(theta) - z * math.sin(theta)
        z_r = y * math.sin(theta) + z * math.cos(theta)
        return (x / 1000, y_r / 1000, (z_r + pivot_z) / 1000)

    grid = [[point(-length / 2 + length * j / n_span, -h * i / n_arc)
             for j in range(n_span + 1)] for i in range(n_arc + 1)]

    triangles: List[Tuple[Vec, Vec, Vec]] = []
    for i in range(n_arc):
        for j in range(n_span):
            a, b = grid[i][j], grid[i][j + 1]
            c, d = grid[i + 1][j + 1], grid[i + 1][j]
            triangles.append((a, b, c))
            triangles.append((a, c, d))

    z_min = min(v[2] for tri in triangles for v in tri)
    if z_min <= 0:
        raise ValueError(f"sail dips {-z_min:.2f} m below the sea surface at sail_angle "
                         f"{sail_angle_deg} deg - geometry is not physical")

    xs = [v[0] for tri in triangles for v in tri]
    ys = [v[1] for tri in triangles for v in tri]
    zs = [v[2] for tri in triangles for v in tri]

    return {
        'triangles': triangles,
        'reference_area_m2': params['sail_width'] * h / 1e6,
        'chord_m': length / 1000,
        'pivot_height_m': pivot_z / 1000,
        'geometric_ce_height_m': (levels['ce_level_mm'] - waterline) / 1000,
        'bounds_m': {'min': [min(xs), min(ys), min(zs)], 'max': [max(xs), max(ys), max(zs)]},
    }


def rig_surface(params: Dict[str, Any], reefing_percentage: float,
                sail_camber_mm: float, sail_angle_deg: float,
                rig_rotation_deg: float, mast_y_mm: float,
                chord_camber_pct: Optional[float] = None) -> Dict[str, Any]:
    """
    One rig's sail placed on the boat, in the boat CFD frame used for
    two-sail (slot) cases.

    Boat frame (metres): the vaka centreline is the y axis with the biru end
    at +y, the mast stands at (0, mast_y), z=0 is the sea surface. This is
    src/design/main.py's frame shifted by vaka_x_offset. As in rotating.py,
    the sail pivot sits yard_spar_length + mast_diameter/2 out along the rig's
    local +x, and the whole rig turns by rig_rotation about the mast axis.
    With rig_rotation 0 the chord runs along the vaka and the sail bulges
    toward +x. chord_camber_pct is passed on to sail_surface.
    """
    surface = sail_surface(params, reefing_percentage, sail_camber_mm, sail_angle_deg,
                           chord_camber_pct=chord_camber_pct)
    pivot_x = (params['yard_spar_length'] + params['mast_diameter'] / 2) / 1000
    c, s = math.cos(math.radians(rig_rotation_deg)), math.sin(math.radians(rig_rotation_deg))

    def place(v: Vec) -> Vec:
        x = v[0] + pivot_x
        return (x * c - v[1] * s, x * s + v[1] * c + mast_y_mm / 1000, v[2])

    triangles = [tuple(place(v) for v in tri) for tri in surface['triangles']]
    xs = [v[0] for tri in triangles for v in tri]
    ys = [v[1] for tri in triangles for v in tri]
    zs = [v[2] for tri in triangles for v in tri]
    # Vertices are shared by neighbouring triangles, so this is the grid's
    # centroid - close enough to the area centroid for a moment reference
    n = len(xs)
    return {
        **surface,
        'triangles': triangles,
        'centroid_m': [sum(xs) / n, sum(ys) / n, sum(zs) / n],
        'bounds_m': {'min': [min(xs), min(ys), min(zs)], 'max': [max(xs), max(ys), max(zs)]},
    }


def min_gap_m(a: List[Tuple[Vec, Vec, Vec]], b: List[Tuple[Vec, Vec, Vec]]) -> float:
    """
    Smallest vertex-to-vertex distance between two triangulated surfaces.

    Overestimates the true gap by up to half a grid cell (~0.1 m with the
    default grid), and two surfaces that cross show up as a gap of about
    one cell - callers should treat anything under a few cells as touching.
    """
    pa = sorted({v for tri in a for v in tri})
    pb = sorted({v for tri in b for v in tri})
    best = math.inf
    for p in pa:
        for q in pb:
            d = (p[0] - q[0])**2 + (p[1] - q[1])**2 + (p[2] - q[2])**2
            if d < best:
                best = d
    return math.sqrt(best)


def write_ascii_stl(path: str, solid_name: str, triangles: List[Tuple[Vec, Vec, Vec]]) -> None:
    """Write triangles as an ASCII STL (normals left for the reader to recompute)."""
    with open(path, 'w', newline='\n') as f:
        f.write(f"solid {solid_name}\n")
        for a, b, c in triangles:
            ux, uy, uz = (b[k] - a[k] for k in range(3))
            vx, vy, vz = (c[k] - a[k] for k in range(3))
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            norm = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            f.write(f"  facet normal {nx / norm:.6e} {ny / norm:.6e} {nz / norm:.6e}\n")
            f.write("    outer loop\n")
            for v in (a, b, c):
                f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write(f"endsolid {solid_name}\n")
