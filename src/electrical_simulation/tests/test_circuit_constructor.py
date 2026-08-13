"""Unit tests for circuit construction from JSON (spec Task 3).

Covers choice resolution (``combine_config_setup``), boat panel arrangement
overrides (``apply_boat_panel_config``), the ``modifications`` dict handled by
``build_circuit_from_json``, the shape of the returned ``component_object``, and
error reporting for incompatible battery/MPPT voltages.

No NgSpice: PySpice only builds a netlist in memory here, nothing is solved. All
``src`` imports happen inside the helpers below so collection stays green when
the simulation dependencies are unavailable.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 11.4
"""

import pytest


def _combine(config: dict, components: dict) -> dict:
    """Resolve component choices in place and return the config."""
    from src.electrical_simulation.__main__ import combine_config_setup

    combine_config_setup(config, components)
    return config


def _apply_boat_panel_config(config: dict, boat_params: dict) -> dict:
    """Apply boat panel arrangement to the circuit config in place."""
    from src.electrical_simulation.__main__ import apply_boat_panel_config

    apply_boat_panel_config(config, boat_params)
    return config


def _build(config: dict, constants: dict, modifications: dict = None):
    """Build a circuit from a resolved config; returns (circuit, objects, errors)."""
    from src.electrical_simulation.circuit_constructor import build_circuit_from_json

    return build_circuit_from_json(
        circuit_setup=config,
        modifications=modifications if modifications is not None else {},
        constants=constants,
    )


def _panel_info(config: dict, key: str = "config_1") -> dict:
    """Shorthand for the panel_info block of one mppt_panel config."""
    return config["mppt_panel"][key]["panel_info"]


# ---------------------------------------------------------------------------
# Requirement 1.2 — component choice resolution
# ---------------------------------------------------------------------------


def test_combine_config_resolves_panel_choice(circuit_config, test_components):
    """Verify panel choice merges the component spec fields into panel_info."""
    config = circuit_config("charging_only_1panel")
    panel = _panel_info(config)
    assert "power" not in panel, "fixture should not pre-supply the spec fields"

    _combine(config, test_components)

    panel = _panel_info(config)
    assert panel["choice"] == "Test_Panel"
    assert panel["power"] == 100
    assert panel["voltage"] == 20.0
    # Circuit-level arrangement is not part of the spec, so it survives the merge.
    assert panel["in_series"] == 1
    assert panel["in_parallel"] == 1
    assert panel["solar_power"] == 1.0


def test_combine_config_resolves_mppt_choice(circuit_config, test_components):
    """Verify MPPT choice resolves every rating the MPPT constructor reads."""
    config = circuit_config("charging_only_1panel")
    mppt = config["mppt_panel"]["config_1"]["mppt_info"]
    assert set(mppt) == {"choice"}, "fixture should only name the choice"

    _combine(config, test_components)

    mppt = config["mppt_panel"]["config_1"]["mppt_info"]
    assert mppt["max_input_voltage"] == 150.0
    assert mppt["max_input_current"] == 45.0
    assert mppt["max_output_voltage"] == 36.0
    assert mppt["max_output_current"] == 10.0
    assert mppt["efficiency"] == 0.9


def test_combine_config_resolves_battery_choice(circuit_config, test_components):
    """Verify battery choice merges spec fields and that the spec wins on collisions."""
    config = circuit_config("charging_only_1panel")
    # Circuit-level value deliberately collides with the component spec.
    config["battery"]["max_charge_current"] = 99

    _combine(config, test_components)

    battery = config["battery"]
    assert battery["min_voltage"] == 20.0
    assert battery["max_voltage"] == 28.0
    assert battery["capacity_ah"] == 50
    assert battery["max_discharge_current"] == 20
    # combine_config_setup does battery.update(spec), so the spec overwrites the
    # circuit-level value; per-circuit overrides only work via `modifications`.
    assert battery["max_charge_current"] == 20
    # Keys absent from the spec are preserved.
    assert battery["battery_in_series"] == 1
    assert battery["current_soc"] == 0.5


