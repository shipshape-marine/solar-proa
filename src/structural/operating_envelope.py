"""
Operating envelope - given the apparent wind (speed and angle relative to
the boat) and wave conditions, find the minimum sail reefing that keeps the
wind/reef-dependent structural checks (mast wind loading, ama-lift/capsize)
at or above min_safety_factor.

Unlike the ISO design check (python -m src.structural, which always applies
ISO 12215-10's N=1.2 side force coefficient), the sail loads here come from
a sail polar (constant/sail_polar/) resolved at the given apparent wind
angle by sail_aero.sail_force_coefficients: the total force coefficient
drives the mast check and the heeling coefficient drives the capsize check.
This is operating guidance for a specific wind, not a substitute for the
ISO design check.

Wave-slam and the other load cases don't depend on sail trim or wind angle
at all and are reported unchanged for context.
"""

import argparse
import json
import math
import os
import sys
from typing import Any, Dict

from .mast_analysis import validate_mast
from .capsize_analysis import calculate_ama_lift_windspeed
from .sail_aero import TRIM_ASSUMPTIONS, load_sail_polar, sail_force_coefficients
from .wave_slam import validate_wave_slam, validate_frontal_wave_slam, validate_sideways_wave_slam

DEFAULT_SAIL_POLAR = os.path.join(os.path.dirname(__file__), '..', '..',
                                  'constant', 'sail_polar', 'placeholder.json')


def find_minimum_reefing(params: Dict[str, Any],
                          mass_data: Dict[str, Any],
                          gz_data: Dict[str, Any],
                          polar_file: Dict[str, Any],
                          apparent_wind_speed_knots: float,
                          apparent_wind_angle_deg: float,
                          trim: str = 'worst_case',
                          min_safety_factor: float = 2.0,
                          tolerance: float = 0.5) -> Dict[str, Any]:
    """
    Binary search for the minimum reefing_percentage (0-100) at which both
    the mast wind-loading test and the ama-lift/capsize test pass at the
    given apparent wind speed and angle.

    Sail force coefficients are re-evaluated at each reefing level, since
    an OpenFOAM polar file can hold a different polar per reef level.
    Bisection assumes safety factor is non-decreasing in reefing - true as
    long as the force coefficient doesn't grow faster than the sail area
    shrinks, which holds for any physically plausible polar set.

    Args:
        params: Design parameters
        mass_data: Mass calculation results
        gz_data: GZ curve data (required - the capsize check needs it)
        polar_file: Loaded sail polar (sail_aero.load_sail_polar)
        apparent_wind_speed_knots: Apparent wind speed felt by the boat
        apparent_wind_angle_deg: Apparent wind angle off the bow, 0-180
            (0=head-to-wind, 90=beam, 180=dead downwind), wind from the ama side
        trim: Trim assumption - see sail_aero
        min_safety_factor: Minimum required safety factor
        tolerance: Bisection stops once the bracket is within this many
            reefing percentage points

    Returns:
        Dict with 'reefing_percentage_needed' (float, or None if unreachable
        even at 100% reefing), 'mast_result', 'capsize_result',
        'sail_coefficients' at the recommended reef, and 'convergent' (False
        if a wind-independent term - e.g. the mast's own dead-weight
        compression - keeps at least one check failing even at 100%
        reefing, so reefing alone can't fix it).
    """
    if gz_data is None:
        raise ValueError("gz_data is required - the capsize/ama-lift check needs the GZ curve")

    def check(reef: float):
        coefficients = sail_force_coefficients(polar_file, apparent_wind_angle_deg, reef, trim)
        mast = validate_mast(params, mass_data, apparent_wind_speed_knots, min_safety_factor, reef,
                             force_coefficient=coefficients['total_force_coefficient'])
        capsize = calculate_ama_lift_windspeed(
            params, gz_data, apparent_wind_speed_knots, min_safety_factor, reef,
            heeling_force_coefficient=coefficients['heeling_force_coefficient'])
        return mast, capsize, coefficients

    mast0, capsize0, coef0 = check(0.0)
    if mast0['passed'] and capsize0['passed']:
        return {
            'reefing_percentage_needed': 0.0,
            'mast_result': mast0,
            'capsize_result': capsize0,
            'sail_coefficients': coef0,
            'convergent': True,
        }

    mast100, capsize100, coef100 = check(100.0)
    if not (mast100['passed'] and capsize100['passed']):
        failing = []
        if not capsize100['passed']:
            failing.append('ama_lift_windspeed (capsize)')
        for check_name, check_result in mast100.get('checks', {}).items():
            if check_result.get('result') == 'FAIL':
                failing.append(f'mast.{check_name}')
        failing_desc = ', '.join(failing) if failing else 'an unidentified check'
        return {
            'reefing_percentage_needed': None,
            'mast_result': mast100,
            'capsize_result': capsize100,
            'sail_coefficients': coef100,
            'convergent': False,
            'note': ('Even fully reefed (100%), the following still fail at '
                     f'{apparent_wind_speed_knots:.0f} knots: {failing_desc}. Reefing reduces '
                     "sail area to (essentially) zero at 100%, so whatever's still "
                     'failing is not wind/sail-load-driven - e.g. local_buckling is a '
                     "pure D/t geometry check and column_below_partner has a wind-"
                     "independent dead-weight term - and needs a design change, not "
                     'a trim change. Check mast_result[\'checks\'] above for which.'),
        }

    lo, hi = 0.0, 100.0
    while hi - lo > tolerance:
        mid = (lo + hi) / 2
        mast_mid, capsize_mid, _ = check(mid)
        if mast_mid['passed'] and capsize_mid['passed']:
            hi = mid
        else:
            lo = mid

    # Only hi is proven to pass, so round toward more reefing (never onto the
    # failing side of the boundary) and re-run the checks at the reported
    # value, so the returned results describe exactly what's recommended.
    needed = min(100.0, math.ceil(hi * 10) / 10)
    mast_needed, capsize_needed, coef_needed = check(needed)

    return {
        'reefing_percentage_needed': needed,
        'mast_result': mast_needed,
        'capsize_result': capsize_needed,
        'sail_coefficients': coef_needed,
        'convergent': True,
    }


