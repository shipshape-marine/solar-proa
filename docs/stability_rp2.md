---
layout: default
title: Roti Proa II - Stability & Buoyancy Analysis
---

[← Back to Roti Proa II Overview]({{ '/rp2.html' | relative_url }})

---

## Buoyancy Analysis

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  <div>
    <img src="{{ '/renders/rp2.beaching.buoyancy_design.render.front.png' | relative_url }}" alt="Buoyancy equilibrium - front view" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Front view at equilibrium</p>
  </div>
  <div>
    <img src="{{ '/renders/rp2.beaching.buoyancy_design.render.right.png' | relative_url }}" alt="Buoyancy equilibrium - side view" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Side view at equilibrium</p>
  </div>
</div>

The buoyancy equilibrium is computed using Newton's method, iteratively adjusting the roll/pitch/z-offset of the boat until the center and amount of buoyancy match the center and amount of mass. The analysis uses the beaching configuration (no sails, rudders lifted).

### Equilibrium Position

| Parameter | Value |
|-----------|-------|
| Z-offset (draft) | {{ site.data.rp2_beaching_buoyancy.equilibrium.z_offset_mm }} mm |
| Pitch | {{ site.data.rp2_beaching_buoyancy.equilibrium.pitch_deg }}° |
| Roll | {{ site.data.rp2_beaching_buoyancy.equilibrium.roll_deg }}° |
| Iterations to converge | {{ site.data.rp2_beaching_buoyancy.iterations }} |

### Vaka (Main Hull)

| Parameter | Value |
|-----------|-------|
| Submerged volume | {{ site.data.rp2_beaching_buoyancy.vaka.submerged_volume_liters }} liters |
| Total volume | {{ site.data.rp2_beaching_buoyancy.vaka.total_volume_liters }} liters |
| Submerged percentage | {{ site.data.rp2_beaching_buoyancy.vaka.submerged_percent }}% |
| Z position (world) | {{ site.data.rp2_beaching_buoyancy.vaka.z_world_mm }} mm |

### Ama (Outrigger Float)

| Parameter | Value |
|-----------|-------|
| Submerged volume | {{ site.data.rp2_beaching_buoyancy.ama.submerged_volume_liters }} liters |
| Total volume | {{ site.data.rp2_beaching_buoyancy.ama.total_volume_liters }} liters |
| Submerged percentage | {{ site.data.rp2_beaching_buoyancy.ama.submerged_percent }}% |
| Z position (world) | {{ site.data.rp2_beaching_buoyancy.ama.z_world_mm }} mm |

### Centers of Mass and Buoyancy

| Point | X (mm) | Y (mm) | Z (mm) |
|-------|--------|--------|--------|
| Center of Gravity | {{ site.data.rp2_beaching_buoyancy.center_of_gravity_world.x }} | {{ site.data.rp2_beaching_buoyancy.center_of_gravity_world.y }} | {{ site.data.rp2_beaching_buoyancy.center_of_gravity_world.z }} |
| Center of Buoyancy | {{ site.data.rp2_beaching_buoyancy.center_of_buoyancy.x }} | {{ site.data.rp2_beaching_buoyancy.center_of_buoyancy.y }} | {{ site.data.rp2_beaching_buoyancy.center_of_buoyancy.z }} |

See [implementation](https://github.com/shipshape-marine/shipshape/blob/main/src/shipshape/buoyancy/__main__.py).

---

## Stability Analysis (GZ Curve)

The GZ curve (righting arm curve) shows how the boat's stability varies with heel angle. For each heel angle, we compute the equilibrium waterline (where buoyancy equals weight) and measure the horizontal distance between the center of buoyancy (CoB) and center of gravity (CoG). This distance—the righting arm GZ—multiplied by displacement gives the righting moment that returns the boat to equilibrium.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/renders/rp2.beaching.gz.png' | relative_url }}" alt="GZ Curve" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Asymmetric Stability Characteristics

As a proa with an outrigger (ama), this vessel has asymmetric stability:

**Towards ama (positive heel):** The ama provides substantial buoyancy leverage when submerged.

| Parameter | Value |
|-----------|-------|
| Maximum righting arm | {{ site.data.rp2_beaching_gz.summary.max_gz_m | times: 100 | round: 0 }} cm |
| Angle of maximum GZ | {{ site.data.rp2_beaching_gz.summary.max_gz_angle_deg }}° |
| Turtle angle | {{ site.data.rp2_beaching_gz.summary.turtle_angle_deg }}° |

**Away from ama (negative heel):** Stability comes from the elevated ama's weight acting as counterweight.

| Parameter | Value |
|-----------|-------|
| Capsize angle | {{ site.data.rp2_beaching_gz.summary.capsize_angle_deg }}° |
| Ama engagement angle | {{ site.data.rp2_beaching_gz.summary.ama_engagement_angle_deg }}° |
| Range of positive stability | {{ site.data.rp2_beaching_gz.summary.range_of_positive_stability_deg }}° |

### Operating Envelope

Traditionally, proas are sailed with the ama to windward. The wind force heels the boat away from the ama, lifting it (partially or even completely) out of the water to reduce drag ("flying the ama"). The operating envelope is typically -5° to -20° heel in that case, well within the stable region.

A _solar_ proa should be able to sail well also with the ama to leeward, to keep the sails from casting a shadow on the solar panels. At a heeling angle of around 4°, the ama will be fully submerged and cause maximum drag but still induce a significant righting moment until the turtle angle is reached.

---

## Natural Periods (Seakeeping)

The vessel's motion in waves is characterized by natural periods for roll, pitch, and heave. These are **rough estimates** using simplified empirical formulas; the standard linearized naval architecture formulas don't apply well to asymmetric proa hulls. Physical testing is recommended for accurate values.

| Motion | Period | Formula | Description |
|--------|--------|---------|-------------|
| Roll | {{ site.data.rp2_beaching_gz.natural_periods.roll_period_s }} s | T ≈ 0.35 × beam | Side-to-side oscillation about longitudinal axis |
| Pitch | {{ site.data.rp2_beaching_gz.natural_periods.pitch_period_s }} s | T ≈ 0.4√LOA + 1.5 | Fore-aft oscillation about transverse axis |
| Heave | {{ site.data.rp2_beaching_gz.natural_periods.heave_period_s }} s | T = 2π√(m/ρgA<sub>wp</sub>) | Vertical oscillation |

### Comfort Considerations

- **Short roll period** (~2s): Reflects the wide beam providing high initial stability. Motion will be quick and snappy.
- **Moderate pitch period** (~2.7s): Typical for lightweight multihulls of this length.
- **Short heave period** (~1s): Characteristic of light, narrow hulls.

For passenger comfort, roll periods of 6-12 seconds are typically preferred. The short roll period of this vessel indicates stiff motion—the boat returns quickly to upright but may feel jerky in beam seas.

**Critical consideration:** If wave periods in the operating area are 3-6 seconds (typical for coastal waters), the vessel may experience pitch resonance, which could be uncomfortable for passengers.

See [implementation](https://github.com/shipshape-marine/shipshape/blob/main/src/shipshape/gz/__main__.py).

---

[← Back to RP2 Overview]({{ '/rp2.html' | relative_url }}) | [View Structural Analysis →]({{ '/validation_rp2.html' | relative_url }})
