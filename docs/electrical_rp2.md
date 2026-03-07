---
layout: default
title: Roti Proa II - Electrical Simulation
---

[← Back to Roti Proa II Overview]({{ '/rp2.html' | relative_url }})

---

## Contents

- [Electrical System Overview](#electrical-system-overview)
- [Cable Sizing and Safety Analysis](#cable-sizing-and-safety-analysis)
- [Components](#components)
  - [Power Generation](#power-generation)
  - [Power Management](#power-management)
  - [Energy Storage](#energy-storage)
  - [Propulsion](#propulsion)
  - [Sensors and Monitoring](#sensors-and-monitoring)
  - [Safety Equipment](#safety-equipment)
- [Circuit Configuration](#circuit-configuration)
- [Operating Point](#operating-point)
- [Sweep: Throttle vs Electrical Response](#sweep-throttle-vs-electrical-response-no-solar)
- [Sweep: Panel Power vs Electrical Response](#sweep-panel-power-vs-electrical-response-full-throttle)
- [Voyage Simulation](#voyage-simulation)

---

## Electrical System Overview

<div style="max-width: 900px; margin: 2em auto;">
  <div style="margin-bottom: 2em;">
    <img src="{{ '/images/circuit_diagrams_temp/Sensor Reader V3.png' | relative_url }}" alt="Overall Electrical Layout" style="width: 100%; border: 1px solid #ddd; border-radius: 4px; background: #fff;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Overall Electrical System Layout</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/images/circuit_diagrams_temp/Sensor Reader V3-Microcontroller.png' | relative_url }}" alt="Microcontroller Sensor Reader" style="width: 100%; border: 1px solid #ddd; border-radius: 4px; background: #fff;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Microcontroller Unit for Sensor Reading</p>
  </div>
</div>

> **Note on Schematic Diagrams**: Will be replaced by a paramatised drawing using SchemDraw in the future

---

## Cable Sizing and Safety Analysis

Proper cable gauge selection is critical for electrical safety on a marine vessel. Using electrical simulation allows us to determine the appropriate wire gauges for different sections of the electrical system by analyzing current flow, voltage drop, and thermal characteristics under various operating conditions.

### Why Simulation Matters

1. **Current Capacity**: Each cable section must handle the maximum expected current without overheating. The simulation sweeps (throttle and panel power) reveal peak current values at different points in the circuit, allowing us to select cables rated for worst-case scenarios with appropriate safety margins.

2. **Voltage Drop**: Excessive voltage drop across long cable runs reduces system efficiency and can cause equipment malfunction. By simulating the full circuit, we can identify runs where voltage drop exceeds acceptable limits and upsize cables accordingly.

3. **Fault Current Analysis**: The simulation helps estimate short-circuit currents, which informs fuse and circuit breaker selection to protect both cables and equipment.

4. **Marine Environment Considerations**: Cables on vessels are subject to vibration, moisture, and temperature extremes. Simulation results are combined with derating factors for:
   - Ambient temperature (engine room vs. deck)
   - Cable bundling (multiple cables in conduit)
   - Installation method (free air vs. enclosed)

### Cable Sections to Analyze

| Section | Expected Current | Notes |
|---------|------------------|-------|
| Solar Panel → MPPT | Varies with irradiance | Short runs, high current at peak |
| MPPT → DC Bus | MPPT output current | Medium runs, regulated current |
| DC Bus → Battery | Charge/discharge current | High current, critical path |
| DC Bus → Motor Controller | Load current | Longest run, highest current |
| Sensor/Control Circuits | < 1A | Low power, signal integrity important |

The operating point and sweep simulations below provide the current values needed to select appropriate gauges using standard marine wire sizing tables (in accordance with ABYC E-11 and ISO 10133:2012).

> **Note on Regulatory Standards**: This vessel operates as an extra-low voltage system (not exceeding 50V AC or 120V DC), running at up to 60V DC only. Singapore's maritime electrical standards such as IEC 60092-354:2020 RLV are not followed due to prohibitively expensive procurement costs and limited applicability to extra-low voltage vessels. The [Electrical Installations Regulations](https://sso.agc.gov.sg/SL/EA2001-RG5) under Singapore's Electrical Act also do not explicitly address extra-low voltage systems. ISO 10133:2012 is referenced as the only publicly available edition, though it is one revision behind the current standard—the latest version is similarly cost-prohibitive to obtain. ABYC E-11 remains freely accessible and well-suited for small craft DC electrical systems.


---

## Components

*This section documents the key electrical components selected for the Roti Proa II electrical system and the rationale behind each choice.*

### Power Generation

{% assign total_panels = 0 %}
{% for entry in site.data.boat_rp2_circuit_setup.mppt_panel %}{% if entry[0] contains "config_" %}{% assign cfg = entry[1] %}
{% if cfg.count > 0 %}
{% assign panels_per_array = cfg.panel_info.in_series | times: cfg.panel_info.in_parallel %}
{% assign array_panels = panels_per_array | times: cfg.count %}
{% assign total_panels = total_panels | plus: array_panels %}
{% endif %}
{% endif %}{% endfor %}

The solar array consists of **{{ total_panels }} panels** configured across {{ site.data.rp2_electrical_simulation_operating_point.mppt_result.array_count }} MPPT arrays (panels in series × panels in parallel × array count).

{% for entry in site.data.boat_rp2_circuit_setup.mppt_panel %}{% if entry[0] contains "config_" %}{% assign cfg = entry[1] %}
{% if cfg.count == 0 %}{% continue %}{% endif %}
{% assign panel_choice = cfg.panel_info.choice %}
{% assign panel = site.data.components.Panel[panel_choice] %}

#### Panel: {{ panel_choice | replace: "_", " " }}

| Parameter | Value |
|-----------|-------|
| Model | {{ panel_choice | replace: "_", " " }} |
| Power Rating | {{ panel.power }} W |
| Voltage | {{ panel.voltage }} V |
| Panels in Series | {{ cfg.panel_info.in_series }} |
| Panels in Parallel | {{ cfg.panel_info.in_parallel }} |
| Arrays Using This Panel | {{ cfg.count }} |

{% endif %}{% endfor %}

### Power Management

{% assign mppt_count = 0 %}
{% for entry in site.data.boat_rp2_circuit_setup.mppt_panel %}{% if entry[0] contains "config_" %}{% assign cfg = entry[1] %}
{% if cfg.count > 0 %}
{% assign mppt_count = mppt_count | plus: cfg.count %}
{% endif %}
{% endif %}{% endfor %}

The power management system uses **{{ mppt_count }} MPPT charge controller(s)** to regulate solar input to the DC bus.

{% for entry in site.data.boat_rp2_circuit_setup.mppt_panel %}{% if entry[0] contains "config_" %}{% assign cfg = entry[1] %}
{% if cfg.count == 0 %}{% continue %}{% endif %}
{% assign mppt_choice = cfg.mppt_info.choice %}
{% assign mppt = site.data.components.MPPT[mppt_choice] %}

#### MPPT: {{ mppt_choice | replace: "_", " " }}

| Parameter | Value |
|-----------|-------|
| Model | {{ mppt_choice | replace: "_", " " }} |
| Max Input Voltage | {{ mppt.max_input_voltage }} V |
| Max Input Current | {{ mppt.max_input_current }} A |
| Max Output Voltage | {{ mppt.max_output_voltage }} V |
| Max Output Current | {{ mppt.max_output_current }} A |
| Efficiency | {{ mppt.efficiency | times: 100 }}% |
| Units in Use | {{ cfg.count }} |

{% endif %}{% endfor %}

### Energy Storage

{% assign bat_choice = site.data.boat_rp2_circuit_setup.battery.choice %}
{% assign bat = site.data.components.Battery[bat_choice] %}
{% assign bat_setup = site.data.boat_rp2_circuit_setup.battery %}
{% assign total_batteries = bat_setup.battery_in_series | times: bat_setup.battery_in_parallel %}
{% assign total_capacity = bat.capacity_ah | times: bat_setup.battery_in_parallel %}
{% assign total_energy = bat.battery_voltage | times: bat_setup.battery_in_series | times: total_capacity | divided_by: 1000.0 %}

The energy storage system uses **{{ total_batteries }} battery cells** ({{ bat_setup.battery_in_series }}S{{ bat_setup.battery_in_parallel }}P configuration) providing a total capacity of {{ total_capacity }} Ah.

#### Battery: {{ bat_choice }}

| Parameter | Value |
|-----------|-------|
| Chemistry | {{ bat_choice }} |
| Nominal Cell Voltage | {{ bat.battery_voltage }} V |
| Cell Voltage Range | {{ bat.min_voltage }} V – {{ bat.max_voltage }} V |
| Cell Capacity | {{ bat.capacity_ah }} Ah |
| Max Charge Current | {{ bat.max_charge_current }} A |
| Max Discharge Current | {{ bat.max_discharge_current }} A |
| Cells in Series | {{ bat_setup.battery_in_series }} |
| Cells in Parallel | {{ bat_setup.battery_in_parallel }} |
| System Voltage Range | {{ bat.min_voltage | times: bat_setup.battery_in_series }} V – {{ bat.max_voltage | times: bat_setup.battery_in_series }} V |
| Total Pack Capacity | {{ total_capacity }} Ah |

### Propulsion

{% assign load_count = 0 %}
{% assign total_power = 0 %}
{% for load_entry in site.data.boat_rp2_circuit_setup.load %}{% assign load_cfg = load_entry[1] %}{% assign load_choice = load_cfg.choice %}{% assign load_spec = site.data.components.Load[load_choice] %}
{% assign load_count = load_count | plus: 1 %}
{% assign total_power = total_power | plus: load_spec.total_power %}
{% endfor %}

The propulsion system consists of **{{ load_count }} motor(s)** with a combined maximum power of {{ total_power }} W.

{% for load_entry in site.data.boat_rp2_circuit_setup.load %}{% assign load_cfg = load_entry[1] %}{% assign load_choice = load_cfg.choice %}{% assign load_spec = site.data.components.Load[load_choice] %}

#### Motor: {{ load_choice | replace: "_", " " }}

| Parameter | Value |
|-----------|-------|
| Model | {{ load_choice | replace: "_", " " }} |
| Max Power | {{ load_spec.total_power }} W |
| Nominal Voltage | {{ load_spec.nominal_voltage }} V |

{% endfor %}

### Sensors and Monitoring

The vessel uses a microcontroller-based sensor reading system (shown in the circuit diagram [above](#electrical-system-overview)) for monitoring:

#### Current Sensors

**2× QNDBK1-21 Hall Effect Sensors**

| Parameter | Value |
|-----------|-------|
| Model | QNDBK1-21 |
| Current Rating | 100A (unidirectional) |
| Output Voltage | 5V |
| Quantity | 2 |

**Sensor Placement:**

| Sensor | Location | Measurement Purpose |
|--------|----------|---------------------|
| MPPT 1 | Output of MPPT arrays (DC bus solar input) | Total solar panel power input |
| MPPT 2 | Before load (output after MPPT arrays + battery positive terminal) | Current the load is using |

**Derived Calculations:**

| Calculation | Formula | Interpretation |
|-------------|---------|----------------|
| Battery Current | MPPT 1 − MPPT 2 | > 0: Battery charging · < 0: Battery discharging |
| Solar Input Current | MPPT 1 | Direct reading from solar array output |
| Load Current | MPPT 2 | Direct reading of current to propulsion/loads |

#### Monitoring Components

**Signal Chain:**

```
Hall Effect Sensors → ADS1115 (ADC) → I2C Level Shifter → ESP8266 (MCU) → Local Server (API)
```

| Component | Description |
|-----------|-------------|
| **ADS1115** | 16-bit analog-to-digital converter (15-bit effective precision for unidirectional sensor output). Converts hall effect sensor voltage signals to digital values. |
| **I2C Level Shifter** | Shifts I2C signal levels between the ADS1115 and ESP8266 for safe communication. |
| **ESP8266** | Microcontroller unit that reads ADC values via I2C and transmits data to the monitoring server via HTTP POST requests. |
| **Local Server** | Receives current data and calculates State of Charge (SoC) using coulomb counting. Provides pilot advisory interface. |

**State of Charge Calculation:**

The system calculates battery SoC using coulomb counting:

$$
\text{SoC}(t) = \text{SoC}(t_0) + \frac{1}{C_{\text{rated}}} \int_{t_0}^{t} I(\tau) \, d\tau
$$

Where:
- $\text{SoC}(t)$ = State of Charge at time $t$
- $\text{SoC}(t_0)$ = Initial State of Charge
- $C_{\text{rated}}$ = Rated battery capacity (Ah)
- $I(\tau)$ = Battery current (positive = charging, negative = discharging)

**Pilot Advisory System:**

The monitoring server provides real-time feedback to the pilot including:
- Current battery SoC percentage
- Estimated time to full charge (when solar input exceeds load)
- Estimated time to depletion (when load exceeds solar input)
- Throttle setting recommendations to maintain safe operating margins

### Safety Equipment

All fuses and circuit protection devices must be selected and placed in accordance with ABYC E-11 guidelines. Fuses should be installed as close to the power source as practical—within 180mm (7 inches) of the battery terminals for battery circuits, and at the source end of each branch circuit.

Cable sizing must be determined using the simulation results in the [Circuit Configuration](#circuit-configuration) and [Operating Point](#operating-point) sections, selecting gauges that:
1. Handle maximum expected current with appropriate safety margin
2. Maintain voltage drop below **3%** for critical circuits (propulsion, navigation)
3. Account for derating factors (ambient temperature, bundling, installation method)

<!-- Add specific fuse and breaker component details here -->

---

<br>

## Circuit Configuration

### Solar Panel & MPPT Setup

Configuration: **{{ site.data.rp2_electrical_simulation_operating_point.mppt_result.array_count }}× MPPT arrays** in parallel.

{% for entry in site.data.boat_rp2_circuit_setup.mppt_panel %}{% if entry[0] contains "config_" %}{% assign cfg = entry[1] %}
{% if cfg.count == 0 %}{% continue %}{% endif %}
{% assign panel_choice = cfg.panel_info.choice %}
{% assign panel = site.data.components.Panel[panel_choice] %}
{% assign mppt_choice = cfg.mppt_info.choice %}
{% assign mppt = site.data.components.MPPT[mppt_choice] %}

#### {{ entry[0] | replace: "_", " " | capitalize }}

| Parameter | Value |
|-----------|-------|
| Array Count | {{ cfg.count }} |
| Panel | {{ panel_choice | replace: "_", " " }} |
| Panel Power | {{ panel.power }} W |
| Panel Voltage | {{ panel.voltage }} V |
| Panels in Series | {{ cfg.panel_info.in_series }} |
| Panels in Parallel | {{ cfg.panel_info.in_parallel }} |
| Solar Power | {{ cfg.panel_info.solar_power | times: 100 }}% |
| MPPT | {{ mppt_choice | replace: "_", " " }} |
| MPPT Max Input Voltage | {{ mppt.max_input_voltage }} V |
| MPPT Max Input Current | {{ mppt.max_input_current }} A |
| MPPT Max Output Voltage | {{ mppt.max_output_voltage }} V |
| MPPT Max Output Current | {{ mppt.max_output_current }} A |
| MPPT Efficiency | {{ mppt.efficiency | times: 100 }}% |

{% endif %}{% endfor %}

### Battery Setup

{% assign bat_choice = site.data.boat_rp2_circuit_setup.battery.choice %}
{% assign bat = site.data.components.Battery[bat_choice] %}
{% assign bat_setup = site.data.boat_rp2_circuit_setup.battery %}

Battery chemistry: **{{ bat_choice }}**

| Parameter | Value |
|-----------|-------|
| Nominal Battery Voltage | {{ bat.battery_voltage }} V |
| Min Voltage | {{ bat.min_voltage }} V |
| Max Voltage | {{ bat.max_voltage }} V |
| Batteries in Series | {{ bat_setup.battery_in_series }} |
| Batteries in Parallel | {{ bat_setup.battery_in_parallel }} |
| System Voltage (series) | {{ bat.min_voltage | times: bat_setup.battery_in_series }} V – {{ bat.max_voltage | times: bat_setup.battery_in_series }} V |
| Max Charge Current | {{ bat.max_charge_current }} A |
| Max Discharge Current | {{ bat.max_discharge_current }} A |
| Capacity | {{ bat.capacity_ah }} Ah |
| Initial SOC | {{ bat_setup.current_soc | times: 100 }}% |

### Load Setup

{% for load_entry in site.data.boat_rp2_circuit_setup.load %}{% assign load_cfg = load_entry[1] %}{% assign load_choice = load_cfg.choice %}{% assign load_spec = site.data.components.Load[load_choice] %}

| Parameter | Value |
|-----------|-------|
| Motor | {{ load_choice | replace: "_", " " }} |
| Total Power | {{ load_spec.total_power }} W |
| Nominal Voltage | {{ load_spec.nominal_voltage }} V |

{% endfor %}

---

<br>

## Operating Point

Steady-state operating point based on the circuit setup configuration.

{% assign op = site.data.rp2_electrical_simulation_operating_point %}

### DC Bus Summary

| Parameter | Value |
|-----------|-------|
| DC Bus Voltage | {{ op.summary.data[0].voltage.total_dc_bus_voltage | round: 2 }} V |
| Total MPPT Output Current | {{ op.summary.data[0].current.total_mppt_output_current | round: 2 }} A |
| Battery Current (negative = discharging) | {{ op.summary.data[0].current.total_battery_input_current | round: 2 }} A |

### MPPT Outputs

| MPPT Array | Output Voltage (V) | Output Current (A) | Output Power (W) |
|------------|--------------------|--------------------|------------------|
{% for mppt in op.mppt_result.data %}| Array {{ mppt.array_index }} | {{ mppt.voltage.mppt_output | round: 2 }} | {{ mppt.current.mppt_output | round: 2 }} | {{ mppt.voltage.mppt_output | times: mppt.current.mppt_output | round: 0 }} |
{% endfor %}

### Solar Array Outputs

| Solar Array | Output Voltage (V) | Output Current (A) | Output Power (W) |
|-------------|--------------------|--------------------|------------------|
{% for solar in op.solar_result.data %}| Array {{ solar.array_index }} | {{ solar.voltage.solar_array_output | round: 2 }} | {{ solar.current.solar_array_output | round: 2 }} | {{ solar.voltage.solar_array_output | times: solar.current.solar_array_output | round: 0 }} |
{% endfor %}

### Battery State

| Parameter | Value |
|-----------|-------|
| Battery Current (per string) | {{ op.battery_result.data[0].current.p0_s0_battery | round: 2 }} A |
| Status | {% if op.battery_result.data[0].current.p0_s0_battery < 0 %}Disharging{% else %}Charging{% endif %} |

### Load

| Load | Voltage (V) | Current (A) | Power (W) |
|------|-------------|-------------|-----------|
{% for load in op.load_result.data %}{% for v in load.voltage %}{% assign load_name = v[0] %}{% assign load_v = v[1] %}{% assign load_i = load.current[load_name] %}| {{ load_name }} | {{ load_v | round: 2 }} | {{ load_i | round: 2 }} | {{ load_v | times: load_i | round: 0 }} |
{% endfor %}{% endfor %}

### Throttle Configuration

| Load | Throttle |
|------|----------|
{% for load_entry in site.data.boat_rp2_circuit_setup.load %}{% assign load_cfg = load_entry[1] %}| {{ load_cfg.choice | replace: "_", " " }} | {{ load_cfg.throttle | times: 100 }}% |
{% endfor %}

{% if op.error.data.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Errors ({{ op.error.data.size }})</strong> — these issues may cause damage to the system and must be resolved.
</div>

<details markdown="1">
<summary><strong>Operating Point Errors ({{ op.error.data.size }})</strong> - Click to show/hide</summary>

| Error Message |
|---------------|
{% for e in op.error.data %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if op.warning.data.size > 0 %}
<details markdown="1">
<summary><strong>Operating Point Warnings ({{ op.warning.data.size }})</strong> - Click to show/hide</summary>

| # | Warning |
|---|---------|
{% for w in op.warning.data %}{% for warning in w %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

{% if op.error.data.size == 0 and op.warning.data.size == 0 %}
> **✓** No errors or warnings at this operating point.
{% endif %}

---

<br> 

## Sweep: Throttle vs Electrical Response (No Solar)

Simulation sweeps throttle from 0% to 100% with no solar input, showing how the electrical system responds to varying motor load on battery power alone.

<div style="max-width: 800px; margin: 2em auto;">
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_throttle.Voltage vs Throttle Input (%).png' | relative_url }}" alt="Voltage vs Throttle" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Voltage vs Throttle Input</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_throttle.Current vs Throttle Input (%).png' | relative_url }}" alt="Current vs Throttle" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Current vs Throttle Input</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_throttle.Power vs Throttle Input (%).png' | relative_url }}" alt="Power vs Throttle" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Power vs Throttle Input</p>
  </div>
</div>

{% assign throttle_errors = site.data.rp2_electrical_simulation_sweep_throttle_sweep_simulation_errors %}
{% assign throttle_warnings = site.data.rp2_electrical_simulation_sweep_throttle_sweep_simulation_warnings %}

{% if throttle_errors.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Errors ({{ throttle_errors.size }})</strong> — these issues may cause damage to the system and must be resolved.
</div>

<details markdown="1">
<summary><strong>Throttle Sweep Errors ({{ throttle_errors.size }})</strong> - Click to show/hide</summary>

| Error Message |
|---------------|
{% for e in throttle_errors %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if throttle_warnings.size == 0 and throttle_errors.size == 0 %}
> **✓** No errors or warnings were generated during the throttle sweep.
{% elsif throttle_warnings.size > 0 %}
<details markdown="1">
<summary><strong>Throttle Sweep Warnings ({{ throttle_warnings.size }})</strong> - Click to show/hide</summary>

| Throttle Input | Warning |
|----------------|---------|
{% for w in throttle_warnings %}{% for warning in w.warnings %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

---

<br>

## Sweep: Panel Power vs Electrical Response (Full Throttle)

Simulation sweeps solar panel output from 0% to 100% at full throttle, showing how increasing solar contribution reduces battery discharge.

<div style="max-width: 800px; margin: 2em auto;">
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_panel_power.Voltage vs Panel Power (%).png' | relative_url }}" alt="Voltage vs Panel Power" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Voltage vs Panel Power</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_panel_power.Current vs Panel Power (%).png' | relative_url }}" alt="Current vs Panel Power" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Current vs Panel Power</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_panel_power.Power vs Panel Power (%).png' | relative_url }}" alt="Power vs Panel Power" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Power vs Panel Power</p>
  </div>
</div>

{% assign panel_errors = site.data.rp2_electrical_simulation_sweep_panel_power_sweep_simulation_errors %}
{% assign panel_warnings = site.data.rp2_electrical_simulation_sweep_panel_power_sweep_simulation_warnings %}

{% if panel_errors.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Errors ({{ panel_errors.size }})</strong> — these issues may cause damage to the system and must be resolved.
</div>

<details markdown="1">
<summary><strong>Panel Power Sweep Errors ({{ panel_errors.size }})</strong> - Click to show/hide</summary>

| Error Message |
|---------------|
{% for e in panel_errors %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if panel_warnings.size > 0 %}
<details markdown="1">
<summary><strong>Panel Power Sweep Warnings ({{ panel_warnings.size }})</strong> - Click to show/hide</summary>

At low solar power levels, the battery discharge current exceeds the configured maximum. The simulation automatically restricts motor throttle to protect the battery:

| Solar Power | Warning |
|-------------|---------|
{% for w in panel_warnings %}{% for warning in w.warnings %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

---

<br>

## Voyage Simulation

{% assign voyage = site.data.voyage_setup %}

### Voyage Profile: {{ voyage.voyage_info.name }}

Initial battery SOC: **{{ voyage.initial_battery_soc | times: 100 }}%**

| Segment | Duration | Throttle | Solar Power |
|---------|----------|----------|-------------|
{% for seg in voyage.segments %}| {{ seg.name }} | {{ seg.duration_minutes }} min | {{ seg.throttle | times: 100 }}% | {{ seg.solar_power | times: 100 }}% |
{% endfor %}

{% assign total_min = 0 %}{% for seg in voyage.segments %}{% assign total_min = total_min | plus: seg.duration_minutes %}{% endfor %}
**Total voyage duration: {{ total_min }} minutes ({{ total_min | divided_by: 60 }} hrs {{ total_min | modulo: 60 }} min)**

<div style="max-width: 800px; margin: 2em auto;">
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Voltage vs Time (minutes).png' | relative_url }}" alt="Voltage vs Time" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Voltage vs Time</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Current vs Time (minutes).png' | relative_url }}" alt="Current vs Time" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Current vs Time</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Power vs Time (minutes).png' | relative_url }}" alt="Power vs Time" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Power vs Time</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Battery Capacity vs Time (minutes).png' | relative_url }}" alt="Battery Capacity vs Time" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Battery Capacity vs Time</p>
  </div>
</div>

{% assign voyage_errors = site.data.rp2_electrical_simulation_voyage_sweep_simulation_errors %}
{% assign voyage_warnings = site.data.rp2_electrical_simulation_voyage_sweep_simulation_warnings %}

{% if voyage_errors.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Errors ({{ voyage_errors.size }})</strong> — these issues may cause damage to the system and must be resolved.
</div>

<details markdown="1">
<summary><strong>Voyage Errors ({{ voyage_errors.size }})</strong> - Click to show/hide</summary>

| Error Message |
|---------------|
{% for e in voyage_errors %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if voyage_warnings.size > 0 %}
<details markdown="1">
<summary><strong>Voyage Warnings ({{ voyage_warnings.size }})</strong> - Click to show/hide</summary>

During the voyage, the battery discharge limit is exceeded at several points due to high throttle with limited or no solar input. The motor throttle is automatically restricted:

| Time (min) | Warning |
|------------|---------|
{% for w in voyage_warnings %}{% for warning in w.warnings %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

---

[← Back to RP2 Overview]({{ '/rp2.html' | relative_url }}) | [View Design Specification →]({{ '/design_rp2.html' | relative_url }})