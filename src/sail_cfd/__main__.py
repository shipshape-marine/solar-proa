#!/usr/bin/env python3
"""
Sail CFD sweep - generate OpenFOAM cases, then turn the results into a
sail polar for src/structural/operating_envelope.py. See README.md.

    python -m src.sail_cfd setup --parameters artifact/rp2.closehaul.parameter.json --run-dir cfd_runs/rp2_medium
    (run cfd_runs/rp2_medium/Allrun inside an OpenFOAM v2412 environment)
    python -m src.sail_cfd postprocess --run-dir cfd_runs/rp2_medium --output constant/sail_polar/rp2_openfoam.json
"""

import argparse
import json
import sys

from .case import MESH_PRESETS, generate_sweep
from .postprocess import build_polar

DEFAULT_REEFS = [0, 25, 50, 75]
DEFAULT_ALPHAS = [0, 5, 10, 15, 20, 25, 30, 35, 45, 60, 75, 90]


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

    args = parser.parse_args()

    if args.command == 'setup':
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
