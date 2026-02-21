import datetime
from .parse_result import parse_simulation_result
from .result_checker import cross_check_result
from PySpice.Spice.Netlist import Circuit

def begin_simulation(circuit, component_object, errors, ngspice_available=False,
                     start_simulation=True, ignore_error=True, simulation_logging=False,
                     show_panels=False, show_errors=False, show_warnings=False, constants=None):
    simulation_started = False
    
    # Errors cannot be ignored for actual run
    has_error = len(errors) > 0
    analysis = None
    result = None

    if not has_error or ignore_error:
        if start_simulation:
            simulation_started = True
            meta_data = {"name": circuit.title, "date": datetime.datetime.now().isoformat()}
            
            analysis, result, struc = __simulate__(circuit, meta_data, errors, ngspice_available, simulation_logging, constants)
            parse_simulation_result(analysis, result, struc, simulation_logging, show_panels, constants=constants)
            cross_check_result(analysis, component_object, result, constants=constants)
    else:
        if show_errors and start_simulation:
            print(f"{constants['BARF']}Simulation Aborted Due to Errors in Circuit Setup.{constants['BARE']}")
    
    if has_error and show_errors:
        print(f"\n{constants['BARF']}Errors Detected During Circuit Setup:{constants['BARE']}")
        for error in errors:
            print(f"\t{error}")
        print()

    # Warning are components with limited output but might still work
    if simulation_started and result["warning"]["array_count"] > 0 and show_warnings:
        print(f"\n{constants['BARF']}Warnings Detected During Simulation:{constants['BARE']}")
        for warning in result["warning"]["data"]:
            print(f"\t{warning}")
        print()

    return analysis, result

def __simulate__(circuit: Circuit, meta_data, errors, NGSPICE_AVAILABLE, simulation_logging=False, constants=None):
    struc = '{"array_index": 0, "voltage": {}, "current": {}}'
    mppt_result = {
        "keyword": "mppt",
        "array_count": 0,
        "data": [],
    }
    solar_result = {
        "keyword": "solar_array",
        "array_count": 0,
        "data": [],
    }
    panel_result = {
        "keyword": "panel",
        "array_count": 0,
        "data": [],
    }
    
    battery_result = {
        "keyword": "battery",
        "array_count": 0,
        "data": [],
    }
    load_result = {
        "keyword": "load",
        "array_count": 0,
        "data": [],
    }
    
    load_balancer = {
        "keyword": "balancing_load",
        "array_count": 0,
        "data": [],
    }
    
    summary = {
        "keyword": "total",
        "array_count": 0,
        "data": [],
    }
    
    error = {
        "keyword": "error",
        "array_count": len(errors),
        "data": errors,
    }
    
    warning = {
        "keyword": "warning",
        "array_count": 0,
        "data": [],
    }
    
    
    result = {
        "info": meta_data,
        "error": error,
        "warning": warning,
        "summary": summary,
        "mppt_result": mppt_result,
        "battery_result": battery_result,
        "solar_result": solar_result,
        "panel_result": panel_result,
        "load_balancer": load_balancer,
        "load_result": load_result,
    }
    
    if not NGSPICE_AVAILABLE:
        err = "NgSpice is not available. Simulation cannot proceed."
        result["error"]["data"].append(err)
        return None, result, struc
    
    try:
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.operating_point()
    except Exception as e:
        result["error"]["data"].append("Error has occured during simulation. Check console for details.")
        return None, result, struc
    
    if simulation_logging:
        print(f"\n{constants['BARF']}Simulation Completed Successfully.{constants['BARE']}")
    return analysis, result, struc
