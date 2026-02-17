---
layout: default
title: Roti Proa II - Structural Safety Report
---

[← Back to Roti Proa II Overview]({{ '/rp2.html' | relative_url }})

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Suspended Ama (Aka Bending)](#1-suspended-ama-aka-bending)
3. [Aka Point Load (Crew Standing)](#2-aka-point-load-crew-standing)
4. [One End Supported (Spine Bending)](#3-one-end-supported-spine-bending)
5. [Mast Wind Loading](#4-mast-wind-loading)
6. [Diagonal Braces (Lateral Loading)](#5-diagonal-braces-lateral-loading)
7. [Wave Slam (Vertical)](#6-wave-slam-vertical)
8. [Frontal Wave Slam](#7-frontal-wave-slam)
9. [Sideways Wave Slam](#8-sideways-wave-slam)
10. [Lifting Sling (Crane Operations)](#9-lifting-sling-crane-operations)
11. [Gunwale Load Distribution](#10-gunwale-load-distribution)
12. [Ama Lift Wind Speed](#11-ama-lift-wind-speed-informational)
13. [Summary Safety Assessment](#summary-safety-assessment)

---

## Executive Summary

The RP2 structural validation suite analyzes the vessel under eleven load scenarios encompassing static loads, dynamic wave impacts, wind forces, and operational conditions. All structural tests pass with safety factors exceeding the required minimum of 2.0.

| Test | Description | Safety Factor | Result |
|------|-------------|---------------|--------|
| Suspended Ama | Aka cantilever bending | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.result }} |
| Aka Point Load | Crew standing on aka | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.result }} |
| One End Supported | Spine bending | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.result }} |
| Mast Wind Loading | 25-knot wind on sail | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.result }} |
| Diagonal Braces | Lateral loading (tilted) | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.result }} |
| Wave Slam (Vertical) | 3 m/s impact, 2.5× dynamic | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.result }} |
| Frontal Wave Slam | Fore-aft impact | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.result }} |
| Sideways Wave Slam | Lateral impact | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.result }} |
| Lifting Sling | V-sling crane lift | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.result }} |
| Gunwale Loads | Load distribution to hull | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.result }} |
| Ama Lift Wind Speed | Stability limit | {{ site.data.rp2_beaching_validate_structure.tests[10].summary.ama_lift_windspeed_knots }} knots | INFO |

---

## 1. Suspended Ama (Aka Bending)

### Scenario

The outrigger (ama) loses all buoyancy support—for example, when the boat is heeled such that the ama is lifted completely out of the water, or during transport on a trailer. The full weight of the outrigger structure hangs from the akas (crossbeams), which act as cantilevers extending from the vaka (main hull).

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/suspended_ama.png' | relative_url }}" alt="suspended ama" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

Each aka is modeled as a cantilever beam fixed at the vaka gunwale. The outrigger mass is divided into:
- **Tip loads**: Concentrated masses at the aka tips (ama ends, solar panel edges, pillar bases)
- **Distributed loads**: Mass spread along the aka length (solar panels, wiring, structural elements)

The bending moment at the vaka attachment is:

$$M = F_{tip} \times L + F_{distributed} \times \frac{L}{2}$$

where *L* is the cantilever length from vaka to pillar. Bending stress is calculated using beam theory:

$$\sigma = \frac{M}{S}$$

where *S* is the section modulus of the aka's rectangular hollow section (RHS).

### Assumptions

- Aka section: {{ site.data.rp2_beaching_validate_structure.tests[0].summary.aka_dimensions }}
- Material: 6061-T6 aluminum (yield strength 240 MPa)
- Four akas share the load equally
- Fixed support at vaka (conservative—actual connection has some compliance)
- Strong axis (101.6 mm height) resists vertical bending

### Results

| Parameter | Value |
|-----------|-------|
| Outrigger mass | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.outrigger_mass_kg }} kg |
| Cantilever length | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.cantilever_length_m }} m |
| Maximum bending stress | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.max_stress_mpa }} MPa |
| Maximum deflection | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.max_deflection_mm }} mm |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.safety_factor }}** |

---

## 2. Aka Point Load (Crew Standing)

### Scenario

During boarding, maintenance, or emergency situations, crew members may need to stand on the akas. This test validates the aka's capacity to support concentrated crew weight at the worst-case location (center of span).

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/aka_point_load.png' | relative_url }}" alt="aka point load" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

