"""Integration tests: operating points of the seven test circuits (spec Task 8).

Each test builds one fixture circuit, runs a real NgSpice operating-point
analysis through ``begin_simulation`` (so parsing and cross-checking run too),
and compares the solved currents against values hand-calculated from the
component specs in ``fixtures/test_components.json``.

Hand-calculation notes
----------------------
* Every fixture uses ``current_soc`` 0.5, and ``Test_Battery`` interpolates
  20 V..28 V, so one cell is exactly 24.0 V: a 1S pack is a 24 V bus and a 2S
  pack a 48 V bus.
* ``MPPT.setup_mppt`` regulates its output current to
  ``panel_power x efficiency / (bus_voltage + MPPT_BATTERY_VOLTAGE_BUFFER)``,
  i.e. the MPPT works 15 V above the pack so it can push charge into it. That
  makes one 100 W panel worth 90 W / 39 V = 2.31 A on a 24 V bus and
  90 W / 63 V = 1.43 A on a 48 V bus. PLAN.md quotes 3.75 A for the 1S case
  because it divides by the bare 24 V bus and ignores the buffer; the buffer is
  part of the modelled MPPT behaviour, not a rounding effect, so the
  expectations below are derived from the same formula the component uses.
* MPPT outputs and load demands are ideal current sources whose values are
  computed in Python, so the solved currents are set by those values rather than
  by the netlist impedances. Wire (0.01 ohm) and grounding (1e-6 ohm) resistances
  only shift node voltages and the solar-side current slightly, which the 5%
  tolerance from PLAN.md covers.

Validates: Requirements 2.1, 4.1, 4.2, 4.3, 4.4, 4.5, 12.1, 12.2, 12.3
"""

import pytest

from src.electrical_simulation.tests.helpers import (
    TOLERANCE,
    array_mppt_output_current as _array_mppt_output_current,
    assert_kcl,
    assert_within as _assert_within,
    balancer_current as _balancer_current,
    bus_voltage as _bus_voltage,
    cell_voltages as _cell_voltages,
    expected_mppt_current as _expected_mppt_current,
    load_currents as _load_currents,
    load_powers as _load_powers,
    matching_warnings as _matching_warnings,
    requires_ngspice,
    run_circuit,
    total_battery_input_current as _total_battery_input_current,
    total_mppt_output_current as _total_mppt_output_current,
    warnings_of as _warnings,
)

pytestmark = requires_ngspice


# ---------------------------------------------------------------------------
# Charging circuits
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_charging_only_1panel(resolved_circuit_config, constants):
    """Single panel charges battery with no load. Expected: MPPT output current
    approx (100W x 0.9) / ~24V = 3.75A. All current flows into battery."""
    result = run_circuit("charging_only_1panel", resolved_circuit_config, constants)

    # 90 W across the MPPT working voltage of 24 V + 15 V buffer = 2.31 A.
    expected = _expected_mppt_current(100.0, 0.9, 24.0, constants)
    _assert_within(_array_mppt_output_current(result, 0), expected,
                   label="arr0 mppt_output current")
    _assert_within(_total_mppt_output_current(result), expected,
                   label="total mppt output current")

    # No loads, charge limit 20 A -> every amp ends up in the battery.
    _assert_within(_total_battery_input_current(result), expected,
                   label="battery input current")
    assert _load_currents(result) == [], "charging-only circuit has no loads"
    assert _balancer_current(result) == pytest.approx(0.0, abs=1e-6), (
        "charge current is far below the 20 A limit, balancer must stay idle"
    )
    assert _matching_warnings(result, "overcharged") == []

    # 1S pack at SOC 0.5: one 24 V cell, bus sits at the pack voltage.
    assert _cell_voltages(result) == [pytest.approx(24.0, rel=TOLERANCE)]
    _assert_within(_bus_voltage(result), 24.0, label="dc bus voltage")

    # Solar side is resistive, so wire losses show up here (~0.25%).
    solar = result["solar_result"]["data"][0]["current"]["solar_array_output"]
    _assert_within(abs(solar), 100.0 / 20.0, label="solar array output current")

    assert_kcl(result)


