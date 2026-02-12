from ..constants import BARF, BARE, GROUNDING_RESISTANCE, WIRE_RESISTANCE, EPSILON

class Solar_Array:
    def __init__(self, circuit, components, **kwargs):
        self.circuit = circuit
        self.PANEL_IN_PARALLEL = kwargs.get("in_parallel")
        self.PANEL_IN_SERIES = kwargs.get("in_series")
        self.PANEL_CURRENT = max(EPSILON, kwargs.get("power") / kwargs.get("voltage"))
        self.PANEL_INTERNAL_R = kwargs.get("voltage") / self.PANEL_CURRENT
        self.PANEL_ARRAY_TOTAL_VOLTAGE = self.PANEL_IN_SERIES * kwargs.get("voltage")
        self.PANEL_ARRAY_TOTAL_CURRENT = self.PANEL_IN_PARALLEL * self.PANEL_CURRENT
        self.PANEL_ARRAY_TOTAL_POWER = self.PANEL_ARRAY_TOTAL_VOLTAGE * self.PANEL_ARRAY_TOTAL_CURRENT
        self.terminal = None
        self.components = components

    # Current source: Return terminal name only
    def create_panels(self, array_number, log=False):
        for p in range(self.PANEL_IN_PARALLEL):
            panel_row = []
            for s in range(self.PANEL_IN_SERIES):
                panel_name = f"arr{array_number}_p{p}_{s}_panel"
                panel_row.append(panel_name)
                
                panel_pos = f"{panel_name}_positive"
                panel_neg = f"{panel_name}_negative"
                
                # Current source: neg -> pos
                self.circuit.I(panel_name, panel_neg, panel_pos, self.PANEL_CURRENT)
                
                # Ground all panel, else panel can only deliver voltage by a factor of 40 for some reason
                self.circuit.R(f"{panel_name}_leak_to_gnd", panel_neg, self.circuit.gnd, GROUNDING_RESISTANCE)

                if s != 0:
                    prev_panel_name = f"arr{array_number}_p{p}_s{s-1}_panel"
                    # Internal resistance
                    self.circuit.R(f"{panel_name}_internal", panel_neg, f"{prev_panel_name}_positive", self.PANEL_INTERNAL_R)

            self.components["panel"].append(panel_row)
        
        for index, row in enumerate(self.components["panel"]):
            solar_row_end = row[-1]
            positive_node = f"{solar_row_end}_positive"
            panel_wire = f"arr{array_number}_panel_wire_{index}"
            self.circuit.R(panel_wire, positive_node, f"arr{array_number}_solar_array_output", WIRE_RESISTANCE)
            self.components["wire"].append(panel_wire)
            # Small resistance to model wiring losses
        
        self.terminal = f"arr{array_number}_solar_array_output_measured"
        
        self.circuit.V(f"arr{array_number}_solar_array_output", 
                       f"arr{array_number}_solar_array_output",
                       f"{self.terminal}", 
                       GROUNDING_RESISTANCE)
        
       
        if log:
            print(self.__str__(array_number))
            
        return None
    
    def get_terminal(self):
        if self.terminal is None:
            raise ValueError("Solar Array terminal not created yet")
        return self.terminal
    
    def get_total_voltage(self):
        return self.PANEL_ARRAY_TOTAL_VOLTAGE
    
    def get_total_current(self):
        return self.PANEL_ARRAY_TOTAL_CURRENT
    
    def __str__(self, array_number=None):
        return f"""\
{BARF}Solar Array Setup {(array_number + 1) if array_number else 1}{BARE}
Configuration: {self.PANEL_IN_SERIES} in series, {self.PANEL_IN_PARALLEL} in parallel
Total Voltage: {self.PANEL_ARRAY_TOTAL_VOLTAGE} V
Total Current: {self.PANEL_ARRAY_TOTAL_CURRENT} A
Total Power: {self.PANEL_ARRAY_TOTAL_POWER} W
"""