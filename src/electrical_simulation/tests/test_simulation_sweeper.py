"""Unit tests for the parameter sweep engine (spec Task 6).

Covers ``sweep_throttle`` and ``sweep_panel_power``: the iteration count and
value range of each sweep, the parameter each sweep pins so the other is
isolated, the propeller_load_factor override, the early stop when a panel power
simulation fails, and the arguments handed to ``generate_graph`` (results list,
x-axis, axis label, display choices, and the save path that drives the PNG and
warning/error JSON output).

No NgSpice, no circuit and no graph files: ``build_circuit_from_json``,
``begin_simulation`` and ``generate_graph`` are replaced on the
``simulation_sweeper`` module with a recorder that captures every call, so each
test observes exactly what the sweep loop asked for. All ``src`` imports happen
inside helpers so collection stays green when the simulation dependencies are
unavailable.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
"""

from copy import deepcopy

import pytest


# ---------------------------------------------------------------------------
# helpers — recorder standing in for circuit build, simulation and plotting
# ---------------------------------------------------------------------------


class _SweepRecorder:
    """Captures the sweep loop's calls; optionally fails from a given iteration.

    ``fail_at`` is the zero-based iteration index from which ``begin_simulation``
    returns ``None`` for the analysis object, which is how a real failed solve
    reports itself.
    """

    def __init__(self, fail_at: int = None):
        self.fail_at = fail_at
        self.build_calls = []
        self.simulate_calls = []
        self.results = []
        self.graph_calls = []

    # stand-in for circuit_constructor.build_circuit_from_json
    def build_circuit_from_json(self, circuit_setup=None, modifications=None,
                                constants=None, **kwargs):
        # Deep-copied: the sweeper reuses one dict per iteration and callers
        # downstream are free to mutate it.
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
        self.simulate_calls.append(
            {
                "circuit": circuit,
                "component_object": component_object,
                "errors": errors,
                "ngspice_available": ngspice_available,
            }
        )
        # Tagged so the order of the list handed to generate_graph is checkable.
        result = {"iteration": index}
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


def _install(monkeypatch, fail_at: int = None):
    """Patch the sweeper's three collaborators and return ``(module, recorder)``.

    The names are patched on ``simulation_sweeper`` itself because that is where
    they are bound by its ``from ... import`` statements.
    """
    from src.electrical_simulation import simulation_sweeper

    recorder = _SweepRecorder(fail_at=fail_at)
    monkeypatch.setattr(
        simulation_sweeper, "build_circuit_from_json", recorder.build_circuit_from_json
    )
    monkeypatch.setattr(
        simulation_sweeper, "begin_simulation", recorder.begin_simulation
    )
    monkeypatch.setattr(simulation_sweeper, "generate_graph", recorder.generate_graph)
    return simulation_sweeper, recorder


def _expected_throttle_range() -> list:
    """0.00 to 1.00 in 0.01 steps, as the requirement states it."""
    return [i / 100 for i in range(0, 101)]


def _expected_panel_range() -> list:
    """1.00 down to 0.01 in 0.01 steps, as the requirement states it."""
    return [i / 100 for i in range(100, 0, -1)]


# ---------------------------------------------------------------------------
# Requirement 6.1 — throttle sweep range and count
# ---------------------------------------------------------------------------


def test_throttle_sweep_101_iterations(monkeypatch, constants, circuit_config):
    """Verify throttle sweep runs exactly 101 simulations from 0% to 100%."""
    module, recorder = _install(monkeypatch)
    setup = circuit_config("load_only_single")

    module.sweep_throttle(setup, save_path=None, ngspice_available=True,
                          save_output=False, constants=constants)

    expected = _expected_throttle_range()
    assert len(recorder.build_calls) == 101
    assert len(recorder.simulate_calls) == 101
    throttles = [mod["throttle_setting"] for mod in recorder.modifications]
    assert throttles == pytest.approx(expected)
    assert throttles[0] == 0.0 and throttles[-1] == 1.0

    # Every iteration is graphed, and the x-axis mirrors the swept values.
    assert len(recorder.graph_call["results"]) == 101
    assert recorder.graph_call["x_axis"] == pytest.approx(expected)