The aka is modeled as a simply supported beam with:
- Support at the vaka gunwale (inboard)
- Support at the pillar (outboard, at ama)

A point load at mid-span produces maximum bending moment:

$$M_{max} = \frac{P \times L}{4}$$

where *P* is the crew weight and *L* is the span between supports.

### Assumptions

- Crew mass: {{ site.data.rp2_beaching_validate_structure.tests[1].crew_mass_kg }} kg (approximately two people)
- Load position: center of span (worst case)
- Simply supported conditions (conservative for moment calculation)

### Results

| Parameter | Value |
|-----------|-------|
| Span (vaka to pillar) | {{ site.data.rp2_beaching_validate_structure.tests[1].geometry.span_mm | divided_by: 1000.0 | round: 2 }} m |
| Point load | {{ site.data.rp2_beaching_validate_structure.tests[1].loading.point_load_n | round: 0 }} N |
| Maximum bending stress | {{ site.data.rp2_beaching_validate_structure.tests[1].analysis.max_stress_mpa }} MPa |
| Maximum deflection | {{ site.data.rp2_beaching_validate_structure.tests[1].analysis.max_deflection_mm }} mm |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[1].summary.safety_factor }}** |

---

## 3. One End Supported (Spine Bending)

### Scenario

The ama is supported at one end only (e.g., resting on a beach or dock) while the other end hangs free. This creates bending in the spine (longitudinal beam connecting the ama sections) as the akas provide intermediate support of varying stiffness.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/one_end_supported.png' | relative_url }}" alt="one end supported" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

The ama is modeled as a continuous beam with:
- Fixed support at one end (beach/dock contact)
- Elastic supports at each aka location (aka flexibility modeled as springs)
- Distributed load from the outrigger structure

The aka spring stiffness is derived from cantilever beam deflection:

$$k_{aka} = \frac{3EI}{L^3}$$

A moment distribution analysis determines reactions at each support and the maximum bending moment in the spine.

### Assumptions

- Spine section: SHS 76.2×76.2×4.5 mm aluminum
- Four akas at equal spacing along the spine
- One end fully fixed (conservative)
- Aka stiffness calculated from cantilever properties

### Results

| Parameter | Value |
|-----------|-------|
| Spine length | {{ site.data.rp2_beaching_validate_structure.tests[2].geometry.spine_length_mm | divided_by: 1000.0 | round: 2 }} m |
| Total outrigger mass | {{ site.data.rp2_beaching_validate_structure.tests[2].ama_analysis.total_outrigger_mass_kg }} kg |
| Maximum spine stress | {{ site.data.rp2_beaching_validate_structure.tests[2].spine_analysis.max_stress_mpa }} MPa |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[2].summary.safety_factor }}** |

---

## 4. Mast Wind Loading

### Scenario

The mast experiences significant bending loads when sailing in strong winds. The sail force acts at the center of effort (CE), creating a moment about the mast partner (deck-level support).

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/mast_wind.png' | relative_url }}" alt="mast wind" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

Wind force on the sail is estimated using:

$$F = \frac{1}{2} \rho V^2 C_d A$$

where *ρ* is air density, *V* is wind speed, *C_d* is drag coefficient, and *A* is sail area. The mast is analyzed for:
- Bending stress at the partner
- Shear stress at the partner
- Combined axial-bending interaction (column buckling)
- Local buckling (D/t ratio check)

### Assumptions

- Wind speed: {{ site.data.rp2_beaching_validate_structure.tests[3].wind_speed_knots }} knots
- Sail perpendicular to wind (maximum force)
- Mast section: {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.mast_diameter_mm }} mm diameter × {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.mast_thickness_mm }} mm wall
- Material: 6061-T6 aluminum
- Unstayed mast (no shrouds or stays)

### Results

| Parameter | Value |
|-----------|-------|
| Sail area | {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.sail_area_m2 }} m² |
| Wind force | {{ site.data.rp2_beaching_validate_structure.tests[3].wind_force_n | round: 0 }} N |
| Bending stress at partner | {{ site.data.rp2_beaching_validate_structure.tests[3].checks.bending_at_partner.stress_mpa }} MPa |
| D/t ratio | {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.d_over_t }} (< 50 OK) |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[3].summary.safety_factor }}** |

---

## 5. Diagonal Braces (Lateral Loading)

### Scenario

