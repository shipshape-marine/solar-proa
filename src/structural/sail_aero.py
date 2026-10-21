"""
Sail aerodynamic force coefficients for a specific apparent wind angle.

ISO 12215-10's wind load (mast_analysis.calculate_wind_force) uses a single
side force coefficient N=1.2 regardless of heading - fine as a design load,
but it can't say how much to reef for a particular wind. This module turns a
sail polar (lift and drag coefficients C_L, C_D vs. angle of attack alpha,
one polar per reefing level) into the two coefficients the structural checks
need at a given apparent wind angle (AWA) beta:

- Total force coefficient C_T = sqrt(C_L^2 + C_D^2) - what bends the mast.
  The mast is an unstayed round tube, so it doesn't matter which way the
  force points: running downwind with the sail squared off, drag alone
  still loads it.
- Heeling (athwartships) coefficient C_H = C_L cos(beta) + C_D sin(beta) -
  what lifts the ama. Peaks close-hauled/reaching, not just beam-on.

Lift is perpendicular to the apparent wind and drag along it, so both are
resolved through beta (the boat's centerline vs. the apparent wind), while
alpha (the sail chord vs. the apparent wind) picks the polar point. The two
are linked by the sheeting angle delta (sail chord vs. centerline):
alpha = beta - delta, with delta limited to [min_sheeting_angle_deg, 90]
(can't sheet past the centerline, rig doesn't rotate past square). Alpha is
also capped at 90 - a sail rotated past broadside isn't a real trim.

Within that feasible range the trim is the crew's choice, so two
assumptions are offered:
- 'worst_case' (default): the alpha that maximizes each load separately -
  e.g. a gust hitting an over-sheeted, stalled sail. Use for safety limits.
- 'max_drive': the alpha that maximizes driving force (C_L sin(beta) -
  C_D cos(beta)) - a well-sailed boat. Less conservative.

Polar files live in constant/sail_polar/. placeholder.json is generic
soft-sail-shaped data, NOT measured or simulated for this rig - see
src/sail_cfd/ for the OpenFOAM pipeline that generates a real one.
"""

import json
import math
from typing import Any, Dict, List

TRIM_ASSUMPTIONS = ('worst_case', 'max_drive')

# Resolution of the alpha sweep within the feasible trim range
ALPHA_STEP_DEG = 0.5


def load_sail_polar(path: str) -> Dict[str, Any]:
    """
    Load and validate a sail polar file (see constant/sail_polar/).

    Returns the parsed dict with each polar's points sorted by angle of
    attack and the polars sorted by reefing_percentage.
    """
    with open(path, 'r') as f:
        polar_file = json.load(f)

    polars = polar_file.get('polars')
    if not polars:
        raise ValueError(f"{path}: no 'polars' entries")
    if 'min_sheeting_angle_deg' not in polar_file:
        raise ValueError(f"{path}: missing 'min_sheeting_angle_deg'")

    for polar in polars:
        points = sorted(polar['points'], key=lambda p: p['angle_of_attack_deg'])
        alphas = [p['angle_of_attack_deg'] for p in points]
        if alphas[0] > 0.0 or alphas[-1] < 90.0:
            raise ValueError(f"{path}: polar at reef {polar['reefing_percentage']}% must "
                             f"span angle of attack 0-90 deg, got {alphas[0]}-{alphas[-1]}")
        polar['points'] = points
    polar_file['polars'] = sorted(polars, key=lambda p: p['reefing_percentage'])
    return polar_file


def _interpolate(points: List[Dict[str, float]], alpha_deg: float) -> Dict[str, float]:
    """Linearly interpolate C_L and C_D at alpha_deg within one polar."""
    for lo, hi in zip(points, points[1:]):
        if lo['angle_of_attack_deg'] <= alpha_deg <= hi['angle_of_attack_deg']:
            span = hi['angle_of_attack_deg'] - lo['angle_of_attack_deg']
            t = (alpha_deg - lo['angle_of_attack_deg']) / span if span > 0 else 0.0
            return {'cl': lo['cl'] + t * (hi['cl'] - lo['cl']),
                    'cd': lo['cd'] + t * (hi['cd'] - lo['cd'])}
    raise ValueError(f"angle of attack {alpha_deg} outside the polar's range")


