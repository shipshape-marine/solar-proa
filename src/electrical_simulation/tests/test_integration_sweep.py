"""Integration tests: sweep and voyage end-to-end (spec Task 9).

These tests drive the real production engines — ``sweep_throttle``,
``sweep_panel_power`` and ``start_voyage`` — against the Task 2 fixture
circuits with a real NgSpice solve at every point, and check the physical
invariants PLAN.md lists under "Validation Approach for Sweep/Voyage Tests":
power conservation and monotonicity, KCL at every point, exact SOC integration,
and SOC staying inside [0.0, 1.0].

How the engines are observed
----------------------------
* Neither sweep nor voyage returns its results; both hand them to
  ``generate_graph``. So ``generate_graph`` is wrapped (not replaced) on the
  engine module: the wrapper snapshots the results and x-axis, then calls the
  real plotter. The engines and the plotter therefore run unmodified, and the
  PNG and warning/error JSON files land under ``tmp_path``, which is what
  Requirement 8 asks for.
* The snapshot is a deep copy taken before plotting, because
  ``generate_graph`` strips the battery negative-terminal entries from the
  result dicts it is given.
* ``SWEEP_INTERVAL_COUNT`` is reduced from 100 to 10 so a sweep is 11 (or 10)
  real solves instead of 101, as PLAN.md suggests for speed. The sweep loop
  reads it as a module global, so the reduction exercises the same code path
  with the same range arithmetic.

Fixture choices
---------------
* Sweeps use circuits whose bus voltage is fixed (``current_soc`` stays 0.5),
  so every point can be compared against the same hand-calculated value.
* Voyage tests use ``high_load_system``: a 1S (24 V) pack, so the cell voltage
  stays inside ``MPPT_BATTERY_VOLTAGE_BUFFER`` of ``Test_MPPT``'s 36 V output
  rating as the SOC moves. A 2S pack drifting toward SOC 1.0 (56 V) would trip
  the MPPT voltage-mismatch error string instead. Its capacity is shrunk to
  2 Ah so a five-minute segment moves the SOC by a readable amount while
  staying clear of both the full and empty boundaries.

Validates: Requirements 6.1, 6.2, 6.4, 6.5, 7.1, 7.2, 7.7, 8.1, 8.4
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.electrical_simulation.tests.helpers import (
    TOLERANCE,
    assert_kcl,
    assert_within,
    expected_mppt_current,
    load_currents,
    load_powers,
    requires_ngspice,
    total_battery_input_current,
    total_mppt_output_current,
)

pytestmark = requires_ngspice

SWEEP_POINTS = 10  # reduced SWEEP_INTERVAL_COUNT: 11 throttle points, 10 panel points
STEP_MINUTES = 1  # SIMULATION_INTERVAL_MIN in simulation_over_time


# ---------------------------------------------------------------------------
# Plot backend
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _headless_plots():
    """Render to a file-only backend and close every figure afterwards.

    The real ``generate_graph`` runs in these tests, and it leaves its combined
    figure open.
    """
    import matplotlib

    matplotlib.use("Agg", force=True)
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


# ---------------------------------------------------------------------------
# Driving the engines
# ---------------------------------------------------------------------------


def _capture_graph(monkeypatch, module) -> list:
    """Wrap ``generate_graph`` on `module`, recording its arguments.

    The real plotter still runs, so the graph and JSON files are produced.
    Returns the list the wrapper appends one entry per call to.
    """
    from src.electrical_simulation import sweep_graph_generation

    real_generate_graph = sweep_graph_generation.generate_graph
    calls = []

    def capturing(results, x_axis, **kwargs):
        calls.append(
            {
                "results": deepcopy(results),
                "x_axis": list(x_axis),
                "kwargs": {
                    key: value for key, value in kwargs.items() if key != "constants"
                },
            }
        )
        return real_generate_graph(results, x_axis, **kwargs)

    monkeypatch.setattr(module, "generate_graph", capturing)
    return calls


def _single_call(calls: list) -> dict:
    """The one plotting call an engine run makes."""
    assert len(calls) == 1, f"expected one generate_graph call, got {len(calls)}"
    return calls[0]


def _run_sweep(monkeypatch, which: str, circuit_setup: dict, constants: dict,
               save_path: str, propeller_load_factor=None) -> dict:
    """Run a reduced throttle or panel power sweep; return the captured call."""
    from src.electrical_simulation import simulation_sweeper

    monkeypatch.setattr(simulation_sweeper, "SWEEP_INTERVAL_COUNT", SWEEP_POINTS)
    calls = _capture_graph(monkeypatch, simulation_sweeper)

    sweep = {
        "throttle": simulation_sweeper.sweep_throttle,
        "panel_power": simulation_sweeper.sweep_panel_power,
    }[which]

    sweep(
        circuit_setup,
        save_path=save_path,
        ngspice_available=True,
        save_output=True,
        constants=constants,
        propeller_load_factor=propeller_load_factor,
    )
    return _single_call(calls)


def _run_voyage(monkeypatch, circuit_setup: dict, voyage_path: str, constants: dict,
                save_path: str) -> dict:
    """Run a voyage end to end; return the captured plotting call."""
    from src.electrical_simulation import simulation_over_time

    calls = _capture_graph(monkeypatch, simulation_over_time)
    simulation_over_time.start_voyage(
        circuit_setup=circuit_setup,
        voyage_config_loc=voyage_path,
        save_path=save_path,
        ngspice_available=True,
        constants=constants,
    )
    return _single_call(calls)


# ---------------------------------------------------------------------------
# Fixture and config plumbing
# ---------------------------------------------------------------------------


def _setup(resolved_circuit_config, name: str, capacity_ah: float = None,
           in_parallel: int = None) -> dict:
    """A resolved circuit setup, optionally with the battery capacity resized.

    The override is applied after choice resolution, so it is not overwritten by
    the component spec. Only the voyage engine reads these two keys (to size the
    pack in A-min); the netlist is unaffected.
    """
    setup = resolved_circuit_config(name)
    if capacity_ah is not None:
        setup["battery"]["capacity_ah"] = capacity_ah
    if in_parallel is not None:
        setup["battery"]["battery_in_parallel"] = in_parallel
    return setup


def _pack_capacity_amin(setup: dict) -> float:
    """Total pack capacity in A-min, as the voyage engine computes it."""
    battery = setup["battery"]
    return battery["capacity_ah"] * battery["battery_in_parallel"] * 60


def _segment(duration_minutes: int, throttle: float, solar_power: float,
             **extra) -> dict:
    """One voyage segment definition."""
    segment = {
        "name": f"{duration_minutes} min @ throttle {throttle} solar {solar_power}",
        "duration_minutes": duration_minutes,
        "throttle": throttle,
        "solar_power": solar_power,
    }
    segment.update(extra)
    return segment


def _write_voyage(tmp_path, segments: list, initial_soc: float = 0.5,
                  filename: str = "voyage.json") -> str:
    """Write a voyage config JSON and return its path as a string."""
    config = {
        "voyage_info": {"name": "integration test voyage"},
        "initial_battery_soc": initial_soc,
        "segments": segments,
    }
    path = tmp_path / filename
    path.write_text(json.dumps(config, indent=4), encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# Assertions on captured runs
# ---------------------------------------------------------------------------


def _load_power(result) -> float:
    """Total power drawn by all loads at one operating point."""
    return sum(load_powers(result))


def _assert_graph_outputs(save_path: str, x_label: str, plot_titles: list):
    """Verify the PNG and JSON artefacts of one plotting run exist.

    ``generate_graph`` writes one PNG per subplot named
    ``{save_path}.{axis title}.png``, a combined PNG, and the warning and error
    JSON files (Requirements 8.1 and 8.4).
    """
    prefix = Path(save_path)
    directory = prefix.parent

    for title in plot_titles:
        expected = directory / f"{prefix.name}.{title} vs {x_label}.png"
        assert expected.exists(), (
            f"missing subplot PNG {expected.name}; "
            f"present: {sorted(item.name for item in directory.iterdir())}"
        )

    combined = directory / f"{prefix.name}.sweep_simulation_results.png"
    assert combined.exists(), "combined multi-plot PNG was not saved"

    for name, expected_type in (
        (f"{prefix.name}.sweep_simulation_warnings.json", list),
        (f"{prefix.name}.sweep_simulation_errors.json", list),
    ):
        path = directory / name
        assert path.exists(), f"{name} was not saved"
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), expected_type)


# ---------------------------------------------------------------------------
# Requirement 6.1, 6.4, 8.1, 8.4 — throttle sweep
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_throttle_sweep_monotonic_power(monkeypatch, resolved_circuit_config,
                                        constants, tmp_path):
    """Sweep throttle 0-100% and verify power is monotonically non-decreasing."""
    save_path = str(tmp_path / "throttle_sweep")
    setup = _setup(resolved_circuit_config, "load_only_single")

    call = _run_sweep(monkeypatch, "throttle", setup, constants, save_path)

    results = call["results"]
    assert len(results) == SWEEP_POINTS + 1, "one solve per swept throttle value"
    assert call["x_axis"] == pytest.approx([i / SWEEP_POINTS for i in range(SWEEP_POINTS + 1)])

    powers = [_load_power(result) for result in results]
    # Linear load: 500 W x throttle, so each step up adds ~50 W at 10% spacing.
    # A tiny slack absorbs solver noise without hiding a real reversal.
    for lower, upper in zip(powers, powers[1:]):
        assert upper >= lower - 1e-3, (
            f"load power dropped as throttle rose: {lower:.6g} W then {upper:.6g} W "
            f"(full trace {powers})"
        )
    assert powers[-1] > powers[0], "full throttle must draw more than zero throttle"
    assert_within(powers[-1], 500.0, label="load power at full throttle")

    # The battery covers the whole load: panel power is pinned at 0 by the sweep,
    # which leaves the solar array at its EPSILON current floor (tens of uA).
    assert all(total_battery_input_current(result) <= 1e-3 for result in results), (
        "with panel_power_setting=0 the battery can only discharge"
    )
    assert all(abs(total_mppt_output_current(result)) < 1e-3 for result in results)

    # Requirements 8.1 and 8.4: every subplot, the combined figure and the
    # warning/error JSON files are written next to each other.
    _assert_graph_outputs(save_path, "Throttle Input (%)", ["Voltage", "Current", "Power"])


@pytest.mark.integration
def test_throttle_sweep_zero_throttle_zero_load(monkeypatch, resolved_circuit_config,
                                                constants, tmp_path):
    """At throttle=0, load power should be approximately zero."""
    save_path = str(tmp_path / "throttle_zero")
    setup = _setup(resolved_circuit_config, "load_only_single")

    call = _run_sweep(monkeypatch, "throttle", setup, constants, save_path)

    first = call["results"][0]
    assert call["x_axis"][0] == 0.0, "the sweep must start at zero throttle"

    # Load.__init__ collapses the demand to GROUNDING_RESISTANCE at zero
    # throttle, so the behavioural source sinks essentially nothing.
    power = _load_power(first)
    assert abs(power) < 0.5, f"zero-throttle load power {power:.6g} W is not ~0"
    for index, current in enumerate(load_currents(first)):
        assert abs(current) < 0.05, f"load {index} draws {current:.6g} A at zero throttle"

    # Nothing in, nothing out: the battery is neither charged nor discharged.
    battery = total_battery_input_current(first)
    assert abs(battery) < 0.05, f"battery current {battery:.6g} A is not ~0"
    assert_kcl(first)


@pytest.mark.integration
def test_throttle_sweep_kcl_all_points(monkeypatch, resolved_circuit_config,
                                       constants, tmp_path):
    """Verify KCL holds at every point in the throttle sweep."""
    save_path = str(tmp_path / "throttle_kcl")
    setup = _setup(resolved_circuit_config, "load_only_single")

    call = _run_sweep(monkeypatch, "throttle", setup, constants, save_path)

    results = call["results"]
    assert len(results) == SWEEP_POINTS + 1
    for throttle, result in zip(call["x_axis"], results):
        # The checker runs on every point too, so a violation would also show up
        # as an error entry; assert both, with the throttle value for context.
        assert result["error"]["data"] == [], (
            f"throttle {throttle:.2f} reported errors: {result['error']['data']}"
        )
        assert_kcl(result)


# ---------------------------------------------------------------------------
# Requirement 6.2 — panel power sweep
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_panel_sweep_decreasing_mppt_current(monkeypatch, resolved_circuit_config,
                                             constants, tmp_path):
    """As panel power decreases, MPPT output current should decrease."""
    save_path = str(tmp_path / "panel_sweep")
    # Charging-only 1S circuit: no load, so MPPT output and battery input are
    # the same current and the 24 V bus does not move during the sweep.
    setup = _setup(resolved_circuit_config, "charging_only_1panel")

    call = _run_sweep(monkeypatch, "panel_power", setup, constants, save_path)

    panel_powers = call["x_axis"]
    results = call["results"]
    assert len(results) == SWEEP_POINTS, "one solve per swept panel power value"
    assert panel_powers == pytest.approx(
        [i / SWEEP_POINTS for i in range(SWEEP_POINTS, 0, -1)]
    )

    currents = [total_mppt_output_current(result) for result in results]
    for lower, upper in zip(currents, currents[1:]):
        assert upper < lower, (
            f"MPPT current did not fall with panel power: {lower:.6g} A then "
            f"{upper:.6g} A (full trace {currents})"
        )

    # Each point matches the MPPT's own regulation formula on the 24 V bus, and
    # with no load every amp goes into the battery.
    for panel_power, result, current in zip(panel_powers, results, currents):
        expected = expected_mppt_current(100.0 * panel_power, 0.9, 24.0, constants)
        assert_within(current, expected, label=f"mppt current at {panel_power:.2f} panel power")
        assert_within(total_battery_input_current(result), expected,
                      label=f"battery charge current at {panel_power:.2f} panel power")
        assert_kcl(result)

    _assert_graph_outputs(save_path, "Panel Power (%)", ["Voltage", "Current", "Power"])


# ---------------------------------------------------------------------------
# Requirements 7.1, 7.2, 7.7, 8.1, 8.4 — voyage
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_voyage_soc_bounds(monkeypatch, resolved_circuit_config, fixtures_dir,
                           constants, tmp_path):
    """Run 3-segment voyage, verify SOC stays within [0.0, 1.0] at all time steps."""
    save_path = str(tmp_path / "voyage")
    setup = _setup(resolved_circuit_config, "high_load_system", capacity_ah=2)
    capacity = _pack_capacity_amin(setup)
    # The Task 2 voyage fixture: discharge, charge, then mixed, 5 minutes each.
    voyage_path = str(fixtures_dir / "test_voyage_setup.json")

    call = _run_voyage(monkeypatch, setup, voyage_path, constants, save_path)

    capacity_trace = call["kwargs"]["battery_capacity"]
    assert capacity_trace, "the voyage must report a battery capacity trace"
    # SOC is capacity / pack capacity, the same ratio the engine feeds back into
    # each circuit build, so bounding the trace bounds the SOC.
    for value in capacity_trace:
        soc = value / capacity
        assert -constants["EPSILON"] <= soc <= 1.0 + constants["EPSILON"], (
            f"SOC {soc:.6f} left [0.0, 1.0] (capacity {value:.6g} of "
            f"{capacity:.6g} A-min)"
        )

    # 15 one-minute steps, and the plotter needs all three traces aligned.
    x_axis = call["x_axis"]
    assert x_axis[0] == 0
    assert x_axis[-1] == pytest.approx(15)
    assert all(a <= b for a, b in zip(x_axis, x_axis[1:])), "timeline must not go back"
    assert len(call["results"]) == len(x_axis) == len(capacity_trace)

    # Requirement 7.7 / 8.1: the voyage plots a battery capacity axis on top of
    # the voltage, current and power axes, and saves the JSON artefacts.
    _assert_graph_outputs(
        save_path, "Time (minutes)",
        ["Voltage", "Current", "Power", "Battery Capacity"],
    )


@pytest.mark.integration
def test_voyage_discharge_segment(monkeypatch, resolved_circuit_config, constants,
                                  tmp_path):
    """During high-throttle/no-solar segment, SOC must decrease."""
    save_path = str(tmp_path / "voyage_discharge")
    setup = _setup(resolved_circuit_config, "high_load_system", capacity_ah=2)
    capacity = _pack_capacity_amin(setup)
    duration = 5
    voyage_path = _write_voyage(
        tmp_path, [_segment(duration, throttle=0.8, solar_power=0.0)]
    )

    call = _run_voyage(monkeypatch, setup, voyage_path, constants, save_path)

    # Every solved point draws from the battery: no solar, high throttle.
    currents = [total_battery_input_current(result) for result in call["results"]]
    assert all(current < 0 for current in currents), (
        f"battery must discharge throughout the segment, got {currents}"
    )

    capacity_trace = call["kwargs"]["battery_capacity"]
    assert capacity_trace[0] == pytest.approx(0.5 * capacity)
    for previous, following in zip(capacity_trace, capacity_trace[1:]):
        assert following <= previous, (
            f"capacity rose during a discharge segment: {capacity_trace}"
        )
    assert capacity_trace[-1] < capacity_trace[0]

    # Requirement 7.2, exact integration: the discharge current is clamped by
    # the pack limit so it is the same at every step, and the capacity falls by
    # current x minutes.
    assert currents == pytest.approx([currents[-1]] * len(currents), rel=TOLERANCE)
    expected_final = capacity_trace[0] + currents[-1] * duration * STEP_MINUTES
    assert_within(capacity_trace[-1], expected_final,
                  label="capacity after the discharge segment")
    assert capacity_trace[-1] > 0, "the fixture must not empty the pack"


@pytest.mark.integration
def test_voyage_charge_segment(monkeypatch, resolved_circuit_config, constants,
                               tmp_path):
    """During zero-throttle/full-solar segment, SOC must increase."""
    save_path = str(tmp_path / "voyage_charge")
    setup = _setup(resolved_circuit_config, "high_load_system", capacity_ah=2)
    capacity = _pack_capacity_amin(setup)
    duration = 5
    voyage_path = _write_voyage(
        tmp_path, [_segment(duration, throttle=0.0, solar_power=1.0)]
    )

    call = _run_voyage(monkeypatch, setup, voyage_path, constants, save_path)

    currents = [total_battery_input_current(result) for result in call["results"]]
    assert all(current > 0 for current in currents), (
        f"battery must charge throughout the segment, got {currents}"
    )
    # Solar alone feeds the pack: one 100 W panel on a 24 V bus.
    assert_within(currents[-1], expected_mppt_current(100.0, 0.9, 24.0, constants),
                  label="charge current")

    capacity_trace = call["kwargs"]["battery_capacity"]
    assert capacity_trace[0] == pytest.approx(0.5 * capacity)
    for previous, following in zip(capacity_trace, capacity_trace[1:]):
        assert following >= previous, (
            f"capacity fell during a charge segment: {capacity_trace}"
        )
    assert capacity_trace[-1] > capacity_trace[0]

    expected_final = capacity_trace[0] + currents[-1] * duration * STEP_MINUTES
    assert_within(capacity_trace[-1], expected_final,
                  label="capacity after the charge segment")
    assert capacity_trace[-1] < capacity, "the fixture must not fill the pack"
