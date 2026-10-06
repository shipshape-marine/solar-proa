"""
Operating envelope - given actual wind/wave conditions, find the minimum
sail reefing that keeps the wind/reef-dependent structural checks (mast
wind loading, ama-lift/capsize) at or above min_safety_factor.

Only mast_analysis.validate_mast and capsize_analysis.calculate_ama_lift_windspeed
take reefing_percentage as an input - none of the point-of-sail fields
(sail_angle, rig_rotation, wind_direction) are read anywhere in src/structural,
because the ISO 12215-10 wind-load model already assumes the worst case
(sail perpendicular to the wind) regardless of heading. So reefing is the
only lever this search can turn; wave-slam and the other load cases don't
depend on sail trim at all and are reported unchanged for context.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

from .mast_analysis import validate_mast
from .capsize_analysis import calculate_ama_lift_windspeed
from .wave_slam import validate_wave_slam, validate_frontal_wave_slam, validate_sideways_wave_slam


def find_minimum_reefing(params: Dict[str, Any],
                          mass_data: Dict[str, Any],
                          gz_data: Dict[str, Any],
                          wind_speed_knots: float,
                          min_safety_factor: float = 2.0,
                          tolerance: float = 0.5) -> Dict[str, Any]:
    """
    Binary search for the minimum reefing_percentage (0-100) at which both
    the mast wind-loading test and the ama-lift/capsize test pass at the
    given wind speed.

    Both checks' safety factor is monotonically non-decreasing in
    reefing_percentage (less sail area -> less force/moment), so bisection
    is sufficient and doesn't require re-deriving a closed form if either
    check's formula changes later.

    Args:
        params: Design parameters
        mass_data: Mass calculation results
        gz_data: GZ curve data (required - the capsize check needs it)
        wind_speed_knots: Actual/operating wind speed to check against
        min_safety_factor: Minimum required safety factor
        tolerance: Bisection stops once the bracket is within this many
            reefing percentage points

    Returns:
        Dict with 'reefing_percentage_needed' (float, or None if unreachable
        even at 100% reefing), 'mast_result', 'capsize_result', and
        'convergent' (False if a wind-independent term - e.g. the mast's own
        dead-weight compression - keeps at least one check failing even at
        100% reefing, so reefing alone can't fix it).
    """
    if gz_data is None:
        raise ValueError("gz_data is required - the capsize/ama-lift check needs the GZ curve")

    def check(reef: float):
        mast = validate_mast(params, mass_data, wind_speed_knots, min_safety_factor, reef)
        capsize = calculate_ama_lift_windspeed(params, gz_data, wind_speed_knots,
                                                min_safety_factor, reef)
        return mast, capsize

    mast0, capsize0 = check(0.0)
    if mast0['passed'] and capsize0['passed']:
        return {
            'reefing_percentage_needed': 0.0,
            'mast_result': mast0,
            'capsize_result': capsize0,
            'convergent': True,
        }

    mast100, capsize100 = check(100.0)
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
            'convergent': False,
            'note': ('Even fully reefed (100%), the following still fail at '
                     f'{wind_speed_knots:.0f} knots: {failing_desc}. Reefing reduces '
                     "sail area to (essentially) zero at 100%, so whatever's still "
                     'failing is not wind/sail-load-driven - e.g. local_buckling is a '
                     "pure D/t geometry check and column_below_partner has a wind-"
                     "independent dead-weight term - and needs a design change, not "
                     'a trim change. Check mast_result[\'checks\'] above for which.'),
        }

    lo, hi = 0.0, 100.0
    mast_hi, capsize_hi = mast100, capsize100
    while hi - lo > tolerance:
        mid = (lo + hi) / 2
        mast_mid, capsize_mid = check(mid)
        if mast_mid['passed'] and capsize_mid['passed']:
            hi = mid
            mast_hi, capsize_hi = mast_mid, capsize_mid
        else:
            lo = mid

    return {
        'reefing_percentage_needed': round(hi, 1),
        'mast_result': mast_hi,
        'capsize_result': capsize_hi,
        'convergent': True,
    }


def recommend_operating_configuration(params: Dict[str, Any],
                                       mass_data: Dict[str, Any],
                                       gz_data: Dict[str, Any],
                                       wind_speed_knots: float,
                                       min_safety_factor: float = 2.0,
                                       impact_velocity_ms: float = 3.0,
                                       dynamic_factor: float = 2.5) -> Dict[str, Any]:
    """
    Given actual wind speed (and, separately, wave impact conditions),
    recommend the minimum reefing percentage that keeps the wind-dependent
    checks safe, and report the wave-slam checks alongside for context.

    Wave slam and the other load cases here are independent of sail trim
    (they're hull/impact checks, not sail-load checks), so they're computed
    once at reef=0 and are NOT part of the reefing search - if one of them
    fails, no amount of reefing changes that; it's a separate structural
    concern, not an operating-configuration one.
    """
    reefing_result = find_minimum_reefing(params, mass_data, gz_data, wind_speed_knots,
                                           min_safety_factor)

    wave_slam_result = validate_wave_slam(params, impact_velocity_ms, dynamic_factor,
                                           min_safety_factor)
    frontal_slam_result = validate_frontal_wave_slam(params, impact_velocity_ms, dynamic_factor,
                                                       min_safety_factor)
    sideways_slam_result = validate_sideways_wave_slam(params, impact_velocity_ms, dynamic_factor,
                                                         min_safety_factor)
    wave_checks_passed = (wave_slam_result['passed'] and frontal_slam_result['passed']
                          and sideways_slam_result['passed'])

    return {
        'wind_speed_knots': wind_speed_knots,
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
    expected shape and an example. Missing fields fall back to the same
    defaults recommend_operating_configuration already uses, so a minimal
    file (just wind_speed_kt) is valid.
    """
    with open(path, 'r') as f:
        condition = json.load(f)

    return {
        'wind_speed_knots': condition.get('wind_speed_kt', 25.0),
        'impact_velocity_ms': condition.get('impact_velocity_ms', 3.0),
        'dynamic_factor': condition.get('dynamic_factor', 2.5),
        'min_safety_factor': condition.get('min_safety_factor', 2.0),
    }


def print_recommendation_report(result: Dict[str, Any], condition_path: str) -> None:
    """Print a human-readable operating-configuration recommendation."""
    reefing = result['reefing']
    waves = result['wave_conditions']

    print()
    print("=" * 60)
    print("OPERATING CONFIGURATION RECOMMENDATION")
    print("=" * 60)
    print(f"Condition file: {condition_path}")
    print(f"Wind speed: {result['wind_speed_knots']:.0f} knots")
    print(f"Required safety factor: {result['min_safety_factor_required']:.1f}")

    print()
    if not reefing['convergent']:
        print("✗ NOT OPERABLE at this wind speed - reefing alone cannot reach the")
        print(f"  required safety factor. {reefing['note']}")
    elif reefing['reefing_percentage_needed'] == 0.0:
        print("✓ Full sail is safe - no reefing required.")
    else:
        print(f"✓ Reef to {reefing['reefing_percentage_needed']:.0f}% to stay within safety limits.")

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
        description='Recommend a safe reefing percentage for a given wind/wave condition')
    parser.add_argument('--parameters', required=True,
                        help='Path to parameter JSON artifact')
    parser.add_argument('--mass', required=True,
                        help='Path to mass JSON artifact')
    parser.add_argument('--gz', required=True,
                        help='Path to GZ curve JSON artifact')
    parser.add_argument('--condition', required=True,
                        help='Path to a condition JSON file (see constant/conditions/)')
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

    result = recommend_operating_configuration(
        params, mass_data, gz_data,
        wind_speed_knots=condition['wind_speed_knots'],
        min_safety_factor=condition['min_safety_factor'],
        impact_velocity_ms=condition['impact_velocity_ms'],
        dynamic_factor=condition['dynamic_factor'],
    )

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)

    if not args.quiet:
        print_recommendation_report(result, args.condition)

    sys.exit(0 if result['overall_operable'] else 1)


if __name__ == "__main__":
    main()