When the boat is tilted (on its side during beaching, or inverted after a capsize), the outrigger weight creates lateral forces on the diagonal braces connecting the pillars to the akas. These braces must resist both compression and tension depending on orientation.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/diagonal_braces.png' | relative_url }}" alt="diagonal braces" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

The lateral force equals the outrigger weight when the boat is fully on its side:

$$F_{lateral} = m_{outrigger} \times g$$

This force is distributed among all diagonal braces. Each brace is checked for:
- **Compression**: Euler buckling and compressive yielding
- **Tension**: Tensile yielding

The critical mode is Euler buckling for slender compression members:

$$\sigma_{cr} = \frac{\pi^2 E}{(L/r)^2}$$

where *L/r* is the slenderness ratio.

### Assumptions

- Brace section: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.section }}
- Brace length: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.length_mm | round: 0 }} mm
- Brace angle: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.angle_deg }}° from horizontal
- Number of braces: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.num_braces }}
- Pin-ended connections (conservative for buckling)

### Results

| Parameter | Value |
|-----------|-------|
| Outrigger mass | {{ site.data.rp2_beaching_validate_structure.tests[4].loading.outrigger_mass_kg }} kg |
| Force per brace | {{ site.data.rp2_beaching_validate_structure.tests[4].compression_check.force_per_brace_n | round: 0 }} N |
| Slenderness ratio | {{ site.data.rp2_beaching_validate_structure.tests[4].compression_check.slenderness_ratio | round: 0 }} |
| Governing mode | {{ site.data.rp2_beaching_validate_structure.tests[4].compression_check.governing_mode }} |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[4].summary.min_safety_factor }}** |

---

## 6. Wave Slam (Vertical)

### Scenario

When sailing in waves, the ama can slam into the water surface with significant velocity, creating impulsive hydrodynamic loads. This test analyzes vertical wave slam—the ama impacting the water from above.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/wave_slam_vertical.png' | relative_url }}" alt="wave slam vertical" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

Slam pressure is estimated using the water hammer formula:

$$P = \frac{1}{2} \rho V^2 C_p$$

where *V* is impact velocity and *C_p* is a pressure coefficient. A dynamic amplification factor accounts for structural response to impulsive loading.

The load path is: **wave → pillars → diagonal braces → akas → vaka**

The aka is modeled as a propped cantilever with:
- Fixed support at vaka
- Elastic spring support at diagonal brace attachment

### Assumptions

- Impact velocity: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.impact_velocity_ms }} m/s
- Dynamic factor: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.dynamic_factor }}×
- Slam coefficient: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.slam_coefficient }}
- Effective ama area: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.effective_area_m2 }} m² (partial immersion)
- Braces provide elastic support to akas

### Results

| Parameter | Value |
|-----------|-------|
| Slam pressure | {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.slam_pressure_kpa }} kPa |
| Total slam force | {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.dynamic_slam_force_n | round: 0 }} N |
| Aka stress | {{ site.data.rp2_beaching_validate_structure.tests[5].checks.aka.combined_stress_mpa }} MPa (SF={{ site.data.rp2_beaching_validate_structure.tests[5].checks.aka.safety_factor }}) |
| Brace stress | {{ site.data.rp2_beaching_validate_structure.tests[5].checks.diagonal_braces.compressive_stress_mpa }} MPa (SF={{ site.data.rp2_beaching_validate_structure.tests[5].checks.diagonal_braces.safety_factor }}) |
| Spine stress | {{ site.data.rp2_beaching_validate_structure.tests[5].checks.spine.max_stress_mpa }} MPa (SF={{ site.data.rp2_beaching_validate_structure.tests[5].checks.spine.safety_factor }}) |
| **Governing Component** | **{{ site.data.rp2_beaching_validate_structure.tests[5].summary.governing_component }}** |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[5].summary.min_safety_factor }}** |

---

## 7. Frontal Wave Slam

### Scenario

The ama encounters a wave head-on, creating a fore-aft impact force. This load is resisted by the X-shaped cross-braces between neighboring pillars.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/frontal_wave_slam.png' | relative_url }}" alt="wave slam frontal" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

Frontal slam force is calculated from the ama's cross-sectional area. The X-braces work as a tension-only system: when loaded, the compression diagonal buckles (due to extreme slenderness), and the tension diagonal carries the full load.

Brace slenderness ratio determines behavior:

$$\lambda = \frac{L}{r} > 100 \implies \text{tension-only behavior}$$

### Assumptions

