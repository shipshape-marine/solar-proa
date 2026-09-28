"""
Capsize analysis - calculates wind speed at which ama lifts when wind comes from ama side.

For a proa, the critical case is wind from the ama side (negative heel),
where stability is lower. This module calculates the wind speed at which
the heeling moment equals the maximum available righting moment.

Pass/fail is a hard cutoff: safety_factor = max_righting_moment /
heeling_moment_at_actual_wind_speed must meet min_safety_factor, the same
convention used by every other check in this package. The model assumes
full sail and no crew weight shift; reefing_percentage now reduces the
sail area (and so the heeling moment) the same way it does for the mast
test. Crew hiking out to windward would add righting moment on top of the
GZ-curve value, but there's no reviewed way to estimate that bonus yet -
crew_righting_moment_bonus_nm is a placeholder for that future work and
defaults to 0 (no effect) until it is.
"""

import math
from typing import Dict, Any, Optional

from .beam_mechanics import GRAVITY


def knots_to_ms(knots: float) -> float:
    """Convert wind speed from knots to m/s."""
    return knots * 0.514444


def ms_to_knots(ms: float) -> float:
    """Convert wind speed from m/s to knots."""
    return ms / 0.514444


def calculate_wind_force(wind_speed_knots: float, sail_area_m2: float,
                         num_sails: int = 2) -> float:
    """
    Calculate total wind force on sails.

    F = 0.72 * V^2 * A per sail (ISO12215-10:2020 Clause 7.2, Table 5, Note 3) -
    the same coefficient mast_analysis.calculate_wind_force uses for the
    same physical load, so the mast and capsize checks don't disagree about
    how hard the wind pushes on the same sail. See that module's docstring
    for the derivation (N=1.2 side-force coefficient, rho=1.2 kg/m3).

    Args:
        wind_speed_knots: Wind speed in knots
        sail_area_m2: Area of one sail in m²
        num_sails: Number of sails (default 2 for proa)

    Returns:
        Total force in Newtons
    """
    V = knots_to_ms(wind_speed_knots)
    force_per_sail = 0.72 * V**2 * sail_area_m2
    return force_per_sail * num_sails


def calculate_heeling_moment(wind_force_n: float,
                              center_of_effort_height_m: float) -> float:
    """
    Calculate heeling moment from wind force.

    Args:
        wind_force_n: Total wind force on sails (N)
        center_of_effort_height_m: Height of sail center of effort above heeling axis (m)

    Returns:
        Heeling moment in N·m
    """
    return wind_force_n * center_of_effort_height_m