def test_throttle_sweep_sets_panel_power_zero(monkeypatch, constants, circuit_config):
    """Verify throttle sweep fixes panel_power_setting=0 to isolate throttle effect."""
    module, recorder = _install(monkeypatch)

    module.sweep_throttle(circuit_config("load_only_single"), save_path=None,
                          ngspice_available=True, save_output=False,
                          constants=constants)

    assert all(mod["panel_power_setting"] == 0 for mod in recorder.modifications)
    # Nothing else is modified unless the caller asks for it.
    assert all(
        set(mod) == {"throttle_setting", "panel_power_setting"}
        for mod in recorder.modifications
    )
    # The unresolved circuit setup is handed through untouched, once per point.
    assert all(
        call["circuit_setup"] is recorder.build_calls[0]["circuit_setup"]
        for call in recorder.build_calls
    )


# ---------------------------------------------------------------------------
# Requirement 6.2 — panel power sweep range and count
# ---------------------------------------------------------------------------


def test_panel_sweep_100_iterations(monkeypatch, constants, circuit_config):
    """Verify panel power sweep runs 100 simulations from 100% down to 1%."""
    module, recorder = _install(monkeypatch)

    module.sweep_panel_power(circuit_config("balanced_system"), save_path=None,
                             ngspice_available=True, save_output=False,
                             constants=constants)

    expected = _expected_panel_range()
    assert len(recorder.build_calls) == 100
    panel_powers = [mod["panel_power_setting"] for mod in recorder.modifications]
    assert panel_powers == pytest.approx(expected)
    assert panel_powers[0] == 1.0 and panel_powers[-1] == pytest.approx(0.01)
    # Descending: the sweep walks the panel power down, never up.
    assert all(a > b for a, b in zip(panel_powers, panel_powers[1:]))

    assert len(recorder.graph_call["results"]) == 100
    assert recorder.graph_call["x_axis"] == pytest.approx(expected)


def test_panel_sweep_sets_throttle_one(monkeypatch, constants, circuit_config):
    """Verify panel sweep fixes throttle_setting=1.0 to isolate solar effect."""
    module, recorder = _install(monkeypatch)

    module.sweep_panel_power(circuit_config("balanced_system"), save_path=None,
                             ngspice_available=True, save_output=False,
                             constants=constants)

    assert all(mod["throttle_setting"] == 1.0 for mod in recorder.modifications)
    assert all(
        set(mod) == {"throttle_setting", "panel_power_setting"}
        for mod in recorder.modifications
    )


# ---------------------------------------------------------------------------
# Requirement 6.3 — stop the panel sweep at the failing point
# ---------------------------------------------------------------------------


def test_panel_sweep_stops_on_failure(monkeypatch, constants, circuit_config, capsys):
    """Verify panel power sweep stops when simulation returns None analysis."""
    # Iterations 0, 1, 2 (100%, 99%, 98%) succeed; iteration 3 (97%) fails.
    module, recorder = _install(monkeypatch, fail_at=3)

    module.sweep_panel_power(circuit_config("balanced_system"), save_path=None,
                             ngspice_available=True, save_output=False,
                             constants=constants)

    # The failing point is simulated but neither kept nor plotted.
    assert len(recorder.simulate_calls) == 4
    graphed = recorder.graph_call
    assert [entry["iteration"] for entry in graphed["results"]] == [0, 1, 2]
    assert graphed["x_axis"] == pytest.approx([1.0, 0.99, 0.98])
    # x-axis and results stay the same length, which the plotter relies on.
    assert len(graphed["x_axis"]) == len(graphed["results"])

    assert "Simulation failed at panel power setting: 97.00%" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Requirement 6.5 — propeller_load_factor override
# ---------------------------------------------------------------------------