- Ama frontal area: {{ site.data.rp2_beaching_validate_structure.tests[6].frontal_slam.frontal_area_m2 }} m² (circular cross-section)
- Cross-brace diameter: {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.geometry.brace_diameter_mm }} mm (solid rod)
- Brace length: {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.geometry.brace_length_mm | round: 0 }} mm
- Number of X-brace pairs: {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.geometry.num_x_brace_pairs }}
- Slam coefficient: {{ site.data.rp2_beaching_validate_structure.tests[6].frontal_slam.slam_coefficient }} (blunt body)

### Results

| Parameter | Value |
|-----------|-------|
| Frontal slam force | {{ site.data.rp2_beaching_validate_structure.tests[6].frontal_slam.dynamic_slam_force_n | round: 0 }} N |
| Slenderness ratio | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.slenderness_ratio | round: 0 }} |
| Mode | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.governing_mode }} |
| Tension per brace | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.tension_force_per_brace_n | round: 0 }} N |
| Stress | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.stress_mpa }} MPa |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[6].summary.min_safety_factor }}** |

---

## 8. Sideways Wave Slam

### Scenario

A wave strikes the ama from the side (athwartships), creating lateral forces. The diagonal pillar braces resist this load in compression.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/sideways_wave_slam.png' | relative_url }}" alt="wave slam sideways" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

The lateral slam force is calculated from the ama's projected side area (length × diameter). The diagonal braces take the horizontal component of this force.

### Assumptions

- Same slam parameters as vertical wave slam
- Diagonal braces at 45° take horizontal load
- Buckling governs for compression braces

### Results

| Parameter | Value |
|-----------|-------|
| Side slam force | {{ site.data.rp2_beaching_validate_structure.tests[7].sideways_slam.dynamic_slam_force_n | round: 0 }} N |
| Force per brace | {{ site.data.rp2_beaching_validate_structure.tests[7].checks.diagonal_braces.axial_force_per_brace_n | round: 0 }} N |
| Euler buckling load | {{ site.data.rp2_beaching_validate_structure.tests[7].checks.diagonal_braces.euler_buckling_load_n | round: 0 }} N |
| **Safety Factor** | **{{ site.data.rp2_beaching_validate_structure.tests[7].summary.min_safety_factor }}** |

---

## 9. Lifting Sling (Crane Operations)

### Scenario

The boat is lifted by crane for launch, haul-out, or transport. A V-sling configuration uses 4 hooks, each connected by two ropes to neighboring akas, distributing the load across all structural elements.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/lifting_sling.png' | relative_url }}" alt="lifting sling" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

The V-sling creates 8 attachment points. Each rope carries a fraction of the vertical load, with increased tension due to the V-angle:

$$T = \frac{F_{vertical}}{\cos(\theta)}$$

Checks include:
- Aka bending (all 4 akas participate)
- Local stress at sling attachment points
- Rope/sling tension capacity
- Global boat bending between supports

### Assumptions

- Total boat mass: {{ site.data.rp2_beaching_validate_structure.tests[8].summary.total_mass_kg }} kg
- V-angle from vertical: {{ site.data.rp2_beaching_validate_structure.tests[8].sling_geometry.v_angle_deg }}°
- Sling type: 50mm polyester flat sling (WLL 2000 kg)
- Aka spacing: {{ site.data.rp2_beaching_validate_structure.tests[8].sling_geometry.aka_spacing_m }} m

### Results

| Component | Stress/Load | Safety Factor |
|-----------|------------|---------------|
| Aka bending | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.aka_bending.max_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.aka_bending.safety_factor }} |
| Sling attachment | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.sling_point.combined_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.sling_point.safety_factor }} |
| Rope tension | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.rope_tension.rope_tension_n | round: 0 }} N | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.rope_tension.safety_factor }} |
| Global bending | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.global_bending.max_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.global_bending.safety_factor }} |
| **Governing** | **{{ site.data.rp2_beaching_validate_structure.tests[8].summary.governing_component }}** | **{{ site.data.rp2_beaching_validate_structure.tests[8].summary.min_safety_factor }}** |

---

## 10. Gunwale Load Distribution

### Scenario

The akas transfer all outrigger loads to the vaka through the gunwales. This test validates that the wooden gunwales (3" × 2", fiberglass-bonded to the hull) can carry and distribute the concentrated aka loads.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/gunwale_loads.png' | relative_url }}" alt="gunwale loads" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

