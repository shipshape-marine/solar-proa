#!/usr/bin/env python3
"""
Sail CFD sweep - generate OpenFOAM cases, then turn the results into a
sail polar for src/structural/operating_envelope.py. See README.md.

    python -m src.sail_cfd setup --parameters artifact/rp2.closehaul.parameter.json --run-dir cfd_runs/rp2_medium
    (run cfd_runs/rp2_medium/Allrun inside an OpenFOAM v2412 environment)
    python -m src.sail_cfd postprocess --run-dir cfd_runs/rp2_medium --output constant/sail_polar/rp2_openfoam.json

Trim study - best rig rotation for one sail at one apparent wind angle:

    python -m src.sail_cfd trim-setup --parameters artifact/rp2.closehaul.parameter.json --run-dir cfd_runs/rp2_trim_c45
    python -m src.sail_cfd trim --run-dir cfd_runs/rp2_trim_c45
"""

import argparse
import json
import os
import sys

from .case import MESH_PRESETS, generate_sweep
from .postprocess import build_polar
from .pair import SAILS, build_pair_report, extend_pair_sweep, generate_pair_sweep
from .trim import build_trim_report, extend_trim_sweep, generate_trim_sweep

DEFAULT_REEFS = [0, 25, 50, 75]
DEFAULT_ALPHAS = [0, 5, 10, 15, 20, 25, 30, 35, 45, 60, 75, 90]
DEFAULT_TRIM_AWA = 45.0
DEFAULT_TRIM_ROTATIONS = [10, 15, 20, 25, 30, 35, 40, 45]
DEFAULT_TRIM_CHORD_CAMBER = 10.0
DEFAULT_PAIR_AFT_ROTATIONS = [5, 10, 15, 20, 25, 30, 35]


