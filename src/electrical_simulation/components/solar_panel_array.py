
class Solar_Array:
    def __init__(self, circuit, components, constants=None, **kwargs):
        """
        Solar panel array component.

        Voltage sources in series/parallel representing panels; provides current
        to the MPPT input.

        Required kwargs:
            in_series (int): Number of panels in series per string
            in_parallel (int): Number of strings in parallel
            voltage (float): Per-panel voltage (V); must be non-zero, it divides
                calculated_power to give the per-panel current
            calculated_power (float): Per-panel power (W) for this run, computed
                upstream by build_circuit_from_json as
                power x (panel_power_setting or solar_power, default 1.0)

        Optional kwargs:
            power (float): Per-panel rated power (W) from the component spec.
                Not read here — build_circuit_from_json reads it to derive
                calculated_power. Accepted and ignored.
            solar_power (float): Irradiance scale factor, 0.0-1.0 (default 1.0
                upstream). Not read here — build_circuit_from_json applies it to
                power unless a panel_power_setting modification overrides it.
                Accepted and ignored.
            choice (str): Component name from electrical_components.json
                (resolved upstream, accepted and ignored here)

        Note: constants defaults to None but EPSILON is read below, so a
        constants dict is effectively mandatory.
        """
        self.circuit = circuit
        self.constants = constants
        self.PANEL_IN_PARALLEL = kwargs.get("in_parallel")
        self.PANEL_IN_SERIES = kwargs.get("in_series")
        self.PANEL_VOLTAGE = kwargs.get("voltage")
        self.PANEL_CURRENT = max(self.constants["EPSILON"], kwargs.get("calculated_power") / self.PANEL_VOLTAGE)
        self.PANEL_INTERNAL_R = self.PANEL_VOLTAGE / self.PANEL_CURRENT
        self.PANEL_ARRAY_TOTAL_VOLTAGE = self.PANEL_IN_SERIES * self.PANEL_VOLTAGE
        self.PANEL_ARRAY_TOTAL_CURRENT = self.PANEL_IN_PARALLEL * self.PANEL_CURRENT
        self.PANEL_ARRAY_TOTAL_POWER = self.PANEL_ARRAY_TOTAL_VOLTAGE * self.PANEL_ARRAY_TOTAL_CURRENT
        self.terminal = None
        self.components = components
        self.array_number = None

    # Current source: Return terminal name only
    def create_panels(self, array_number, log=False):
        self.array_number = array_number
        for p in range(self.PANEL_IN_PARALLEL):
            panel_row = []
            for s in range(self.PANEL_IN_SERIES):
                panel_name = f"arr{array_number}_p{p}_s{s}_panel"
                panel_row.append(panel_name)
                
                panel_pos = f"{panel_name}_positive"
                panel_neg = f"{panel_name}_negative"
                
                self.circuit.V(panel_name, panel_pos, panel_neg, self.PANEL_VOLTAGE)
                if s == 0:
                    self.circuit.R(f"{panel_name}_grounding", panel_neg, self.circuit.gnd, self.constants["GROUNDING_RESISTANCE"])
                else:
                    prev_panel_name = f"arr{array_number}_p{p}_s{s-1}_panel"
                    self.circuit.R(f"{panel_name}_internal", panel_neg, f"{prev_panel_name}_positive", self.constants["WIRE_RESISTANCE"])
                
            self.components["panel"].append(panel_row)
        
        # Wire positive terminal of each parallel string      
        for index, row in enumerate(self.components["panel"]):
            panel_row_end = row[-1]
            positive_node = f"{panel_row_end}_positive"
            panel_wire = f"arr{array_number}_panel_wire_{index}"
            self.circuit.R(panel_wire, positive_node, "panel_input_measured", self.constants["WIRE_RESISTANCE"])  
            self.components["wire"].append(panel_wire)
            
        self.terminal = f"arr{array_number}_solar_array_output"
        self.circuit.V(f"arr{array_number}_solar_array_output", 
                       "panel_input_measured", 
                       self.terminal,
                       self.constants["GROUNDING_RESISTANCE"])
        
        if log:
            print(self)        

        return None
    
    def get_terminal(self):
        if self.terminal is None:
            raise ValueError("Solar Array terminal not created yet")
        return self.terminal
    
    def get_total_voltage(self):
        return self.PANEL_ARRAY_TOTAL_VOLTAGE
    
    def get_total_current(self):
        return self.PANEL_ARRAY_TOTAL_CURRENT
    
    def __str__(self):
        return f"""\
{self.constants['BARF']}Solar Array Setup {self.array_number + 1}{self.constants['BARE']}
Configuration: {self.PANEL_IN_SERIES} in series, {self.PANEL_IN_PARALLEL} in parallel
Total Voltage: {self.PANEL_ARRAY_TOTAL_VOLTAGE} V
Total Current: {self.PANEL_ARRAY_TOTAL_CURRENT} A
Total Power: {self.PANEL_ARRAY_TOTAL_POWER} W
"""