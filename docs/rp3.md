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
    <img src="{{ '/renders/rp3.closehaul.render.view3.png' | relative_url }}" alt="Roti Proa III" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
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
| Overall Length (LOA) | ~13m |
| Beam (hull) | ~1.2m (traditional dragon boat proportions) |
| Beam (with outrigger) | ~7-8m (TBD based on optimization) |
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

*Design visualization coming soon*

{% assign render_files = site.static_files | where_exp: "file", "file.path contains 'renders'" | where_exp: "file", "file.path contains 'RP3'" | where_exp: "file", "file.extname == '.png'" %}

{% if render_files.size > 0 %}
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
{% for file in render_files limit:8 %}
  <div>
    <img src="{{ file.path | relative_url }}" alt="{{ file.basename }}" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">
      {{ file.basename | replace: "RotiProa_RP3_", "" | replace: "_", " " }}
    </p>
  </div>
{% endfor %}
</div>

<p style="text-align: center; margin-top: 2em;">
  <a href="{{ '/rp3-gallery.html' | relative_url }}">View All RP3 Configurations →</a>
</p>
{% else %}
  <div style="background: #f8f8f8; padding: 3em; text-align: center; border-radius: 8px; margin: 2em 0;">
    <p style="color: #666; font-size: 1.1em;"><em>Detailed CAD renders will be available as the design progresses through 2026</em></p>
    <p style="margin-top: 1em;">Currently, we're in the conceptual design phase, refining the dragon boat hull adaptation and optimizing the outrigger configuration for the larger vessel size.</p>
  </div>
{% endif %}

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

**RP1 (2025):** Proved the concept  
**RP2 (2026):** Validates commercial day-tourism operations  
**RP3 (2027):** Demonstrates multi-day voyage capability

This progression de-risks the technology while building toward our ultimate vision: a fleet of carbon-neutral vessels serving Southeast Asia's coastal eco-tourism market.

---

## Technical Documentation

Detailed CAD models, structural analysis, and system specifications will be published as the design matures through 2026.

**Stay Updated:** All design files and renders are automatically published to this site via our parametric CAD workflow.

---

[← Back to Home]({{ '/' | relative_url }}) | [View RP1 →]({{ '/rp1.html' | relative_url }}) | [View RP2 →]({{ '/rp2.html' | relative_url }})
