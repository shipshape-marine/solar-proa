"""Unit tests for result validation and cross-checking (spec Task 4).

Covers ``cross_check_result``: the Kirchhoff current-law check on the summary
currents, the MPPT output-limit / battery-overcharge / battery-over-discharge
warnings, and the ``motor_physics`` block attached to each load result for both
the BLDC and the linear motor model.

No NgSpice and no circuit: every test feeds ``cross_check_result`` a synthetic
result dict shaped exactly like the one ``pyspice_simulator.__simulate__``
creates and ``parse_result`` fills in, plus fake component handles exposing only
the methods the checker calls (``get_output_limit``, ``get_efficiency``,
``power_rating``, ``throttle_setting``, ``get_motor_operating_point``). All
``src`` imports happen inside helpers so collection stays green when the
simulation dependencies are unavailable.

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2
"""

import pytest


# ---------------------------------------------------------------------------
# helpers — synthetic result dicts and fake component handles
# ---------------------------------------------------------------------------


def _cross_check(component_object: dict, result: dict, constants: dict) -> dict:
    """Run the checker over a synthetic result and return the same dict."""
    from src.electrical_simulation.result_checker import cross_check_result

    # `analysis` is only tested for None by the checker, never dereferenced.
    cross_check_result(object(), component_object, result, constants=constants)
    return result


def _entry(index: int = 0, voltage: dict = None, current: dict = None) -> dict:
    """One parsed data entry, matching the `struc` template in pyspice_simulator."""
    return {
        "array_index": index,
        "voltage": dict(voltage or {}),
        "current": dict(current or {}),
    }


def _section(keyword: str, data: list = None) -> dict:
    """One result section with its array_count kept consistent with its data."""
    data = list(data or [])
    return {"keyword": keyword, "array_count": len(data), "data": data}


def _make_result(
    *,
    total_mppt_output: float = 0.0,
    total_battery_input: float = 0.0,
    mppt_data: list = None,
    solar_data: list = None,
    load_data: list = None,
    balancing_load: float = 0.0,
) -> dict:
    """Build a result dict in the shape produced by a parsed simulation.

    Only the sections ``cross_check_result`` reads are populated; the rest are
    present and empty so the dict keeps the production key set.
    """
    return {
        "info": _section("info"),
        "error": _section("error"),
        "warning": _section("warning"),
        "summary": _section(
            "total",
            [
                _entry(
                    current={
                        "total_mppt_output_current": total_mppt_output,
                        "total_battery_input_current": total_battery_input,
                    }
                )
            ],
        ),
        "mppt_result": _section("mppt", mppt_data),
        "battery_result": _section("battery"),
        "solar_result": _section("solar_array", solar_data),
        "panel_result": _section("panel"),
        # The checker indexes data[0] unconditionally, so a balancer entry
        # always exists in a real result.
        "load_balancer": _section(
            "balancing_load", [_entry(current={"balancing_load": balancing_load})]
        ),
        "load_result": _section("load", load_data),
        "l_array_result": _section("l_array"),
    }


def _mppt_entry(index: int = 0, voltage: float = 24.0, current: float = 0.0) -> dict:
    """MPPT output node/branch entry for array `index`."""
    return _entry(
        index, voltage={"mppt_output": voltage}, current={"mppt_output": current}
    )


def _solar_entry(index: int = 0, voltage: float = 20.0, current: float = 0.0) -> dict:
    """Solar array output node/branch entry for array `index`."""
    return _entry(
        index,
        voltage={"solar_array_output": voltage},
        current={"solar_array_output": current},
    )


def _load_entry(index: int = 0, voltage: float = 48.0, current: float = 0.0) -> dict:
    """Load entry; the checker reads the first voltage and first current value."""
    return _entry(
        index,
        voltage={f"load{index}_positive": voltage},
        current={f"load{index}_current": current},
    )


class _FakeMPPT:
    """MPPT handle exposing just the two accessors the checker uses."""

    def __init__(self, output_limit: float = 20.0, efficiency: float = 0.9):
        self._output_limit = output_limit
        self._efficiency = efficiency

    def get_output_limit(self):
        return self._output_limit

    def get_efficiency(self):
        return self._efficiency


