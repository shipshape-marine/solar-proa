"""
Trim study: which rig rotation gives one sail the most driving force at a
single apparent wind angle (AWA).

Only one sail is in the model, as in every case.py sweep - the other rig
is left out entirely - so this optimises e.g. the foresail on its own,
before any interaction between the two sails. The rig rotation delta (sail
chord vs. hull centerline, the rig_rotation_* parameters) sets the angle of
attack alpha = AWA - delta, so the study is an ordinary single-reef
case.py sweep over alpha that shares one mesh.

Driving and heeling coefficients are resolved through the AWA as in
src/structural/sail_aero.py:
    C_drive = C_L sin(AWA) - C_D cos(AWA)   (along the hull, forward)
    C_heel  = C_L cos(AWA) + C_D sin(AWA)   (athwartships)
"""

import json
import math
import os
from typing import Any, Dict, List, Optional

from .case import generate_sweep
from .postprocess import CONVERGENCE_WARNING, case_coefficients


def generate_trim_sweep(run_dir: str, params: Dict[str, Any], parameters_path: str,
                        awa_deg: float, rig_rotations: List[float],
                        sail_camber_mm: float, sail_angle_deg: float,
                        mesh: str, n_procs: int,
                        chord_camber_pct: Optional[float] = None) -> Dict[str, Any]:
    """Write one unreefed sail's cases, one per rig rotation, plus sweep.json and Allrun."""
    for rotation in rig_rotations:
        if not awa_deg - 90 <= rotation <= awa_deg:
            raise ValueError(f"rig rotation {rotation} deg gives angle of attack "
                             f"{awa_deg - rotation} deg at AWA {awa_deg} - must be 0-90")
    alphas = [awa_deg - r for r in rig_rotations]
    if len(set(alphas)) != len(alphas):
        raise ValueError(f"duplicate rig rotations: {sorted(rig_rotations)}")

    sweep = generate_sweep(run_dir, params, parameters_path, [0], alphas,
                           sail_camber_mm, sail_angle_deg, mesh, n_procs, full_polar=False,
                           chord_camber_pct=chord_camber_pct)
    sweep['apparent_wind_angle_deg'] = awa_deg
    for case in sweep['reefs'][0]['cases']:
        case['rig_rotation_deg'] = awa_deg - case['angle_of_attack_deg']
    with open(os.path.join(run_dir, 'sweep.json'), 'w') as f:
        json.dump(sweep, f, indent=2)
    return sweep


def _parabola_peak(points: List[List[float]]) -> Optional[float]:
    """x of the vertex of the parabola through three (x, y) points, if it opens downward."""
    (x0, y0), (x1, y1), (x2, y2) = points
    denom = (x0 - x1) * (x0 - x2) * (x1 - x2)
    a = (x2 * (y1 - y0) + x1 * (y0 - y2) + x0 * (y2 - y1)) / denom
    b = (x2**2 * (y0 - y1) + x1**2 * (y2 - y0) + x0**2 * (y1 - y2)) / denom
    return -b / (2 * a) if a < 0 else None


def build_trim_report(run_dir: str) -> Dict[str, Any]:
    """Driving/heeling coefficients per rig rotation and the best one, from a finished trim sweep."""
    with open(os.path.join(run_dir, 'sweep.json'), 'r') as f:
        sweep = json.load(f)
    if 'apparent_wind_angle_deg' not in sweep:
        raise ValueError(f"{run_dir}/sweep.json is not a trim sweep (use trim-setup)")

    beta = math.radians(sweep['apparent_wind_angle_deg'])
    reef = sweep['reefs'][0]
    q_area = 0.5 * sweep['air_density'] * sweep['reference_speed_ms']**2 * reef['reference_area_m2']

    rows, warnings = [], []
    for case in reef['cases']:
        c = case_coefficients(os.path.join(run_dir, case['case']), case['lift_dir'],
                              case['drag_dir'], q_area)
        if c['force_relative_std'] > CONVERGENCE_WARNING:
            warnings.append(f"{case['case']}: force fluctuates {c['force_relative_std']:.1%} "
                            "over the averaging window")
        drive = c['cl'] * math.sin(beta) - c['cd'] * math.cos(beta)
        heel = c['cl'] * math.cos(beta) + c['cd'] * math.sin(beta)
        rows.append({
            'rig_rotation_deg': case['rig_rotation_deg'],
            'angle_of_attack_deg': case['angle_of_attack_deg'],
            'driving_coefficient': round(drive, 4),
            'heeling_coefficient': round(heel, 4),
            'drive_to_heel': round(drive / heel, 3) if heel > 0 else None,
            **c,
        })
    rows.sort(key=lambda r: r['rig_rotation_deg'])

    i = max(range(len(rows)), key=lambda k: rows[k]['driving_coefficient'])
    best = {'rig_rotation_deg': rows[i]['rig_rotation_deg'],
            'driving_coefficient': rows[i]['driving_coefficient']}
    if 0 < i < len(rows) - 1:
        peak = _parabola_peak([[r['rig_rotation_deg'], r['driving_coefficient']]
                               for r in rows[i - 1:i + 2]])
        if peak is not None:
            best['interpolated_rig_rotation_deg'] = round(peak, 1)
    else:
        warnings.append(f"best drive is at the edge of the sweep (rig rotation "
                        f"{rows[i]['rig_rotation_deg']} deg) - the optimum may lie beyond it")

    return {
        'apparent_wind_angle_deg': sweep['apparent_wind_angle_deg'],
        'sail_angle_deg': sweep['sail_angle_deg'],
        'sail_camber_mm': sweep['sail_camber_mm'],
        'chord_camber_pct': sweep.get('chord_camber_pct'),
        'mesh': sweep['mesh'],
        'reference_area_m2': reef['reference_area_m2'],
        'parameters': sweep['parameters'],
        'run_dir': run_dir,
        'best': best,
        'convergence_warnings': warnings,
        'rows': rows,
    }