def test_propeller_load_factor_passed_through(monkeypatch, constants, circuit_config):
    """Verify propeller_load_factor override reaches modifications dict."""
    module, recorder = _install(monkeypatch)

    module.sweep_throttle(circuit_config("load_only_single"), save_path=None,
                          ngspice_available=True, save_output=False,
                          constants=constants, propeller_load_factor=0.6)

    assert len(recorder.modifications) == 101
    assert all(mod["propeller_load_factor"] == 0.6 for mod in recorder.modifications)

    # Same override on the panel power sweep.
    module, recorder = _install(monkeypatch)
    module.sweep_panel_power(circuit_config("balanced_system"), save_path=None,
                             ngspice_available=True, save_output=False,
                             constants=constants, propeller_load_factor=0.25)

    assert len(recorder.modifications) == 100
    assert all(mod["propeller_load_factor"] == 0.25 for mod in recorder.modifications)

    # Omitted (or explicitly None) leaves the key out so the circuit config's own
    # value survives.
    module, recorder = _install(monkeypatch)
    module.sweep_throttle(circuit_config("load_only_single"), save_path=None,
                          ngspice_available=True, save_output=False,
                          constants=constants, propeller_load_factor=None)

    assert all("propeller_load_factor" not in mod for mod in recorder.modifications)


# ---------------------------------------------------------------------------
# Requirement 6.4 — graph and output arguments
# ---------------------------------------------------------------------------


def test_graph_called_with_correct_args(monkeypatch, constants, circuit_config,
                                        tmp_path):
    """Verify generate_graph receives results list and correct x-axis."""
    save_path = str(tmp_path / "sweep")

    module, recorder = _install(monkeypatch)
    module.sweep_throttle(circuit_config("load_only_single"), save_path=save_path,
                          ngspice_available=True, save_output=True,
                          constants=constants)

    call = recorder.graph_call
    # Results are the very dicts begin_simulation returned, in sweep order.
    assert call["results"] == recorder.results
    assert [entry["iteration"] for entry in call["results"]] == list(range(101))
    assert call["x_axis"] == pytest.approx(_expected_throttle_range())
    assert call["kwargs"]["x_label"] == "Throttle Input (%)"
    assert call["kwargs"]["voltage_display_choice"] == ["load_result", "battery_result"]
    assert call["kwargs"]["current_display_choice"] == [
        "solar_result", "load_result", "battery_result"
    ]
    assert call["kwargs"]["power_display_choice"] == ["load_result"]
    assert call["kwargs"]["constants"] is constants
    # save_output=True forwards the path, which is the prefix generate_graph
    # appends the PNG and warning/error JSON file names to.
    assert call["kwargs"]["save_path"] == save_path

    # The panel sweep plots the extra MPPT and solar traces.
    module, recorder = _install(monkeypatch)
    module.sweep_panel_power(circuit_config("balanced_system"), save_path=save_path,
                             ngspice_available=True, save_output=True,
                             constants=constants)

    call = recorder.graph_call
    assert call["x_axis"] == pytest.approx(_expected_panel_range())
    assert call["kwargs"]["x_label"] == "Panel Power (%)"
    assert call["kwargs"]["voltage_display_choice"] == [
        "mppt_result", "load_result", "battery_result"
    ]
    assert call["kwargs"]["current_display_choice"] == [
        "mppt_result", "solar_result", "load_result", "battery_result"
    ]
    assert call["kwargs"]["power_display_choice"] == ["load_result", "solar_result"]
    assert call["kwargs"]["save_path"] == save_path

    # save_output=False suppresses the path, so no PNG or JSON is written.
    module, recorder = _install(monkeypatch)
    module.sweep_throttle(circuit_config("load_only_single"), save_path=save_path,
                          ngspice_available=True, save_output=False,
                          constants=constants)

    assert recorder.graph_call["kwargs"]["save_path"] is None
    assert list(tmp_path.iterdir()) == [], "generate_graph is mocked: nothing on disk"
