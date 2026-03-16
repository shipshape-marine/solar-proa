
def cross_check_result(analysis, component_object, result, constants=None):
    if analysis is None:
        return
    mppt = result["mppt_result"]
    solar = result["solar_result"]
    load = result["load_result"]
    load_balancer = result["load_balancer"]
    
    # --Error analysis---
    total_mppt_output = result["summary"]["data"][0]["current"]["total_mppt_output_current"]
    total_battery_input = result["summary"]["data"][0]["current"]["total_battery_input_current"]
    total_load_current = 0.0
    for each in load["data"]:
        for key in each["current"]:
            total_load_current += each["current"][key]
    
    for each in load_balancer["data"]:
        for key in each["current"]:
            total_load_current += each["current"][key]
            
    if total_mppt_output - total_battery_input - total_load_current > constants["EPSILON"]:
        result["error"]["data"].append(f"Kirchhoff's Law violated. MPPT Output Current ({total_mppt_output} A) \
does not equal Battery Input Current ({total_battery_input} A) + Load Current ({total_load_current} A)")
    
    result["error"]["array_count"] = len(result["error"]["data"])
    
    
    # ---Warning analysis---
    # Check solar array power into mppt
    set_count = solar["array_count"]
    solar_data = solar["data"]
    mppt_data = mppt["data"]
    for i in range(set_count):
        if component_object.get("mppt") is None:
            continue
        output_curr_limit = component_object["mppt"][i].get_output_limit()
        actual_curr_output = mppt_data[i]["current"]["mppt_output"]
        actual_voltage_output = mppt_data[i]["voltage"]["mppt_output"]
        solar_output_voltage = solar_data[i]["voltage"]["solar_array_output"]
        solar_output_current = solar_data[i]["current"]["solar_array_output"]
        input_power = solar_output_voltage * solar_output_current * component_object["mppt"][i].get_efficiency()
        if output_curr_limit - actual_curr_output < constants["EPSILON"]:
            result["warning"]["data"].append(f"(Array {i}) Excess power input into MPPT due to {output_curr_limit} A output limit. \
Total Input Power: {input_power:.2f} W, restricted to: {actual_voltage_output*actual_curr_output:.2f} W")
    
    # Check battery charge
    excess_current = load_balancer['data'][0]["current"]["balancing_load"]
    if excess_current > constants["EPSILON"]:
        result["warning"]["data"].append(f"Battery is overcharged by {excess_current} A")
        
    # Check battery discharge and add motor physics info
    for each in load["data"]:
        voltage = float(list(each["voltage"].values())[0])
        current = float(list(each["current"].values())[0])
        actual_power = voltage * current

        mppt_count = len(component_object.get("mppt", []))
        temp_eff_calculation = 0.0
        for i in range(mppt_count):
            temp_eff_calculation += component_object["mppt"][i].get_efficiency()
        average_efficiency = temp_eff_calculation / mppt_count if mppt_count > 0 else 1.0
            
        index = each["array_index"]
        load_obj = component_object["load"][index]
        power_rating = load_obj.power_rating() * average_efficiency
        throttle_setting = load_obj.throttle_setting()
        actual_throttle = actual_power / power_rating if power_rating > 0 else 0.0
        
        # Add motor physics data to result if available
        motor_op = load_obj.get_motor_operating_point()
        if motor_op is not None:
            each["motor_physics"] = {
                "model_type": "BLDC",
                "speed_rpm": motor_op.speed_rpm,
                "efficiency": motor_op.efficiency,
                "power_mechanical_w": motor_op.power_mechanical_w,
                "power_electrical_w": motor_op.power_electrical_w,
                "torque_nm": motor_op.torque_nm,
                "is_stalled": motor_op.is_stalled,
                "is_current_limited": motor_op.is_current_limited,
                "propeller_load_factor": motor_op.propeller_load_factor
            }
            # Add info message about motor model
            result["info"]["data"].append(
                f"Motor {index}: Using BLDC physics model - "
                f"{motor_op.speed_rpm:.0f} RPM, {motor_op.efficiency*100:.1f}% efficiency, "
                f"{motor_op.power_mechanical_w:.1f}W mechanical output"
            )
        else:
            each["motor_physics"] = {
                "model_type": "linear",
                "speed_rpm": None,
                "efficiency": None,
                "power_mechanical_w": None,
                "power_electrical_w": actual_power,
                "torque_nm": None,
                "is_stalled": None
            }
        
        # Check if motor is current-limited by ESC or battery
        if motor_op is not None:
            # Warn when ESC is current-limiting the motor
            if motor_op.is_current_limited and throttle_setting < 1.0:
                result["warning"]["data"].append(
                    f"Motor {index} ESC current-limited at {motor_op.current_amps:.1f}A. "
                    f"Power capped at {motor_op.power_electrical_w:.0f}W "
                    f"({throttle_setting*100:.0f}% throttle)."
                )
            
            # Also check if battery further restricts below what the motor model expects
            expected_power = motor_op.power_electrical_w
            bldc_tolerance = max(constants["POWER_MISMATCH_TOLERANCE_PERCENTAGE"], 5.0)
            if expected_power > 0 and (expected_power - actual_power) / expected_power * 100 > bldc_tolerance:
                pct_delivered = actual_power / expected_power * 100 if expected_power > 0 else 0.0
                result["warning"]["data"].append(f"Battery array is being over-discharged. Motor {index} \
has been restricted to {pct_delivered:.2f}% of expected {expected_power:.0f}W at {throttle_setting*100:.0f}% throttle.")
        elif (throttle_setting - actual_throttle) * 100 > constants["POWER_MISMATCH_TOLERANCE_PERCENTAGE"]:
            actual_throttle = actual_power / power_rating if power_rating > 0 else 0.0
            result["warning"]["data"].append(f"Battery array is being over-discharged. Motor {index} \
has been restricted to {actual_throttle*100:.2f}% instead of {throttle_setting*100:.2f}% throttle level.")
        
    result["warning"]["array_count"] = len(result["warning"]["data"])
    result["info"]["array_count"] = len(result["info"]["data"])
    return None
        