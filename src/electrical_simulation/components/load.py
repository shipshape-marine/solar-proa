from ..components.battery_array import Battery_Array

RAWSPICE_ITERATIONS = 1e6

class Load:
    def __init__(self, circuit, components, constants=None, **kwargs):
        self.load_name = kwargs.get("load_name")
        self.throttle = kwargs.get("throttle", 1.0)
        self.MOTOR_VOLTAGE = kwargs.get("nominal_voltage")
        self.MOTOR_TOTAL_POWER = kwargs.get("total_power")
        self.components = components
        self.constants = constants
        self.circuit = circuit
        self.MOTOR_POWER_DEMAND = self.MOTOR_TOTAL_POWER * self.throttle if self.throttle > 0.0 else self.constants["GROUNDING_RESISTANCE"]

    def setup_load(self, battery_array: Battery_Array, log = False):       
        BATTERY_MAX_DISCHARGE_CURRENT = battery_array.get_discharge_limit()
        MOTOR_CURRENT_DEMAND = self.MOTOR_POWER_DEMAND / battery_array.get_total_voltage()
        MOTOR_RESISTANCE = self.MOTOR_VOLTAGE / MOTOR_CURRENT_DEMAND
        POWER_SOURCE = battery_array.get_terminal()
        POWER_SOURCE_ID = battery_array.get_terminal_id()
        
        
        self.circuit.V(f"{self.load_name}", POWER_SOURCE, f"{self.load_name}", self.constants["GROUNDING_RESISTANCE"])
        # Restrict total current into loads from bus first, then in Load, calcuate percentage restricted
        # and multiply that by the current demand in each load
        #print(MOTOR_CURRENT_DEMAND, BATTERY_MAX_DISCHARGE_CURRENT)
        self.circuit.raw_spice += f"B{self.load_name} {self.load_name} 0 I = I(V{POWER_SOURCE_ID})<-{BATTERY_MAX_DISCHARGE_CURRENT} ? {MOTOR_CURRENT_DEMAND}+(I(V{POWER_SOURCE_ID})+{BATTERY_MAX_DISCHARGE_CURRENT})*{RAWSPICE_ITERATIONS} : {MOTOR_CURRENT_DEMAND})\n"
        
        self.components["load"].append(f"{self.load_name}")
        if log:
            print(self.__str__(self.MOTOR_POWER_DEMAND, MOTOR_CURRENT_DEMAND, MOTOR_RESISTANCE))
        
        if abs(battery_array.get_total_voltage() - self.MOTOR_VOLTAGE) > self.constants["MOTOR_VOLTAGE_MISMATCH_TOLERANCE"]:
            return f"Mismatch between battery voltage ({battery_array.get_total_voltage()} V) and motor nominal voltage ({self.MOTOR_VOLTAGE} V) exceeds tolerance of {self.constants['MOTOR_VOLTAGE_MISMATCH_TOLERANCE']} V"
        
        return None
            
    def power_rating(self):
        return self.MOTOR_TOTAL_POWER
    
    def throttle_setting(self):
        return self.throttle
    
    def __str__(self, MOTOR_POWER_DEMAND=None, MOTOR_CURRENT_DEMAND=None, MOTOR_RESISTANCE=None):
        return f"""
{self.constants['BARF']}Load Setup (Before balancing){self.constants['BARE']}
Motor Power Demand: {MOTOR_POWER_DEMAND} W
Motor Current Demand: {MOTOR_CURRENT_DEMAND:.2f} A
Motor Resistance: {MOTOR_RESISTANCE:.2f} Ohm
"""