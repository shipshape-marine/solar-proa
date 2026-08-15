# Electrical Simulation Testing Plan

## Overview

Add a comprehensive test suite for the `electrical_simulation` module with:
- Unit tests (no NgSpice dependency)
- Integration tests (requires NgSpice)
- New Makefile targets: `make test-unit`, `make test-integration`, `make test`

---

## Component kwargs Reference

| Component | Required kwargs | Optional kwargs |
|---|---|---|
| `Battery_Array` | `battery_in_series`, `battery_in_parallel`, `battery_voltage` OR (`min_voltage` + `max_voltage`), `max_charge_current`, `max_discharge_current`, `capacity_ah` | `current_soc` (default 1.0), `choice` |
| `Solar_Array` | `in_series`, `in_parallel`, `voltage`, `calculated_power` | `solar_power` (used upstream to compute calculated_power) |
| `MPPT` | `max_input_voltage`, `max_input_current`, `max_output_voltage`, `max_output_current`, `efficiency` | — |
| `Load` | `load_name`, `nominal_voltage`, `total_power` | `throttle` (default 1.0), `motor_kv`, `motor_resistance`, `motor_no_load_current`, `propeller_kp`, `propeller_load_factor` |
| `Load_Balancer` | *(no kwargs)* | — |
| `Load_Array` | *(positional: circuit, components, constants, load_list)* | — |

## Component Descriptions

| Component | What it represents |
|---|---|
| `Solar_Array` | Voltage sources in series/parallel representing panels; provides current to MPPT input |
| `MPPT` | Current regulator converting solar input to DC bus output; limited by max_output_current; applies efficiency loss |
| `Battery_Array` | Voltage sources in series/parallel representing battery cells; provides DC bus reference voltage |
| `Load` | Behavioral current sink on DC bus; power demand from BLDC motor model or linear scaling (throttle x total_power) |
| `Load_Array` | Bus node connecting all loads; handles current distribution and discharge limiting |
| `Load_Balancer` | Behavioral current sink absorbing excess charge current when battery is full |

---

## Test Circuits

| Circuit Name | Panels | MPPTs | Batteries | Loads | Purpose |
|---|---|---|---|---|---|
| `charging_only_1panel` | 1x1 (1 array) | 1 | 1S1P | 0 | Pure charging, all solar to battery |
| `charging_only_2panel` | 1x1 (2 arrays) | 2 | 2S1P | 0 | Multi-array charging |
| `load_only_single` | 1x1 (solar_power=0) | 1 | 2S1P | 1 (linear) | Battery discharge only |
| `load_only_dual` | 1x1 (solar_power=0) | 1 | 2S1P | 2 (BLDC+linear) | Multi-load discharge, current distribution |
| `balanced_system` | 1x1 | 1 | 2S1P | 1 (BLDC) | Solar approx equals load, near equilibrium |
| `oversized_solar` | 1x1 (2 count) | 2 | 1S1P | 1 (linear, low throttle) | Excess solar triggers charge limiting |
| `high_load_system` | 1x1 | 1 | 1S1P (low discharge limit) | 1 (BLDC, high throttle) | Battery discharge limiting warning |

Test component values (simple round numbers for hand-calculation):
- **Test_Panel**: 100W, 20V
- **Test_MPPT**: max_output_current 10A, efficiency 0.9
- **Test_Battery**: 24V per cell, min 20V, max 28V, capacity 50Ah, charge/discharge limit 20A
- **Test_Battery_Low_Discharge**: same but max_discharge_current 5A
- **Test_Load_Linear**: 500W, 24V nominal (no motor physics)
- **Test_Load_BLDC**: 500W, 24V, motor_kv=100, motor_resistance=0.1, no_load_current=1.0

---

## Task Breakdown

### Task 1: Project test infrastructure setup

**Objective:** Set up pytest configuration, directory structure, conftest.py with shared fixtures, add pytest to requirements.txt.