def find_max_righting_moment_negative_heel(gz_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find maximum righting moment for negative heel angles (wind from ama side).

    For a proa, negative heel = heeling away from the ama.
    This is the less stable direction.

    Args:
        gz_data: GZ curve data from gz phase

    Returns:
        Dictionary with max righting moment and angle
    """
    gz_curve = gz_data.get('gz_curve', [])

    # Filter to negative heel angles (away from ama)
    negative_heel_points = [
        p for p in gz_curve
        if p.get('converged', False) and p['heel_deg'] < 0
    ]

    if not negative_heel_points:
        return {
            'max_righting_moment_nm': 0,
            'max_righting_angle_deg': None,
            'error': 'No converged negative heel points in GZ data'
        }

    # Find maximum righting moment
    max_rm = max(p['righting_moment_Nm'] for p in negative_heel_points)
    max_point = next(p for p in negative_heel_points if p['righting_moment_Nm'] == max_rm)

    return {
        'max_righting_moment_nm': max_rm,
        'max_righting_angle_deg': max_point['heel_deg'],
        'gz_at_max_m': max_point['gz_m']
    }


def find_capsize_angle(gz_data: Dict[str, Any]) -> Optional[float]:
    """
    Find the capsize angle from GZ summary.

    This is the negative heel angle where GZ crosses zero.

    Args:
        gz_data: GZ curve data

    Returns:
        Capsize angle in degrees, or None if not found
    """
    return gz_data.get('summary', {}).get('capsize_angle_deg')


def estimate_center_of_effort_height(params: Dict[str, Any],
                                      reefing_percentage: float = 0.0) -> float:
    """
    Estimate the height of sail center of effort above the heeling axis.

    The heeling axis is approximately at the waterline.
    CE is roughly at 40% of (reefed) sail height above the boom, matching
    mast_analysis.calculate_mast_geometry's ce_above_partner.

    Args:
        params: Design parameters
        reefing_percentage: Sail reduction (0-100), furled from the boom
            upward (reduces sail_height only).

    Returns:
        CE height in meters
    """
    # Mast partner is roughly at deck level (matches mast_analysis.calculate_mast_geometry's fallback)
    mast_partner_level_mm = params.get('aka_base_level', 1406)

    # Waterline is roughly at bottom_height + some immersion
    # For simplicity, assume heeling axis is near waterline, about 500mm below partner
    heeling_axis_mm = mast_partner_level_mm - 500

    # Boom is at partner level, CE is 40% of effective sail height above boom.
    # sail_height is a required base parameter (see boat/*.json) - matching
    # mast_analysis.calculate_mast_geometry, no silent fallback here either,
    # so a malformed/incomplete params dict raises instead of using a made-up value.
    sail_height_mm = params['sail_height']
    effective_sail_height_mm = sail_height_mm * (100 - reefing_percentage) / 100
    ce_above_boom_mm = effective_sail_height_mm * 0.40

    # CE height above heeling axis
    ce_height_mm = (mast_partner_level_mm - heeling_axis_mm) + ce_above_boom_mm

    return ce_height_mm / 1000  # Convert to meters


def calculate_ama_lift_windspeed(params: Dict[str, Any],
                                  gz_data: Dict[str, Any],
                                  wind_speed_knots: float = 25.0,
                                  min_safety_factor: float = 2.0,
                                  reefing_percentage: float = 0.0,
                                  crew_righting_moment_bonus_nm: float = 0.0) -> Dict[str, Any]:
    """
    Check ama-lift (capsize) margin at the given wind speed, wind from the
    ama side (the proa's less stable direction).

    safety_factor = max_righting_moment / heeling_moment_at_wind_speed_knots.
    This is a hard pass/fail, using the same min_safety_factor convention as
    every other structural check.

    Args:
        params: Design parameters
        gz_data: GZ curve data from gz phase
        wind_speed_knots: Actual/operating wind speed to check against
        min_safety_factor: Minimum required safety factor
        reefing_percentage: Sail reduction (0-100), reduces sail area and CE
            height the same way as the mast test
        crew_righting_moment_bonus_nm: Placeholder for a future crew-weight-
            shift model (hiking out to windward adds righting moment beyond
            the static GZ curve). Defaults to 0 - not yet estimated from any
            parameter here.

    Returns:
        Analysis results with the capsize safety factor and critical wind speeds
    """
    # Sail area (reefed) - required base parameters, no silent fallback
    # (matches mast_analysis.calculate_mast_geometry)
    sail_height = params['sail_height']
    sail_width = params['sail_width']
    effective_sail_height = sail_height * (100 - reefing_percentage) / 100
    sail_area_m2_before_reefing = (sail_height * sail_width) / 1e6
    sail_area_m2 = (effective_sail_height * sail_width) / 1e6
    num_sails = 2  # Proa has two sails

    # Center of effort height (reefed)
    ce_height_m = estimate_center_of_effort_height(params, reefing_percentage)

    # Maximum righting moment from GZ curve (negative heel), plus any
    # (currently unmodeled) crew weight-shift bonus
    rm_data = find_max_righting_moment_negative_heel(gz_data)
    max_righting_moment = rm_data['max_righting_moment_nm'] + crew_righting_moment_bonus_nm

    # Capsize angle from GZ data
    capsize_angle = find_capsize_angle(gz_data)

    # Critical wind speed: heeling moment = max righting moment (safety_factor = 1)
    # Heeling moment = 0.72 * V² * A * num_sails * ce_height (ISO12215-10 coefficient)
    coefficient = 0.72 * sail_area_m2 * num_sails * ce_height_m

    if coefficient > 0 and max_righting_moment > 0:
        V_squared = max_righting_moment / coefficient
        V_ms = math.sqrt(V_squared)
        critical_windspeed_knots = ms_to_knots(V_ms)
        # Wind speed at which safety_factor drops to exactly min_safety_factor
        safe_windspeed_limit_knots = critical_windspeed_knots / math.sqrt(min_safety_factor)
    else:
        critical_windspeed_knots = 0
        safe_windspeed_limit_knots = 0

    # Heeling moment and safety factor at the actual/operating wind speed
    wind_force = calculate_wind_force(wind_speed_knots, sail_area_m2, num_sails)
    heeling_moment = calculate_heeling_moment(wind_force, ce_height_m)

    if max_righting_moment <= 0:
        # No inherent stability margin at all (degenerate/missing GZ data,
        # or a hull with no righting ability at this heel) - this is the
        # most dangerous state possible, not a safe one. Hard fail
        # regardless of wind speed.
        safety_factor = 0.0
    elif heeling_moment <= 0:
        # No wind-driven heeling moment (e.g. wind_speed_knots == 0) - no
        # capsize risk from wind at all.
        safety_factor = float('inf')
    else:
        safety_factor = max_righting_moment / heeling_moment

    passed = safety_factor >= min_safety_factor

    return {
        'test_name': 'ama_lift_windspeed',
        'description': f'Ama-lift/capsize margin under {wind_speed_knots:.0f} knot wind (wind from ama side)',
        'passed': passed,
        'sail_geometry': {
            'sail_area_m2': round(sail_area_m2, 2),
            'sail_area_m2_before_reefing': round(sail_area_m2_before_reefing, 2),
            'reefing_percentage': reefing_percentage,
            'num_sails': num_sails,
            'total_sail_area_m2': round(sail_area_m2 * num_sails, 2),
            'ce_height_m': round(ce_height_m, 2),
        },
        'stability': {
            'max_righting_moment_nm': round(max_righting_moment, 1),
            'max_righting_angle_deg': rm_data.get('max_righting_angle_deg'),
            'capsize_angle_deg': capsize_angle,
            'crew_righting_moment_bonus_nm': crew_righting_moment_bonus_nm,
        },
        'at_wind_speed': {
            'wind_speed_knots': wind_speed_knots,
            'wind_force_n': round(wind_force, 1),
            'heeling_moment_nm': round(heeling_moment, 1),
            'moment_ratio': round(heeling_moment / max_righting_moment, 2) if max_righting_moment > 0 else None,
        },
        'summary': {
            'ama_lift_windspeed_knots': round(critical_windspeed_knots, 1),
            'safe_windspeed_limit_knots': round(safe_windspeed_limit_knots, 1),
            'safety_factor': round(safety_factor, 2) if safety_factor != float('inf') else safety_factor,
            'result': 'PASS' if passed else 'FAIL'
        }
    }
