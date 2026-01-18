#!/usr/bin/env python3
"""
GZ curve computation - calculates the righting arm curve for stability analysis.

The GZ (righting arm) curve shows how the boat's righting moment varies with heel angle.
For each heel angle:
1. Find equilibrium z (where buoyancy = weight) with fixed roll
2. Compute GZ = horizontal distance between CoB and CoG (transverse)
3. Righting moment = GZ × displacement × g

For a proa with outrigger (ama), the stability is asymmetric:
- Positive roll (towards ama): high stability due to ama leverage
- Negative roll (away from ama): lower stability, similar to monohull

Usage:
    python -m src.gz \
        --design artifact/boat.design.FCStd \
        --buoyancy artifact/boat.buoyancy.json \
        --output artifact/boat.gz.json \
        --output-png artifact/boat.gz.png
"""

import sys
import os
import json
import argparse
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    import FreeCAD as App
except ImportError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("This script must be run with FreeCAD's Python", file=sys.stderr)
    sys.exit(1)

from src.physics.center_of_buoyancy import compute_center_of_buoyancy

# Physical constants
GRAVITY_M_S2 = 9.81


def transform_point(point: dict, z_displacement: float, pitch_deg: float,
                    roll_deg: float, rotation_center: dict) -> dict:
    """
    Transform a point by z displacement and pitch/roll rotations.
    Same transformation as in buoyancy solver.
    """
    x = point['x'] - rotation_center['x']
    y = point['y'] - rotation_center['y']
    z = point['z'] - rotation_center['z']

    pitch_rad = math.radians(pitch_deg)
    roll_rad = math.radians(roll_deg)

    cos_p = math.cos(pitch_rad)
    sin_p = math.sin(pitch_rad)
    cos_r = math.cos(roll_rad)
    sin_r = math.sin(roll_rad)

    # R = Ry(roll) * Rx(pitch)
    x_new = cos_r * x + sin_r * sin_p * y + sin_r * cos_p * z
    y_new = cos_p * y - sin_p * z
    z_new = -sin_r * x + cos_r * sin_p * y + cos_r * cos_p * z

    return {
        'x': x_new + rotation_center['x'],
        'y': y_new + rotation_center['y'],
        'z': z_new + rotation_center['z'] + z_displacement
    }


def find_equilibrium_z_at_heel(fcstd_path: str, target_weight_N: float,
                               pitch_deg: float, roll_deg: float,
                               z_initial: float = -500.0,
                               tolerance: float = 0.01,
                               max_iterations: int = 30) -> dict:
    """
    Find equilibrium z displacement at a fixed heel (roll) angle.

    Uses bisection to find z where buoyancy = weight.

    Args:
        fcstd_path: Path to FreeCAD design file
        target_weight_N: Target weight (buoyancy must equal this)
        pitch_deg: Pitch angle (usually 0 for GZ curve)
        roll_deg: Roll (heel) angle
        z_initial: Initial guess for z
        tolerance: Relative tolerance for force balance
        max_iterations: Maximum iterations

    Returns:
        Dictionary with equilibrium z and CoB result
    """
    # Binary search bounds
    z_min, z_max = -5000.0, 500.0  # mm

    # First, bracket the solution
    cob_min = compute_center_of_buoyancy(fcstd_path, z_min, pitch_deg, roll_deg)
    cob_max = compute_center_of_buoyancy(fcstd_path, z_max, pitch_deg, roll_deg)

    buoyancy_min = cob_min['buoyancy_force_N']
    buoyancy_max = cob_max['buoyancy_force_N']

    # Check if target is within range
    if target_weight_N > buoyancy_min:
        # Boat is too heavy even when fully submerged
        return {
            'converged': False,
            'z_mm': z_min,
            'cob_result': cob_min,
            'error': 'Boat too heavy - cannot float'
        }

    if target_weight_N < buoyancy_max:
        # Boat is too light even when barely touching water
        return {
            'converged': False,
            'z_mm': z_max,
            'cob_result': cob_max,
            'error': 'Boat too light - pops out of water'
        }

    # Bisection search
    for iteration in range(max_iterations):
        z_mid = (z_min + z_max) / 2
        cob_mid = compute_center_of_buoyancy(fcstd_path, z_mid, pitch_deg, roll_deg)
        buoyancy_mid = cob_mid['buoyancy_force_N']

        force_error = abs(buoyancy_mid - target_weight_N) / target_weight_N

        if force_error < tolerance:
            return {
                'converged': True,
                'z_mm': z_mid,
                'cob_result': cob_mid,
                'iterations': iteration + 1
            }

        if buoyancy_mid > target_weight_N:
            # Too much buoyancy, rise up (less negative z)
            z_min = z_mid
        else:
            # Not enough buoyancy, sink more (more negative z)
            z_max = z_mid

    # Return best result even if not fully converged
    return {
        'converged': False,
        'z_mm': z_mid,
        'cob_result': cob_mid,
        'iterations': max_iterations,
        'error': f'Did not converge, force error: {force_error:.4f}'
    }


