"""Schema validation for the electrical_simulation test fixtures (spec Task 2).

These tests keep the fixture JSONs honest: every file must parse, expose the
keys the production loaders read (``combine_config_setup``,
``build_circuit_from_json``, ``start_voyage``), and every component choice must
resolve against ``test_components.json``.

Unit level only: no circuit is built and NgSpice is never touched.

Validates: Requirements 1.1, 1.2, 1.5
"""

import json

import pytest

CIRCUIT_NAMES = [
    "charging_only_1panel",
    "charging_only_2panel",
    "load_only_single",
    "load_only_dual",
    "balanced_system",
    "oversized_solar",
    "high_load_system",
]

# Keys each resolved component config must expose, mirroring the kwargs the
# component constructors read.
PANEL_REQUIRED = ("in_series", "in_parallel", "voltage", "power")
MPPT_REQUIRED = (
    "max_input_voltage",
    "max_input_current",
    "max_output_voltage",
    "max_output_current",
    "efficiency",
)
BATTERY_REQUIRED = (
    "battery_in_series",
    "battery_in_parallel",
    "max_charge_current",
    "max_discharge_current",
    "capacity_ah",
)
LOAD_REQUIRED = ("total_power", "nominal_voltage")


def _specs(section: dict) -> dict:
    """Component specs in a section, skipping free-text entries like Description."""
    return {name: spec for name, spec in section.items() if isinstance(spec, dict)}


def test_all_fixture_files_parse_as_json(fixtures_dir):
    """Verify every JSON file in fixtures/ parses into a dict."""
    files = sorted(fixtures_dir.glob("*.json"))
    assert files, f"no fixture JSON files found in {fixtures_dir}"
    for path in files:
        with path.open(encoding="utf-8") as handle:
            assert isinstance(json.load(handle), dict), f"{path.name} is not a JSON object"


def test_expected_fixture_files_exist(fixtures_dir):
    """Verify the fixture set the conftest loaders and later tasks expect."""
    expected = {"test_components.json", "test_voyage_setup.json"}
    expected |= {f"{name}.json" for name in CIRCUIT_NAMES}
    present = {path.name for path in fixtures_dir.glob("*.json")}
    assert expected <= present, f"missing fixtures: {sorted(expected - present)}"


def test_components_has_all_sections(test_components):
    """Verify test_components.json mirrors the production section layout."""
    for section in ("MPPT", "Panel", "Battery", "Load"):
        assert section in test_components, f"missing section: {section}"
        assert _specs(test_components[section]), f"section {section} has no component specs"


def test_components_named_specs_present(test_components):
    """Verify the named test components from the plan are all defined."""
    assert "Test_Panel" in test_components["Panel"]
    assert "Test_MPPT" in test_components["MPPT"]
    for battery in ("Test_Battery", "Test_Battery_Low_Discharge", "Test_Battery_Low_Charge"):
        assert battery in test_components["Battery"], f"missing battery spec: {battery}"
    for load in ("Test_Load_Linear", "Test_Load_BLDC"):
        assert load in test_components["Load"], f"missing load spec: {load}"


def test_component_specs_expose_required_fields(test_components):
    """Verify each test component spec carries the kwargs its component reads."""
    for name, spec in _specs(test_components["Panel"]).items():
        for key in ("power", "voltage"):
            assert key in spec, f"Panel {name} missing {key}"

    for name, spec in _specs(test_components["MPPT"]).items():
        for key in MPPT_REQUIRED:
            assert key in spec, f"MPPT {name} missing {key}"

    for name, spec in _specs(test_components["Battery"]).items():
        for key in ("max_charge_current", "max_discharge_current", "capacity_ah"):
            assert key in spec, f"Battery {name} missing {key}"
        has_nominal = "battery_voltage" in spec
        has_range = "min_voltage" in spec and "max_voltage" in spec
        assert has_nominal or has_range, f"Battery {name} needs battery_voltage or min/max_voltage"

    for name, spec in _specs(test_components["Load"]).items():
        for key in LOAD_REQUIRED:
            assert key in spec, f"Load {name} missing {key}"


def test_bldc_load_has_motor_physics_constants(test_components):
    """Verify Test_Load_BLDC triggers the physics model and Test_Load_Linear does not."""
    bldc = test_components["Load"]["Test_Load_BLDC"]
    for key in ("motor_kv", "motor_resistance"):
        assert key in bldc, f"Test_Load_BLDC missing {key}"

    linear = test_components["Load"]["Test_Load_Linear"]
    assert "motor_kv" not in linear
    assert "motor_resistance" not in linear


@pytest.mark.parametrize("name", CIRCUIT_NAMES)
def test_circuit_setup_top_level_schema(circuit_config, name):
    """Verify each circuit setup exposes the keys build_circuit_from_json reads."""
    config = circuit_config(name)

    for key in ("mppt_panel", "load", "battery"):
        assert key in config, f"{name}: missing top-level key {key}"

    assert isinstance(config["load"], dict), f"{name}: load must be an object (may be empty)"
    assert isinstance(config["battery"], dict)

    mppt_panel = config["mppt_panel"]
    assert mppt_panel, f"{name}: mppt_panel must define at least one config"
    for key, entry in mppt_panel.items():
        assert key.startswith("config_"), f"{name}: {key} is ignored, keys must start with config_"
        assert isinstance(entry["count"], int) and entry["count"] >= 1
        assert "panel_info" in entry and "mppt_info" in entry


