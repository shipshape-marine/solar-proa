---
layout: default
title: Roti Proa II - 9m Day Tourism Vessel
---

<div style="display: flex; align-items: center; gap: 2em; margin-bottom: 2em; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 400px; max-width: 600px;">
    <img src="{{ '/images/rp2construction.jpg' | relative_url }}" alt="Roti Proa II Construction" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <p style="font-size: 0.9em; color: #666; margin-top: 0.5em; font-style: italic;">Main hull of Roti Proa II under construction by Kim Tuck Huat Pte Ltd, 5/2/2026, Johor Bahru, Malaysia</p>
  </div>
</div>

[← Back to Home]({{ '/' | relative_url }})

---

## Design

Roti Proa II is a 9m daysailer that combines the basic body plan of a
Pacific proa with a fiberglass, PVC, aluminium materials to achieve a
configurable and scalable vessel concept.

**[View Full Design Specs →]({{ '/design_rp2.html' | relative_url }})**

**Hull Construction:**
- Professional fiberglass construction by Singapore boat maker
- Optimized for electric propulsion efficiency
- Delivery scheduled mid-February 2026

**Solar-Electric System:**
- 8 x 500W solar panels (4kW total)
- 48V electrical system
- Sponsored 4kW electric motor
- Integrated battery management

**Sailing Rig:**
- Dual aluminum stay-less masts
- Traditional tanja-inspired rectangular sails
- Shunting configuration for tropical conditions
- Backup propulsion capability

**Outrigger (Ama):**
- Aluminum crossbeam (aka) construction
- PVC pipe float construction  
- Optimized solar panel mounting
- Enhanced stability for passenger comfort

---

## Stability & Buoyancy

The vessel's stability has been analyzed using automated buoyancy equilibrium and GZ curve calculations.

**[View Full Stability & Buoyancy Analysis →]({{ '/stability_rp2.html' | relative_url }})**

| Parameter | Value | Description |
|-----------|-------|-------------|
| Draft | {{ site.data.rp2_beaching_buoyancy.equilibrium.z_offset_mm }} mm | Depth below waterline at equilibrium |
| Max righting arm | {{ site.data.rp2_beaching_gz.summary.max_gz_m | times: 100 | round: 0 }} cm | At {{ site.data.rp2_beaching_gz.summary.max_gz_angle_deg }}° heel |
| Capsize angle | {{ site.data.rp2_beaching_gz.summary.capsize_angle_deg }}° | Away from ama |
| Turtle angle | {{ site.data.rp2_beaching_gz.summary.turtle_angle_deg }}° | Towards ama |
| Roll period | {{ site.data.rp2_beaching_gz.natural_periods.roll_period_s }} s | Rough estimate |
| Pitch period | {{ site.data.rp2_beaching_gz.natural_periods.pitch_period_s }} s | Rough estimate |
| Heave period | {{ site.data.rp2_beaching_gz.natural_periods.heave_period_s }} s | Rough estimate |

---

## Structural Validation

The vessel's structural integrity has been validated under multiple load scenarios including static loads, wave impacts, wind forces, and crane operations. All tests pass with safety factors exceeding the required minimum of 2.0.

**[View Full Structural Safety Report →]({{ '/validation_rp2.html' | relative_url }})**

| Test | Safety Factor | Result |
|------|---------------|--------|
| Suspended ama (aka bending) | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.result }} |
| Aka point load (crew standing) | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.result }} |
| One end supported (spine bending) | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.result }} |
| Mast wind loading (25 knots) | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.result }} |
| Diagonal braces (lateral) | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.result }} |
| Wave slam (vertical) | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.result }} |
| Frontal wave slam | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.result }} |
| Sideways wave slam | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.result }} |
| Lifting sling (crane) | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.result }} |
| Gunwale loads | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.result }} |
| Ama lift wind speed | {{ site.data.rp2_beaching_validate_structure.tests[10].summary.ama_lift_windspeed_knots }} knots | INFO |

---

## Electrical Simulation

The electrical system is modelled as a solar panel–MPPT–battery–motor DC circuit. The simulation computes the steady-state operating point, sweeps throttle and solar power levels to map system limits, and runs a multi-segment voyage profile to evaluate battery endurance and discharge constraints under realistic conditions.

**[View Full Electrical Setup & Simulation Result →]({{ '/electrical_rp2.html' | relative_url }})**


## Project Status

**Current Phase:** Under Construction

**Completed:**
- ✅ Detailed CAD design and optimization
- ✅ Hull order placed with boat maker
- ✅ Outrigger structure in progress
- ✅ Electrical system design
- ✅ Component procurement

**Next Steps:**
- Hull delivery (February 2026)
- Final assembly (March-April 2026)
- Sea trials (May-June 2026)
- Commercial validation with partners (Q3 2026)

---

[← Back to Home]({{ '/' | relative_url }}) | [View RP1 →]({{ '/rp1.html' | relative_url }}) | [View RP3 →]({{ '/rp3.html' | relative_url }})