def main():
    parser = argparse.ArgumentParser(description='OpenFOAM sail polar sweep')
    sub = parser.add_subparsers(dest='command', required=True)

    setup = sub.add_parser('setup', help='Generate the OpenFOAM cases')
    setup.add_argument('--parameters', required=True, help='Path to parameter JSON artifact')
    setup.add_argument('--run-dir', required=True, help='New directory to write the cases into')
    setup.add_argument('--rig', choices=['biru', 'kuning'], default='biru',
                       help="Which rig's sail_camber_*/sail_angle_* to use (default: biru)")
    setup.add_argument('--reef', type=float, nargs='+', default=DEFAULT_REEFS,
                       help=f'Reefing percentages to simulate (default: {DEFAULT_REEFS})')
    setup.add_argument('--alpha', type=float, nargs='+', default=DEFAULT_ALPHAS,
                       help=f'Angles of attack, must span 0-90 (default: {DEFAULT_ALPHAS})')
    setup.add_argument('--mesh', choices=list(MESH_PRESETS), default='medium',
                       help='Mesh refinement preset (default: medium)')
    setup.add_argument('--procs', type=int, default=12,
                       help='MPI processes per case (default: 12)')

    post = sub.add_parser('postprocess', help='Build a sail polar from a finished sweep')
    post.add_argument('--run-dir', required=True, help='Sweep directory (contains sweep.json)')
    post.add_argument('--output', required=True, help='Sail polar JSON to write')
    post.add_argument('--min-sheeting-angle', type=float, default=10.0,
                      help='Closest the sail chord sheets to the centerline, deg (default: 10)')

    trim_setup = sub.add_parser('trim-setup',
                                help='Generate one sail\'s cases over rig rotations at one AWA')
    trim_setup.add_argument('--parameters', required=True, help='Path to parameter JSON artifact')
    trim_setup.add_argument('--run-dir', required=True, help='New directory to write the cases into')
    trim_setup.add_argument('--rig', choices=['biru', 'kuning'], default='biru',
                            help="Which rig's sail_camber_* to use (default: biru)")
    trim_setup.add_argument('--awa', type=float, default=DEFAULT_TRIM_AWA,
                            help=f'Apparent wind angle off the bow, deg (default: {DEFAULT_TRIM_AWA:g}, '
                                 'close-hauled)')
    trim_setup.add_argument('--rig-rotation', type=float, nargs='+', default=DEFAULT_TRIM_ROTATIONS,
                            help=f'Rig rotations (sail chord vs. centerline) to simulate, deg '
                                 f'(default: {DEFAULT_TRIM_ROTATIONS})')
    trim_setup.add_argument('--sail-angle', type=float, default=0.0,
                            help='Sail tilt about the yard spar, deg (default: 0 = yard and boom '
                                 'horizontal)')
    trim_setup.add_argument('--chord-camber', type=float, default=DEFAULT_TRIM_CHORD_CAMBER,
                            help='Chordwise camber, %% of chord at mid-height - replaces the CAD '
                                 'sail shape, whose sail_camber_* curve runs yard to boom only '
                                 f'(default: {DEFAULT_TRIM_CHORD_CAMBER:g})')
    trim_setup.add_argument('--mesh', choices=list(MESH_PRESETS), default='coarse',
                            help='Mesh refinement preset (default: coarse)')
    trim_setup.add_argument('--procs', type=int, default=12,
                            help='MPI processes per case (default: 12)')

    trim_extend = sub.add_parser('trim-extend',
                                 help='Add rig rotations to a trim sweep, reusing its mesh')
    trim_extend.add_argument('--run-dir', required=True, help='Trim sweep directory (contains sweep.json)')
    trim_extend.add_argument('--rig-rotation', type=float, nargs='+', required=True,
                             help='Rig rotations to add, deg')
    trim_extend.add_argument('--procs', type=int, default=12,
                             help='MPI processes per case (default: 12)')

    trim = sub.add_parser('trim', help='Rank the rig rotations of a finished trim sweep by drive')
    trim.add_argument('--run-dir', required=True, help='Trim sweep directory (contains sweep.json)')
    trim.add_argument('--output', help='Also write the report as JSON here')

    pair_setup = sub.add_parser('pair-setup',
                                help='Foresail locked, aft sail swept over rig rotations at one AWA')
    pair_setup.add_argument('--parameters', required=True, help='Path to parameter JSON artifact')
    pair_setup.add_argument('--run-dir', required=True, help='New directory to write the cases into')
    pair_setup.add_argument('--awa', type=float, default=DEFAULT_TRIM_AWA,
                            help=f'Apparent wind angle off the bow, deg (default: {DEFAULT_TRIM_AWA:g})')
    pair_setup.add_argument('--fore-rotation', type=float, required=True,
                            help='Locked foresail rig rotation, deg (e.g. the trim sweep\'s best)')
    pair_setup.add_argument('--aft-rotation', type=float, nargs='+', default=DEFAULT_PAIR_AFT_ROTATIONS,
                            help=f'Aft sail rig rotations to simulate, deg '
                                 f'(default: {DEFAULT_PAIR_AFT_ROTATIONS})')
    pair_setup.add_argument('--sail-angle', type=float, default=0.0,
                            help='Sail tilt about the yard spar, both sails, deg (default: 0)')
    pair_setup.add_argument('--chord-camber', type=float, default=DEFAULT_TRIM_CHORD_CAMBER,
                            help=f'Chordwise camber of both sails, %% of chord '
                                 f'(default: {DEFAULT_TRIM_CHORD_CAMBER:g})')
    pair_setup.add_argument('--mesh', choices=list(MESH_PRESETS), default='coarse',
                            help='Mesh refinement preset (default: coarse)')
    pair_setup.add_argument('--procs', type=int, default=12,
                            help='MPI processes per case (default: 12)')

    pair_extend = sub.add_parser('pair-extend', help='Add aft rotations to a pair sweep')
    pair_extend.add_argument('--run-dir', required=True, help='Pair sweep directory (contains sweep.json)')
    pair_extend.add_argument('--aft-rotation', type=float, nargs='+', required=True,
                             help='Aft sail rig rotations to add, deg')
    pair_extend.add_argument('--fore-rotation', type=float, nargs='+',
                             help='Foresail rig rotations to pair each aft rotation with, deg '
                                  '(default: the sweep\'s locked one) - to re-check the foresail')
    pair_extend.add_argument('--parameters',
                             help='Parameter JSON artifact (default: the one the sweep was made from)')
    pair_extend.add_argument('--procs', type=int, default=12,
                             help='MPI processes per case (default: 12)')

    pair = sub.add_parser('pair', help='Rank the aft rotations of a finished pair sweep by total drive')
    pair.add_argument('--run-dir', required=True, help='Pair sweep directory (contains sweep.json)')
    pair.add_argument('--output', help='Also write the report as JSON here')

    args = parser.parse_args()

    if args.command == 'pair-setup':
        with open(args.parameters, 'r') as f:
            params = json.load(f)
        sweep = generate_pair_sweep(
            args.run_dir, params, args.parameters, args.awa, args.fore_rotation, args.aft_rotation,
            sail_angle_deg=args.sail_angle, chord_camber_pct=args.chord_camber,
            mesh=args.mesh, n_procs=args.procs)
        print(f"Wrote {len(sweep['configs'])} configs (mesh + case each) to {args.run_dir}:")
        for c in sweep['configs']:
            gap = '' if c['min_gap_m'] is None else f"  (sails {c['min_gap_m']} m apart)"
            print(f"  {c['name']}{gap}")
        print(f"Run {args.run_dir}/Allrun inside OpenFOAM v2412, then pair.")
    elif args.command == 'pair-extend':
        with open(os.path.join(args.run_dir, 'sweep.json'), 'r') as f:
            parameters = args.parameters or json.load(f)['parameters']
        with open(parameters, 'r') as f:
            params = json.load(f)
        names = extend_pair_sweep(args.run_dir, params, args.aft_rotation, args.procs,
                                  fore_rotations=args.fore_rotation)
        print(f"Added {', '.join(names)} to {args.run_dir}")
        print(f"Rerun {args.run_dir}/Allrun (finished configs are skipped), then pair.")
    elif args.command == 'pair':
        report = build_pair_report(args.run_dir)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Wrote {args.output}")
        print(f"AWA {report['apparent_wind_angle_deg']:g} deg, foresail locked at "
              f"{report['fore_rotation_deg']:g} deg, sail angle {report['sail_angle_deg']:g} deg, "
              + ('CAD sail shape' if report['chord_camber_pct'] is None
                 else f"chord camber {report['chord_camber_pct']:g}%")
              + f", {report['mesh']} mesh")
        alone = report['fore_alone']
        print(f"Foresail alone: C_drive {alone['c_drive']:.4f}, C_heel {alone['c_heel']:.4f}")
        print(f"{'fore rot':>8} {'aft rot':>7} {'gap m':>6} {'fore drv':>8} {'aft drv':>8} "
              f"{'TOTAL drv':>9} {'fore heel':>9} {'aft heel':>8} {'TOTAL heel':>10}")
        for r in report['rows']:
            print(f"{r['fore_rotation_deg']:8g} {r['aft_rotation_deg']:7g} {r['min_gap_m']:6.2f} "
                  f"{r['fore']['c_drive']:8.4f} {r['aft']['c_drive']:8.4f} {r['c_drive_total']:9.4f} "
                  f"{r['fore']['c_heel']:9.4f} {r['aft']['c_heel']:8.4f} {r['c_heel_total']:10.4f}")
        best = report['best']
        if best:
            line = (f"Best total drive: fore {best['fore_rotation_deg']:g} / aft "
                    f"{best['aft_rotation_deg']:g} deg (C_drive total {best['c_drive_total']:.4f})")
            peaks = [f"{sail} ~{best[f'interpolated_{sail}_rotation_deg']:g}"
                     for sail in SAILS if f'interpolated_{sail}_rotation_deg' in best]
            if peaks:
                line += f", parabola peak {', '.join(peaks)} deg"
            print(line)
        for w in report['convergence_warnings']:
            print(f"  warning: {w}")
    elif args.command == 'trim-setup':
        with open(args.parameters, 'r') as f:
            params = json.load(f)
        sweep = generate_trim_sweep(
            args.run_dir, params, args.parameters, args.awa, args.rig_rotation,
            sail_camber_mm=params[f'sail_camber_{args.rig}'], sail_angle_deg=args.sail_angle,
            mesh=args.mesh, n_procs=args.procs, chord_camber_pct=args.chord_camber)
        print(f"Wrote 1 mesh and {len(sweep['reefs'][0]['cases'])} cases to {args.run_dir}")
        print(f"Run {args.run_dir}/Allrun inside OpenFOAM v2412, then trim.")
    elif args.command == 'trim-extend':
        names = extend_trim_sweep(args.run_dir, args.rig_rotation, args.procs)
        print(f"Added {len(names)} cases to {args.run_dir}: {', '.join(names)}")
        print(f"Run {args.run_dir}/Allrun.extend inside OpenFOAM v2412, then trim.")
    elif args.command == 'trim':
        report = build_trim_report(args.run_dir)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Wrote {args.output}")
        print(f"AWA {report['apparent_wind_angle_deg']:g} deg, sail angle "
              f"{report['sail_angle_deg']:g} deg, "
              + ('CAD sail shape' if report['chord_camber_pct'] is None
                 else f"chord camber {report['chord_camber_pct']:g}%")
              + f", {report['mesh']} mesh, single sail")
        print(f"{'rotation':>8} {'alpha':>6} {'C_L':>7} {'C_D':>7} {'C_drive':>8} {'C_heel':>7} "
              f"{'drive/heel':>10}")
        for r in report['rows']:
            ratio = '-' if r['drive_to_heel'] is None else f"{r['drive_to_heel']:.3f}"
            print(f"{r['rig_rotation_deg']:8g} {r['angle_of_attack_deg']:6g} {r['cl']:7.4f} "
                  f"{r['cd']:7.4f} {r['driving_coefficient']:8.4f} {r['heeling_coefficient']:7.4f} "
                  f"{ratio:>10}")
        best = report['best']
        line = f"Best drive: rig rotation {best['rig_rotation_deg']:g} deg (C_drive {best['driving_coefficient']:.4f})"
        if 'interpolated_rig_rotation_deg' in best:
            line += f", parabola peak ~{best['interpolated_rig_rotation_deg']:g} deg"
        print(line)
        for w in report['convergence_warnings']:
            print(f"  warning: {w}")
    elif args.command == 'setup':
        with open(args.parameters, 'r') as f:
            params = json.load(f)
        sweep = generate_sweep(
            args.run_dir, params, args.parameters, args.reef, args.alpha,
            sail_camber_mm=params[f'sail_camber_{args.rig}'],
            sail_angle_deg=params[f'sail_angle_{args.rig}'],
            mesh=args.mesh, n_procs=args.procs)
        n_cases = sum(len(r['cases']) for r in sweep['reefs'])
        print(f"Wrote {len(sweep['reefs'])} meshes and {n_cases} cases to {args.run_dir}")
        print(f"Run {args.run_dir}/Allrun inside OpenFOAM v2412, then postprocess.")
    else:
        polar = build_polar(args.run_dir, args.min_sheeting_angle)
        with open(args.output, 'w') as f:
            json.dump(polar, f, indent=2)
        print(f"Wrote {args.output}")
        for w in polar['convergence_warnings']:
            print(f"  warning: {w}")
        if polar['convergence_warnings']:
            sys.exit(1)


if __name__ == "__main__":
    main()