@pytest.mark.parametrize("name", CIRCUIT_NAMES)
def test_circuit_choices_resolve_against_test_components(circuit_config, test_components, name):
    """Verify every component choice names an entry in test_components.json."""
    config = circuit_config(name)

    for key, entry in config["mppt_panel"].items():
        panel_choice = entry["panel_info"]["choice"]
        mppt_choice = entry["mppt_info"]["choice"]
        assert panel_choice in test_components["Panel"], f"{name}/{key}: unknown panel {panel_choice}"
        assert mppt_choice in test_components["MPPT"], f"{name}/{key}: unknown MPPT {mppt_choice}"

    for key, load in config["load"].items():
        choice = load["choice"]
        assert choice in test_components["Load"], f"{name}/{key}: unknown load {choice}"

    battery_choice = config["battery"]["choice"]
    assert battery_choice in test_components["Battery"], f"{name}: unknown battery {battery_choice}"


@pytest.mark.parametrize("name", CIRCUIT_NAMES)
def test_resolved_circuit_supplies_component_kwargs(resolved_circuit_config, name):
    """Verify choice resolution yields every kwarg the components require."""
    config = resolved_circuit_config(name)

    for key, entry in config["mppt_panel"].items():
        panel_info = entry["panel_info"]
        for field in PANEL_REQUIRED:
            assert field in panel_info, f"{name}/{key}: panel_info missing {field}"
        for field in MPPT_REQUIRED:
            assert field in entry["mppt_info"], f"{name}/{key}: mppt_info missing {field}"

    battery = config["battery"]
    for field in BATTERY_REQUIRED:
        assert field in battery, f"{name}: battery missing {field}"

    for key, load in config["load"].items():
        for field in LOAD_REQUIRED:
            assert field in load, f"{name}/{key}: load missing {field}"
        assert "throttle" in load, f"{name}/{key}: load missing throttle"


@pytest.mark.parametrize("name", CIRCUIT_NAMES)
def test_resolved_battery_and_mppt_voltages_are_compatible(resolved_circuit_config, constants, name):
    """Verify fixture voltages stay inside MPPT_BATTERY_VOLTAGE_BUFFER.

    MPPT.setup_mppt reports a setup error when the battery pack voltage differs
    from the MPPT max output voltage by more than the buffer, so the fixtures
    must be sized to keep the error list empty.
    """
    config = resolved_circuit_config(name)
    battery = config["battery"]

    soc = battery.get("current_soc", 1.0)
    if battery.get("min_voltage") is not None and battery.get("max_voltage") is not None:
        cell_voltage = battery["min_voltage"] + (battery["max_voltage"] - battery["min_voltage"]) * soc
    else:
        cell_voltage = battery["battery_voltage"]
    pack_voltage = cell_voltage * battery["battery_in_series"]

    buffer_v = constants["MPPT_BATTERY_VOLTAGE_BUFFER"]
    for key, entry in config["mppt_panel"].items():
        mppt_output_v = entry["mppt_info"]["max_output_voltage"]
        assert abs(pack_voltage - mppt_output_v) <= buffer_v, (
            f"{name}/{key}: pack {pack_voltage} V vs MPPT max output {mppt_output_v} V "
            f"exceeds buffer {buffer_v} V"
        )


@pytest.mark.parametrize("name", CIRCUIT_NAMES)
def test_resolved_panel_current_within_mppt_input_limits(resolved_circuit_config, name):
    """Verify panel array voltage and current stay inside the MPPT input ratings."""
    config = resolved_circuit_config(name)

    for key, entry in config["mppt_panel"].items():
        panel = entry["panel_info"]
        mppt = entry["mppt_info"]
        array_voltage = panel["voltage"] * panel["in_series"]
        power = panel["power"] * panel.get("solar_power", 1.0)
        array_current = (power / panel["voltage"]) * panel["in_parallel"]

        assert array_voltage <= mppt["max_input_voltage"], f"{name}/{key}: panel voltage too high"
        assert array_current <= mppt["max_input_current"], f"{name}/{key}: panel current too high"


def test_voyage_config_schema(voyage_config):
    """Verify the voyage fixture exposes what start_voyage reads."""
    assert "voyage_info" in voyage_config
    assert "name" in voyage_config["voyage_info"]

    soc = voyage_config["initial_battery_soc"]
    assert 0.0 <= soc <= 1.0

    segments = voyage_config["segments"]
    assert len(segments) == 3, "plan calls for 3 segments"
    for index, segment in enumerate(segments):
        for key in ("duration_minutes", "throttle", "solar_power"):
            assert key in segment, f"segment {index} missing {key}"
        assert segment["duration_minutes"] == 5, f"segment {index} should run 5 minutes"
        assert 0.0 <= segment["throttle"] <= 1.0
        assert 0.0 <= segment["solar_power"] <= 1.0


def test_voyage_segments_cover_discharge_charge_and_mixed(voyage_config):
    """Verify the three segments exercise discharge, charge, and mixed conditions."""
    discharge, charge, mixed = voyage_config["segments"]

    assert discharge["throttle"] > 0.0 and discharge["solar_power"] == 0.0
    assert charge["throttle"] == 0.0 and charge["solar_power"] > 0.0
    assert mixed["throttle"] > 0.0 and mixed["solar_power"] > 0.0


def test_voyage_battery_capacity_fields_available(resolved_circuit_config):
    """Verify a resolved circuit exposes the capacity fields start_voyage integrates."""
    config = resolved_circuit_config("balanced_system")
    battery = config["battery"]
    assert battery["capacity_ah"] > 0
    assert battery["battery_in_parallel"] >= 1
