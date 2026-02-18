
class Battery_Array:
    def __init__(self, circuit, components, constants=None, **kwargs):
        self.circuit = circuit
        self.BATTERY_IN_PARALLEL = kwargs.get("battery_in_parallel")
        self.BATTERY_IN_SERIES = kwargs.get("battery_in_series")
        
        self.SOC = kwargs.get("current_soc", 1.0)
        if kwargs.get("min_voltage") is not None and kwargs.get("max_voltage") is not None:
            self.BATTERY_VOLTAGE = self.__estimate_battery_voltage(self.SOC, kwargs.get("min_voltage"), kwargs.get("max_voltage"))
        else:
            self.BATTERY_VOLTAGE = kwargs.get("battery_voltage")
        #print("Estimated Battery Voltage:", self.BATTERY_VOLTAGE, "SOC:", self.SOC)
            
        self.BATTERY_MAX_CHARGE_CURRENT = kwargs.get("max_charge_current")
        self.BATTERY_MAX_DISCHARGE_CURRENT = kwargs.get("max_discharge_current")
        self.terminal = None
        self.terminal_id = None
        self.components = components
        self.constants = constants
    
    # Battery types should not be mixed, hence no array_number parameter
    def create_battery_array(self, log=False):
        for p in range(self.BATTERY_IN_PARALLEL):
            battery_row = []
            for s in range(self.BATTERY_IN_SERIES):
                battery_name = f"p{p}_s{s}_battery"
                battery_row.append(battery_name)
                
                battery_pos = f"{battery_name}_positive"
                battery_neg = f"{battery_name}_negative"
                
                self.circuit.V(battery_name, battery_pos, battery_neg, self.BATTERY_VOLTAGE)
                if s == 0:
                    self.circuit.R(f"{battery_name}_grounding", battery_neg, self.circuit.gnd, self.constants["GROUNDING_RESISTANCE"])
                else:
                    prev_battery_name = f"p{p}_s{s-1}_battery"
                    self.circuit.R(f"{battery_name}_internal", battery_neg, f"{prev_battery_name}_positive", self.constants["WIRE_RESISTANCE"])
                
            self.components["battery"].append(battery_row)
                        
        for index, row in enumerate(self.components["battery"]):
            battery_row_end = row[-1]
            positive_node = f"{battery_row_end}_positive"
            battery_wire = f"battery_wire_{index}"
            self.circuit.R(battery_wire, positive_node, "battery_input_measured", self.constants["WIRE_RESISTANCE"])  
            self.components["wire"].append(battery_wire)
            
        self.terminal_id = "total_battery_input_current"
        self.terminal = "total_dc_bus_voltage"   
        
        self.circuit.V(self.terminal_id,
                       self.terminal, "battery_input_measured",
                       self.constants["GROUNDING_RESISTANCE"])
        
        if log:
            print(self)        

        return None
    
    def get_terminal(self):
        if self.terminal is None:
            raise ValueError("Battery Array terminal not created yet")
        return self.terminal
    
    def get_terminal_id(self):
        if self.terminal_id is None:
            raise ValueError("Battery Array terminal not created yet")
        return self.terminal_id
            
    def get_discharge_limit(self):
        return self.BATTERY_IN_PARALLEL * self.BATTERY_MAX_DISCHARGE_CURRENT
    
    def get_charge_limit(self):
        return self.BATTERY_IN_PARALLEL * self.BATTERY_MAX_CHARGE_CURRENT
    
    def get_total_voltage(self):
        return self.BATTERY_IN_SERIES * self.BATTERY_VOLTAGE   
        
    def __estimate_battery_voltage(self, soc, min_voltage, max_voltage):
        """Simple linear estimation"""
        return min_voltage + (max_voltage - min_voltage) * soc

    def __str__(self):
        return f"""
{self.constants['BARF']}Battery Setup{self.constants['BARE']}
Configuration: {self.BATTERY_IN_SERIES} in series, {self.BATTERY_IN_PARALLEL} in parallel
Total Voltage: {self.get_total_voltage()} V
Max Charge Current: {self.get_charge_limit()} A
Max Discharge Current: {self.get_discharge_limit()} A
"""