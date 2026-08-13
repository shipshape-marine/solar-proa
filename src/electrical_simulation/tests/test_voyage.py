"""Unit tests for the voyage engine (spec Task 7).

Covers ``start_voyage``: state-of-charge integration over 1-minute steps, the
step split when the battery hits full or empty mid-step (with the charge /
discharge limit forced to zero for the remainder), segment sequencing and the
per-segment propeller load factor, the abort path when a solve fails, and the
step-function duplication ``step_up_prev`` performs on the plot data.

No NgSpice, no circuit and no graph files: ``build_circuit_from_json``,
``begin_simulation`` and ``generate_graph`` are replaced on the
``simulation_over_time`` module (where its ``from ... import`` statements bind
them) with a recorder that hands back result dicts carrying a known battery
current, so the SOC arithmetic is exactly predictable. All ``src`` imports
happen inside helpers so collection stays green when the simulation
dependencies are unavailable.

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
"""

import json
from copy import deepcopy

import pytest


# ---------------------------------------------------------------------------
# helpers — synthetic results and a recorder for the voyage collaborators
# ---------------------------------------------------------------------------


def _section(keyword: str, data: list = None) -> dict:
    """One result section with its array_count kept consistent with its data."""
    data = list(data or [])
    return {"keyword": keyword, "array_count": len(data), "data": data}


def _result(index: int, battery_current: float) -> dict:
    """A result dict shaped like ``pyspice_simulator.__simulate__`` output.

    Only the summary section the voyage loop reads is populated; the remaining
    sections are present and empty so the production key set is preserved.
    ``iteration`` tags the dict so the order of the graphed list is checkable.
    """
    return {
        "iteration": index,
        "info": _section("info"),
        "error": _section("error"),
        "warning": _section("warning"),
        "summary": _section(
            "total",
            [
                {
                    "array_index": 0,
                    "voltage": {},
                    "current": {
                        "total_mppt_output_current": 0.0,
                        "total_battery_input_current": battery_current,
                    },
                }
            ],
        ),
        "mppt_result": _section("mppt"),
        "battery_result": _section("battery"),
        "solar_result": _section("solar_array"),
        "panel_result": _section("panel"),
        "load_balancer": _section("balancing_load"),
        "load_result": _section("load"),
        "l_array_result": _section("l_array"),
    }


class _VoyageRecorder:
    """Captures the voyage loop's calls and feeds it a known battery current.

    ``battery_current`` is either a constant (amps into the battery, negative
    while discharging) or a callable taking the modifications dict, which lets a
    test make the current depend on the segment's throttle / solar settings. A
    constant reports 0 A whenever the loop has pinned ``max_charge_current`` or
    ``max_discharge_current`` to 0, which is what a real re-simulation of the
    remainder of a split step returns.

    ``fail_at`` is the zero-based simulation index from which ``begin_simulation``
    returns ``None`` for the analysis object, the way a failed solve reports
    itself.
    """

    def __init__(self, battery_current, fail_at: int = None):
        if callable(battery_current):
            self._current_fn = battery_current
        else:
            value = float(battery_current)

            def _limited(modifications):
                if (
                    modifications.get("max_charge_current") == 0
                    or modifications.get("max_discharge_current") == 0
                ):
                    return 0.0
                return value

            self._current_fn = _limited

        self.fail_at = fail_at
        self.build_calls = []
        self.simulate_calls = []
        self.results = []
        self.graph_calls = []

    # stand-in for circuit_constructor.build_circuit_from_json
    def build_circuit_from_json(self, circuit_setup=None, modifications=None,
                                constants=None, **kwargs):
        # Deep-copied: the loop reuses one modifications dict per step and adds
        # the charge/discharge limit to it between the two builds of a split step.
        self.build_calls.append(
            {
                "circuit_setup": circuit_setup,
                "modifications": deepcopy(modifications),
                "constants": constants,
            }
        )
        return "circuit", "component_object", []

    # stand-in for pyspice_simulator.begin_simulation
    def begin_simulation(self, circuit, component_object, errors,
                         ngspice_available=False, constants=None, **kwargs):
        index = len(self.simulate_calls)
        modifications = self.build_calls[-1]["modifications"]
        self.simulate_calls.append({"modifications": modifications})

        result = _result(index, self._current_fn(modifications))
        self.results.append(result)

        failed = self.fail_at is not None and index >= self.fail_at
        return (None if failed else object()), result

    # stand-in for sweep_graph_generation.generate_graph
    def generate_graph(self, results, x_axis, **kwargs):
        self.graph_calls.append(
            {"results": results, "x_axis": list(x_axis), "kwargs": kwargs}
        )

    # -- convenience accessors -------------------------------------------

    @property
    def modifications(self) -> list:
        """The modifications dict passed to each build, in call order."""
        return [call["modifications"] for call in self.build_calls]

    @property
    def graph_call(self) -> dict:
        """The single generate_graph call, asserting it happened exactly once."""
        assert len(self.graph_calls) == 1, "generate_graph must be called once"
        return self.graph_calls[0]

    @property
    def x_axis(self) -> list:
        """The voyage timeline handed to the plotter."""
        return self.graph_call["x_axis"]

    @property
    def battery_capacity(self) -> list:
        """The battery capacity trace (A-min) handed to the plotter."""
        return self.graph_call["kwargs"]["battery_capacity"]