class _FakeLoad:
    """Load handle exposing the three accessors the checker uses."""

    def __init__(self, total_power: float, throttle: float, motor_op=None):
        self._total_power = total_power
        self._throttle = throttle
        self._motor_op = motor_op

    def power_rating(self):
        return self._total_power

    def throttle_setting(self):
        return self._throttle

    def get_motor_operating_point(self):
        return self._motor_op


def _operating_point(**overrides):
    """A real MotorOperatingPoint so field names stay in sync with the model."""
    from src.electrical_simulation.components.motor_model import MotorOperatingPoint

    values = {
        "throttle": 0.8,
        "speed_rpm": 1500.0,
        "speed_rad_s": 157.08,
        "current_amps": 8.3,
        "torque_nm": 2.1,
        "power_electrical_w": 400.0,
        "power_mechanical_w": 340.0,
        "efficiency": 0.85,
        "is_stalled": False,
        "is_current_limited": False,
        "propeller_load_factor": 0.6,
    }
    values.update(overrides)
    return MotorOperatingPoint(**values)


# ---------------------------------------------------------------------------
# Requirements 4.1, 4.2 — Kirchhoff's current law
# ---------------------------------------------------------------------------


def test_kcl_balanced_no_error(constants):
    """Verify no KCL error when MPPT output equals battery input plus load current."""
    result = _make_result(
        total_mppt_output=10.0,
        total_battery_input=4.0,
        mppt_data=[_mppt_entry(current=10.0)],
        load_data=[_load_entry(current=5.0)],
        balancing_load=1.0,
    )
    component_object = {
        "mppt": [_FakeMPPT()],
        "load": [_FakeLoad(total_power=500, throttle=0.5)],
    }

    _cross_check(component_object, result, constants)

    # 10 A out = 4 A into the battery + 5 A load + 1 A balancer.
    assert result["error"]["data"] == []
    assert result["error"]["array_count"] == 0


def test_kcl_violated_generates_error(constants):
    """Verify KCL violation generates error when currents don't sum to zero."""
    result = _make_result(
        total_mppt_output=10.0,
        total_battery_input=1.0,
        mppt_data=[_mppt_entry(current=10.0)],
        load_data=[_load_entry(current=2.0)],
    )
    component_object = {
        "mppt": [_FakeMPPT()],
        "load": [_FakeLoad(total_power=500, throttle=0.5)],
    }

    _cross_check(component_object, result, constants)

    assert result["error"]["array_count"] == 1
    message = result["error"]["data"][0]
    assert "Kirchhoff's Law violated" in message
    # The reported values are the three terms of the imbalance: 10 - 1 - 2 = 7 A.
    assert "10.0 A" in message
    assert "1.0 A" in message
    assert "2.0 A" in message


@pytest.mark.xfail(
    reason=(
        "Implementation gap in cross_check_result: the KCL test is one-sided "
        "(`total_mppt_output - total_battery_input - total_load_current > EPSILON`), "
        "so an imbalance of the opposite sign — more current leaving the bus than "
        "entering it — is never reported even though Req 4.1 asks for equality "
        "within EPSILON. An `abs(...)` comparison would catch it. Not fixed here: "
        "Task 4 may not change src/."
    ),
)
def test_kcl_negative_imbalance_generates_error(constants):
    """Verify a negative KCL imbalance is also reported as an error."""
    result = _make_result(
        total_mppt_output=2.0,
        total_battery_input=1.0,
        mppt_data=[_mppt_entry(current=2.0)],
        load_data=[_load_entry(current=9.0)],
    )
    component_object = {
        "mppt": [_FakeMPPT()],
        "load": [_FakeLoad(total_power=500, throttle=0.5)],
    }

    _cross_check(component_object, result, constants)

    # 2 - 1 - 9 = -8 A: as far off balance as the positive case above.
    assert result["error"]["array_count"] == 1


# ---------------------------------------------------------------------------
# Requirement 4.3 — MPPT output current limit
# ---------------------------------------------------------------------------