def recommend_operating_configuration(params: Dict[str, Any],
                                       mass_data: Dict[str, Any],
                                       gz_data: Dict[str, Any],
                                       polar_file: Dict[str, Any],
                                       apparent_wind_speed_knots: float,
                                       apparent_wind_angle_deg: float,
                                       trim: str = 'worst_case',
                                       min_safety_factor: float = 2.0,
                                       impact_velocity_ms: float = 3.0,
                                       dynamic_factor: float = 2.5) -> Dict[str, Any]:
    """
    Given the apparent wind (and, separately, wave impact conditions),
    recommend the minimum reefing percentage that keeps the wind-dependent
    checks safe, and report the wave-slam checks alongside for context.

    Wave slam and the other load cases here are independent of sail trim
    (they're hull/impact checks, not sail-load checks), so they're computed
    once and are NOT part of the reefing search - if one of them fails, no
    amount of reefing changes that; it's a separate structural concern, not
    an operating-configuration one.
    """
    reefing_result = find_minimum_reefing(params, mass_data, gz_data, polar_file,
                                           apparent_wind_speed_knots, apparent_wind_angle_deg,
                                           trim, min_safety_factor)

    wave_slam_result = validate_wave_slam(params, impact_velocity_ms, dynamic_factor,
                                           min_safety_factor)
    frontal_slam_result = validate_frontal_wave_slam(params, impact_velocity_ms, dynamic_factor,
                                                       min_safety_factor)
    sideways_slam_result = validate_sideways_wave_slam(params, impact_velocity_ms, dynamic_factor,
                                                         min_safety_factor)
    wave_checks_passed = (wave_slam_result['passed'] and frontal_slam_result['passed']
                          and sideways_slam_result['passed'])

    return {
        'apparent_wind_speed_knots': apparent_wind_speed_knots,
        'apparent_wind_angle_deg': apparent_wind_angle_deg,
        'trim': trim,
        'sail_polar_source': polar_file.get('source', 'unknown'),
        'min_safety_factor_required': min_safety_factor,
        'reefing': reefing_result,
        'wave_conditions': {
            'impact_velocity_ms': impact_velocity_ms,
            'dynamic_factor': dynamic_factor,
            'wave_slam': wave_slam_result,
            'frontal_wave_slam': frontal_slam_result,
            'sideways_wave_slam': sideways_slam_result,
            'passed': wave_checks_passed,
        },
        'overall_operable': reefing_result['convergent'] and wave_checks_passed,
    }


def load_condition(path: str) -> Dict[str, Any]:
    """
    Load a sailing/weather condition file - see constant/conditions/ for the
    expected shape and examples. apparent_wind_speed_kt and
    apparent_wind_angle_deg are required; the rest fall back to the same
    defaults recommend_operating_configuration uses.
    """
    with open(path, 'r') as f:
        condition = json.load(f)

    for field in ('apparent_wind_speed_kt', 'apparent_wind_angle_deg'):
        if field not in condition:
            raise ValueError(f"{path}: missing required field '{field}'")

    return {
        'apparent_wind_speed_knots': condition['apparent_wind_speed_kt'],
        'apparent_wind_angle_deg': condition['apparent_wind_angle_deg'],
        'trim': condition.get('trim', 'worst_case'),
        'impact_velocity_ms': condition.get('impact_velocity_ms', 3.0),
        'dynamic_factor': condition.get('dynamic_factor', 2.5),
        'min_safety_factor': condition.get('min_safety_factor', 2.0),
    }