def _install(monkeypatch, battery_current, fail_at: int = None):
    """Patch the voyage module's three collaborators; return ``(module, recorder)``."""
    from src.electrical_simulation import simulation_over_time

    recorder = _VoyageRecorder(battery_current, fail_at=fail_at)
    monkeypatch.setattr(
        simulation_over_time, "build_circuit_from_json", recorder.build_circuit_from_json
    )
    monkeypatch.setattr(
        simulation_over_time, "begin_simulation", recorder.begin_simulation
    )
    monkeypatch.setattr(simulation_over_time, "generate_graph", recorder.generate_graph)
    return simulation_over_time, recorder


def _setup(circuit_config, capacity_ah: float = 10, in_parallel: int = 1) -> dict:
    """A test circuit setup whose battery capacity is sized for the test.

    Total capacity is ``capacity_ah * in_parallel * 60`` A-min; the loop reads
    nothing else from the setup (the circuit build is mocked).
    """
    setup = circuit_config("load_only_single")
    setup["battery"]["capacity_ah"] = capacity_ah
    setup["battery"]["battery_in_parallel"] = in_parallel
    return setup


def _write_voyage(tmp_path, segments: list, initial_soc: float = 0.5,
                  filename: str = "voyage.json") -> str:
    """Write a voyage config JSON and return its path as a string."""
    config = {
        "voyage_info": {"name": "unit test voyage"},
        "initial_battery_soc": initial_soc,
        "segments": segments,
    }
    path = tmp_path / filename
    path.write_text(json.dumps(config), encoding="utf-8")
    return str(path)


def _segment(duration_minutes: int, throttle: float, solar_power: float,
             **extra) -> dict:
    """One voyage segment definition."""
    segment = {
        "name": f"{duration_minutes} min @ {throttle} throttle",
        "duration_minutes": duration_minutes,
        "throttle": throttle,
        "solar_power": solar_power,
    }
    segment.update(extra)
    return segment


def _soc_values(recorder: _VoyageRecorder) -> list:
    """The current_soc handed to each circuit build, in call order."""
    return [mod["current_soc"] for mod in recorder.modifications]


# ---------------------------------------------------------------------------
# Requirements 7.1, 7.2, 7.7 — SOC integration while charging
# ---------------------------------------------------------------------------