**Implementation:**
- Create `tests/` directory at project root
- Create `tests/__init__.py` (empty)
- Create `tests/electrical_simulation/__init__.py` (empty)
- Create `pyproject.toml` with:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  markers = [
      "integration: requires NgSpice shared library (deselect with '-m not integration')",
  ]
  ```
- Create `tests/conftest.py` loading `constant/electrical/constants.json` as session-scoped fixture
- Create `tests/electrical_simulation/conftest.py` with fixtures loading test component specs and circuit configs from `tests/electrical_simulation/fixtures/`
- Add `pytest` and `pytest-mock` to `requirements.txt`

**Verify:** `pytest --collect-only` runs without errors.

---

### Task 2: Test fixture circuit configs

**Objective:** Create purpose-built JSON circuit configurations for testing.

**Implementation:**
- Create `tests/electrical_simulation/fixtures/` directory
- Create `test_components.json` with Test_Panel, Test_MPPT, Test_Battery, Test_Battery_Low_Discharge, Test_Load_Linear, Test_Load_BLDC
- Create circuit setup JSONs (one per test scenario from table above):
  - `charging_only_1panel.json`: 1 panel array (count=1), 1S1P battery, no loads
    - Expected: MPPT current = (100W x 0.9) / ~24V = 3.75A all into battery
  - `charging_only_2panel.json`: 1 panel array (count=2), 2S1P battery
    - Expected: ~2 x 3.75A charging
  - `load_only_single.json`: panel solar_power=0, 1 linear load at throttle=0.5
    - Expected: 250W / 48V = 5.2A from battery
  - `load_only_dual.json`: panel solar_power=0, 1 BLDC + 1 linear load
    - Expected: sum of both loads from battery
  - `balanced_system.json`: solar power approx equals load demand
    - Expected: battery current near 0
  - `oversized_solar.json`: 2 panel arrays, low-throttle load
    - Expected: load_balancer absorbs excess
  - `high_load_system.json`: 1 panel, battery with low discharge limit, high throttle
    - Expected: discharge warning
- Create `test_voyage_setup.json` (3 segments x 5 min):
  - Segment 1: throttle=0.8, solar=0 (discharge)
  - Segment 2: throttle=0, solar=1.0 (charge)
  - Segment 3: throttle=0.5, solar=0.5 (mixed)

**Verify:** All fixture files parse as valid JSON.

---

### Task 3: Unit tests — circuit constructor

**Objective:** Test circuit_constructor.py logic without NgSpice.

**File:** `tests/electrical_simulation/test_circuit_constructor.py`

**Tests:**
- `test_combine_config_resolves_panel_choice` — Verify panel choice merges component spec fields
- `test_combine_config_resolves_mppt_choice` — Verify MPPT choice resolves correctly
- `test_combine_config_resolves_battery_choice` — Verify battery choice resolves correctly
- `test_combine_config_resolves_load_choice` — Verify load choice resolves correctly
- `test_apply_boat_panel_config_overrides` — Verify in_series/in_parallel override from boat params
- `test_apply_boat_panel_config_noop_without_fields` — Verify no-op when boat_params lacks panel fields
- `test_modifications_throttle_single` — Verify throttle_setting modifies load throttle (single value)
- `test_modifications_throttle_list` — Verify throttle_setting as list assigns per-load
- `test_modifications_panel_power` — Verify panel_power_setting modifies calculated_power
- `test_modifications_soc` — Verify current_soc passed to battery
- `test_modifications_discharge_limit` — Verify max_discharge_current override
- `test_modifications_charge_limit` — Verify max_charge_current override
- `test_modifications_propeller_load_factor` — Verify propeller_load_factor passed to loads
- `test_component_object_keys` — Verify returned dict has battery_array, mppt, solar_array, load, l_array, load_balancer
- `test_error_on_voltage_mismatch` — Verify errors list populated on battery/MPPT mismatch

**Verify:** All pass with `pytest -m "not integration"`.

---

### Task 4: Unit tests — result checker

**Objective:** Test result_checker.py validation logic with synthetic data.

**File:** `tests/electrical_simulation/test_result_checker.py`

**Tests:**
- `test_kcl_balanced_no_error` — "Verify no KCL error when MPPT output equals battery input plus load current"
- `test_kcl_violated_generates_error` — "Verify KCL violation generates error when currents don't sum to zero"
- `test_overcharge_warning_when_balancer_active` — "Verify overcharge warning when load_balancer carries positive current"
- `test_overdischarge_warning_on_power_mismatch` — "Verify over-discharge warning when load receives less power than expected"
- `test_motor_physics_attached_for_bldc` — "Verify BLDC motor_physics dict attached to load result when motor model exists"
- `test_linear_model_fallback_attached` — "Verify linear model motor_physics attached when no motor model"

**Approach:** Build synthetic result dicts mimicking real structure. Mock component_object with `.get_motor_operating_point()`, `.power_rating()`, `.throttle_setting()`, `.get_efficiency()`, `.get_output_limit()`.

**Verify:** All pass without NgSpice.

---

### Task 5: Unit tests — parse_result and result_saver

**Objective:** Test result parsing and JSON serialization.

**Files:**
- `tests/electrical_simulation/test_parse_result.py`
- `tests/electrical_simulation/test_result_saver.py`

**Tests (parse_result):**
- `test_nodes_categorized_by_keyword` — "Verify node voltages placed in correct result section based on keyword match"
- `test_array_index_extraction` — "Verify array index correctly extracted from node name pattern arr{N}_"
- `test_battery_voltage_postprocess` — "Verify per-cell voltage computed as positive minus negative terminal"
- `test_unmatched_node_printed` — "Verify unmatched node names printed to stdout" (use capsys)
- `test_branch_current_categorization` — "Verify branch currents placed in correct section with v-prefix stripped"

**Tests (result_saver):**
- `test_saves_valid_json` — "Verify result dict saved as valid JSON with 4-space indent"
- `test_file_is_readable` — "Verify saved file can be loaded back and matches original"

**Approach:** Mock NgSpice analysis object with `.nodes` and `.branches` dicts. Each value has `.as_ndarray()` returning `np.array([float_value])`. Use `tmp_path` for file tests.

**Verify:** All pass without NgSpice.

---

### Task 6: Unit tests — simulation_sweeper logic

**Objective:** Test sweep iteration counts, parameter ranges, failure handling.

**File:** `tests/electrical_simulation/test_simulation_sweeper.py`

**Tests:**
- `test_throttle_sweep_101_iterations` — "Verify throttle sweep runs exactly 101 simulations from 0% to 100%"
- `test_throttle_sweep_sets_panel_power_zero` — "Verify throttle sweep fixes panel_power_setting=0 to isolate throttle effect"
- `test_panel_sweep_100_iterations` — "Verify panel power sweep runs 100 simulations from 100% down to 1%"
- `test_panel_sweep_sets_throttle_one` — "Verify panel sweep fixes throttle_setting=1.0 to isolate solar effect"
- `test_panel_sweep_stops_on_failure` — "Verify panel power sweep stops when simulation returns None analysis"
- `test_propeller_load_factor_passed_through` — "Verify propeller_load_factor override reaches modifications dict"
- `test_graph_called_with_correct_args` — "Verify generate_graph receives results list and correct x-axis"

**Approach:** Mock `build_circuit_from_json`, `begin_simulation`, and `generate_graph`. No NgSpice, no graph files.

**Verify:** Fast unit tests, all pass without NgSpice.

---

### Task 7: Unit tests — simulation_over_time (voyage) logic

**Objective:** Test voyage SOC tracking, boundary splitting, segment transitions.

**File:** `tests/electrical_simulation/test_voyage.py`

**Tests:**
- `test_soc_increases_during_charging` — "Verify SOC increases when battery input current is positive"
- `test_soc_decreases_during_discharge` — "Verify SOC decreases when battery input current is negative"
- `test_soc_clamped_at_one` — "Verify SOC does not exceed 1.0; step splits and max_charge_current set to 0"
- `test_soc_clamped_at_zero` — "Verify SOC does not go below 0.0; step splits and max_discharge_current set to 0"
- `test_boundary_split_time_calculation` — "Verify time-to-full/empty calculated correctly from current and remaining capacity"
- `test_multi_segment_order` — "Verify segments execute in order with correct throttle and solar settings"
- `test_abort_on_simulation_failure` — "Verify voyage stops and generates partial graph when analysis is None"
- `test_step_up_prev_duplicates_entry` — "Verify step-function plot data correctly duplicated at boundaries"

**Math verification:** Given capacity=100Amin, current=10A, time_to_full = (max - current) / current.

**Approach:** Mock `build_circuit_from_json` and `begin_simulation` to return controlled results with known battery currents.

**Verify:** All pass without NgSpice.

---

### Task 8: Integration tests — simple circuit operating points

**Objective:** Run real NgSpice simulations with test circuits, validate against hand-calculated values.

**File:** `tests/electrical_simulation/test_integration_circuits.py`

**Mark:** All tests with `@pytest.mark.integration`

**Shared helpers:**
```python
def assert_kcl(result, epsilon=1e-3):
    """Verify KCL: MPPT_out - battery_in - load_current = 0"""

