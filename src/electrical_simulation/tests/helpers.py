"""Shared helpers for the electrical_simulation integration tests.

Holds the NgSpice availability probe and the result-reading helpers used by
both integration modules (``test_integration_circuits.py`` for operating points
and ``test_integration_sweep.py`` for sweeps and voyages), so the KCL check and
the section accessors exist in exactly one place.

Every ``src`` import happens inside a function so importing this module is safe
even when PySpice or the NgSpice shared library is missing: collection stays
green and the affected modules skip.
"""

import pytest

TOLERANCE = 0.05  # 5% per PLAN.md "Validation Approach"


def _probe_ngspice() -> bool:
    """True when the NgSpice shared library can actually be loaded.

    Mirrors ``src.electrical_simulation.__main__.check_ngspice`` but stays quiet
    and imports PySpice lazily, so a machine without PySpice or without the
    shared library skips the integration modules instead of erroring during
    collection.
    """
    try:
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


NGSPICE_AVAILABLE = _probe_ngspice()

#: Module-level guard for integration modules: ``pytestmark = requires_ngspice``.
requires_ngspice = pytest.mark.skipif(
    not NGSPICE_AVAILABLE,
    reason="NgSpice shared library is not available; install it to run integration tests",
)


# ---------------------------------------------------------------------------
# Running a circuit
# ---------------------------------------------------------------------------


def run_circuit(fixture_name: str, resolved_circuit_config, constants: dict,
                modifications: dict = None) -> dict:
    """Build and simulate a test circuit, return result dict.

    Runs the production path: ``build_circuit_from_json`` then
    ``begin_simulation`` (which solves, parses and cross-checks). Fails the test
    if the solver did not produce an analysis (Requirement 2.1).
    """
    from src.electrical_simulation.circuit_constructor import build_circuit_from_json
    from src.electrical_simulation.pyspice_simulator import begin_simulation

    circuit, component_object, errors = build_circuit_from_json(
        circuit_setup=resolved_circuit_config(fixture_name),
        modifications=modifications if modifications is not None else {},
        constants=constants,
    )
    assert errors == [], f"{fixture_name} should build without setup errors: {errors}"

    analysis, result = begin_simulation(
        circuit=circuit,
        component_object=component_object,
        errors=errors,
        ngspice_available=True,
        constants=constants,
    )
    assert analysis is not None, (
        f"{fixture_name} produced no analysis: {result['error']['data']}"
    )
    assert result["error"]["data"] == [], (
        f"{fixture_name} reported errors: {result['error']['data']}"
    )
    return result


# ---------------------------------------------------------------------------
# Physical invariants
# ---------------------------------------------------------------------------


def assert_kcl(result, epsilon=1e-3):
    """Verify KCL: MPPT_out - battery_in - load_current = 0.

    Uses ``abs`` on the residual (Requirement 4.1 asks for zero within
    tolerance in either direction) and includes the load balancer branch, the
    same set of terms ``cross_check_result`` sums.
    """
    mppt_out = total_mppt_output_current(result)
    battery_in = total_battery_input_current(result)
    load_current = total_load_current(result)

    residual = mppt_out - battery_in - load_current
    assert abs(residual) < epsilon, (
        f"KCL residual {residual:.6g} A exceeds {epsilon} A "
        f"(mppt {mppt_out:.6g}, battery {battery_in:.6g}, load {load_current:.6g})"
    )


def assert_within(actual: float, expected: float, tolerance: float = TOLERANCE,
                  label: str = "value"):
    """Assert a relative deviation below `tolerance` (absolute near zero)."""
    if abs(expected) < 1e-9:
        assert abs(actual) < 1e-3, f"{label}: expected ~0 A, got {actual:.6g}"
        return
    deviation = abs(actual - expected) / abs(expected)
    assert deviation < tolerance, (
        f"{label}: {actual:.6g} deviates {deviation * 100:.2f}% from expected "
        f"{expected:.6g} (limit {tolerance * 100:.0f}%)"
    )


def expected_mppt_current(panel_power_w: float, efficiency: float,
                          bus_voltage: float, constants: dict) -> float:
    """MPPT output current as MPPT.setup_mppt computes it.

    The MPPT regulates to ``power x efficiency / (bus_voltage + buffer)``: it
    has to work above the pack voltage to push charge into it.
    """
    working_voltage = bus_voltage + constants["MPPT_BATTERY_VOLTAGE_BUFFER"]
    return panel_power_w * efficiency / working_voltage


# ---------------------------------------------------------------------------
# Result section accessors
# ---------------------------------------------------------------------------


def summary_currents(result) -> dict:
    """DC-bus totals. parse_result puts these in `summary`, not `mppt_result`."""
    return result["summary"]["data"][0]["current"]


def total_mppt_output_current(result) -> float:
    """Current leaving all MPPTs into the DC bus (positive = delivering)."""
    return summary_currents(result)["total_mppt_output_current"]


def total_battery_input_current(result) -> float:
    """Battery branch current (positive = charging, negative = discharging)."""
    return summary_currents(result)["total_battery_input_current"]


def array_mppt_output_current(result, index: int) -> float:
    """Regulated output current of one MPPT array."""
    return result["mppt_result"]["data"][index]["current"]["mppt_output"]


def load_currents(result) -> list:
    """One total current per load, in load-array order."""
    return [sum(entry["current"].values()) for entry in result["load_result"]["data"]]


def load_powers(result) -> list:
    """One power per load, terminal voltage x current, in load-array order."""
    powers = []
    for entry in result["load_result"]["data"]:
        voltage = sum(entry["voltage"].values())
        powers.append(voltage * sum(entry["current"].values()))
    return powers


def balancer_current(result) -> float:
    """Current absorbed by the load balancer (positive = dumping excess charge)."""
    return result["load_balancer"]["data"][0]["current"]["balancing_load"]


def total_load_current(result) -> float:
    """Loads plus load balancer, matching cross_check_result's KCL terms."""
    return sum(load_currents(result)) + balancer_current(result)


def bus_voltage(result) -> float:
    """Solved DC-bus node voltage."""
    return result["summary"]["data"][0]["voltage"]["total_dc_bus_voltage"]


def cell_voltages(result) -> list:
    """Per-cell battery voltages after parse_result's terminal post-processing."""
    voltages = result["battery_result"]["data"][0]["voltage"]
    return [value for key, value in voltages.items() if "positive" in key]


def warnings_of(result) -> list:
    """All warning strings the checker raised for one result."""
    return result["warning"]["data"]


def matching_warnings(result, needle: str) -> list:
    """Warning strings containing `needle`."""
    return [text for text in warnings_of(result) if needle in text]