def lift_drag_at(polar_file: Dict[str, Any], alpha_deg: float,
                 reefing_percentage: float) -> Dict[str, float]:
    """
    C_L and C_D at an angle of attack and reefing level, interpolating
    linearly between the polars either side of reefing_percentage (and
    clamping to the nearest polar outside the simulated reef range - a
    placeholder file with a single polar applies it at every reef level).
    """
    polars = polar_file['polars']
    if reefing_percentage <= polars[0]['reefing_percentage']:
        return _interpolate(polars[0]['points'], alpha_deg)
    if reefing_percentage >= polars[-1]['reefing_percentage']:
        return _interpolate(polars[-1]['points'], alpha_deg)
    for lo, hi in zip(polars, polars[1:]):
        if lo['reefing_percentage'] <= reefing_percentage <= hi['reefing_percentage']:
            t = ((reefing_percentage - lo['reefing_percentage'])
                 / (hi['reefing_percentage'] - lo['reefing_percentage']))
            a = _interpolate(lo['points'], alpha_deg)
            b = _interpolate(hi['points'], alpha_deg)
            return {'cl': a['cl'] + t * (b['cl'] - a['cl']),
                    'cd': a['cd'] + t * (b['cd'] - a['cd'])}
    raise AssertionError("unreachable: polars are sorted by reefing_percentage")


def feasible_alpha_range(apparent_wind_angle_deg: float,
                         min_sheeting_angle_deg: float) -> List[float]:
    """
    [alpha_min, alpha_max] the crew can actually set at this AWA:
    alpha = AWA - delta with delta in [min_sheeting_angle_deg, 90], alpha
    capped to [0, 90]. Pointing closer than min_sheeting_angle_deg leaves
    only alpha=0 (sail luffing).
    """
    alpha_max = min(90.0, max(0.0, float(apparent_wind_angle_deg - min_sheeting_angle_deg)))
    alpha_min = min(alpha_max, max(0.0, float(apparent_wind_angle_deg - 90.0)))
    return [alpha_min, alpha_max]


def sail_force_coefficients(polar_file: Dict[str, Any],
                            apparent_wind_angle_deg: float,
                            reefing_percentage: float,
                            trim: str = 'worst_case') -> Dict[str, Any]:
    """
    Total (mast) and heeling (capsize) force coefficients at an apparent
    wind angle (0=head-to-wind, 90=beam, 180=dead downwind), under the given
    trim assumption - see module docstring.

    Returns:
        Dict with 'total_force_coefficient', 'heeling_force_coefficient',
        the angle of attack each was taken at, and the feasible alpha range.
    """
    if not 0.0 <= apparent_wind_angle_deg <= 180.0:
        raise ValueError(f"apparent_wind_angle_deg must be within 0-180, got {apparent_wind_angle_deg}")
    if trim not in TRIM_ASSUMPTIONS:
        raise ValueError(f"trim must be one of {TRIM_ASSUMPTIONS}, got {trim!r}")

    beta = math.radians(apparent_wind_angle_deg)
    alpha_min, alpha_max = feasible_alpha_range(apparent_wind_angle_deg,
                                                polar_file['min_sheeting_angle_deg'])

    n_steps = max(1, math.ceil((alpha_max - alpha_min) / ALPHA_STEP_DEG))
    samples = []
    for i in range(n_steps + 1):
        alpha = alpha_min + (alpha_max - alpha_min) * i / n_steps
        c = lift_drag_at(polar_file, alpha, reefing_percentage)
        samples.append({
            'alpha': alpha,
            'total': math.hypot(c['cl'], c['cd']),
            # Clamped at 0: a negative value means the sail pushes the ama
            # down (to windward), which isn't an ama-lift load
            'heeling': max(0.0, c['cl'] * math.cos(beta) + c['cd'] * math.sin(beta)),
            'driving': c['cl'] * math.sin(beta) - c['cd'] * math.cos(beta),
        })

    if trim == 'worst_case':
        total_at = max(samples, key=lambda s: s['total'])
        heeling_at = max(samples, key=lambda s: s['heeling'])
    else:
        total_at = heeling_at = max(samples, key=lambda s: s['driving'])

    return {
        'apparent_wind_angle_deg': apparent_wind_angle_deg,
        'reefing_percentage': reefing_percentage,
        'trim': trim,
        'feasible_angle_of_attack_deg': [round(alpha_min, 1), round(alpha_max, 1)],
        'total_force_coefficient': round(total_at['total'], 3),
        'total_force_angle_of_attack_deg': round(total_at['alpha'], 1),
        'heeling_force_coefficient': round(heeling_at['heeling'], 3),
        'heeling_force_angle_of_attack_deg': round(heeling_at['alpha'], 1),
        'polar_source': polar_file.get('source', 'unknown'),
    }