def run_circuit(fixture_name, conftest_fixtures) -> dict:
    """Build and simulate a test circuit, return result dict."""
```

**Tests (each with descriptive docstring):**
- `test_charging_only_1panel`:
  > "Single panel charges battery with no load. Expected: MPPT output current approx (100W x 0.9) / ~24V = 3.75A. All current flows into battery."
- `test_charging_only_2panel`:
  > "Two independent panel arrays charge battery. Expected: Each MPPT approx 3.75A, total approx 7.5A into battery."
- `test_load_only_single`:
  > "Single linear load draws from battery with no solar. Expected: load current approx 250W / 48V = 5.2A from battery."
- `test_load_only_dual`:
  > "Two loads (BLDC + linear) share DC bus. Expected: total current = sum of individual demands."
- `test_balanced_system`:
  > "Solar input approximately equals load demand. Expected: battery current near zero."
- `test_oversized_solar`:
  > "Excess solar exceeds battery charge limit. Expected: load balancer absorbs excess, overcharge warning."
- `test_high_load_system`:
  > "Load demand exceeds battery discharge limit. Expected: load restricted, over-discharge warning."

**Tolerance:** 5% for current/power comparisons:
```python
expected_current = (panel_power * efficiency) / bus_voltage
actual_current = result["mppt_result"]["data"][0]["current"]["mppt_output"]
assert abs(actual_current - expected_current) / expected_current < 0.05
```

**Verify:** Requires NgSpice. Each test self-contained with clear docstrings.

---

### Task 9: Integration tests — sweep and voyage end-to-end

**Objective:** Run sweeps and voyage with test fixtures, validate physical invariants.

**File:** `tests/electrical_simulation/test_integration_sweep.py`

**Mark:** All with `@pytest.mark.integration`

**Tests:**
- `test_throttle_sweep_monotonic_power`:
  > "Sweep throttle 0-100% and verify power is monotonically non-decreasing."
- `test_throttle_sweep_zero_throttle_zero_load`:
  > "At throttle=0, load power should be approximately zero."
- `test_throttle_sweep_kcl_all_points`:
  > "Verify KCL holds at every point in the throttle sweep."
- `test_panel_sweep_decreasing_mppt_current`:
  > "As panel power decreases, MPPT output current should decrease."
- `test_voyage_soc_bounds`:
  > "Run 3-segment voyage, verify SOC stays within [0.0, 1.0] at all time steps."
- `test_voyage_discharge_segment`:
  > "During high-throttle/no-solar segment, SOC must decrease."
- `test_voyage_charge_segment`:
  > "During zero-throttle/full-solar segment, SOC must increase."

**Approach:** Use reduced sweep (11 points) or call loop logic directly for speed. Use `tmp_path` for outputs.

**Verify:** Requires NgSpice. Physical invariants hold across all points.

---

### Task 10: Add kwargs documentation to component source files

**Objective:** Add docstrings documenting required/optional kwargs to each component's `__init__`.

**Files to modify:**
- `src/electrical_simulation/components/battery_array.py` — Battery_Array.__init__
- `src/electrical_simulation/components/solar_panel_array.py` — Solar_Array.__init__
- `src/electrical_simulation/components/mppt.py` — MPPT.__init__
- `src/electrical_simulation/components/load.py` — Load.__init__
- `src/electrical_simulation/components/load_array.py` — Load_Array.__init__
- `src/electrical_simulation/components/load_balancer.py` — Load_Balancer.__init__

**Example (Battery_Array):**
```python
def __init__(self, circuit, components, constants=None, **kwargs):
    """
    Battery array component.

    Required kwargs:
        battery_in_series (int): Number of cells in series
        battery_in_parallel (int): Number of strings in parallel
        battery_voltage (float): Per-cell nominal voltage (V) — used if min/max not provided
        min_voltage (float): Per-cell min voltage (V) — used with max_voltage for SOC estimation
        max_voltage (float): Per-cell max voltage (V)
        max_charge_current (float): Max charge current per string (A)
        max_discharge_current (float): Max discharge current per string (A)
        capacity_ah (float): Per-string capacity (Ah) — used by voyage for SOC tracking

    Optional kwargs:
        current_soc (float): Current state of charge, 0.0-1.0 (default: 1.0)
        choice (str): Component name from electrical_components.json (resolved upstream)
    """
