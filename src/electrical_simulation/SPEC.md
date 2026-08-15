# Electrical Simulation Module (`src/electrical_simulation`)

## Purpose

SPICE-based electrical circuit simulation of the solar proa's power system. Models solar panels, MPPT charge controllers, batteries, and electric motor loads to analyse power flow, validate component sizing, and simulate voyage energy profiles.

## Status: Active Development

Core simulation pipeline is functional. See `todo.md` for planned fixes.

---

## Architecture

```
__main__.py              CLI entry point & orchestrator
├── circuit_constructor  Builds PySpice netlist from JSON config
├── pyspice_simulator    Executes NgSpice operating point analysis
├── parse_result         Extracts node voltages/branch currents → structured dict
├── result_checker       Validates results (Kirchhoff, component limits, motor physics)
├── result_saver         Serialises results to JSON
├── simulation_sweeper   Runs parameter sweeps (throttle, panel power)
├── simulation_over_time Multi-segment voyage simulation with SOC tracking
├── sweep_graph_generation Matplotlib graph output (PNG)
├── cable_sizing         Derives cable gauge from max-current simulation
└── components/
    ├── solar_panel_array  Solar panel PySpice model (series/parallel)
    ├── mppt               MPPT charge controller model
    ├── battery_array      Battery bank model (series/parallel, SOC)
    ├── load               Individual load with BLDC motor physics
    ├── load_array         Multi-load bus connection & current distribution
    ├── load_balancer      Virtual battery discharge limiter
    └── motor_model        BLDC motor physics (back-EMF, propeller coupling)
```

---

## Dependencies (Centralised Parameters)

All parameters are loaded at runtime from JSON — no hardcoded values.

| File | Purpose | Key Fields |
|------|---------|-----------|
| `constant/electrical/{boat}_circuit_setup.json` | Circuit topology per boat | `mppt_panel` (arrays, count, panel/MPPT choice), `load` (choice, throttle), `battery` (choice, series, parallel, SOC) |
| `constant/electrical/electrical_components.json` | Component specifications | `MPPT` (voltage/current limits, efficiency), `Panel` (power, voltage), `Battery` (voltage, capacity, charge/discharge limits), `Load` (power, voltage, motor physics) |
| `constant/electrical/constants.json` | Simulation constants | `GROUNDING_RESISTANCE`, `WIRE_RESISTANCE`, `EPSILON`, `ARRAY_DECODER_PATTERN`, tolerance values |
| `constant/electrical/voyage_setup.json` | Voyage segments | `segments[]` (duration_minutes, throttle, solar_power, propeller_load_factor) |
| `constant/boat/{boat}.json` | Boat physical params | `panels_longitudinal`, `panels_transversal`, `panels_per_string` → derived `in_series`, `in_parallel` for panel arrays |

### Dependency Graph

```
constant/boat/{boat}.json ──────────────────┐
constant/electrical/{boat}_circuit_setup.json ├──→ circuit_constructor → pyspice_simulator
constant/electrical/electrical_components.json ┘           │
constant/electrical/constants.json ─────────────────────── ┤
constant/electrical/voyage_setup.json ──────────── simulation_over_time
```

---

## CLI Usage

```bash
python -m src.electrical_simulation \
  --circuit constant/electrical/rp2_circuit_setup.json \
  --constants constant/electrical/constants.json \
  --components constant/electrical/electrical_components.json \
  --boat rp2 \
  --boat-params constant/boat/rp2.json \
  --voyage constant/electrical/voyage_setup.json \
  --output artifact/rp2.electrical_simulation \
  --simulation-type all
```

### Simulation Types