def test_soc_increases_during_charging(monkeypatch, constants, circuit_config,
                                      tmp_path):
    """Verify SOC increases when battery input current is positive."""
    # 10 Ah x 1P x 60 = 600 A-min total, starting at SOC 0.5 = 300 A-min.
    # +10 A for three 1-minute steps adds exactly 10 A-min per step.
    module, recorder = _install(monkeypatch, battery_current=10.0)
    voyage = _write_voyage(tmp_path, [_segment(3, throttle=0.0, solar_power=1.0)])

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=10),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    assert len(recorder.build_calls) == 3, "one simulation per 1-minute step"
    # Step-function trace: each new value is emitted twice so the plot holds
    # flat across the step and jumps at its boundary.
    assert recorder.battery_capacity == pytest.approx(
        [300, 300, 310, 310, 320, 320, 330]
    )
    assert recorder.x_axis == pytest.approx([0, 0, 1, 1, 2, 2, 3])

    # SOC fed back into each build is the integrated capacity over the total.
    assert _soc_values(recorder) == pytest.approx([0.5, 310 / 600, 320 / 600])
    assert all(a < b for a, b in zip(_soc_values(recorder), _soc_values(recorder)[1:]))

    # Req 7.7: the timeline, the capacity trace and the traces to plot.
    kwargs = recorder.graph_call["kwargs"]
    assert kwargs["x_label"] == "Time (minutes)"
    assert kwargs["voltage_display_choice"] == ["load_result", "mppt_result"]
    assert kwargs["current_display_choice"] == ["summary", "load_result"]
    assert kwargs["power_display_choice"] == ["load_result", "battery_result"]
    assert len(recorder.graph_call["results"]) == len(recorder.x_axis)


# ---------------------------------------------------------------------------
# Requirements 7.1, 7.2 — SOC integration while discharging
# ---------------------------------------------------------------------------


def test_soc_decreases_during_discharge(monkeypatch, constants, circuit_config,
                                        tmp_path):
    """Verify SOC decreases when battery input current is negative."""
    # Same 600 A-min pack from SOC 0.5, now drawing 10 A: -10 A-min per step.
    module, recorder = _install(monkeypatch, battery_current=-10.0)
    voyage = _write_voyage(tmp_path, [_segment(3, throttle=0.8, solar_power=0.0)])

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=10),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    assert recorder.battery_capacity == pytest.approx(
        [300, 300, 290, 290, 280, 280, 270]
    )
    assert _soc_values(recorder) == pytest.approx([0.5, 290 / 600, 280 / 600])
    assert all(a > b for a, b in zip(_soc_values(recorder), _soc_values(recorder)[1:]))


# ---------------------------------------------------------------------------
# Requirement 7.3 — full battery splits the step and stops charging
# ---------------------------------------------------------------------------


def test_soc_clamped_at_one(monkeypatch, constants, circuit_config, tmp_path):
    """Verify SOC does not exceed 1.0; step splits and max_charge_current set to 0."""
    # 1 Ah x 1P x 60 = 60 A-min, starting at SOC 0.9 = 54 A-min. At +10 A the
    # pack fills after (60 - 54) / 10 = 0.6 min, leaving 0.4 min of the step.
    module, recorder = _install(monkeypatch, battery_current=10.0)
    voyage = _write_voyage(
        tmp_path, [_segment(2, throttle=0.0, solar_power=1.0)], initial_soc=0.9
    )

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=1),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    # Step 1 splits at 0.6 min; step 2 starts already full so only the
    # charge-inhibited remainder is simulated.
    assert len(recorder.build_calls) == 4
    assert recorder.x_axis == pytest.approx([0, 0, 0.6, 0.6, 1.0, 1.0, 2.0])
    assert recorder.battery_capacity == pytest.approx([54, 54, 60, 60, 60, 60, 60])
    assert max(recorder.battery_capacity) == pytest.approx(60), "never overshoots full"

    # The remainder of each step is re-simulated with charging inhibited.
    charge_limits = [mod.get("max_charge_current") for mod in recorder.modifications]
    assert charge_limits == [None, 0, None, 0]
    # The limit is not carried into the next step's first build: the loop builds
    # a fresh modifications dict each step.
    assert all(soc <= 1.0 for soc in _soc_values(recorder))
    assert _soc_values(recorder)[-1] == 1.0


# ---------------------------------------------------------------------------
# Requirement 7.4 — empty battery splits the step and stops discharging
# ---------------------------------------------------------------------------


