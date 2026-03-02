from ..components.load import Load

from ..components.battery_array import Battery_Array


class Load_Array():
    def __init__(self, circuit, components, constants, load_list: list):
        self.circuit = circuit
        self.components = components
        self.constants = constants
        self.load_list: list[Load] = load_list
        self.terminal = "load_array_positive"
        self.terminal_id = "load_array_current"
        self.__create_array()
            
    def __create_array(self):
        """Connect all loads in parallel - each load shares the same positive and ground nodes."""
        for index, load in enumerate(self.load_list):
            load_name = load.name()
            load_resistance = load.MOTOR_VOLTAGE / (load.MOTOR_POWER_DEMAND / load.MOTOR_VOLTAGE) if load.MOTOR_POWER_DEMAND > 0 else 1e9
            
            # Each load connects between the common positive terminal and ground (parallel)
            self.circuit.R(f"load_{load_name}", self.terminal, self.circuit.gnd, load_resistance)
    
    def setup_loads(self, battery_array: Battery_Array, log=False):
        """Connect the load array to the power source from battery_array."""
        POWER_SOURCE = battery_array.get_terminal()
        # Connect battery terminal to load array positive terminal via wire resistance
        self.circuit.R(self.terminal_id, POWER_SOURCE, self.terminal, self.constants["WIRE_RESISTANCE"])
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