| Type | Description | Output |
|------|-------------|--------|
| `operating_point` | Single DC steady-state | `.operating_point.json` |
| `cable_sizing` | Max-current operating point for cable gauge | `.max_operating_point.json` |
| `sweep_throttle` | 0→100% throttle sweep (101 points) | `.sweep_throttle.*.png`, `.json` |
| `sweep_panel_power` | 100→1% panel power sweep (100 points) | `.sweep_panel_power.*.png`, `.json` |
| `voyage` | Multi-segment time simulation | `.voyage.*.png` |
| `all` | Run all of the above sequentially | All outputs |

### Makefile Integration

```makefile
make electrical-simulation BOAT=rp2 SIMULATION_TYPE=all
```

---

## Result Structure

Results are a nested dictionary with these top-level keys:

```
info            → metadata (name, date)
error           → critical violations (Kirchhoff's law, component limits)
warning         → operational restrictions (discharge limiting, ESC capping)
summary         → total MPPT output voltage/current, DC bus voltage
mppt_result     → per-array MPPT output voltage/current
battery_result  → per-cell voltage, charge/discharge current
solar_result    → per-array solar output voltage/current
panel_result    → per-panel voltage (usually not critical)
load_balancer   → virtual balancer voltage/current
load_result     → per-load voltage/current + motor_physics
l_array_result  → load array bus voltage
```

Each section follows: `{ keyword, array_count, data: [{ array_index, voltage: {}, current: {} }] }`

---

## Key Algorithms

### Motor Physics (BLDC Model)

When `motor_kv`, `motor_resistance` are specified in component config:
1. Compute back-EMF constant: `Ke = 1 / (motor_kv * 2π/60)`
2. Auto-derive propeller Kp so motor reaches rated current at full throttle
3. Solve propeller-motor equilibrium: motor torque = Kp_effective × ω²
4. ESC current limiting: cap winding current at `total_power / nominal_voltage`
5. Output: speed_rpm, efficiency, torque, power_mechanical, is_stalled, is_current_limited

Falls back to linear model (`power = throttle × total_power`) when physics constants absent.

### Voyage SOC Tracking

1. Simulate each segment at 1-minute intervals
2. Integrate battery current: `capacity += current × step_time`
3. Boundary handling: split time step at exact SOC=0 or SOC=1 boundary
4. Re-simulate with discharge/charge disabled for remaining interval

---

## Unit Testing Guidance

### Critical Invariants to Test

1. **Kirchhoff's Current Law**: `Σ MPPT_out - Σ battery_in - Σ load_current = 0` (within EPSILON)
2. **Power conservation**: Input solar power × efficiency ≈ output power + losses
3. **SOC bounds**: `0.0 ≤ SOC ≤ 1.0` at all voyage time steps
4. **Motor physics**: speed, torque, efficiency within physical bounds
5. **Current limiting**: load current ≤ battery max_discharge_current

### Suggested Test Structure

```
tests/
├── test_circuit_constructor.py    # Config loading, component resolution
├── test_motor_model.py            # BLDC equilibrium, current limiting, edge cases
├── test_result_checker.py         # Kirchhoff validation, warning generation
├── test_simulation_sweeper.py     # Sweep produces expected point count
├── test_voyage.py                 # SOC boundary splitting, segment transitions
└── test_cable_sizing.py           # Current → gauge mapping
```

### Test Fixtures

- Use `constant/electrical/rp2_circuit_setup.json` as reference config
- Mock NgSpice for unit tests (test circuit_constructor independently)
- Use known-good result JSON as regression fixtures

---

## Related Modules

| Module | Relationship |
|--------|-------------|
| `src/electrical_drawing` | Generates schematics of the same circuits (visual verification) |
| `src/power_cables` | Generates 3D cable geometry using same panel layout params |
| `src/parameter` | Computes derived parameters from boat JSON (upstream) |
| `src/design` | Generates FreeCAD geometry (upstream of power_cables) |

---

## Planned Work

- [ ] Multiple voyage configurations per boat
- [ ] Fix load current distribution: restrict total bus current first, then distribute proportionally
- [ ] Cable sizing implementation (currently stub)
