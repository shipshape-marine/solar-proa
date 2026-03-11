from .motor_model import create_motor_model_from_config, MotorModel

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
        
        # Try to create motor physics model from config
        self.motor_model = create_motor_model_from_config(kwargs, self.MOTOR_VOLTAGE)
        
        # Calculate power demand using motor model or linear fallback
        if self.throttle <= 0.0:
            self.MOTOR_POWER_DEMAND = self.constants["GROUNDING_RESISTANCE"]
            self._motor_operating_point = None
        elif self.motor_model is not None:
            # Use motor physics model
            self._motor_operating_point = self.motor_model.calculate_operating_point(self.throttle)
            self.MOTOR_POWER_DEMAND = self._motor_operating_point.power_electrical_w
        else:
            # Fallback to linear model
            self.MOTOR_POWER_DEMAND = self.MOTOR_TOTAL_POWER * self.throttle
            self._motor_operating_point = None
    
    def name(self):
        return self.load_name   
    
    def power_rating(self):
        return self.MOTOR_TOTAL_POWER
    
    def throttle_setting(self):
        return self.throttle
    
    def get_motor_operating_point(self):
        """Return motor operating point if using physics model, else None."""
        return self._motor_operating_point
    
    def uses_motor_physics(self):
        """Return True if using motor physics model, False if linear fallback."""
        return self.motor_model is not None
    
    def __str__(self):
        current = self.MOTOR_POWER_DEMAND / self.MOTOR_VOLTAGE if self.MOTOR_VOLTAGE > 0 else 0
        base_info = f"""
{self.constants['BARF']}Load Setup (Before balancing){self.constants['BARE']}
Motor Power Demand: {self.MOTOR_POWER_DEMAND:.1f} W
Motor Current Demand: {current:.2f} A
Motor Resistance: {self.MOTOR_VOLTAGE / current if self.MOTOR_POWER_DEMAND > 0 else 0:.2f} Ohm
"""
        if self._motor_operating_point is not None:
            op = self._motor_operating_point
            base_info += f"""Motor Model: BLDC Physics
Motor Speed: {op.speed_rpm:.0f} RPM
Motor Efficiency: {op.efficiency * 100:.1f}%
Mechanical Power: {op.power_mechanical_w:.1f} W
"""
        else:
            base_info += "Motor Model: Linear (no physics constants)\n"
        
        return base_info