def test_excess_power_warning_at_mppt_output_limit(constants):
    """Verify excess-power warning when MPPT output current reaches its output limit."""
    component_object = {"mppt": [_FakeMPPT(output_limit=10.0, efficiency=0.9)], "load": []}

    def check(mppt_current: float) -> list:
        result = _make_result(
            total_mppt_output=mppt_current,
            total_battery_input=mppt_current,
            mppt_data=[_mppt_entry(voltage=24.0, current=mppt_current)],
            solar_data=[_solar_entry(voltage=20.0, current=15.0)],
        )
        return _cross_check(component_object, result, constants)["warning"]["data"]

    # Comfortably below the limit: nothing to report.
    assert check(6.0) == []

    # Exactly at the limit.
    warnings = check(10.0)
    assert len(warnings) == 1
    assert "(Array 0) Excess power input into MPPT" in warnings[0]
    assert "10.0 A output limit" in warnings[0]
    assert "Total Input Power: 270.00 W" in warnings[0], "20 V x 15 A x 0.9"
    assert "restricted to: 240.00 W" in warnings[0], "24 V x 10 A"

    # Over the limit warns as well.
    assert len(check(11.0)) == 1


# ---------------------------------------------------------------------------
# Requirement 4.4 — battery overcharge
# ---------------------------------------------------------------------------


def test_overcharge_warning_when_balancer_active(constants):
    """Verify overcharge warning when load_balancer carries positive current."""
    component_object = {"mppt": [_FakeMPPT()], "load": []}

    def check(balancing_load: float) -> list:
        result = _make_result(
            total_mppt_output=10.0,
            total_battery_input=10.0 - balancing_load,
            mppt_data=[_mppt_entry(current=10.0)],
            balancing_load=balancing_load,
        )
        return _cross_check(component_object, result, constants)["warning"]["data"]

    # Balancer idle (and the small negative leakage a real solve produces).
    assert check(0.0) == []
    assert check(-1e-9) == []

    warnings = check(3.0)
    assert len(warnings) == 1
    assert warnings[0] == "Battery is overcharged by 3.0 A"


# ---------------------------------------------------------------------------
# Requirement 4.5 — battery over-discharge
# ---------------------------------------------------------------------------


def test_overdischarge_warning_on_power_mismatch(constants):
    """Verify over-discharge warning when load receives less power than expected."""
    # Linear load: expected power is power_rating x average MPPT efficiency x throttle
    # = 500 W x 0.9 x 0.5 = 225 W. Delivering 150 W (48 V x 3.125 A) puts the
    # achieved throttle at 33.33%, far outside POWER_MISMATCH_TOLERANCE_PERCENTAGE.
    result = _make_result(
        total_mppt_output=0.0,
        total_battery_input=-3.125,
        mppt_data=[_mppt_entry(current=0.0)],
        load_data=[_load_entry(voltage=48.0, current=3.125)],
    )
    component_object = {
        "mppt": [_FakeMPPT(efficiency=0.9)],
        "load": [_FakeLoad(total_power=500, throttle=0.5)],
    }

    _cross_check(component_object, result, constants)

    assert result["error"]["data"] == [], "the synthetic currents are KCL-balanced"
    warnings = result["warning"]["data"]
    assert len(warnings) == 1
    assert "Battery array is being over-discharged" in warnings[0]
    assert "Motor 0" in warnings[0]
    assert "33.33%" in warnings[0], "150 W of the 450 W effective rating"
    assert "50.00% throttle" in warnings[0]


def test_overdischarge_not_warned_when_power_matches(constants):
    """Verify no over-discharge warning when delivered power matches the throttle."""
    # 48 V x 4.6875 A = 225 W, exactly the expected 500 W x 0.9 x 0.5.
    result = _make_result(
        total_mppt_output=0.0,
        total_battery_input=-4.6875,
        mppt_data=[_mppt_entry(current=0.0)],
        load_data=[_load_entry(voltage=48.0, current=4.6875)],
    )
    component_object = {
        "mppt": [_FakeMPPT(efficiency=0.9)],
        "load": [_FakeLoad(total_power=500, throttle=0.5)],
    }

    _cross_check(component_object, result, constants)

    assert result["warning"]["data"] == []


