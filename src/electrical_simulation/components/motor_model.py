"""
BLDC Motor Physics Model with Optional Propeller Load Coupling

This module calculates realistic power consumption from throttle input by solving
the motor-propeller equilibrium equations. The model accounts for:
- Back-EMF (speed-dependent voltage opposing current)
- Winding resistance losses
- No-load current (friction, windage)
- Propeller load curve (torque ∝ ω²)

Motor Equations:
    V_effective = throttle x V_bus
    V_emf = Ke x ω (back-EMF)
    I = (V_effective - V_emf) / R_winding
    τ_motor = Kt x (I - I_no_load)
    V_motor = Ke x ω + I x R  (actual terminal voltage)
    P_electrical = V_motor x I

Propeller Equilibrium:
    τ_propeller = Kp x ω²
    At equilibrium: τ_motor = τ_propeller
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class MotorConstants:
    """BLDC motor electrical and mechanical constants."""
    kv: float  # Motor velocity constant (RPM/V)
    resistance: float  # Winding resistance (ohms)
    no_load_current: float = 0.0  # No-load current (amps)
    
    @property
    def ke(self) -> float:
        """Back-EMF constant (V/(rad/s)), derived from Kv."""
        return 60.0 / (2.0 * math.pi * self.kv)
    
    @property
    def kt(self) -> float:
        """Torque constant (N·m/A), equals Ke for BLDC motors."""
        return self.ke


@dataclass
class PropellerConstants:
    """Propeller load curve constants."""
    kp: float  # Load coefficient (N·m/(rad/s)²)
    load_factor: float = 1.0  # 1.0 = startup/bollard, <1.0 = cruise equilibrium
    
    @property
    def effective_kp(self) -> float:
        """Kp scaled by load_factor to model reduced load at cruise speed."""
        return self.kp * self.load_factor


@dataclass
class MotorOperatingPoint:
    """Results from motor equilibrium calculation."""
    throttle: float  # Input throttle [0, 1]
    speed_rpm: float  # Motor speed (RPM)
    speed_rad_s: float  # Motor speed (rad/s)
    current_amps: float  # Motor current draw (A)
    torque_nm: float  # Motor torque (N·m)
    power_electrical_w: float  # Electrical power consumption (W)
    power_mechanical_w: float  # Mechanical power output (W)
    efficiency: float  # Motor efficiency (0-1)
    is_stalled: bool  # True if motor is in stall condition
    is_current_limited: bool = False  # True if ESC is limiting winding current
    propeller_load_factor: float = 1.0  # Load factor used (1.0=startup, <1.0=cruise)
    

class MotorModel:
    """
    BLDC motor model with optional propeller load coupling.
    
    Calculates power consumption from throttle by solving for the equilibrium
    operating point where motor torque equals propeller load torque.
    """
    
    SPEED_TOLERANCE = 1e-6  # rad/s convergence tolerance
    MAX_ITERATIONS = 100
    MIN_SPEED_RAD_S = 0.01  # Minimum speed to avoid division by zero
    
    def __init__(
        self,
        motor: MotorConstants,
        propeller: Optional[PropellerConstants] = None,
        bus_voltage: float = 48.0,
        max_power: float = None,
        max_current: float = None
    ):
        """
        Initialize motor model.
        
        Args:
            motor: Motor electrical constants
            propeller: Propeller load constants (optional)
            bus_voltage: DC bus voltage (V)
            max_power: Maximum power rating for fallback linear model (W)
            max_current: ESC winding current limit (A), typically total_power/nominal_voltage
        """
        self.motor = motor
        self.propeller = propeller
        self.bus_voltage = bus_voltage
        self.max_power = max_power
        self.max_current = max_current
        
    def calculate_operating_point(self, throttle: float) -> MotorOperatingPoint:
        """
        Calculate motor operating point for given throttle.
        
        For propeller-coupled motors, solves equilibrium equation.
        For uncoupled motors, uses simplified model.
        
        Args:
            throttle: Throttle position [0, 1]
            
        Returns:
            MotorOperatingPoint with all calculated values
        """
        if throttle <= 0.0:
            return self._zero_throttle_result()
        
        throttle = min(throttle, 1.0)  # Clamp to valid range
        
        if self.propeller:
            return self._solve_propeller_equilibrium(throttle)
        else:
            return self._solve_simple_model(throttle)
    
    def _zero_throttle_result(self) -> MotorOperatingPoint:
        """Return operating point for zero throttle."""
        load_factor = self.propeller.load_factor if self.propeller else 1.0
        return MotorOperatingPoint(
            throttle=0.0,
            speed_rpm=0.0,
            speed_rad_s=0.0,
            current_amps=0.0,
            torque_nm=0.0,
            power_electrical_w=0.0,
            power_mechanical_w=0.0,
            efficiency=0.0,
            is_stalled=False,
            propeller_load_factor=load_factor
        )
    
    def _solve_propeller_equilibrium(self, throttle: float) -> MotorOperatingPoint:
        """
        Solve for equilibrium speed where motor torque = propeller torque.
        
        Motor torque: τ_m = Kt x (I - I_nl)
        Motor current: I = (V_eff - Kexω) / R
        Propeller torque: τ_p = Kp x ω²
        
        At equilibrium: Kt x ((V_eff - Kexω)/R - I_nl) = Kp x ω²
        
        Rearranging: Kpxω² + (KtxKe/R)xω + KtxI_nl - KtxV_eff/R = 0
        
        This is a quadratic in ω, but we use Newton-Raphson for robustness.
        """
        v_effective = throttle * self.bus_voltage
        kt = self.motor.kt
        ke = self.motor.ke
        r = self.motor.resistance
        i_nl = self.motor.no_load_current
        kp = self.propeller.effective_kp
        
        # Initial guess: no-load speed (back-EMF equals applied voltage)
        omega_no_load = v_effective / ke if ke > 0 else 0
        omega = omega_no_load * 0.8  # Start slightly below no-load
        
        # Phase 1: Solve unconstrained equilibrium via Newton-Raphson
        for _ in range(self.MAX_ITERATIONS):
            i_motor = (v_effective - ke * omega) / r
            
            if i_motor < i_nl:
                return self._stall_result(throttle, v_effective)
            
            tau_motor = kt * (i_motor - i_nl)
            tau_prop = kp * omega * omega
            f = tau_motor - tau_prop
            
            # d(tau_motor)/d(omega) = -Kt x Ke / R
            # d(tau_prop)/d(omega) = 2 x Kp x omega
            df = -kt * ke / r - 2 * kp * omega
            
            if abs(df) < 1e-12:
                break
                
            omega_new = omega - f / df
            omega_new = max(self.MIN_SPEED_RAD_S, min(omega_new, omega_no_load))
            
            if abs(omega_new - omega) < self.SPEED_TOLERANCE:
                omega = omega_new
                break
                
            omega = omega_new
        
        # Phase 2: Check if equilibrium current exceeds ESC limit
        i_eq = (v_effective - ke * omega) / r
        if self.max_current is not None and i_eq > self.max_current:
            # Solve current-limited case analytically:
            # tau = kt * (I_max - I_nl) = constant, tau = kp * omega^2
            tau_limited = kt * (self.max_current - i_nl)
            if tau_limited > 0 and kp > 0:
                omega = math.sqrt(tau_limited / kp)
            else:
                return self._stall_result(throttle, v_effective)
        
        return self._calculate_result(throttle, omega, v_effective)
    
    def _solve_simple_model(self, throttle: float) -> MotorOperatingPoint:
        """
        Simplified model without propeller coupling.
        
        Assumes motor runs at a speed proportional to throttle (like no-load),
        but with some efficiency loss. Power scales with throttle.
        """
        v_effective = throttle * self.bus_voltage
        ke = self.motor.ke
        r = self.motor.resistance
        i_nl = self.motor.no_load_current
        
        # Assume motor runs near no-load speed with small load
        omega_no_load = v_effective / ke if ke > 0 else 0
        omega = omega_no_load * 0.95  # Slight load
        
        return self._calculate_result(throttle, omega, v_effective)
    
    def _calculate_result(
        self, 
        throttle: float, 
        omega: float, 
        v_effective: float
    ) -> MotorOperatingPoint:
        """Calculate full operating point from speed."""
        ke = self.motor.ke
        kt = self.motor.kt
        r = self.motor.resistance
        i_nl = self.motor.no_load_current
        
        # Winding current (this IS the total motor current, includes no-load contribution)
        i_motor = (v_effective - ke * omega) / r
        i_motor = max(0, i_motor)
        
        # Apply ESC current limiting
        is_limited = False
        if self.max_current is not None and i_motor > self.max_current:
            i_motor = self.max_current
            is_limited = True
        
        # Net torque (only current above no-load produces useful torque)
        tau = kt * max(0, i_motor - i_nl)
        
        # Motor terminal voltage (may be less than v_effective when current-limited)
        v_motor = ke * omega + i_motor * r
        
        # Power = motor terminal voltage x current
        p_elec = v_motor * i_motor
        p_elec = max(0, p_elec)
        
        p_mech = tau * omega
        p_mech = max(0, p_mech)
        
        # Efficiency
        efficiency = p_mech / p_elec if p_elec > 0 else 0.0
        efficiency = min(efficiency, 1.0)
        
        # Speed in RPM
        rpm = omega * 60.0 / (2.0 * math.pi)
        
        load_factor = self.propeller.load_factor if self.propeller else 1.0
        
        return MotorOperatingPoint(
            throttle=throttle,
            speed_rpm=rpm,
            speed_rad_s=omega,
            current_amps=i_motor,
            torque_nm=tau,
            power_electrical_w=p_elec,
            power_mechanical_w=p_mech,
            efficiency=efficiency,
            is_stalled=False,
            is_current_limited=is_limited,
            propeller_load_factor=load_factor
        )
    
    def _stall_result(self, throttle: float, v_effective: float) -> MotorOperatingPoint:
        """Calculate operating point for stalled motor."""
        r = self.motor.resistance
        
        # Stall current (no back-EMF)
        i_stall = v_effective / r
        
        # Apply ESC current limiting
        is_limited = False
        if self.max_current is not None and i_stall > self.max_current:
            i_stall = self.max_current
            is_limited = True
        
        # At stall: all power is I^2R heat, terminal voltage = I*R
        p_elec = i_stall * i_stall * r
        
        load_factor = self.propeller.load_factor if self.propeller else 1.0
        
        return MotorOperatingPoint(
            throttle=throttle,
            speed_rpm=0.0,
            speed_rad_s=0.0,
            current_amps=i_stall,
            torque_nm=self.motor.kt * i_stall,
            power_electrical_w=p_elec,
            power_mechanical_w=0.0,
            efficiency=0.0,
            is_stalled=True,
            is_current_limited=is_limited,
            propeller_load_factor=load_factor
        )
    
    def get_power_from_throttle(self, throttle: float) -> float:
        """
        Convenience method to get electrical power consumption from throttle.
        
        This is the main interface for integration with the Load class.
        
        Args:
            throttle: Throttle position [0, 1]
            
        Returns:
            Electrical power consumption in watts
        """
        op = self.calculate_operating_point(throttle)
        return op.power_electrical_w
    
    def get_efficiency_at_throttle(self, throttle: float) -> float:
        """Get motor efficiency at given throttle."""
        op = self.calculate_operating_point(throttle)
        return op.efficiency


def derive_propeller_kp(kv, resistance, no_load_current, total_power, nominal_voltage):
    """
    Derive propeller load coefficient from motor specs.
    
    Calculates kp such that the motor reaches rated current at full throttle,
    ensuring the propeller is matched to the motor's rated operating point.
    """
    ke = 60.0 / (2.0 * math.pi * kv)
    kt = ke
    i_max = total_power / nominal_voltage
    omega_rated = (nominal_voltage - i_max * resistance) / ke
    
    if omega_rated <= 0:
        return 1e-6  # Fallback for invalid parameters
    
    tau_rated = kt * (i_max - no_load_current)
    return tau_rated / (omega_rated * omega_rated)


def create_motor_model_from_config(
    motor_config: dict,
    bus_voltage: float
) -> Optional[MotorModel]:
    """
    Factory function to create MotorModel from configuration dict.
    
    Expected config keys:
        motor_kv: Motor Kv rating (RPM/V)
        motor_resistance: Winding resistance (ohms)
        motor_no_load_current: No-load current (amps, optional)
        propeller_kp: Propeller load coefficient (optional, auto-derived if omitted)
        total_power: Motor rated power (W)
        nominal_voltage: Motor nominal voltage (V)
    
    If propeller_kp is not provided but total_power and nominal_voltage are,
    kp is auto-derived so the motor reaches rated current at full throttle.
    
    Returns None if motor physics constants are not provided,
    allowing fallback to linear model.
    """
    # Check for required motor constants
    if "motor_kv" not in motor_config or "motor_resistance" not in motor_config:
        return None
    
    motor = MotorConstants(
        kv=motor_config["motor_kv"],
        resistance=motor_config["motor_resistance"],
        no_load_current=motor_config.get("motor_no_load_current", 0.0)
    )
    
    max_power = motor_config.get("total_power")
    nominal_voltage = motor_config.get("nominal_voltage")
    
    # Derive ESC current limit from motor ratings
    max_current = None
    if max_power and nominal_voltage:
        max_current = max_power / nominal_voltage
    
    propeller = None
    if "propeller_kp" in motor_config:
        # Explicit kp override
        propeller = PropellerConstants(
            kp=motor_config["propeller_kp"],
            load_factor=motor_config.get("propeller_load_factor", 1.0)
        )
    elif max_power and nominal_voltage:
        # Auto-derive kp from motor specs
        # derive_propeller_kp returns the effective kp needed for rated operation.
        # Divide by load_factor so that effective_kp = (kp/lf) * lf = kp_rated
        load_factor = motor_config.get("propeller_load_factor", 1.0)
        kp_rated = derive_propeller_kp(
            kv=motor_config["motor_kv"],
            resistance=motor_config["motor_resistance"],
            no_load_current=motor_config.get("motor_no_load_current", 0.0),
            total_power=max_power,
            nominal_voltage=nominal_voltage
        )
        kp_base = kp_rated / load_factor if load_factor > 0 else kp_rated
        propeller = PropellerConstants(
            kp=kp_base,
            load_factor=load_factor
        )
    
    return MotorModel(
        motor=motor,
        propeller=propeller,
        bus_voltage=bus_voltage,
        max_power=max_power,
        max_current=max_current
    )
