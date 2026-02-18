---
layout: default
title: Roti Proa II - Electrical Simulation
---

[← Back to Roti Proa II Overview]({{ '/rp2.html' | relative_url }})

---

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