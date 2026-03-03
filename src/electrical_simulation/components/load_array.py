from ..components.load import Load

from ..components.battery_array import Battery_Array

RAWSPICE_ITERATIONS = 1e6


class Load_Array():
    def __init__(self, circuit, components, constants, load_list: list):
        self.circuit = circuit
        self.components = components
        self.constants = constants
        self.load_list: list[Load] = load_list
        self.terminal = "l_array_positive"
        self.terminal_id = "l_array"
        self.__create_array()
            
    def __create_array(self):
        """Connect all load positive terminals to a single wire and negative terminals to ground."""
        for load in self.load_list:
            load_name = load.name()

            # Wire from single wire to per-load node, current probe, then grounding resistor
            load_node = f"{load_name}_positive"
            load_measured = f"{load_name}_measured"
            self.circuit.R(f"{load_name}_wire", self.terminal, load_node, self.constants["WIRE_RESISTANCE"])
            self.circuit.V(f"{load_name}", load_node, load_measured, 1e-06)
            self.circuit.R(f"{load_name}_gnd", load_measured, self.circuit.gnd, 1e9)
    
    def setup_loads(self, battery_array: Battery_Array):
        """Connect the power source to the single wire created in create_array.
        Restricts individual load currents if battery discharge limit is exceeded."""
        POWER_SOURCE = battery_array.get_terminal()
        POWER_SOURCE_ID = battery_array.get_terminal_id()
        BATTERY_MAX_DISCHARGE_CURRENT = battery_array.get_discharge_limit()

        self.circuit.R(self.terminal_id, POWER_SOURCE, self.terminal, self.constants["WIRE_RESISTANCE"])

        # Replace each load resistor with a behavioral current source that scales back
        # proportionally when total battery discharge current exceeds the limit
        for load in self.load_list:
            load_name = load.name()
            motor_current_demand = load.MOTOR_POWER_DEMAND / battery_array.get_total_voltage() if load.MOTOR_POWER_DEMAND > 0 else 0

            self.circuit.raw_spice += (
                f"B{load_name}_limit {load_name}_measured 0 "
                f"I = I(V{POWER_SOURCE_ID})<-{BATTERY_MAX_DISCHARGE_CURRENT} ? "
                f"{motor_current_demand}+(I(V{POWER_SOURCE_ID})+{BATTERY_MAX_DISCHARGE_CURRENT})*{RAWSPICE_ITERATIONS} "
                f": {motor_current_demand}\n"
            )

        return None
    
    def get_terminal(self):
        return self.terminal
    
    def get_terminal_id(self):
        return self.terminal_id
    
    
    def __str__(self):
        return f"""{self.constants['BARF']}Load Array Setup{self.constants['BARE']}
Loads: {', '.join([load.name() for load in self.load_list])}
Count: {len(self.load_list)}
"""