def test_soc_clamped_at_zero(monkeypatch, constants, circuit_config, tmp_path):
    """Verify SOC does not go below 0.0; step splits and max_discharge_current set to 0."""
    # 60 A-min pack starting at SOC 0.1 = 6 A-min. At -10 A it empties after
    # 6 / 10 = 0.6 min, leaving 0.4 min of the step.
    module, recorder = _install(monkeypatch, battery_current=-10.0)
    voyage = _write_voyage(
        tmp_path, [_segment(2, throttle=0.8, solar_power=0.0)], initial_soc=0.1
    )

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=1),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    assert len(recorder.build_calls) == 4
    assert recorder.x_axis == pytest.approx([0, 0, 0.6, 0.6, 1.0, 1.0, 2.0])
    assert recorder.battery_capacity == pytest.approx([6, 6, 0, 0, 0, 0, 0])
    assert min(recorder.battery_capacity) == 0, "never goes negative"

    discharge_limits = [
        mod.get("max_discharge_current") for mod in recorder.modifications
    ]
    assert discharge_limits == [None, 0, None, 0]
    assert all(soc >= 0.0 for soc in _soc_values(recorder))
    assert _soc_values(recorder)[-1] == 0.0


# ---------------------------------------------------------------------------
# Requirements 7.3, 7.4 — exact split times
# ---------------------------------------------------------------------------


def test_boundary_split_time_calculation(monkeypatch, constants, circuit_config,
                                        tmp_path):
    """Verify time-to-full/empty calculated correctly from current and remaining capacity."""
    # 1 Ah x 2P x 60 = 120 A-min, so the parallel count is part of the capacity.
    # Full: start at SOC 0.95 = 114 A-min, +12 A -> (120 - 114) / 12 = 0.5 min.
    module, recorder = _install(monkeypatch, battery_current=12.0)
    voyage = _write_voyage(
        tmp_path, [_segment(1, throttle=0.0, solar_power=1.0)], initial_soc=0.95
    )

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=1, in_parallel=2),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    assert recorder.x_axis == pytest.approx([0, 0, 0.5, 0.5, 1.0])
    assert recorder.battery_capacity == pytest.approx([114, 114, 120, 120, 120])

    # Empty: start at SOC 0.05 = 6 A-min, -24 A -> 6 / 24 = 0.25 min.
    module, recorder = _install(monkeypatch, battery_current=-24.0)
    voyage = _write_voyage(
        tmp_path,
        [_segment(1, throttle=1.0, solar_power=0.0)],
        initial_soc=0.05,
        filename="voyage_empty.json",
    )

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=1, in_parallel=2),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    assert recorder.x_axis == pytest.approx([0, 0, 0.25, 0.25, 1.0])
    assert recorder.battery_capacity == pytest.approx([6, 6, 0, 0, 0])


# ---------------------------------------------------------------------------
# Requirement 7.1 — segment sequencing
# ---------------------------------------------------------------------------


def test_multi_segment_order(monkeypatch, constants, circuit_config, voyage_config,
                             tmp_path):
    """Verify segments execute in order with correct throttle and solar settings."""
    # The Task 2 voyage fixture: 3 x 5 min at (0.8, 0.0), (0.0, 1.0), (0.5, 0.5).
    segments = voyage_config["segments"]

    # Battery current follows the segment settings, staying inside the 600 A-min
    # pack so no step splits and each minute is exactly one simulation.
    def current(modifications):
        return 10 * modifications["panel_power_setting"] - 10 * modifications[
            "throttle_setting"
        ]

    module, recorder = _install(monkeypatch, battery_current=current)
    voyage = _write_voyage(
        tmp_path, segments, initial_soc=voyage_config["initial_battery_soc"]
    )

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=10),
        voyage_config_loc=voyage,
        save_path=str(tmp_path / "voyage_out"),
        ngspice_available=True,
        constants=constants,
    )

    assert len(recorder.build_calls) == 15, "3 segments x 5 one-minute steps"
    throttles = [mod["throttle_setting"] for mod in recorder.modifications]
    panel_powers = [mod["panel_power_setting"] for mod in recorder.modifications]
    assert throttles == [0.8] * 5 + [0.0] * 5 + [0.5] * 5
    assert panel_powers == [0.0] * 5 + [1.0] * 5 + [0.5] * 5

    # Nothing else is modified: no segment declares a propeller load factor and
    # no boundary was hit, so no charge/discharge limit was pinned.
    assert all(
        set(mod) == {"panel_power_setting", "throttle_setting", "current_soc"}
        for mod in recorder.modifications
    )

    # -8 A-min per minute, then +10, then 0: 300 -> 260 -> 310 -> 310.
    assert recorder.battery_capacity[-1] == pytest.approx(310)
    assert recorder.x_axis[-1] == pytest.approx(15)
    assert recorder.graph_call["kwargs"]["save_path"] == str(tmp_path / "voyage_out")
    assert list(tmp_path.glob("*.png")) == [], "generate_graph is mocked"