def compute_gz_curve(fcstd_path: str, buoyancy_result: dict,
                     heel_angles: list = None,
                     verbose: bool = True) -> dict:
    """
    Compute the GZ curve by sweeping through heel angles.

    For each heel angle:
    1. Find equilibrium z (buoyancy = weight)
    2. Transform CoG to world frame
    3. Compute GZ = CoB_x - CoG_x (transverse separation)

    Args:
        fcstd_path: Path to FreeCAD design file
        buoyancy_result: Result from buoyancy equilibrium solver
        heel_angles: List of heel angles in degrees (default: -20 to 60)
        verbose: Print progress

    Returns:
        Dictionary with GZ curve data
    """
    if heel_angles is None:
        # For a proa: negative = away from ama, positive = towards ama
        # Use finer resolution near 0° to capture ama engagement transition
        heel_angles = (
            list(range(-60, -5, 5)) +       # -60, -55, ... -10
            list(range(-5, 6, 1)) +         # -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5 (fine steps)
            list(range(10, 70, 5))          # 10, 15, 20, ... 65
        )

    # Extract equilibrium data
    eq = buoyancy_result['equilibrium']
    eq_z = eq['z_offset_mm']
    eq_pitch = eq['pitch_deg']

    # CoG in body frame
    cog_body = buoyancy_result['center_of_gravity_body']

    # Weight/mass
    weight_N = buoyancy_result['weight_N']
    total_mass_kg = buoyancy_result['total_mass_kg']

    # Get rotation center from the equilibrium CoB calculation
    # We'll recompute it for each heel angle

    gz_data = []

    for roll_deg in heel_angles:
        if verbose:
            print(f"  Computing GZ at heel = {roll_deg:+.1f}°...", end='', flush=True)

        # Find equilibrium z at this heel angle
        # Keep pitch at equilibrium value (or 0 for simplicity)
        result = find_equilibrium_z_at_heel(
            fcstd_path, weight_N,
            pitch_deg=0.0,  # Assume level pitch for GZ curve
            roll_deg=roll_deg,
            z_initial=eq_z
        )

        if not result['converged']:
            if verbose:
                print(f" FAILED: {result.get('error', 'unknown')}")
            # Still record the point but mark as unconverged
            gz_data.append({
                'heel_deg': roll_deg,
                'converged': False,
                'gz_m': 0.0,
                'righting_moment_Nm': 0.0,
                'error': result.get('error', 'Did not converge')
            })
            continue

        cob_result = result['cob_result']
        z_eq = result['z_mm']

        # Get rotation center
        rotation_center = cob_result['pose'].get('rotation_center', cog_body)

        # Transform CoG to world frame at this pose
        cog_world = transform_point(cog_body, z_eq, 0.0, roll_deg, rotation_center)

        # CoB is already in world frame
        cob = cob_result['CoB']

        # GZ = transverse righting arm
        # The righting moment is M = (CoG_x - CoB_x) × Buoyancy
        # For positive roll (heel to starboard), righting means M < 0 (roll back to port)
        # For negative roll (heel to port), righting means M > 0 (roll back to starboard)
        #
        # To get GZ positive for righting in both cases:
        # GZ = sign(roll) × (CoB_x - CoG_x)
        #
        # This way:
        # - At positive heel: CoB outboard (larger x) → positive GZ → righting
        # - At negative heel: CoB inboard (smaller x) → negative raw, but sign flip → positive GZ → righting
        raw_gz_mm = cob['x'] - cog_world['x']
        if abs(roll_deg) < 0.01:
            # At near-zero heel, use raw value (sign is ambiguous)
            gz_mm = raw_gz_mm
        else:
            # Apply sign correction for proper righting arm convention
            sign = 1 if roll_deg > 0 else -1
            gz_mm = sign * raw_gz_mm
        gz_m = gz_mm / 1000.0

        # Righting moment = GZ × displacement × g
        # But we already have weight = mass × g, so RM = GZ × weight
        righting_moment_Nm = gz_m * weight_N

        if verbose:
            print(f" GZ = {gz_m*100:.1f} cm, RM = {righting_moment_Nm:.0f} Nm")

        gz_data.append({
            'heel_deg': roll_deg,
            'converged': True,
            'z_eq_mm': round(z_eq, 2),
            'cob_x_mm': round(cob['x'], 2),
            'cob_y_mm': round(cob['y'], 2),
            'cob_z_mm': round(cob['z'], 2),
            'cog_world_x_mm': round(cog_world['x'], 2),
            'cog_world_y_mm': round(cog_world['y'], 2),
            'cog_world_z_mm': round(cog_world['z'], 2),
            'raw_gz_mm': round(raw_gz_mm, 2),  # CoB_x - CoG_x (before sign correction)
            'gz_mm': round(gz_mm, 2),  # Sign-corrected righting arm
            'gz_m': round(gz_m, 4),
            'righting_moment_Nm': round(righting_moment_Nm, 2),
            'buoyancy_force_N': round(cob_result['buoyancy_force_N'], 2),
            'submerged_volume_liters': round(cob_result['submerged_volume_liters'], 2)
        })

    # Compute summary statistics
    converged_points = [p for p in gz_data if p.get('converged', False)]

    if converged_points:
        gz_values = [p['gz_m'] for p in converged_points]
        max_gz = max(gz_values)
        max_gz_idx = gz_values.index(max_gz)
        max_gz_angle = converged_points[max_gz_idx]['heel_deg']

        # Find range of positive stability (angles where GZ > 0)
        positive_heel_angles = [p['heel_deg'] for p in converged_points if p['gz_m'] > 0]
        if positive_heel_angles:
            range_positive = max(positive_heel_angles)
        else:
            range_positive = 0

        # Find turtle angle (positive heel where GZ crosses zero from positive)
        # This is where the ama gets driven under and boat inverts
        turtle_angle = None
        for i in range(1, len(converged_points)):
            if (converged_points[i-1]['heel_deg'] > 0 and
                converged_points[i-1]['gz_m'] > 0 and converged_points[i]['gz_m'] <= 0):
                # Linear interpolation to find zero crossing
                gz1 = converged_points[i-1]['gz_m']
                gz2 = converged_points[i]['gz_m']
                angle1 = converged_points[i-1]['heel_deg']
                angle2 = converged_points[i]['heel_deg']
                if gz1 != gz2:
                    turtle_angle = angle1 + gz1 * (angle2 - angle1) / (gz1 - gz2)
                else:
                    turtle_angle = angle1
                break

        # Find capsize angle (negative heel where GZ crosses zero from positive)
        # This is where the boat rolls over away from the ama
        capsize_angle = None
        for i in range(len(converged_points) - 1, 0, -1):
            if (converged_points[i]['heel_deg'] < 0 and
                converged_points[i]['gz_m'] > 0 and converged_points[i-1]['gz_m'] <= 0):
                # Linear interpolation to find zero crossing
                gz1 = converged_points[i-1]['gz_m']
                gz2 = converged_points[i]['gz_m']
                angle1 = converged_points[i-1]['heel_deg']
                angle2 = converged_points[i]['heel_deg']
                if gz1 != gz2:
                    capsize_angle = angle1 + gz1 * (angle2 - angle1) / (gz1 - gz2)
                else:
                    capsize_angle = angle1
                break

        # Detect ama engagement angle (large jump in CoB_x)
        # This is where the ama first touches the water
        ama_engagement_angle = None
        cob_x_values = [p['cob_x_mm'] for p in converged_points]
        for i in range(1, len(converged_points)):
            delta_cob_x = cob_x_values[i] - cob_x_values[i-1]
            delta_angle = converged_points[i]['heel_deg'] - converged_points[i-1]['heel_deg']
            # A jump of > 500mm per degree indicates ama engagement
            if delta_angle > 0 and delta_cob_x / delta_angle > 500:
                # Ama engages somewhere between these two angles
                ama_engagement_angle = (converged_points[i-1]['heel_deg'] +
                                        converged_points[i]['heel_deg']) / 2
                break

        summary = {
            'max_gz_m': round(max_gz, 4),
            'max_gz_angle_deg': max_gz_angle,
            'range_of_positive_stability_deg': range_positive,
            'turtle_angle_deg': round(turtle_angle, 1) if turtle_angle else None,
            'capsize_angle_deg': round(capsize_angle, 1) if capsize_angle else None,
            'ama_engagement_angle_deg': round(ama_engagement_angle, 1) if ama_engagement_angle else None,
            'total_points': len(gz_data),
            'converged_points': len(converged_points)
        }
    else:
        summary = {
            'max_gz_m': 0,
            'max_gz_angle_deg': None,
            'range_of_positive_stability_deg': 0,
            'turtle_angle_deg': None,
            'capsize_angle_deg': None,
            'ama_engagement_angle_deg': None,
            'total_points': len(gz_data),
            'converged_points': 0
        }

    return {
        'validator': 'gz',
        'summary': summary,
        'total_mass_kg': total_mass_kg,
        'weight_N': weight_N,
        'equilibrium_pose': eq,
        'center_of_gravity_body': cog_body,
        'gz_curve': gz_data
    }