The gunwale is modeled as a beam on elastic foundation. The characteristic length over which load spreads is:

$$\lambda = \left(\frac{4EI}{k}\right)^{0.25}$$

where *k* is the foundation stiffness (hull skin supporting the gunwale).

Checks include:
- Gunwale bending stress
- Bearing stress (wood perpendicular to grain)
- Bond shear (fiberglass joint to hull)

### Assumptions

- Gunwale section: {{ site.data.rp2_beaching_validate_structure.tests[9].gunwale_section.width_mm | round: 1 }} × {{ site.data.rp2_beaching_validate_structure.tests[9].gunwale_section.height_mm }} mm
- Material: Douglas fir or similar (allowable bending 50 MPa, bearing 10 MPa)
- Fiberglass bond allowable shear: 5 MPa
- Design load: wave slam (governs over static suspended ama)

### Results

| Check | Stress | Allowable | Safety Factor |
|-------|--------|-----------|---------------|
| Gunwale bending | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bending.bending_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bending.allowable_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bending.safety_factor }} |
| Bearing (perp. grain) | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bearing.bearing_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bearing.allowable_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bearing.safety_factor }} |
| Bond shear | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bond_shear.shear_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bond_shear.allowable_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bond_shear.safety_factor }} |

**Load Distribution**: Aka spacing ({{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.aka_spacing_mm | round: 0 }} mm) is {{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.spacing_ratio }}× the distribution length ({{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.distribution_length_mm | round: 0 }} mm), so loads are **{{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.interaction }}**.

---

## 11. Ama Lift Wind Speed (Informational)

### Scenario

This informational calculation determines the wind speed at which the heeling moment (wind from the ama side) equals the maximum righting moment, causing the ama to lift clear of the water.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/ama_lift_wind.png' | relative_url }}" alt="ama lift wind speed" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Method

The heeling moment from wind force is:

$$M_{heel} = F_{wind} \times h_{CE}$$

where *h_CE* is the height of the sail's center of effort above the heeling axis. This is compared against the maximum righting moment from the GZ curve analysis.

### Results

| Parameter | Value |
|-----------|-------|
| Total sail area | {{ site.data.rp2_beaching_validate_structure.tests[10].sail_geometry.total_sail_area_m2 }} m² |
| CE height | {{ site.data.rp2_beaching_validate_structure.tests[10].sail_geometry.ce_height_m }} m |
| Max righting moment | {{ site.data.rp2_beaching_validate_structure.tests[10].stability.max_righting_moment_nm | round: 0 }} N·m |
| **Ama lift wind speed** | **{{ site.data.rp2_beaching_validate_structure.tests[10].summary.ama_lift_windspeed_knots }} knots** |

*Note: This is the theoretical wind speed with full sail and no crew weight adjustment. In practice, crew can move to windward and sails can be reefed.*

---

## Summary Safety Assessment

### Overall Structural Integrity

The Roti Proa II structural design **passes all validation tests** with safety factors exceeding the required minimum of 2.0. The structure demonstrates adequate strength and stiffness for:

- **Normal operations**: Sailing, motoring, anchoring, beaching
- **Dynamic events**: Wave slam impacts from multiple directions
- **Handling operations**: Crane lifting, trailer transport
- **Emergency scenarios**: Capsize, crew on crossbeams

### Critical Load Paths

1. **Outrigger to Vaka**: Loads transfer through akas → gunwales → hull
2. **Wave Impact**: Forces distribute through pillars → braces → akas
3. **Wind Loads**: Sail forces transfer through mast → partner → hull

### Recommendations

1. **Inspection Points**: Regularly inspect aka-gunwale connections, diagonal brace welds, and fiberglass bonds
2. **Lifting Operations**: Use the V-sling configuration with 4 hooks to neighboring akas
3. **Wave Slam Limits**: The 3 m/s impact velocity represents moderate conditions; avoid extreme wave encounters
4. **Wind Limits**: The mast is validated for 25 knots; reef sails in stronger conditions

### Validation Software

This report was generated automatically from the parametric CAD model using the `validate-structure` module. Source code: [github.com/shipshape-marine/solar-proa](https://github.com/shipshape-marine/solar-proa/tree/main/src/structural)

---

[← Back to RP2 Overview]({{ '/rp2.html' | relative_url }}) | [View Stability & Buoyancy Analysis →]({{ '/stability_rp2.html' | relative_url }})