# ---------------------------------------------------------------------------
# Requirements 4.6, 4.7, 5.1, 5.2 — motor_physics attachment
# ---------------------------------------------------------------------------


def test_motor_physics_attached_for_bldc(constants):
    """Verify BLDC motor_physics dict attached to load result when motor model exists."""
    motor_op = _operating_point()
    # 48 V x 8.3 A = 398.4 W against the model's 400 W: inside tolerance, so the
    # over-discharge branch stays quiet and only the info message is emitted.
    result = _make_result(
        total_mppt_output=0.0,
        total_battery_input=-8.3,
        mppt_data=[_mppt_entry(current=0.0)],
        load_data=[_load_entry(voltage=48.0, current=8.3)],
    )
    component_object = {
        "mppt": [_FakeMPPT(efficiency=0.9)],
        "load": [_FakeLoad(total_power=500, throttle=0.8, motor_op=motor_op)],
    }

    _cross_check(component_object, result, constants)

    physics = result["load_result"]["data"][0]["motor_physics"]
    assert physics == {
        "model_type": "BLDC",
        "speed_rpm": 1500.0,
        "efficiency": 0.85,
        "power_mechanical_w": 340.0,
        "power_electrical_w": 400.0,
        "torque_nm": 2.1,
        "is_stalled": False,
        "is_current_limited": False,
        "propeller_load_factor": 0.6,
    }
    assert result["warning"]["data"] == []
    assert result["info"]["array_count"] == 1
    info = result["info"]["data"][0]
    assert "Motor 0: Using BLDC physics model" in info
    assert "1500 RPM" in info
    assert "85.0% efficiency" in info
    assert "340.0W mechanical output" in info


def test_linear_model_fallback_attached(constants):
    """Verify linear model motor_physics attached when no motor model."""
    result = _make_result(
        total_mppt_output=0.0,
        total_battery_input=-4.6875,
        mppt_data=[_mppt_entry(current=0.0)],
        load_data=[_load_entry(voltage=48.0, current=4.6875)],
    )
    component_object = {
        "mppt": [_FakeMPPT(efficiency=0.9)],
        "load": [_FakeLoad(total_power=500, throttle=0.5)],
    }

    _cross_check(component_object, result, constants)

    physics = result["load_result"]["data"][0]["motor_physics"]
    assert physics["model_type"] == "linear"
    # Every physics field is null except the measured electrical power
    # (48 V x 4.6875 A). Note the linear block carries no is_current_limited or
    # propeller_load_factor keys, unlike the BLDC block.
    assert physics["power_electrical_w"] == pytest.approx(225.0)
    assert physics["speed_rpm"] is None
    assert physics["efficiency"] is None
    assert physics["power_mechanical_w"] is None
    assert physics["torque_nm"] is None
    assert physics["is_stalled"] is None
    # No BLDC info message for a linear load.
    assert result["info"]["data"] == []


def test_motor_physics_per_load_by_array_index(constants):
    """Verify each load result gets the motor_physics of its own array_index."""
    # Bus current is shared, so keep both loads modest and KCL-balanced.
    result = _make_result(
        total_mppt_output=0.0,
        total_battery_input=-(8.3 + 4.6875),
        mppt_data=[_mppt_entry(current=0.0)],
        load_data=[
            _load_entry(index=0, voltage=48.0, current=8.3),
            _load_entry(index=1, voltage=48.0, current=4.6875),
        ],
    )
    component_object = {
        "mppt": [_FakeMPPT(efficiency=0.9)],
        "load": [
            _FakeLoad(total_power=500, throttle=0.8, motor_op=_operating_point()),
            _FakeLoad(total_power=500, throttle=0.5),
        ],
    }

    _cross_check(component_object, result, constants)

    loads = result["load_result"]["data"]
    assert loads[0]["motor_physics"]["model_type"] == "BLDC"
    assert loads[1]["motor_physics"]["model_type"] == "linear"
    assert result["warning"]["data"] == []
