from ..components.battery_array import Battery_Array
from ..components.solar_panel_array import Solar_Array
from ..constants import GROUNDING_RESISTANCE, MPPT_BATTERY_VOLTAGE_BUFFER, VOLTAGE_MISMATCH_TOLERANCE, WIRE_RESISTANCE, BARF, BARE

class MPPT:
    def __init__(self, circuit, components, **kwargs):
        self.MPPT_MAX_INPUT_VOLTAGE = kwargs.get("max_input_voltage")
        self.MPPT_MAX_INPUT_CURRENT = kwargs.get("max_input_current")
        self.MPPT_MAX_OUTPUT_VOLTAGE = kwargs.get("max_output_voltage")
        self.MPPT_MAX_OUTPUT_CURRENT = kwargs.get("max_output_current")
        self.MPPT_OUTPUT_BUFFER_VOLTAGE = MPPT_BATTERY_VOLTAGE_BUFFER
        self.MPPT_EFFICIENCY = kwargs.get("efficiency")
        self.circuit = circuit
        self.components = components
        self.terminal = None
        self.MPPT_OUTPUT_VOLTAGE = None
    
    def setup_mppt(self, array_number, solar_array: Solar_Array, battery_array: Battery_Array, log=False):
        MPPT_INPUT_VOLTAGE = solar_array.get_total_voltage()
        MPPT_INPUT_CURRENT = solar_array.get_total_current()
        MPPT_MAX_INPUT_POWER = MPPT_INPUT_VOLTAGE * MPPT_INPUT_CURRENT
        MPPT_INPUT_RESISTANCE = MPPT_INPUT_VOLTAGE / MPPT_INPUT_CURRENT
        
        self.MPPT_OUTPUT_VOLTAGE = battery_array.get_total_voltage() + self.MPPT_OUTPUT_BUFFER_VOLTAGE
        MPPT_OUTPUT_POWER = MPPT_MAX_INPUT_POWER * self.MPPT_EFFICIENCY
        MPPT_OUTPUT_CURRENT = MPPT_OUTPUT_POWER / self.MPPT_OUTPUT_VOLTAGE

        SOLAR_POWER_RAIL = solar_array.get_terminal()
        self.circuit.R(f"arr{array_number}_mppt_input_load", 
                 f"{SOLAR_POWER_RAIL}", self.circuit.gnd, 
                 MPPT_INPUT_RESISTANCE)

        # Regulate output current to calculated amount
        self.circuit.raw_spice += f"""Barr{array_number}_mppt_current_reg 0 arr{array_number}_mppt_output I = min({self.MPPT_MAX_OUTPUT_CURRENT}, {MPPT_OUTPUT_CURRENT})\n"""
        
        self.circuit.V(f"arr{array_number}_mppt_output", f"arr{array_number}_mppt_output", f"arr{array_number}_mppt_output_measured", GROUNDING_RESISTANCE)
        
        self.terminal = "total_mppt_output"
        # Connect MPPT output to DC bus
        self.circuit.R(f"arr{array_number}_mppt_out_wire", f"arr{array_number}_mppt_output_measured", self.terminal, WIRE_RESISTANCE)
        #dc_bus is shared positive node for battery and load

        self.components["mppt"].append(f"arr{array_number}_mppt_current_reg")
        self.components["wire"].append(f"arr{array_number}_mppt_out_wire")
        if log:
            print(self.__str__(array_number, MPPT_INPUT_VOLTAGE, MPPT_MAX_INPUT_POWER, MPPT_OUTPUT_POWER, MPPT_OUTPUT_CURRENT))
            
        if abs(battery_array.get_total_voltage() - self.MPPT_MAX_OUTPUT_VOLTAGE) > VOLTAGE_MISMATCH_TOLERANCE:
            return f"Mismatch between battery voltage ({battery_array.get_total_voltage()} V) and MPPT max output voltage ({self.MPPT_MAX_OUTPUT_VOLTAGE} V) exceeds tolerance of {VOLTAGE_MISMATCH_TOLERANCE} V"
        if MPPT_INPUT_VOLTAGE > self.MPPT_MAX_INPUT_VOLTAGE:
            return f"(Array {array_number}) Panel input voltage ({MPPT_INPUT_VOLTAGE} V) exceeds max MPPT input voltage ({self.MPPT_MAX_INPUT_VOLTAGE} V)"
        if MPPT_INPUT_CURRENT > self.MPPT_MAX_INPUT_CURRENT:
            return f"(Array {array_number}) Panel input current ({MPPT_INPUT_CURRENT} A) exceeds max MPPT input current ({self.MPPT_MAX_INPUT_CURRENT} A)"
        else:
            return None
    
    def get_terminal(self):
        if self.terminal is None:
            return "MPPT terminal has not been set up yet."
        return self.terminal
    
    def get_efficiency(self):
        return self.MPPT_EFFICIENCY
    
    def get_output_limit(self):
        return self.MPPT_MAX_OUTPUT_CURRENT
    
    def get_working_voltage(self):
        if self.MPPT_OUTPUT_VOLTAGE is None:
            return "MPPT has not been set up yet."
        return self.MPPT_OUTPUT_VOLTAGE
    
    def __str__(self, array_number, MPPT_INPUT_VOLTAGE, MPPT_MAX_INPUT_POWER, MPPT_OUTPUT_POWER, MPPT_OUTPUT_CURRENT):
        return f"""
{BARF}MPPT Setup {array_number + 1}{BARE}
Input Voltage: {MPPT_INPUT_VOLTAGE} V
Output Voltage: {self.MPPT_OUTPUT_VOLTAGE} V
Max Power: {MPPT_MAX_INPUT_POWER} W
Output Power: {MPPT_OUTPUT_POWER:.2f} W
Output Current: {MPPT_OUTPUT_CURRENT:.2f} A
"""