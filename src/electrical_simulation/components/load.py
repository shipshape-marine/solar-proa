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
    
    def name(self):
        return self.load_name   
    
    def power_rating(self):
        return self.MOTOR_TOTAL_POWER
    
    def throttle_setting(self):
        return self.throttle
    
    def __str__(self):
        current = self.MOTOR_POWER_DEMAND / self.MOTOR_VOLTAGE if self.MOTOR_VOLTAGE > 0 else 0
        return f"""
{self.constants['BARF']}Load Setup (Before balancing){self.constants['BARE']}
Motor Power Demand: {self.MOTOR_POWER_DEMAND} W
Motor Current Demand: {current:.2f} A
Motor Resistance: {self.MOTOR_VOLTAGE / current if self.MOTOR_POWER_DEMAND > 0 else 0:.2f} Ohm
"""