def print_recommendation_report(result: Dict[str, Any], condition_path: str,
                                polar_path: str) -> None:
    """Print a human-readable operating-configuration recommendation."""
    reefing = result['reefing']
    coef = reefing['sail_coefficients']
    waves = result['wave_conditions']

    print()
    print("=" * 60)
    print("OPERATING CONFIGURATION RECOMMENDATION")
    print("=" * 60)
    print(f"Condition file: {condition_path}")
    print(f"Apparent wind: {result['apparent_wind_speed_knots']:.0f} knots at "
          f"{result['apparent_wind_angle_deg']:.0f} deg off the bow (ama side)")
    print(f"Trim assumption: {result['trim']}")
    print(f"Sail polar: {polar_path} (source: {result['sail_polar_source']})")
    if result['sail_polar_source'] == 'placeholder':
        print("  ⚠ PLACEHOLDER polar - generic data, not this rig. Generate a real one")
        print("    with src/sail_cfd/ before relying on this recommendation.")
    print(f"Required safety factor: {result['min_safety_factor_required']:.1f}")

    print()
    if not reefing['convergent']:
        print("✗ NOT OPERABLE in this wind - reefing alone cannot reach the")
        print(f"  required safety factor. {reefing['note']}")
    elif reefing['reefing_percentage_needed'] == 0.0:
        print("✓ Full sail is safe - no reefing required.")
    else:
        print(f"✓ Reef to {math.ceil(reefing['reefing_percentage_needed']):.0f}% to stay within safety limits.")

    print(f"\n  Sail force coefficients at this reef (per sail, vs. ISO N=1.20):")
    print(f"    Total (mast):      {coef['total_force_coefficient']:.2f}  "
          f"at angle of attack {coef['total_force_angle_of_attack_deg']:.0f} deg")
    print(f"    Heeling (capsize): {coef['heeling_force_coefficient']:.2f}  "
          f"at angle of attack {coef['heeling_force_angle_of_attack_deg']:.0f} deg")

    mast_sf = reefing['mast_result']['summary']['safety_factor']
    capsize_sf = reefing['capsize_result']['summary']['safety_factor']
    print(f"\n  Mast wind-loading SF:     {mast_sf:.2f} {'PASS' if reefing['mast_result']['passed'] else 'FAIL'}")
    print(f"  Ama-lift/capsize SF:      {capsize_sf:.2f} {'PASS' if reefing['capsize_result']['passed'] else 'FAIL'}")

    print(f"\nWave conditions (impact {waves['impact_velocity_ms']:.1f} m/s, "
          f"{waves['dynamic_factor']:.1f}x dynamic factor) - unaffected by reefing:")
    for name, key in [('Vertical wave slam', 'wave_slam'),
                       ('Frontal wave slam', 'frontal_wave_slam'),
                       ('Sideways wave slam', 'sideways_wave_slam')]:
        r = waves[key]
        sf = r['summary']['min_safety_factor']
        print(f"  {name}: SF={sf:.2f} {'PASS' if r['passed'] else 'FAIL'}")

    print()
    print("=" * 60)
    status = "✓ OPERABLE" if result['overall_operable'] else "✗ NOT OPERABLE"
    print(f"OVERALL: {status}")
    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Recommend a safe reefing percentage for a given apparent wind and wave condition')
    parser.add_argument('--parameters', required=True,
                        help='Path to parameter JSON artifact')
    parser.add_argument('--mass', required=True,
                        help='Path to mass JSON artifact')
    parser.add_argument('--gz', required=True,
                        help='Path to GZ curve JSON artifact')
    parser.add_argument('--condition', required=True,
                        help='Path to a condition JSON file (see constant/conditions/)')
    parser.add_argument('--sail-polar', default=os.path.normpath(DEFAULT_SAIL_POLAR),
                        help='Path to a sail polar JSON file (default: the placeholder in '
                             'constant/sail_polar/)')
    parser.add_argument('--output',
                        help='Optional path to write the full result JSON')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress human-readable output')

    args = parser.parse_args()

    with open(args.parameters, 'r') as f:
        params = json.load(f)
    with open(args.mass, 'r') as f:
        mass_data = json.load(f)
    with open(args.gz, 'r') as f:
        gz_data = json.load(f)

    condition = load_condition(args.condition)
    if condition['trim'] not in TRIM_ASSUMPTIONS:
        parser.error(f"condition 'trim' must be one of {TRIM_ASSUMPTIONS}, got {condition['trim']!r}")
    polar_file = load_sail_polar(args.sail_polar)

    result = recommend_operating_configuration(
        params, mass_data, gz_data, polar_file,
        apparent_wind_speed_knots=condition['apparent_wind_speed_knots'],
        apparent_wind_angle_deg=condition['apparent_wind_angle_deg'],
        trim=condition['trim'],
        min_safety_factor=condition['min_safety_factor'],
        impact_velocity_ms=condition['impact_velocity_ms'],
        dynamic_factor=condition['dynamic_factor'],
    )

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)

    if not args.quiet:
        print_recommendation_report(result, args.condition, args.sail_polar)

    sys.exit(0 if result['overall_operable'] else 1)


if __name__ == "__main__":
    main()