def test_combine_config_resolves_load_choice(circuit_config, test_components):
    """Verify each load choice resolves independently and keeps its own throttle."""
    config = circuit_config("load_only_dual")

    _combine(config, test_components)

    bldc = config["load"]["load_1"]
    assert bldc["total_power"] == 500
    assert bldc["nominal_voltage"] == 24.0
    assert bldc["motor_kv"] == 100
    assert bldc["motor_resistance"] == 0.1
    assert bldc["throttle"] == 0.5

    linear = config["load"]["load_2"]
    assert linear["total_power"] == 500
    assert "motor_kv" not in linear, "linear load must stay on the fallback model"
    assert linear["throttle"] == 0.5


# ---------------------------------------------------------------------------
# Requirement 1.3 — boat panel arrangement override
# ---------------------------------------------------------------------------


def test_apply_boat_panel_config_overrides(circuit_config, test_components):
    """Verify in_series/in_parallel come from boat params when the circuit omits them."""
    config = _combine(circuit_config("charging_only_1panel"), test_components)
    panel = _panel_info(config)
    panel.pop("in_series")
    panel.pop("in_parallel")

    _apply_boat_panel_config(
        config,
        {"panels_per_string": 2, "panels_longitudinal": 6, "panels_transversal": 3},
    )

    panel = _panel_info(config)
    assert panel["in_series"] == 2, "in_series comes from panels_per_string"
    assert panel["in_parallel"] == 2, "in_parallel is panels_longitudinal // panels_transversal"


@pytest.mark.xfail(
    raises=UnboundLocalError,
    reason=(
        "Implementation bug in apply_boat_panel_config: in_series/in_parallel are only "
        "bound inside the `boat_has_panel_config` branch, but both the override and the "
        "already-configured branches read them unconditionally. Boat params without the "
        "panel fields therefore raise UnboundLocalError instead of leaving the circuit "
        "config untouched. Not fixed here: Task 3 may not change src/."
    ),
)
def test_apply_boat_panel_config_noop_without_fields(circuit_config, test_components):
    """Verify the circuit panel arrangement is untouched when boat params lack panel fields."""
    config = _combine(circuit_config("charging_only_1panel"), test_components)

    _apply_boat_panel_config(config, {"hull_length": 6.0})

    panel = _panel_info(config)
    assert panel["in_series"] == 1
    assert panel["in_parallel"] == 1


# ---------------------------------------------------------------------------
# Requirement 1.4 — modifications applied before construction
# ---------------------------------------------------------------------------


def test_modifications_throttle_single(resolved_circuit_config, constants):
    """Verify a scalar throttle_setting is applied to every load."""
    config = resolved_circuit_config("load_only_dual")

    _, component_object, _ = _build(config, constants, {"throttle_setting": 0.75})

    assert [load.throttle_setting() for load in component_object["load"]] == [0.75, 0.75]


def test_modifications_throttle_list(resolved_circuit_config, constants):
    """Verify a list throttle_setting assigns one value per load, in config order."""
    config = resolved_circuit_config("load_only_dual")

    _, component_object, _ = _build(config, constants, {"throttle_setting": [0.2, 0.8]})

    loads = component_object["load"]
    assert [load.throttle_setting() for load in loads] == [0.2, 0.8]
    assert loads[0].name().endswith("Test_Load_BLDC")
    assert loads[1].name().endswith("Test_Load_Linear")


def test_modifications_panel_power(resolved_circuit_config, constants):
    """Verify panel_power_setting scales calculated_power and the panel current."""
    config = resolved_circuit_config("charging_only_1panel")

    _, component_object, _ = _build(config, constants, {"panel_power_setting": 0.5})

    panel_info = _panel_info(config)
    assert panel_info["calculated_power"] == pytest.approx(50.0), "100 W x 0.5"
    solar_array = component_object["solar_array"][0]
    assert solar_array.PANEL_CURRENT == pytest.approx(2.5), "50 W / 20 V"


def test_modifications_soc(resolved_circuit_config, constants):
    """Verify current_soc reaches the battery and shifts the interpolated cell voltage."""
    baseline = resolved_circuit_config("charging_only_1panel")
    _, baseline_objects, _ = _build(baseline, constants)
    assert baseline_objects["battery_array"].SOC == 0.5
    assert baseline_objects["battery_array"].BATTERY_VOLTAGE == pytest.approx(24.0)

    config = resolved_circuit_config("charging_only_1panel")
    _, component_object, _ = _build(config, constants, {"current_soc": 1.0})

    battery = component_object["battery_array"]
    assert battery.SOC == 1.0
    assert battery.BATTERY_VOLTAGE == pytest.approx(28.0), "min 20 V + (28-20) x 1.0"


