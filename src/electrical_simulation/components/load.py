from .motor_model import create_motor_model_from_config, MotorModel

RAWSPICE_ITERATIONS = 1e6

class Load:
    def __init__(self, circuit, components, constants=None, bus_voltage=None, **kwargs):
        """
        Load component.

        Behavioural current sink on the DC bus; the power demand comes from the
        BLDC motor model when motor constants are present, otherwise from linear
        scaling (throttle x total_power).

        Named parameters (not kwargs):
            bus_voltage (float): Actual DC bus voltage (V) the motor model is
                solved against; build_circuit_from_json passes the battery pack
                voltage. Falls back to nominal_voltage when None.

        Required kwargs:
            load_name (str): Node-name prefix for this load. Injected by
                build_circuit_from_json as arr{N}_load_{choice}, not read from
                the circuit JSON.
            nominal_voltage (float): Motor nominal voltage (V); also the
                bus_voltage fallback, and the divisor for the ESC current limit
                (total_power / nominal_voltage)
            total_power (float): Motor rated power (W); the linear model's
                full-throttle demand and the basis of the ESC current limit

        Optional kwargs:
            throttle (float): Throttle position, 0.0-1.0 (default: 1.0). At
                throttle <= 0.0 the demand is pinned to GROUNDING_RESISTANCE and
                no operating point is produced.
            motor_kv (float): Motor velocity constant (RPM/V)
            motor_resistance (float): Winding resistance (ohms)
                motor_kv and motor_resistance must BOTH be present to enable the
                BLDC physics model; if either is missing the linear fallback is
                used regardless of the other motor/propeller kwargs.
            motor_no_load_current (float): No-load current (A) (default: 0.0)
            propeller_kp (float): Propeller load coefficient (N·m/(rad/s)^2).
                When omitted it is auto-derived from total_power and
                nominal_voltage so rated current is reached at full throttle.
            propeller_load_factor (float): Load scale, 1.0 = startup/bollard,
                <1.0 = cruise equilibrium (default: 1.0)
            choice (str): Component name from electrical_components.json
                (resolved upstream, accepted and ignored here)

        Note: constants defaults to None but GROUNDING_RESISTANCE is read below
        on the zero-throttle path, so a constants dict is effectively mandatory.
        """
        self.load_name = kwargs.get("load_name")
        self.throttle = kwargs.get("throttle", 1.0)
        self.MOTOR_VOLTAGE = kwargs.get("nominal_voltage")
        self.MOTOR_TOTAL_POWER = kwargs.get("total_power")
        self.components = components
        self.constants = constants
        self.circuit = circuit
        
        # Use actual bus voltage if provided, otherwise fall back to nominal
        actual_bus_voltage = bus_voltage if bus_voltage is not None else self.MOTOR_VOLTAGE
        
        # Try to create motor physics model from config
        self.motor_model = create_motor_model_from_config(kwargs, actual_bus_voltage)
        
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