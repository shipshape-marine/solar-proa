---
layout: default
title: Roti Proa III - 13m Multi-Day Vessel
---

<div style="display: flex; align-items: center; gap: 2em; margin-bottom: 2em; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 300px;">
    <h1 style="margin: 0;">Roti Proa III</h1>
    <h2 style="margin-top: 0.5em; font-weight: 300;">13-Meter Solar-Electric Multi-Day Cruiser</h2>
  </div>
  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/renders/rp3.closehaul.render.isometric.png' | relative_url }}" alt="Roti Proa III" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>
</div>

[← Back to Home]({{ '/' | relative_url }})

---

## Vision: Scaling Up for Multi-Day Voyages

**Status:** 🔵 Design Phase | **Target:** Mid-2027 validation

Roti Proa III represents our vision for carbon-neutral multi-day coastal cruising in tropical Southeast Asia. Building on the lessons from RP1 (prototype) and RP2 (day tourism), RP3 will demonstrate that solar-electric propulsion can support extended voyages with overnight accommodation.

---

## Design Concept

Roti Proa III will be based on a **Dragon Boat DB22 hull** - a proven traditional design that offers:

- **Optimal length-to-beam ratio** for efficient electric propulsion
- **Proven seaworthiness** in Southeast Asian waters
- **Cultural significance** connecting to regional maritime heritage
- **Ample interior volume** for passenger accommodation
- **Established construction methods** for reliable building

### Why Dragon Boat Heritage?

Dragon boats have been used across Asia for over 2,000 years. The DB22 design represents centuries of refinement for tropical coastal waters - exactly our operational environment. By adapting this traditional hull to modern solar-electric propulsion, we honor maritime tradition while pioneering sustainable technology.

---

## Preliminary Specifications

| Specification | Estimated Value |
|--------------|----------------|
| Overall Length (LOA) | {{ site.data.rp3_closehaul_parameter.vaka_length }} mm |
| Beam (hull) | ~1.2m (traditional dragon boat proportions) |
| Beam (with outrigger) | {{ site.data.rp3_closehaul_parameter.beam }} mm |
| Capacity | 5-6 passengers + 2 crew |
| Solar Power | 6-8kW peak (estimated) |
| Motor Power | 5-6kW electric (estimated) |
| Cruising Speed | 8-10 knots |
| Range | Multi-day (100+ nautical miles) |
| Accommodation | Sleeping quarters for passengers |
| Galley | Electric cooking from solar excess |
| Water | Integrated desalination capability |

*Note: Specifications are preliminary and subject to refinement during detailed design phase*

---

## Buoyancy analysis

