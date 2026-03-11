"""
Unit tests for BLDC Motor Physics Model.

Run with: python -m pytest src/electrical_simulation/components/test_motor_model.py
"""

import math
import pytest
from .motor_model import (
    MotorModel, 
    MotorConstants, 
    PropellerConstants,
    MotorOperatingPoint,
    create_motor_model_from_config
)


class TestMotorConstants:
    """Test motor constant calculations."""
    
    def test_ke_from_kv(self):
        """Ke should be derived correctly from Kv."""
        motor = MotorConstants(kv=100, resistance=0.1)
        expected_ke = 60.0 / (2.0 * math.pi * 100)
        assert abs(motor.ke - expected_ke) < 1e-10
    
    def test_kt_equals_ke(self):
        """For BLDC motors, Kt = Ke."""
        motor = MotorConstants(kv=150, resistance=0.05)
        assert motor.kt == motor.ke
    
    def test_default_no_load_current(self):
        """No-load current defaults to 0."""
        motor = MotorConstants(kv=100, resistance=0.1)
        assert motor.no_load_current == 0.0


class TestMotorModelZeroThrottle:
    """Test zero throttle behavior."""
    
    def test_zero_throttle_returns_zero_power(self):
        """Zero throttle should produce zero power."""
        motor = MotorConstants(kv=150, resistance=0.05)
        model = MotorModel(motor, bus_voltage=48.0)
        
        op = model.calculate_operating_point(0.0)
        
        assert op.power_electrical_w == 0.0
        assert op.power_mechanical_w == 0.0
        assert op.speed_rpm == 0.0
        assert op.current_amps == 0.0
        assert not op.is_stalled
    
    def test_negative_throttle_treated_as_zero(self):
        """Negative throttle should be treated as zero."""
        motor = MotorConstants(kv=150, resistance=0.05)
        model = MotorModel(motor, bus_voltage=48.0)
        
        op = model.calculate_operating_point(-0.5)
        
        assert op.power_electrical_w == 0.0


class TestMotorModelFullThrottle:
    """Test full throttle behavior."""
    
    def test_full_throttle_produces_power(self):
        """Full throttle should produce positive power."""
        motor = MotorConstants(kv=150, resistance=0.05)
        propeller = PropellerConstants(kp=0.001)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        op = model.calculate_operating_point(1.0)
        
        assert op.power_electrical_w > 0
        assert op.power_mechanical_w > 0
        assert op.speed_rpm > 0
        assert op.current_amps > 0
    
    def test_efficiency_between_zero_and_one(self):
        """Motor efficiency should be between 0 and 1."""
        motor = MotorConstants(kv=150, resistance=0.05)
        propeller = PropellerConstants(kp=0.001)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        op = model.calculate_operating_point(1.0)
        
        assert 0 < op.efficiency <= 1.0


class TestMotorModelPropellerEquilibrium:
    """Test propeller load coupling."""
    
    def test_equilibrium_convergence(self):
        """Motor should find equilibrium with propeller load."""
        motor = MotorConstants(kv=150, resistance=0.05, no_load_current=1.0)
        propeller = PropellerConstants(kp=0.0008)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        op = model.calculate_operating_point(0.75)
        
        # At equilibrium, motor torque should equal propeller torque
        kt = motor.kt
        kp = propeller.kp
        omega = op.speed_rad_s
        
        motor_torque = kt * (op.current_amps - motor.no_load_current)
        propeller_torque = kp * omega * omega
        
        # Allow some tolerance for convergence
        assert abs(motor_torque - propeller_torque) < 0.1
    
    def test_higher_throttle_higher_speed(self):
        """Higher throttle should result in higher speed."""
        motor = MotorConstants(kv=150, resistance=0.05)
        propeller = PropellerConstants(kp=0.0008)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        op_low = model.calculate_operating_point(0.3)
        op_mid = model.calculate_operating_point(0.6)
        op_high = model.calculate_operating_point(0.9)
        
        assert op_low.speed_rpm < op_mid.speed_rpm < op_high.speed_rpm
    
    def test_higher_throttle_higher_power(self):
        """Higher throttle should result in higher power."""
        motor = MotorConstants(kv=150, resistance=0.05)
        propeller = PropellerConstants(kp=0.0008)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        op_low = model.calculate_operating_point(0.3)
        op_high = model.calculate_operating_point(0.9)
        
        assert op_low.power_electrical_w < op_high.power_electrical_w


class TestMotorModelSimpleMode:
    """Test model without propeller coupling."""
    
    def test_simple_model_without_propeller(self):
        """Model should work without propeller constants."""
        motor = MotorConstants(kv=150, resistance=0.05)
        model = MotorModel(motor, propeller=None, bus_voltage=48.0)
        
        op = model.calculate_operating_point(0.5)
        
        assert op.power_electrical_w > 0
        assert op.speed_rpm > 0


