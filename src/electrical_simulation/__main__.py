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
        print("Follow steps indicated in wiki to install NgSpice.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run electrical simulation for solar proa power system')
    parser.add_argument('--circuit', required=True,
                        help='Path to circuit setup JSON (e.g. constant/electrical/circuit_setup.json)')
    parser.add_argument('--constants', required=True,
                        help='Path to constants JSON (e.g. constant/electrical/constants.json)')
    parser.add_argument('--components', required=True,
                        help='Path to components JSON (e.g. constant/electrical/components.json)')
    parser.add_argument('--boat', required=True,
                        help='Boat name to select circuit configuration (e.g. rp1)')
    parser.add_argument('--voyage', default=None,
                        help='Path to voyage setup JSON (required for voyage simulation type)')
    parser.add_argument('--output', required=True,
                        help='Path to output artifact directory or file')
    parser.add_argument('--simulation-type', required=True,
                        choices=['operating_point', 'sweep_throttle', 'sweep_panel_power', 'voyage', 'all'],
                        help='Type of simulation to run')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable simulation logging')
    parser.add_argument('--show-plot', action='store_true',
                        help='Display plots interactively')

    args = parser.parse_args()

    # Load constants from JSON
    constants = json.load(open(args.constants))
    components = json.load(open(args.components))
    circuit_setup = json.load(open(args.circuit))
    combine_config_setup(circuit_setup, components)
    ngspice_available = check_ngspice()

    output_dir = args.output

    if args.simulation_type == 'all':
        run_operating_point_simulation(args, circuit_setup, ngspice_available, output_dir, constants)
        run_sweep_throttle(args, circuit_setup, ngspice_available, output_dir, constants)
        run_sweep_panel_power(args, circuit_setup, ngspice_available, output_dir, constants)
        run_voyage_simulation(args, circuit_setup, ngspice_available, output_dir, constants)

    elif args.simulation_type == 'operating_point':
        run_operating_point_simulation(args, circuit_setup, ngspice_available, output_dir, constants)

    elif args.simulation_type == 'sweep_throttle':
        run_sweep_throttle(args, circuit_setup, ngspice_available, output_dir, constants)

    elif args.simulation_type == 'sweep_panel_power':
        run_sweep_panel_power(args, circuit_setup, ngspice_available, output_dir, constants)

    elif args.simulation_type == 'voyage':
        run_voyage_simulation(args, circuit_setup, ngspice_available, output_dir, constants)

def run_operating_point_simulation(args, circuit_setup, ngspice_available, output_dir, constants):
    circuit, component_object, errors = build_circuit_from_json(circuit_setup=circuit_setup, constants=constants)
    analysis, result = begin_simulation(
        circuit=circuit,
        component_object=component_object, 
        errors=errors,
        ngspice_available=ngspice_available,
        simulation_logging=args.verbose, show_errors=args.verbose,
        show_warnings=args.verbose,
        constants=constants)

    save_to_file(result, save_path=output_dir + ".operating_point.json", constants=constants)
    print(f"✓ Operating point simulation complete: {output_dir}.operating_point.json")


def run_sweep_throttle(args, circuit_setup, ngspice_available, output_dir, constants):
    sweep_throttle(
        circuit_setup=circuit_setup,
        save_path=output_dir + ".sweep_throttle",
        ngspice_available=ngspice_available,
        simulation_logging=args.verbose,
        save_output=True,
        constants=constants) 
    print(f"✓ Sweep throttle simulation complete: {output_dir}.sweep_throttle")
    
def run_sweep_panel_power(args, circuit_setup, ngspice_available, output_dir, constants):
    sweep_panel_power(
        circuit_setup=circuit_setup,
        save_path=output_dir + ".sweep_panel_power",
        ngspice_available=ngspice_available,
        simulation_logging=args.verbose,
        save_output=True,
        constants=constants)   
    print(f"✓ Sweep panel power simulation complete: {output_dir}.sweep_panel_power")

def run_voyage_simulation(args, circuit_setup, ngspice_available, output_dir, constants):
    start_voyage(
        circuit_setup=circuit_setup,
        voyage_config_loc=args.voyage,
        save_path=output_dir + ".voyage",
        ngspice_available=ngspice_available,
        constants=constants) 
    print(f"✓ Voyage simulation complete: {output_dir}.voyage")

def combine_config_setup(circuit_config, component_config):
    if circuit_config.get("mppt_panel") is not None:
        for key, config in circuit_config["mppt_panel"].items():
            panel_choice = config["panel_info"]["choice"]
            mppt_choice = config["mppt_info"]["choice"]
            config["panel_info"].update(component_config["Panel"][panel_choice])
            config["mppt_info"].update(component_config["MPPT"][mppt_choice])
            
    if circuit_config.get("load") is not None:
        for key, load in circuit_config["load"].items():
            load_choice = load["choice"]
            load.update(component_config["Load"][load_choice])
            
    if circuit_config.get("battery") is not None:
        battery_choice = circuit_config["battery"]["choice"]
        circuit_config["battery"].update(component_config["Battery"][battery_choice])
     
if __name__ == "__main__":
    main()