def plot_gz_curve(gz_result: dict, output_path: str):
    """
    Generate a PNG plot of the GZ curve.

    Args:
        gz_result: Result from compute_gz_curve
        output_path: Path for output PNG file
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    # Extract data for plotting
    gz_data = gz_result['gz_curve']
    converged = [p for p in gz_data if p.get('converged', False)]

    if not converged:
        print("Warning: No converged points to plot")
        return

    angles = [p['heel_deg'] for p in converged]
    gz_values = [p['gz_m'] * 100 for p in converged]  # Convert to cm for readability
    rm_values = [p['righting_moment_Nm'] for p in converged]

    # Get equilibrium roll angle
    eq_roll = gz_result['equilibrium_pose']['roll_deg']

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot GZ curve
    color1 = '#2563eb'
    ax1.set_xlabel('Heel Angle (degrees)', fontsize=12)
    ax1.set_ylabel('GZ Righting Arm (cm)', color=color1, fontsize=12)
    line1, = ax1.plot(angles, gz_values, 'o-', color=color1, linewidth=2,
                      markersize=4, label='GZ (cm)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=0, color='gray', linestyle='--', alpha=0.5)

    # Mark the equilibrium roll angle
    ax1.axvline(x=eq_roll, color='green', linestyle=':', alpha=0.7, linewidth=2,
                label=f'Equilibrium ({eq_roll:.1f}°)')

    # Add grid
    ax1.grid(True, alpha=0.3)

    # Second y-axis for righting moment
    ax2 = ax1.twinx()
    color2 = '#dc2626'
    ax2.set_ylabel('Righting Moment (Nm)', color=color2, fontsize=12)
    line2, = ax2.plot(angles, rm_values, 's--', color=color2, linewidth=1.5,
                      markersize=3, alpha=0.7, label='RM (Nm)')
    ax2.tick_params(axis='y', labelcolor=color2)

    # Mark ama engagement angle if detected
    ama_angle = gz_result['summary'].get('ama_engagement_angle_deg')
    if ama_angle is not None:
        ax1.axvline(x=ama_angle, color='orange', linestyle=':', alpha=0.7, linewidth=2,
                    label=f'Ama engages ({ama_angle:.1f}°)')

    # Add summary statistics to plot
    summary = gz_result['summary']
    stats_text = (
        f"Max GZ: {summary['max_gz_m']*100:.1f} cm at {summary['max_gz_angle_deg']}°"
    )
    if summary.get('turtle_angle_deg'):
        stats_text += f"\nTurtle: {summary['turtle_angle_deg']:.1f}°"
    if summary.get('capsize_angle_deg'):
        stats_text += f"\nCapsize: {summary['capsize_angle_deg']:.1f}°"
    if ama_angle is not None:
        stats_text += f"\nAma engages: {ama_angle:.1f}°"
    stats_text += f"\nEquilibrium roll: {eq_roll:.1f}°"

    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Title
    mass = gz_result['total_mass_kg']
    plt.title(f'GZ Curve (Righting Arm) - Displacement: {mass:.0f} kg', fontsize=14)

    # Combined legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')

    # Tight layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ GZ curve plot saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Compute GZ (righting arm) curve for stability analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--design', required=True,
                        help='Path to FCStd design file')
    parser.add_argument('--buoyancy', required=True,
                        help='Path to buoyancy.json artifact')
    parser.add_argument('--output', required=True,
                        help='Path to output JSON file')
    parser.add_argument('--output-png',
                        help='Path to output PNG plot (optional, defaults to same name as output with .png)')
    parser.add_argument('--min-heel', type=float, default=-60.0,
                        help='Minimum heel angle in degrees (default: -60)')
    parser.add_argument('--max-heel', type=float, default=65.0,
                        help='Maximum heel angle in degrees (default: 65)')
    parser.add_argument('--heel-step', type=float, default=5.0,
                        help='Heel angle step in degrees (default: 5)')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress progress output')

    args = parser.parse_args()

    if not os.path.exists(args.design):
        print(f"ERROR: Design file not found: {args.design}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.buoyancy):
        print(f"ERROR: Buoyancy file not found: {args.buoyancy}", file=sys.stderr)
        sys.exit(1)

    verbose = not args.quiet

    if verbose:
        print(f"Computing GZ curve: {args.design}")

    # Load buoyancy result
    with open(args.buoyancy) as f:
        buoyancy_result = json.load(f)

    if verbose:
        eq = buoyancy_result['equilibrium']
        print(f"  Equilibrium pose: z={eq['z_offset_mm']:.1f}mm, "
              f"pitch={eq['pitch_deg']:.2f}°, roll={eq['roll_deg']:.2f}°")
        print(f"  Mass: {buoyancy_result['total_mass_kg']:.1f} kg")

    # Generate heel angles with fine steps near 0° to capture ama engagement
    heel_angles = []
    angle = args.min_heel
    while angle <= args.max_heel + 0.01:  # Small epsilon for float comparison
        heel_angles.append(angle)
        # Use 1° steps between -5° and +5°, otherwise use heel_step
        if -6 < angle < 5:
            angle += 1.0
        else:
            angle += args.heel_step

    if verbose:
        print(f"  Computing {len(heel_angles)} points from {args.min_heel}° to {args.max_heel}°")

    # Compute GZ curve
    result = compute_gz_curve(
        args.design,
        buoyancy_result,
        heel_angles=heel_angles,
        verbose=verbose
    )

    # Write JSON output
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    if verbose:
        print(f"✓ GZ curve data saved to {args.output}")
        summary = result['summary']
        print(f"  Max GZ: {summary['max_gz_m']*100:.1f} cm at {summary['max_gz_angle_deg']}°")
        print(f"  Range of positive stability: {summary['range_of_positive_stability_deg']}°")
        if summary.get('turtle_angle_deg'):
            print(f"  Turtle angle (ama down): {summary['turtle_angle_deg']:.1f}°")
        if summary.get('capsize_angle_deg'):
            print(f"  Capsize angle (ama up): {summary['capsize_angle_deg']:.1f}°")

    # Generate PNG plot
    png_path = args.output_png
    if not png_path:
        png_path = args.output.replace('.json', '.png')

    plot_gz_curve(result, png_path)


if __name__ == "__main__":
    main()