# ---------------------------------------------------------------------------
# Requirement 7.5 — per-segment propeller load factor
# ---------------------------------------------------------------------------


def test_segment_propeller_load_factor_passed(monkeypatch, constants, circuit_config,
                                              tmp_path):
    """Verify a segment's propeller_load_factor is passed as a modification for that segment only."""
    module, recorder = _install(monkeypatch, battery_current=-1.0)
    voyage = _write_voyage(
        tmp_path,
        [
            _segment(2, throttle=0.8, solar_power=0.0),
            _segment(2, throttle=0.8, solar_power=0.0, propeller_load_factor=0.6),
        ],
    )

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=10),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    factors = [mod.get("propeller_load_factor") for mod in recorder.modifications]
    # Segment 1 omits the key entirely so the circuit config's own value stands;
    # segment 2 overrides it on every one of its steps.
    assert factors == [None, None, 0.6, 0.6]
    assert all(
        "propeller_load_factor" not in mod for mod in recorder.modifications[:2]
    )


# ---------------------------------------------------------------------------
# Requirements 7.6, 7.7 — abort on a failed solve
# ---------------------------------------------------------------------------


def test_abort_on_simulation_failure(monkeypatch, constants, circuit_config,
                                     tmp_path, capsys):
    """Verify voyage stops and generates partial graph when analysis is None."""
    # Steps 1 and 2 solve; the third returns None for the analysis.
    module, recorder = _install(monkeypatch, battery_current=-10.0, fail_at=2)
    voyage = _write_voyage(
        tmp_path,
        [_segment(5, throttle=0.8, solar_power=0.0), _segment(5, 0.0, 1.0)],
    )

    module.start_voyage(
        circuit_setup=_setup(circuit_config, capacity_ah=10),
        voyage_config_loc=voyage,
        save_path=None,
        ngspice_available=True,
        constants=constants,
    )

    # The failing step is simulated, then both the step loop and the segment
    # loop break: the second segment never starts.
    assert len(recorder.simulate_calls) == 3
    assert "Simulation Aborted" in capsys.readouterr().out

    # Graphs still come out, from the two completed steps only.
    graphed = recorder.graph_call
    assert graphed["x_axis"] == pytest.approx([0, 0, 1, 1, 2])
    assert len(graphed["results"]) == len(graphed["x_axis"])
    assert [entry["iteration"] for entry in graphed["results"]] == [0, 0, 0, 1, 1]
    assert recorder.battery_capacity == pytest.approx([300, 300, 290, 290, 280])


# ---------------------------------------------------------------------------
# Requirement 7.7 — step-function plot data
# ---------------------------------------------------------------------------


def test_step_up_prev_duplicates_entry(constants):
    """Verify step-function plot data correctly duplicated at boundaries."""
    from src.electrical_simulation.simulation_over_time import step_up_prev

    first = _result(0, battery_current=-10.0)
    second = _result(1, battery_current=-10.0)
    results = [first, second]
    time_range_min = [0, 1]
    battery_capacity_list = [300, 290]

    step_up_prev(results, time_range_min, battery_capacity_list)

    # The newest result is duplicated so the plotted trace holds its value...
    assert len(results) == 3
    assert results[2] == second
    assert results[2] is not second, "a copy, so later mutation cannot leak back"
    # ...while the timeline repeats the previous instant, giving a vertical edge.
    assert time_range_min == [0, 0, 1]
    # The capacity trace repeats the previous value, keeping its slope visible.
    assert battery_capacity_list == [300, 300, 290]
    # All three lists stay the same length, which the plotter relies on.
    assert len(results) == len(time_range_min) == len(battery_capacity_list)

    results[2]["summary"]["data"][0]["current"]["total_battery_input_current"] = 0.0
    assert (
        second["summary"]["data"][0]["current"]["total_battery_input_current"] == -10.0
    )