def test_modifications_discharge_limit(resolved_circuit_config, constants):
    """Verify max_discharge_current overrides the resolved battery spec value."""
    config = resolved_circuit_config("charging_only_1panel")
    assert config["battery"]["max_discharge_current"] == 20

    _, component_object, _ = _build(config, constants, {"max_discharge_current": 7})

    assert component_object["battery_array"].get_discharge_limit() == 7
    assert config["battery"]["max_discharge_current"] == 20, "source config must not mutate"


def test_modifications_charge_limit(resolved_circuit_config, constants):
    """Verify max_charge_current overrides the resolved battery spec value."""
    config = resolved_circuit_config("charging_only_1panel")
    assert config["battery"]["max_charge_current"] == 20

    _, component_object, _ = _build(config, constants, {"max_charge_current": 3})

    assert component_object["battery_array"].get_charge_limit() == 3
    assert config["battery"]["max_charge_current"] == 20, "source config must not mutate"


def test_modifications_propeller_load_factor(resolved_circuit_config, constants):
    """Verify propeller_load_factor reaches the loads and their motor models."""
    config = resolved_circuit_config("load_only_dual")

    _, component_object, _ = _build(config, constants, {"propeller_load_factor": 0.4})

    for load_config in config["load"].values():
        assert load_config["propeller_load_factor"] == 0.4

    bldc, linear = component_object["load"]
    assert bldc.uses_motor_physics()
    assert bldc.motor_model.propeller.load_factor == pytest.approx(0.4)
    assert bldc.get_motor_operating_point().propeller_load_factor == pytest.approx(0.4)
    assert not linear.uses_motor_physics(), "linear load has no propeller to scale"


# ---------------------------------------------------------------------------
# Requirements 1.1, 1.5 — returned component object
# ---------------------------------------------------------------------------


def test_component_object_keys(resolved_circuit_config, constants):
    """Verify build returns every component handle, one pair per panel array count."""
    single = resolved_circuit_config("load_only_dual")
    _, component_object, _ = _build(single, constants)

    assert set(component_object) == {
        "battery_array",
        "mppt",
        "solar_array",
        "load",
        "l_array",
        "load_balancer",
    }
    assert len(component_object["mppt"]) == 1
    assert len(component_object["solar_array"]) == 1
    assert len(component_object["load"]) == 2

    # count = 2 must yield two independent MPPT/panel array instances (Req 1.5).
    multi = resolved_circuit_config("charging_only_2panel")
    _, multi_objects, _ = _build(multi, constants)
    assert len(multi_objects["mppt"]) == 2
    assert len(multi_objects["solar_array"]) == 2
    assert [array.array_number for array in multi_objects["solar_array"]] == [0, 1]
    assert multi_objects["load"] == [], "charging-only circuit defines no loads"


# ---------------------------------------------------------------------------
# Requirement 1.6 — error reporting
# ---------------------------------------------------------------------------


def test_error_on_voltage_mismatch(resolved_circuit_config, constants):
    """Verify a battery/MPPT voltage mismatch is reported as an error string, not raised."""
    config = resolved_circuit_config("charging_only_1panel")
    assert _build(config, constants)[2] == [], "baseline fixture must be error-free"

    mismatched = resolved_circuit_config("charging_only_1panel")
    # 4S at 24 V/cell = 96 V pack against a 36 V MPPT max output: far outside
    # MPPT_BATTERY_VOLTAGE_BUFFER.
    mismatched["battery"]["battery_in_series"] = 4

    _, component_object, errors = _build(mismatched, constants)

    assert len(errors) == 1
    assert "Mismatch between battery voltage" in errors[0]
    assert "96.0 V" in errors[0] and "36.0 V" in errors[0]
    # Construction continued despite the error.
    assert component_object["battery_array"].get_total_voltage() == pytest.approx(96.0)