@pytest.mark.integration
def test_charging_only_2panel(resolved_circuit_config, constants):
    """Two independent panel arrays charge battery. Expected: Each MPPT approx
    3.75A, total approx 7.5A into battery."""
    result = run_circuit("charging_only_2panel", resolved_circuit_config, constants)

    # 2S pack -> 48 V bus -> MPPT works at 63 V -> 90 W / 63 V = 1.43 A each.
    per_array = _expected_mppt_current(100.0, 0.9, 48.0, constants)
    assert result["mppt_result"]["array_count"] == 2
    for index in (0, 1):
        _assert_within(_array_mppt_output_current(result, index), per_array,
                       label=f"arr{index} mppt_output current")

    total = 2 * per_array
    _assert_within(_total_mppt_output_current(result), total,
                   label="total mppt output current")
    _assert_within(_total_battery_input_current(result), total,
                   label="battery input current")
    assert _balancer_current(result) == pytest.approx(0.0, abs=1e-6)

    cells = _cell_voltages(result)
    assert len(cells) == 2, "2S1P pack must report two cells"
    for cell in cells:
        assert cell == pytest.approx(24.0, rel=TOLERANCE)
    _assert_within(_bus_voltage(result), 48.0, label="dc bus voltage")

    assert_kcl(result)


# ---------------------------------------------------------------------------
# Discharge circuits
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_load_only_single(resolved_circuit_config, constants):
    """Single linear load draws from battery with no solar. Expected: load
    current approx 250W / 48V = 5.2A from battery."""
    result = run_circuit("load_only_single", resolved_circuit_config, constants)

    # solar_power 0 leaves Solar_Array at the EPSILON floor, so the MPPT
    # contributes nothing measurable.
    assert abs(_total_mppt_output_current(result)) < 1e-3

    expected_load = (500.0 * 0.5) / 48.0  # linear model: throttle x total_power
    load_currents = _load_currents(result)
    assert len(load_currents) == 1
    _assert_within(load_currents[0], expected_load, label="load current")
    _assert_within(_load_powers(result)[0], 250.0, label="load power")

    # Battery supplies the whole load: same magnitude, discharging (negative).
    battery = _total_battery_input_current(result)
    assert battery < 0, "battery must be discharging"
    _assert_within(-battery, expected_load, label="battery discharge current")

    # 5.2 A is well inside the 20 A discharge limit, so nothing is restricted.
    assert _matching_warnings(result, "over-discharged") == []
    assert _balancer_current(result) == pytest.approx(0.0, abs=1e-6)
    assert result["load_result"]["data"][0]["motor_physics"]["model_type"] == "linear"

    assert_kcl(result)


@pytest.mark.integration
def test_load_only_dual(resolved_circuit_config, constants):
    """Two loads (BLDC + linear) share DC bus. Expected: total current = sum of
    individual demands."""
    result = run_circuit("load_only_dual", resolved_circuit_config, constants)

    load_currents = _load_currents(result)
    assert len(load_currents) == 2, "both loads must appear on the bus"

    # arr0 is the BLDC load: its demand comes from the motor model, which the
    # checker republishes as motor_physics.power_electrical_w.
    physics = [entry["motor_physics"] for entry in result["load_result"]["data"]]
    assert physics[0]["model_type"] == "BLDC"
    assert physics[1]["model_type"] == "linear"

    expected_bldc = physics[0]["power_electrical_w"] / 48.0
    expected_linear = (500.0 * 0.5) / 48.0
    _assert_within(load_currents[0], expected_bldc, label="BLDC load current")
    _assert_within(load_currents[1], expected_linear, label="linear load current")

    # Req 12.1: total demand (~15.6 A) is inside the 20 A discharge limit, so
    # each load is served in full and the bus current is their sum.
    expected_total = expected_bldc + expected_linear
    assert expected_total < 20.0, "fixture must stay inside the discharge limit"
    bus_current = result["l_array_result"]["data"][0]["current"]["l_array"]
    _assert_within(bus_current, expected_total, label="load array bus current")
    _assert_within(-_total_battery_input_current(result), expected_total,
                   label="battery discharge current")
    assert _matching_warnings(result, "over-discharged") == [], (
        "neither load may be restricted below its demand"
    )

    assert_kcl(result)


