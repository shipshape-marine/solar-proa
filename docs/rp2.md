---
layout: default
title: Roti Proa II - 9m Day Tourism Vessel
---

# Roti Proa II
## 9-Meter Solar-Electric Day Tourism Vessel

[← Back to Home]({{ '/' | relative_url }})

---

## Specifications

**Overall Length:** {{ site.data.rp2_closehaul.parameters.vaka_length }}mm  
**Beam:** {{ site.data.rp2_closehaul.parameters.beam }}mm (with outrigger)  
**Capacity:** 4 passengers + 2 crew  
**Solar Power:** 4kW peak (8 panels)  
**Motor Power:** 4kW electric  
**Cruising Speed:** 10 knots  
**Daily Range:** 50 nautical miles (solar-electric only)  
**Battery Type:** LiFePO₄  
**Motor Runtime:** 5 hours (battery only)

---

## Design Features

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

## Configurations

The vessel can be configured for different sailing conditions and use cases:

{% assign rp2_configs = "beaching,beamreach,broadreach,closehaul,closehaulreefed,goosewing" | split: "," %}

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in rp2_configs %}
  <div style="border: 1px solid #ddd; padding: 1em; border-radius: 4px;">
    <h4>{{ config | capitalize | replace: "beamreach", "Beam Reach" | replace: "broadreach", "Broad Reach" | replace: "closehaul", "Close Haul" | replace: "closehaulreefed", "Close Haul Reefed" | replace: "goosewing", "Goose Wing" }}</h4>
    <p style="font-size: 0.9em; color: #666;">
    {% if config == "beaching" %}Beached configuration for maintenance{% endif %}
    {% if config == "beamreach" %}Cross-wind sailing{% endif %}
    {% if config == "broadreach" %}Downwind sailing{% endif %}
    {% if config == "closehaul" %}Upwind sailing{% endif %}
    {% if config == "closehaulreefed" %}Reefed for heavy weather{% endif %}
    {% if config == "goosewing" %}Running downwind{% endif %}
    </p>
  </div>
{% endfor %}
</div>

---

## 3D Renders

*Automatically generated from parametric CAD models*

{% assign render_files = site.static_files | where_exp: "file", "file.path contains 'renders'" | where_exp: "file", "file.path contains 'rp2'" | where_exp: "file", "file.extname == '.png'" %}

{% for config in rp2_configs %}
  <h3>{{ config | capitalize | replace: "beamreach", "Beam Reach" | replace: "broadreach", "Broad Reach" | replace: "closehaul", "Close Haul" | replace: "closehaulreefed", "Close Haul Reefed" | replace: "goosewing", "Goose Wing" }}</h3>
  
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  {% assign config_files = render_files | where_exp: "file", "file.basename contains config" | sort: "basename" %}
  {% for file in config_files %}
    <div>
      <img src="{{ file.path | relative_url }}" alt="{{ file.basename }}" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
      <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">
        {{ file.basename | remove: "rp2." | remove: config | remove: ".render." | remove: "_" | replace: "Front", "Front View" | replace: "Isometric", "Isometric View" | replace: "Right", "Right View" | replace: "Top", "Top View" }}
      </p>
    </div>
  {% endfor %}
  </div>
{% endfor %}

---

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

## Download CAD Models

Access parametric FreeCAD models for all sail configurations.
These files include the complete 3D geometry and can be modified for your specific requirements.

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in site.data.rp2_downloads.configurations %}
  <div style="padding: 1em; border: 1px solid #ddd; border-radius: 4px; text-align: center;">
    <div style="font-size: 2em; margin-bottom: 0.5em;">📐</div>
    <a href="{{ '/downloads/' | append: config.filename | relative_url }}" style="font-weight: bold; display: block; margin-bottom: 0.5em;">
      {{ config.name | replace: "_", " " }}
    </a>
    {% if config.description %}
    <div style="font-size: 0.85em; color: #666;">
      {{ config.description }}
    </div>
    {% endif %}
  </div>
{% endfor %}
</div>

**Software Required:** [FreeCAD](https://www.freecad.org/) (free and open-source)

**License:** Models are shared under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) - free to use, modify, and share with attribution.

---

[← Back to Home]({{ '/' | relative_url }}) | [View RP1 →]({{ '/rp1.html' | relative_url }}) | [View RP3 →]({{ '/rp3.html' | relative_url }})