```

**Verify:** No behavioral change. Existing test_motor_model.py still passes.

---

### Task 11: Makefile targets and CI integration

**Objective:** Add make targets and optionally wire into CI.

**Add to Makefile:**
```makefile
# ==============================================================================
# TESTING
# ==============================================================================

.PHONY: test test-unit test-integration

test-unit:
	@echo "Running unit tests (no NgSpice required)..."
	@$(PYTHON) -m pytest tests/ -m "not integration" -v --tb=short
	@echo ""
	@echo "✓ Unit tests complete"

test-integration:
	@echo "Running integration tests (requires NgSpice)..."
	@$(PYTHON) -m pytest tests/ -m "integration" -v --tb=short
	@echo ""
	@echo "✓ Integration tests complete"

test:
	@echo "Running all tests..."
	@echo ""
	@$(MAKE) test-unit
	@echo ""
	@$(MAKE) test-integration
	@echo ""
	@echo "✓ All tests complete"
```

**Add to help target:**
```
@echo "  make test                   - Run all tests (unit first, then integration)"
@echo "  make test-unit              - Run unit tests only (no NgSpice needed)"
@echo "  make test-integration       - Run integration tests only (requires NgSpice)"
```

**Move existing test:** `src/electrical_simulation/components/test_motor_model.py` to `tests/electrical_simulation/test_motor_model.py` (update imports from relative to absolute).

**Optional CI step** in `.github/workflows/pages.yml` after "Install PySpice":
```yaml
- name: Run electrical simulation tests
  run: |
    make test
```

**Verify:** `make test-unit` works without NgSpice. `make test` shows unit results first, then integration.

---

## Validation Approach for Sweep/Voyage Tests

For simulations like sweep and voyage, use mathematical estimation:

1. **Power conservation:** Input solar power x efficiency = output power + losses
2. **KCL at every point:** Sum of currents at DC bus = 0 (within EPSILON)
3. **Monotonic relationships:** More throttle = more power (always)
4. **SOC integration:** capacity += current x time (exact math, verifiable)
5. **Boundary conditions:** SOC in [0, 1], current limited at boundaries

Tolerance of 5% accounts for wire resistances (~0.01 ohm) and grounding resistors (~1e-6 ohm) which introduce small deviations from ideal calculations.

---

## Execution Order

Tasks must be executed in sequence (1 through 11). Each builds on the previous:
- Task 1-2: Infrastructure and fixtures (no tests yet)
- Task 3-7: Unit tests (can run immediately, no NgSpice)
- Task 8-9: Integration tests (require NgSpice + fixtures from Task 2)
- Task 10: Documentation (no dependency)
- Task 11: Makefile wiring (depends on all tests existing)
