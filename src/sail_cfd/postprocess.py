"""
Turn a finished OpenFOAM sweep into a sail polar file for
src/structural/sail_aero.py.

For each case, the 'forces' function object's force and moment histories
(about CofR (0 0 0), the sea surface below the pivot) are averaged over the
last AVERAGE_FRACTION of iterations - stalled high-alpha cases never settle
to a steady value under steady RANS, so a single last iteration would be
arbitrary. The spread over that window is reported per point so poorly
converged cases are visible rather than silently averaged.

Lift and drag are the force components along the sweep's lift/drag
directions, nondimensionalised by 0.5 * rho * U^2 * A with A the same sail
area the structural checks use (sail_width x reefed height). The centre of
pressure height comes from the horizontal force and the moment about the
origin: z = (My*Fx - Mx*Fy) / (Fx^2 + Fy^2).
"""

import json
import math
import os
import statistics
from typing import Any, Dict, List

AVERAGE_FRACTION = 0.2
# Flag a point when its force fluctuates by more than this (relative std)
# over the averaging window
CONVERGENCE_WARNING = 0.02


def read_vector_history(path: str) -> List[List[float]]:
    """
    Read a forces function-object .dat file into rows of [time, Fx, Fy, Fz]
    (total = pressure + viscous).

    Handles the column-per-component layout of current openfoam.com
    releases (header '# Time total_x total_y total_z ...') and the older
    parenthesised '((px py pz) (vx vy vz))' layout.
    """
    header: List[str] = []
    rows = []
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                names = line[1:].split()
                if names and names[0] == 'Time':
                    header = names
                continue
            values = [float(v) for v in line.replace('(', ' ').replace(')', ' ').split()]
            if not values:
                continue
            if 'total_x' in header:
                i = header.index('total_x')
                rows.append([values[0], values[i], values[i + 1], values[i + 2]])
            else:
                # time, pressure xyz, viscous xyz[, porous xyz]
                rows.append([values[0], values[1] + values[4], values[2] + values[5],
                             values[3] + values[6]])
    if not rows:
        raise ValueError(f"{path}: no data rows")
    return rows


def _find_dat(case_dir: str, name: str, function: str = 'forces') -> str:
    """postProcessing/<function>/<startTime>/<name>.dat, taking the latest restart."""
    base = os.path.join(case_dir, 'postProcessing', function)
    if not os.path.isdir(base):
        raise FileNotFoundError(f"{base} missing - did the case run?")
    starts = sorted(os.listdir(base), key=float)
    return os.path.join(base, starts[-1], f"{name}.dat")


def mean_force_moment(case_dir: str, function: str = 'forces') -> Dict[str, Any]:
    """
    One forces function object's force and moment, averaged over the last
    AVERAGE_FRACTION of iterations, plus the centre of pressure height and
    the convergence spread over that window.
    """
    force = read_vector_history(_find_dat(case_dir, 'force', function))
    moment = read_vector_history(_find_dat(case_dir, 'moment', function))
    n = max(1, int(len(force) * AVERAGE_FRACTION))
    f_win, m_win = force[-n:], moment[-n:]

    def mean(rows, k):
        return statistics.fmean(r[k] for r in rows)

    f = [mean(f_win, 1), mean(f_win, 2), mean(f_win, 3)]
    mx, my = mean(m_win, 1), mean(m_win, 2)

    magnitudes = [math.hypot(r[1], r[2]) for r in f_win]
    mean_mag = statistics.fmean(magnitudes)
    f_h2 = f[0] * f[0] + f[1] * f[1]

    return {
        'force': f,
        'center_of_pressure_height_m': round((my * f[0] - mx * f[1]) / f_h2, 3) if f_h2 > 0 else None,
        'iterations': int(force[-1][0]),
        'averaged_iterations': n,
        'force_relative_std': round(statistics.pstdev(magnitudes) / mean_mag if mean_mag > 0 else 0.0, 4),
    }


def case_coefficients(case_dir: str, lift_dir: List[float], drag_dir: List[float],
                      q_area: float) -> Dict[str, Any]:
    """Averaged C_L, C_D, centre of pressure height and convergence spread for one case."""
    m = mean_force_moment(case_dir)
    f = m.pop('force')
    return {
        'cl': round(sum(f[k] * lift_dir[k] for k in range(3)) / q_area, 4),
        'cd': round(sum(f[k] * drag_dir[k] for k in range(3)) / q_area, 4),
        **m,
    }


def build_polar(run_dir: str, min_sheeting_angle_deg: float) -> Dict[str, Any]:
    """Assemble the sail polar file from every case in run_dir/sweep.json."""
    with open(os.path.join(run_dir, 'sweep.json'), 'r') as f:
        sweep = json.load(f)

    q = 0.5 * sweep['air_density'] * sweep['reference_speed_ms']**2
    polars, warnings = [], []
    for reef in sweep['reefs']:
        points = []
        for case in reef['cases']:
            c = case_coefficients(os.path.join(run_dir, case['case']), case['lift_dir'],
                                  case['drag_dir'], q * reef['reference_area_m2'])
            if c['force_relative_std'] > CONVERGENCE_WARNING:
                warnings.append(f"{case['case']}: force fluctuates {c['force_relative_std']:.1%} "
                                "over the averaging window")
            points.append({'angle_of_attack_deg': case['angle_of_attack_deg'], **c})
        polars.append({
            'reefing_percentage': reef['reefing_percentage'],
            'reference_area_m2': reef['reference_area_m2'],
            'geometric_ce_height_m': reef['geometric_ce_height_m'],
            'points': points,
        })

    return {
        'source': 'openfoam',
        'description': (f"OpenFOAM simpleFoam k-omega SST sweep, {sweep['mesh']} mesh "
                        f"(sail level {sweep['sail_level']}), single sail only, camber "
                        f"{sweep['sail_camber_mm']} mm, sail_angle {sweep['sail_angle_deg']} deg, "
                        f"from {sweep['parameters']}"),
        'min_sheeting_angle_deg': min_sheeting_angle_deg,
        'min_sheeting_angle_note': 'Closest the sail chord can be sheeted to the hull '
                                   'centerline. Not an output of the CFD - set by hand.',
        'run_dir': run_dir,
        'convergence_warnings': warnings,
        'polars': polars,
    }