We derive the following buoyancy characteristics from
our automated analysis using Newton's method, iteratively adjusting the
roll/pitch/z-offset of the boat according to the difference between the center/amount of buoyancy and the center/amount of mass. The numbers indicate the equilibrium achieved after 
{{ site.data.rp3_beaching_buoyancy.iterations }} iterations using
the beaching configuration (no sails and rudders lifted),
see [implementation](https://github.com/solar-proa/CAD/blob/main/src/buoyancy/__main__.py).

**Z-offset (boat lowering into the water):** {{ site.data.rp3_beaching_buoyancy.equilibrium.z_offset_mm }} mm  
**Pitch degrees:** {{ site.data.rp3_beaching_buoyancy.equilibrium.pitch_deg }} arc degrees  
**Roll degrees:** {{ site.data.rp3_beaching_buoyancy.equilibrium.roll_deg }} arc degrees  
**Vaka submerged volume:** {{ site.data.rp3_beaching_buoyancy.vaka.submerged_volume_liters }} liters  
**Vaka total volume:** {{ site.data.rp3_beaching_buoyancy.vaka.total_volume_liters }} liters  
**Vaka submerged percentage:** {{ site.data.rp3_beaching_buoyancy.vaka.submerged_percent }} %  
**Vaka z-offset:** {{ site.data.rp3_beaching_buoyancy.vaka.z_world_mm }} mm  
**Ama submerged volume:** {{ site.data.rp3_beaching_buoyancy.ama.submerged_volume_liters }} liters  
**Ama total volume:** {{ site.data.rp3_beaching_buoyancy.ama.total_volume_liters }} liters  
**Ama submerged percentage:** {{ site.data.rp3_beaching_buoyancy.ama.submerged_percent }} %  
**Ama z-offset:** {{ site.data.rp3_beaching_buoyancy.ama.z_world_mm }} mm  
**Center of gravity (world-coordinates x, y, z):** {{ site.data.rp3_beaching_buoyancy.center_of_gravity_world.x }}, {{ site.data.rp3_beaching_buoyancy.center_of_gravity_world.y }}, {{ site.data.rp3_beaching_buoyancy.center_of_gravity_world.z }} mm  
**Center of buoyancy (world-coordinates x, y, z):** {{ site.data.rp3_beaching_buoyancy.center_of_buoyancy.x }}, {{ site.data.rp3_beaching_buoyancy.center_of_buoyancy.y }}, {{ site.data.rp3_beaching_buoyancy.center_of_buoyancy.z }} mm  

---

## Key Innovations for Multi-Day Operation

**Extended Solar Capacity:**
- Larger solar array (6-8kW) for overnight battery charging
- Excess power for onboard cooking and water desalination
- Shore power compatibility for dock charging

**Accommodation Design:**
- Sleeping berths for 5-6 passengers
- Covered deck area for weather protection
- Galley with electric cooking facilities
- Freshwater storage and desalination
- Marine toilet facilities

**Enhanced Sailing Rig:**
- Scaled-up version of RP2's proven shunting design
- Increased sail area for long-distance passages
- Storm rig capability for safety

**Redundant Systems:**
- Dual motor configuration option
- Backup sailing capability
- Enhanced battery capacity for overnight operations

---

## Development Timeline

**2026 Q4:** Hull design finalization based on DB22 platform  
**2027 Q1-Q2:** Construction and system integration  
**2027 Q2-Q3:** Sea trials and certification  
**2027 Q4:** Commercial validation with strategic partners

---

## Target Applications

**Multi-Day Eco-Tourism:**
- Island-hopping expeditions (3-5 days)
- Marine wildlife observation cruises
- Cultural heritage coastal tours
- Educational sailing experiences
- Slow travel experiences connecting coastal communities

**Operational Advantages:**
- Zero fuel costs on multi-day voyages
- Quiet operation for wildlife observation
- Onboard cooking without diesel generators
- Fresh water generation from excess solar
- Premium eco-tourism positioning

---

## Design Philosophy

Roti Proa III embodies our core principle: **combining Southeast Asian maritime traditions with cutting-edge sustainable technology.**

The dragon boat hull represents 2,000+ years of Asian maritime engineering. Our contribution is adapting this proven design for the 21st century - replacing human paddlers with solar-electric propulsion while maintaining the hull's fundamental efficiency and seaworthiness.

This isn't just about technology transfer; it's about **cultural continuity** - showing that traditional designs remain relevant when paired with modern sustainability solutions.

---

## 3D Renders

*Automatically generated from parametric CAD models*

{% assign render_files = site.static_files | where_exp: "file", "file.path contains 'renders'" | where_exp: "file", "file.path contains 'rp3'" | where_exp: "file", "file.extname == '.png'" %}

{% for config in site.data.configurations %}
<<<<<<< HEAD
  {% assign config_pattern = config.name | append: ".render" %}
  <h3>{{ config.display_name }}</h3>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  {% assign config_files = render_files | where_exp: "file", "file.basename contains config_pattern" | sort: "basename" %}
=======
  <h3>{{ config.display_name }}</h3>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  {% assign config_files = render_files | where_exp: "file", "file.basename contains config.name" | sort: "basename" %}
>>>>>>> 5ec7cc0 (Add technical page and systematic configuration display names)
  {% for file in config_files %}
    {% assign view_name = file.basename | split: ".render." | last %}
    <div>
      <img src="{{ file.path | relative_url }}" alt="{{ file.basename }}" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
      <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">
<<<<<<< HEAD
        {{ site.data.views[view_name].display_name }}
=======
        {{ file.basename | remove: "rp3." | remove: config.name | remove: ".render." | remove: "_" | replace: "front", "Back View" | replace: "isometric", "Isometric View" | replace: "right", "Right View" | replace: "top", "Top View" }}
>>>>>>> 5ec7cc0 (Add technical page and systematic configuration display names)
      </p>
    </div>
  {% endfor %}
  </div>
{% endfor %}

---

## Partnership Opportunities

RP3 development presents unique opportunities for strategic partners interested in:

- **Early-stage design collaboration** on multi-day eco-tourism vessels
- **Field testing participation** in 2027 validation phase
- **Market validation** for premium sustainable tourism experiences
- **Technology demonstration** for corporate sustainability initiatives

The 2027 timeline allows partners to influence design decisions while maintaining exposure to a novel market segment.

---

## From Prototype to Production

**RP3 (2025):** Proved the concept  
**RP2 (2026):** Validates commercial day-tourism operations  
**RP3 (2027):** Demonstrates multi-day voyage capability

This progression de-risks the technology while building toward our ultimate vision: a fleet of carbon-neutral vessels serving Southeast Asia's coastal eco-tourism market.

---

## Download CAD Models

Access CAD models for all sail configurations in FreeCAD (.FCStd) and STEP (.step) formats.
These files include the complete 3D geometry and can be modified for your specific requirements.

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in site.data.rp3_downloads.configuration %}
  <div style="padding: 1em; border: 1px solid #ddd; border-radius: 4px;">
    <div style="font-weight: bold; margin-bottom: 0.5em; text-transform: capitalize;">
      {{ config.name | replace: "_", " " }}
    </div>
    {% if config.description %}
    <div style="font-size: 0.85em; color: #666; margin-bottom: 0.75em;">
      {{ config.description }}
    </div>
    {% endif %}
    <div style="display: flex; gap: 0.5em; flex-wrap: wrap;">
      <a href="{{ '/downloads/' | append: config.filename | relative_url }}" style="background: #28a745; color: white; padding: 0.4em 0.8em; border-radius: 4px; text-decoration: none; font-size: 0.9em;">
        📐 FreeCAD
      </a>
      {% if config.step_filename %}
      <a href="{{ '/downloads/' | append: config.step_filename | relative_url }}" style="background: #007bff; color: white; padding: 0.4em 0.8em; border-radius: 4px; text-decoration: none; font-size: 0.9em;">
        📦 STEP
      </a>
      {% endif %}
    </div>
  </div>
{% endfor %}
</div>

**Formats:**
- **FreeCAD (.FCStd):** Parametric model for [FreeCAD](https://www.freecad.org/) (free and open-source)
- **STEP (.step):** Universal CAD format compatible with most CAD software

**License:** Models are shared under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) - free to use, modify, and share with attribution.

---

[← Back to Home]({{ '/' | relative_url }}) | [View RP1 →]({{ '/rp1.html' | relative_url }}) | [View RP2 →]({{ '/rp2.html' | relative_url }})
