import json

from .constants import *
from PySpice.Spice.Netlist import Circuit
from .constants import GROUNDING_RESISTANCE
from .components.load_balancer import Load_Balancer
from .components.load import Load
from .components.battery_array import Battery_Array
from .components.mppt import MPPT
from .components.solar_panel_array import Solar_Array


def build_circuit_from_json(circuit_config_loc: str, modifications: dict = {},
                            component_logging=False, show_components=False, show_netlist=False):
    circuit = Circuit("Solar_Panel-Mppt-Battery-Motor Circuit Thingy")
    components = {
        "panel": [],
        "battery": [],
        "load": [],
        "wire": [],
        "mppt": []
    }
    
    with open(circuit_config_loc, 'r') as f:
        input_data = json.load(f)

    component_object = {}
    errors = []
    
    # Battery Array
    battery_array = input_data['battery_setup']
    battery_choice = battery_array['choice']
    battery_config = battery_array[battery_choice]
    
    if modifications.get('max_discharge_current') is not None:
        battery_config['max_discharge_current'] = modifications['max_discharge_current']
        
    if modifications.get('max_charge_current') is not None:
        battery_config['max_charge_current'] = modifications['max_charge_current']
    
    if modifications.get('current_soc') is not None:
        battery_config['current_soc'] = modifications['current_soc']
        
    battery_array = Battery_Array(circuit, components, **battery_config)
    err = battery_array.create_battery_array(log=component_logging)
    
    component_object["battery_array"] = battery_array
    errors.append(err) if err else None

    # MPPT Array
    mppt_array = input_data['mppt_panel_setup']
    mppt_index = 0
    for key in mppt_array.keys():
        if not key.startswith("config_"):
            continue
        config = mppt_array[key]
        for _ in range(config['count']):
            if modifications.get('panel_power_setting') is not None:
                config['panel_info']['power'] *= modifications['panel_power_setting']
            solar_array = Solar_Array(
                circuit, components, **config['panel_info'])
            mppt = MPPT(circuit, components, **config['mppt_info'])

            solar_array.create_panels(mppt_index, log=component_logging)
            err = mppt.setup_mppt(mppt_index, solar_array,
                                  battery_array, log=component_logging)
            
            errors.append(err) if err else None
            component_object["mppt"] = component_object.get("mppt", []) + [mppt]
            component_object["solar_array"] = component_object.get("solar_array", []) + [solar_array]
            mppt_index += 1

    POWER_FROM = mppt.get_terminal() if mppt_index > 0 else None
    POWER_TO = battery_array.get_terminal()
    
    circuit.V("total_mppt_output_current", POWER_FROM, POWER_TO, GROUNDING_RESISTANCE)

    # Load/Motor
    index = 0
    for key in input_data["load_setup"].keys():
        if key == "description":
            continue
        load_name = f"{key}_load_i{index}"
        
        if modifications.get('throttle_setting') is not None:
            if type(modifications['throttle_setting']) == list:
                input_data['load_setup'][key]['throttle'] = modifications['throttle_setting'][index]
            else:
                input_data['load_setup'][key]['throttle'] = modifications['throttle_setting']
                
        load = Load(circuit, components, load_name=load_name, **input_data['load_setup'][key])
        err = load.setup_load(battery_array, log=component_logging)
        
        component_object["load"] = component_object.get("load", []) + [load]
        errors.append(err) if err else None
        index += 1  
        
    # Load Balancer (One is enough to restrict battery output)
    load_balancer = Load_Balancer(circuit, components)
    err = load_balancer.balance_loads(battery_array)
    
    component_object["load_balancer"] = load_balancer
    errors.append(err) if err else None

    if show_components:
        display_components(components)
    if show_netlist:
        display_netlist(circuit)

    return circuit, component_object, errors


def display_components(components):
    print("\nComponents in Circuit:")
    for comp_type, comp_list in components.items():
        print(f"{comp_type.capitalize()}: {len(comp_list)}")
        for comp in comp_list:
            print(f"  - {comp}")


def display_netlist(circuit):
    print("\nCircuit Netlist:")
    print(circuit)
    