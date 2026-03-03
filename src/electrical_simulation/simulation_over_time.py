from copy import deepcopy
import json
from .sweep_graph_generation import generate_graph
from .pyspice_simulator import begin_simulation
from .circuit_constructor import build_circuit_from_json

SIMULATION_INTERVAL_MIN = 1

def start_voyage(circuit_setup: json, voyage_config_loc: str, save_path: str, ngspice_available: bool, constants=None):
    with open(voyage_config_loc, 'r') as f:
        data = json.load(f)

    voyage_info = data['voyage_info']
    current_soc = data['initial_battery_soc']
    segments = data['segments']
    
    battery_info = circuit_setup['battery']
    battery_capacity_Amin = battery_info['capacity_ah'] * battery_info['battery_in_parallel'] * 60
    
    current_capacity_Amin = current_soc * battery_capacity_Amin

    time_range_min = [0]
    results = []
    battery_capacity_list = [current_capacity_Amin]
    
    segment_length = len(segments)
    
    for segment_idx in range(segment_length):
        segment = segments[segment_idx]
        
        duration_minutes = segment['duration_minutes']
        throttle_setting = segment['throttle']
        panel_power_setting = segment['solar_power']
        
        elapsed = 0
        while elapsed < duration_minutes:
            step = min(SIMULATION_INTERVAL_MIN, duration_minutes - elapsed)
            
            modifications = {}
            modifications['panel_power_setting'] = panel_power_setting
            modifications['throttle_setting'] = throttle_setting
            modifications['current_soc'] = current_soc
            
            circuit, component_object, errors = build_circuit_from_json(circuit_setup=circuit_setup, modifications=modifications, constants=constants)
            analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available, constants=constants)

            if results == []:
                results.append(result)

            if analysis is None:
                print(f"{constants['BARF']}Simulation Aborted{constants['BARE']}")
                break
            
            battery_charge_current_A = result["summary"]["data"][0]["current"]["total_battery_input_current"]  
            
            if current_capacity_Amin + (battery_charge_current_A * step) > battery_capacity_Amin:
                time_to_full = (battery_capacity_Amin - current_capacity_Amin) / battery_charge_current_A
                
                if time_to_full > constants["EPSILON"]:
                    results.append(result)
                    time_range_min.append(time_range_min[-1] + time_to_full)
                    current_capacity_Amin = battery_capacity_Amin
                    battery_capacity_list.append(current_capacity_Amin)
                    current_soc = 1.0
                    step_up_prev(results, time_range_min, battery_capacity_list)
                
                remaining = step - time_to_full
                if remaining > constants["EPSILON"]:
                    modifications['max_charge_current'] = 0
                    circuit, component_object, errors = build_circuit_from_json(circuit_setup=circuit_setup, modifications=modifications, constants=constants)
                    analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available, constants=constants)
                    
                    results.append(result)
                    time_range_min.append(time_range_min[-1] + remaining)
                    battery_capacity_list.append(current_capacity_Amin)
                    step_up_prev(results, time_range_min, battery_capacity_list)
            
            elif current_capacity_Amin + (battery_charge_current_A * step) < 0:
                time_to_empty = abs(current_capacity_Amin / battery_charge_current_A)
                
                if time_to_empty > constants["EPSILON"]:
                    results.append(result)
                    time_range_min.append(time_range_min[-1] + time_to_empty)
                    current_capacity_Amin = 0
                    battery_capacity_list.append(current_capacity_Amin)
                    step_up_prev(results, time_range_min, battery_capacity_list)
                
                remaining = step - time_to_empty
                if remaining > constants["EPSILON"]:
                    modifications['max_discharge_current'] = 0
                    circuit, component_object, errors = build_circuit_from_json(circuit_setup=circuit_setup, modifications=modifications, constants=constants)
                    analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available, constants=constants)
                    
                    results.append(result)
                    time_range_min.append(time_range_min[-1] + remaining)
                    battery_capacity_list.append(current_capacity_Amin)
                    current_soc = 0.0
                    step_up_prev(results, time_range_min, battery_capacity_list)
            
            else:          
                results.append(result)
                time_range_min.append(time_range_min[-1] + step)
                current_capacity_Amin = current_capacity_Amin + (battery_charge_current_A * step)
                current_soc = current_capacity_Amin / battery_capacity_Amin
                battery_capacity_list.append(current_capacity_Amin)
                step_up_prev(results, time_range_min, battery_capacity_list)
            
            elapsed += step
        
        if analysis is None:
            break
    
    #print(json.dumps(results, indent=4))
    generate_graph(results=results, x_axis=time_range_min, x_label="Time (minutes)",
                   voltage_display_choice=['load_result', "mppt_result"],
                   current_display_choice=['summary', 'load_result'],
                   power_display_choice=['load_result'],
                   battery_capacity=battery_capacity_list,
                   save_path=save_path, constants=constants)   
    
def real_time_digital_simulation(circuit_setup: json, ngspice_available: bool):
    None

def step_up_prev(results: list, time_range_min: list, battery_capacity_list: list):
    prev = results[-2]
    curr = results[-1]
    
    copy = deepcopy(curr)
    """ if copy.get('battery_result') is not None:
        if copy['battery_result'].get("data") is not None:
            data = copy['battery_result']["data"]
            data[0]["voltage"] = prev['battery_result']["data"][0]["voltage"]
     """
    results.append(copy)
    
    
    time_range_min.insert(-1, time_range_min[-2])
    
    # Keep the battery slanted
    battery_capacity_list.insert(-1, battery_capacity_list[-2])