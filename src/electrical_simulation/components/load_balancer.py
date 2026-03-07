from ..components.battery_array import Battery_Array

RAWSPICE_ITERATIONS = 1e6

class Load_Balancer:
    def __init__(self, circuit, components, constants=None):
        self.circuit = circuit
        self.components = components
        self.constants = constants
        
    def balance_loads(self, battery_array: Battery_Array):
        # Balancing load to limit battery charge current
        # Note: No idea how did this worked. PySpice might have allowed cyclical calculation such that:
        # I(Vbattery_input_current)-{BATTERY_MAX_CHARGE_CURRENT} repeats until it tends to the max charge current 
        
        POWER_SOURCE_ID = battery_array.get_terminal_id()
        POWER_SOURCE = battery_array.get_terminal()
        BATTERY_MAX_CHARGE_CURRENT = battery_array.get_charge_limit()
        
        self.circuit.V("balancing_load", POWER_SOURCE, "balancing_load", self.constants["GROUNDING_RESISTANCE"]) 
        self.circuit.raw_spice += f"Bbalancing_load balancing_load 0 I = I(V{POWER_SOURCE_ID})>{BATTERY_MAX_CHARGE_CURRENT} ? (I(V{POWER_SOURCE_ID})-{BATTERY_MAX_CHARGE_CURRENT})*{RAWSPICE_ITERATIONS} : 0\n"
        
        return None