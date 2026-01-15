---
layout: default
title: Roti Proa I - 4.2m Prototype
---

<div style="display: flex; align-items: center; gap: 2em; margin-bottom: 2em; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 300px;">
    <h1 style="margin: 0;">Roti Proa I</h1>
    <h2 style="margin-top: 0.5em; font-weight: 300;">4.2-Meter Proof-of-Concept Prototype</h2>
  </div>
  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/renders/rp1.closehaul.render.isometric.png' | relative_url }}" alt="Roti Proa I" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>
</div>

[← Back to Home]({{ '/' | relative_url }})

---

## Overview

**Status:** ✅ Completed and tested (December 2024 - June 2025)

Roti Proa I was our proof-of-concept prototype that validated the feasibility of combining traditional outrigger design with modern solar-electric propulsion in tropical waters. The 4.2-meter vessel successfully demonstrated the core principles that inform our larger commercial designs.

**Key Achievements:**
- **Sea trials validated** in Singapore waters near Changi
- **Top speed:** 6.5 knots (12 km/h) under electric power
- **Solar capacity:** 1kW peak (2 panels)
- **Propulsion:** 2kW electric outboard motor
- **Battery:** LiFePO₄ system
- **Sailing rig:** Dual independent sport rigs for experimental configuration

The prototype proved that solar proas are viable for tropical Southeast Asian waters and provided crucial data for scaling up to the 9-meter Roti Proa II design.

---

## Featured Publication

For a detailed account of the Roti Proa I development, testing, and lessons learned, read the full article published by the Changi Sailing Club in Singapore:

**[Roti Proa: An Experimental Wind and Solar Powered Boat](https://www.csc.org.sg/2025/07/11/roti-proa-an-experimental-wind-and-solar-powered-boat/)**

This comprehensive article covers:
- Design philosophy and traditional influences
- Construction process and material choices
- Sea trial results and performance data
- Lessons learned for future development
- Technical challenges and solutions

---

## Quick Specifications

| Specification | Value |
|--------------|-------|
| Overall Length (LOA) | 4.2m |
| Beam | 2.5m |
| Solar Power | 1kW peak |
| Motor Power | 2kW electric outboard |
| Battery Type | LiFePO₄ |
| Top Speed | 6.5 knots |
| Crew | 1-2 persons |
| Status | Testing completed June 2025 |

---

## 3D Renders

*Automatically generated from parametric CAD models*

{% assign render_files = site.static_files | where_exp: "file", "file.path contains 'renders'" | where_exp: "file", "file.path contains 'rp1'" | where_exp: "file", "file.extname == '.png'" %}

{% assign rp1_configs = "beaching,beamreach,broadreach,closehaul,closehaulreefed,goosewing" | split: "," %}

{% for config in rp1_configs %}
  <h3>{{ config | capitalize | replace: "beamreach", "Beam Reach" | replace: "broadreach", "Broad Reach" | replace: "closehaul", "Close Haul" | replace: "closehaulreefed", "Close Haul Reefed" | replace: "goosewing", "Goose Wing" }}</h3>
  
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  {% assign config_files = render_files | where_exp: "file", "file.basename contains config" | sort: "basename" %}
  {% for file in config_files %}
    <div>
      <img src="{{ file.path | relative_url }}" alt="{{ file.basename }}" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
      <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">
        {{ file.basename | remove: "rp1." | remove: config | remove: ".render." | remove: "_" | replace: "front", "Back View" | replace: "isometric", "Isometric View" | replace: "right", "Right View" | replace: "top", "Top View" }}
      </p>
    </div>
  {% endfor %}
  </div>
{% endfor %}

---

## Legacy & Impact

Roti Proa I's successful trials provided the confidence and empirical data needed to pursue commercial-scale development. The prototype demonstrated that:

✅ Solar-electric propulsion is viable in tropical waters  
✅ Traditional outrigger designs adapt well to modern electric systems  
✅ Shunting proas can effectively integrate solar panels  
✅ The combination creates a compelling eco-tourism experience

These insights directly informed the design of Roti Proa II and validate our approach for the 13-meter Roti Proa III.

---

## Funding & Support

Roti Proa I was funded through:
- **Maybank Green Fund:** S$5,000 (via NUS Office of Student Affairs)
- **Private donations and sponsorships:** S$7,000
- **Total project cost:** S$12,000

---

## From Prototype to Product

The success of Roti Proa I demonstrates that our vision is technically sound. Now, with Roti Proa II under construction, we're taking the next step toward commercial viability—a vessel designed not just to prove a concept, but to serve real eco-tourism operations in tropical Southeast Asia.

**Read the full story:** [Changi Sailing Club Article →](https://www.csc.org.sg/2025/07/11/roti-proa-an-experimental-wind-and-solar-powered-boat/)

---

## Download CAD Models

Access CAD models for all sail configurations in FreeCAD (.FCStd) and STEP (.step) formats.
These files include the complete 3D geometry and can be modified for your specific requirements.

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in site.data.rp1_downloads.configurations %}
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

[← Back to Home]({{ '/' | relative_url }}) | [View RP2 →]({{ '/rp2.html' | relative_url }}) | [View RP3 →]({{ '/rp3.html' | relative_url }})