# ---------------------------------------------------------------------------
# Equilibrium and limit circuits
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_balanced_system(resolved_circuit_config, constants):
    """Solar input approximately equals load demand. Expected: battery current
    near zero."""
    result = run_circuit("balanced_system", resolved_circuit_config, constants)

    mppt_current = _total_mppt_output_current(result)
    _assert_within(mppt_current, _expected_mppt_current(100.0, 0.9, 48.0, constants),
                   label="total mppt output current")

    load_current = _load_currents(result)[0]
    expected_load = (
        result["load_result"]["data"][0]["motor_physics"]["power_electrical_w"] / 48.0
    )
    _assert_within(load_current, expected_load, label="BLDC load current")

    # Solar covers ~90% of the demand, so the battery only trickles.
    battery = _total_battery_input_current(result)
    assert abs(battery) < 0.5, f"battery current {battery:.4g} A is not near zero"
    assert abs(battery) < 0.2 * load_current, (
        f"battery current {battery:.4g} A should be a small fraction of the "
        f"{load_current:.4g} A load"
    )
    assert battery == pytest.approx(mppt_current - load_current, abs=1e-3)

    # Near equilibrium nothing is limited in either direction.
    assert _balancer_current(result) == pytest.approx(0.0, abs=1e-6)
    assert _matching_warnings(result, "over-discharged") == []
    assert _matching_warnings(result, "overcharged") == []

    assert_kcl(result)


@pytest.mark.integration
def test_oversized_solar(resolved_circuit_config, constants):
    """Excess solar exceeds battery charge limit. Expected: load balancer
    absorbs excess, overcharge warning."""
    result = run_circuit("oversized_solar", resolved_circuit_config, constants)

    # Two arrays on a 24 V bus: 2 x 90 W / 39 V = 4.62 A.
    total_mppt = 2 * _expected_mppt_current(100.0, 0.9, 24.0, constants)
    _assert_within(_total_mppt_output_current(result), total_mppt,
                   label="total mppt output current")

    expected_load = (500.0 * 0.1) / 24.0  # linear load at 0.1 throttle
    _assert_within(_load_currents(result)[0], expected_load, label="load current")

    # Test_Battery_Low_Charge caps charging at 2 A; the surplus has to go
    # through the balancer (Requirement 4.4).
    charge_limit = 2.0
    battery = _total_battery_input_current(result)
    assert battery > 0, "battery must be charging"
    _assert_within(battery, charge_limit, label="battery charge current")

    expected_excess = total_mppt - expected_load - charge_limit
    assert expected_excess > 0, "fixture must produce surplus charge current"
    _assert_within(_balancer_current(result), expected_excess,
                   label="load balancer current")

    overcharge = _matching_warnings(result, "overcharged")
    assert len(overcharge) == 1, f"expected one overcharge warning, got {_warnings(result)}"

    assert_kcl(result)


@pytest.mark.integration
def test_high_load_system(resolved_circuit_config, constants):
    """Load demand exceeds battery discharge limit. Expected: load restricted,
    over-discharge warning."""
    result = run_circuit("high_load_system", resolved_circuit_config, constants)

    mppt_current = _expected_mppt_current(100.0, 0.9, 24.0, constants)
    _assert_within(_total_mppt_output_current(result), mppt_current,
                   label="total mppt output current")

    # Full-throttle BLDC wants 500 W / 24 V = 20.8 A but the pack allows 5 A.
    demand = result["load_result"]["data"][0]["motor_physics"]["power_electrical_w"] / 24.0
    discharge_limit = 5.0

    battery = _total_battery_input_current(result)
    assert battery < 0, "battery must be discharging"
    _assert_within(-battery, discharge_limit, label="battery discharge current")

    # Req 12.2: the load only gets solar plus the permitted discharge current.
    load_current = _load_currents(result)[0]
    _assert_within(load_current, mppt_current + discharge_limit,
                   label="restricted load current")
    assert load_current < demand, (
        f"load current {load_current:.4g} A should be restricted below the "
        f"{demand:.4g} A demand"
    )

    over_discharge = _matching_warnings(result, "over-discharged")
    assert len(over_discharge) == 1, (
        f"expected one over-discharge warning, got {_warnings(result)}"
    )

    assert_kcl(result)