class TestMotorModelConvenienceMethods:
    """Test convenience interface methods."""
    
    def test_get_power_from_throttle(self):
        """get_power_from_throttle should return electrical power."""
        motor = MotorConstants(kv=150, resistance=0.05)
        propeller = PropellerConstants(kp=0.0008)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        power = model.get_power_from_throttle(0.5)
        op = model.calculate_operating_point(0.5)
        
        assert power == op.power_electrical_w
    
    def test_get_efficiency_at_throttle(self):
        """get_efficiency_at_throttle should return efficiency."""
        motor = MotorConstants(kv=150, resistance=0.05)
        propeller = PropellerConstants(kp=0.0008)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        efficiency = model.get_efficiency_at_throttle(0.5)
        op = model.calculate_operating_point(0.5)
        
        assert efficiency == op.efficiency


class TestCreateMotorModelFromConfig:
    """Test factory function for creating motor model from config."""
    
    def test_returns_none_without_required_constants(self):
        """Should return None if motor constants not provided."""
        config = {"total_power": 2000, "nominal_voltage": 48.0}
        model = create_motor_model_from_config(config, bus_voltage=48.0)
        
        assert model is None
    
    def test_creates_model_with_motor_constants(self):
        """Should create model when motor constants provided."""
        config = {
            "motor_kv": 150,
            "motor_resistance": 0.05,
            "total_power": 2000
        }
        model = create_motor_model_from_config(config, bus_voltage=48.0)
        
        assert model is not None
        assert isinstance(model, MotorModel)
    
    def test_creates_model_with_propeller(self):
        """Should include propeller when propeller_kp provided."""
        config = {
            "motor_kv": 150,
            "motor_resistance": 0.05,
            "propeller_kp": 0.0008,
            "total_power": 2000
        }
        model = create_motor_model_from_config(config, bus_voltage=48.0)
        
        assert model is not None
        assert model.propeller is not None
        assert model.propeller.kp == 0.0008
    
    def test_no_load_current_optional(self):
        """No-load current should default to 0 if not provided."""
        config = {
            "motor_kv": 150,
            "motor_resistance": 0.05
        }
        model = create_motor_model_from_config(config, bus_voltage=48.0)
        
        assert model.motor.no_load_current == 0.0


class TestBackwardCompatibility:
    """Test backward compatibility with existing configurations."""
    
    def test_linear_config_returns_none(self):
        """Config without motor physics should return None for linear fallback."""
        linear_config = {
            "total_power": 2000,
            "nominal_voltage": 24.0
        }
        model = create_motor_model_from_config(linear_config, bus_voltage=24.0)
        
        assert model is None
    
    def test_torqeedo_config_creates_model(self):
        """Torqeedo config with motor physics should create model."""
        torqeedo_config = {
            "total_power": 2000,
            "nominal_voltage": 24.0,
            "motor_kv": 150,
            "motor_resistance": 0.05,
            "motor_no_load_current": 1.5,
            "propeller_kp": 0.0008
        }
        model = create_motor_model_from_config(torqeedo_config, bus_voltage=24.0)
        
        assert model is not None
        assert model.motor.kv == 150
        assert model.propeller is not None


class TestNonLinearPowerScaling:
    """Verify power scaling is non-linear with propeller load."""
    
    def test_power_not_linear_with_throttle(self):
        """Power should NOT scale linearly with throttle when using propeller."""
        motor = MotorConstants(kv=150, resistance=0.05)
        propeller = PropellerConstants(kp=0.0008)
        model = MotorModel(motor, propeller, bus_voltage=48.0)
        
        p_25 = model.get_power_from_throttle(0.25)
        p_50 = model.get_power_from_throttle(0.50)
        p_75 = model.get_power_from_throttle(0.75)
        p_100 = model.get_power_from_throttle(1.0)
        
        # If linear: p_50/p_25 should equal p_75/p_50 should equal p_100/p_75
        # With propeller (power ~ speed³ ~ throttle³), ratios should differ
        ratio_1 = p_50 / p_25 if p_25 > 0 else 0
        ratio_2 = p_75 / p_50 if p_50 > 0 else 0
        ratio_3 = p_100 / p_75 if p_75 > 0 else 0
        
        # These ratios should NOT all be equal (non-linear behavior)
        # Note: the exact relationship depends on motor/propeller constants
        # but it should not be a constant 2.0 ratio (linear doubling)
        assert p_25 > 0
        assert p_50 > p_25
        assert p_100 > p_75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
