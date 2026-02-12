#!/usr/bin/env python3
"""
Electrical simulation for solar proa power system.

Supports multiple simulation types:
  operating_point  - Single operating point analysis
  sweep_throttle   - Sweep throttle from 0-100%
  sweep_panel_power - Sweep panel power from 100-0%
  voyage           - Multi-segment voyage simulation
"""

import argparse
import json
import os
import sys

from .constants import load_constants, BARF, BARE
from .circuit_constructor import build_circuit_from_json
from .pyspice_simulator import begin_simulation
from .result_saver import save_to_file
from .simulation_over_time import start_voyage
from .simulation_sweeper import sweep_panel_power, sweep_throttle


def check_ngspice():
    try:
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared
        NgSpiceShared.new_instance()
        
        print("NgSpice is available.")
        return True
    except Exception as e:
        print(f"NgSpice initialization failed: {e}")
        print("Follow steps indicated in readme.md to install NgSpice.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run electrical simulation for solar proa power system')
    parser.add_argument('--circuit', required=True,
                        help='Path to circuit setup JSON (e.g. constant/electrical/circuit_setup.json)')
    parser.add_argument('--constants', required=True,
                        help='Path to constants JSON (e.g. constant/electrical/constants.json)')
    parser.add_argument('--voyage', default=None,
                        help='Path to voyage setup JSON (required for voyage simulation type)')
    parser.add_argument('--output', required=True,
                        help='Path to output artifact directory or file')
    parser.add_argument('--simulation-type', required=True,
                        choices=['operating_point', 'sweep_throttle', 'sweep_panel_power', 'voyage'],
                        help='Type of simulation to run')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable simulation logging')
    parser.add_argument('--show-plot', action='store_true',
                        help='Display plots interactively')

    args = parser.parse_args()

    # Load constants from JSON
    load_constants(args.constants)

    ngspice_available = check_ngspice()

    output_dir = os.path.dirname(args.output) or '.'
    os.makedirs(output_dir, exist_ok=True)

    if args.simulation_type == 'operating_point':
        circuit, component_object, errors = build_circuit_from_json(args.circuit)
        analysis, result = begin_simulation(
            circuit, component_object, errors, ngspice_available,
            simulation_logging=args.verbose, show_errors=args.verbose,
            show_warnings=args.verbose)

        save_to_file(result, save_path=output_dir)
        print(f"✓ Operating point simulation complete: {args.output}")

    elif args.simulation_type == 'sweep_throttle':
        sweep_throttle(
            circuit_config_loc=args.circuit,
            save_path=output_dir,
            ngspice_available=ngspice_available,
            simulation_logging=args.verbose,
            save_output=True)
        print(f"✓ Sweep throttle simulation complete: {output_dir}")

    elif args.simulation_type == 'sweep_panel_power':
        sweep_panel_power(
            circuit_config_loc=args.circuit,
            save_path=output_dir,
            ngspice_available=ngspice_available,
            simulation_logging=args.verbose,
            save_output=True)
        print(f"✓ Sweep panel power simulation complete: {output_dir}")

    elif args.simulation_type == 'voyage':
        if not args.voyage:
            print("ERROR: --voyage is required for voyage simulation type")
            sys.exit(1)
        start_voyage(
            circuit_config_loc=args.circuit,
            voyage_config_loc=args.voyage,
            save_path=output_dir,
            ngspice_available=ngspice_available)
        print(f"✓ Voyage simulation complete: {output_dir}")


if __name__ == "__main__":
    main()