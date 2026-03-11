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
    I = (V_effective - V_emf) / R_winding + I_no_load
    P_electrical = V_bus x I
    τ_motor = Kt x (I - I_no_load)

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
        max_power: float = None
    ):
        """
        Initialize motor model.
        
        Args:
            motor: Motor electrical constants
            propeller: Propeller load constants (optional)
            bus_voltage: DC bus voltage (V)
            max_power: Maximum power rating for fallback linear model (W)
        """
        self.motor = motor
        self.propeller = propeller
        self.bus_voltage = bus_voltage
        self.max_power = max_power
        
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
        return MotorOperatingPoint(
            throttle=0.0,
            speed_rpm=0.0,
            speed_rad_s=0.0,
            current_amps=0.0,
            torque_nm=0.0,
            power_electrical_w=0.0,
            power_mechanical_w=0.0,
            efficiency=0.0,
            is_stalled=False
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
        kp = self.propeller.kp
        
        # Initial guess: no-load speed (back-EMF equals applied voltage)
        omega_no_load = v_effective / ke if ke > 0 else 0
        omega = omega_no_load * 0.8  # Start slightly below no-load
        
        # Newton-Raphson iteration
        for _ in range(self.MAX_ITERATIONS):
            # Motor current at this speed
            i_motor = (v_effective - ke * omega) / r
            
            # Check for stall (current limited by resistance only)
            if i_motor < i_nl:
                return self._stall_result(throttle, v_effective)
            
            # Motor torque (net torque producing acceleration)
            tau_motor = kt * (i_motor - i_nl)
            
            # Propeller torque
            tau_prop = kp * omega * omega
            
            # Residual (should be zero at equilibrium)
            f = tau_motor - tau_prop
            
            # Derivative of residual w.r.t. omega
            # d(tau_motor)/d(omega) = -Kt x Ke / R
            # d(tau_prop)/d(omega) = 2 x Kp x omega
            df = -kt * ke / r - 2 * kp * omega
            
            if abs(df) < 1e-12:
                break
                
            # Newton step
            omega_new = omega - f / df
            
            # Clamp to valid range
            omega_new = max(self.MIN_SPEED_RAD_S, min(omega_new, omega_no_load))
            
            if abs(omega_new - omega) < self.SPEED_TOLERANCE:
                omega = omega_new
                break
                
            omega = omega_new
        
        # Calculate final operating point
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
        # Estimate speed as fraction of no-load speed
        omega_no_load = v_effective / ke if ke > 0 else 0
        omega = omega_no_load * 0.95  # Slight load
        
        # Calculate current
        i_motor = (v_effective - ke * omega) / r + i_nl
        i_motor = max(0, i_motor)
        
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
        
        # Current calculation
        i_motor = (v_effective - ke * omega) / r
        i_motor = max(0, i_motor)
        
        # Include no-load current for total draw
        i_total = i_motor + i_nl
        
        # Torque (only from current above no-load)
        tau = kt * max(0, i_motor)
        
        # Power calculations
        p_elec = self.bus_voltage * i_total * throttle  # Actual power from bus
        p_elec = max(0, p_elec)
        
        p_mech = tau * omega
        p_mech = max(0, p_mech)
        
        # Efficiency
        efficiency = p_mech / p_elec if p_elec > 0 else 0.0
        efficiency = min(efficiency, 1.0)
        
        # Speed in RPM
        rpm = omega * 60.0 / (2.0 * math.pi)
        
        return MotorOperatingPoint(
            throttle=throttle,
            speed_rpm=rpm,
            speed_rad_s=omega,
            current_amps=i_total,
            torque_nm=tau,
            power_electrical_w=p_elec,
            power_mechanical_w=p_mech,
            efficiency=efficiency,
            is_stalled=False
        )
    
    def _stall_result(self, throttle: float, v_effective: float) -> MotorOperatingPoint:
        """Calculate operating point for stalled motor."""
        r = self.motor.resistance
        
        # Stall current (no back-EMF)
        i_stall = v_effective / r
        
        # Power is all dissipated as heat
        p_elec = self.bus_voltage * i_stall * throttle
        
        return MotorOperatingPoint(
            throttle=throttle,
            speed_rpm=0.0,
            speed_rad_s=0.0,
            current_amps=i_stall,
            torque_nm=self.motor.kt * i_stall,
            power_electrical_w=p_elec,
            power_mechanical_w=0.0,
            efficiency=0.0,
            is_stalled=True
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
        propeller_kp: Propeller load coefficient (optional)
    
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
    
    propeller = None
    if "propeller_kp" in motor_config:
        propeller = PropellerConstants(
            kp=motor_config["propeller_kp"]
        )
    
    max_power = motor_config.get("total_power")
    
    return MotorModel(
        motor=motor,
        propeller=propeller,
        bus_voltage=bus_voltage,
        max_power=max_power
    )
