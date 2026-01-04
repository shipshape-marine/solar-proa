---
layout: default
title: Roti Proa II - 9m Day Tourism Vessel
---

# Roti Proa II
## 9-Meter Solar-Electric Day Tourism Vessel

[← Back to Home]({{ '/' | relative_url }})

---

## Specifications

**Overall Length:** {{ site.data.rp2_closehaul.LOA_m }}m  
**Beam:** {{ site.data.rp2_closehaul.beam_m }}m (with outrigger)  
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
- Dual carbon fiber stay-less masts
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

{% assign rp2_configs = "Beaching,BeamReach,BroadReach,CloseHaul,CloseHaulReefed,GooseWing" | split: "," %}

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in rp2_configs %}
  <div style="border: 1px solid #ddd; padding: 1em; border-radius: 4px;">
    <h4>{{ config | replace: "BeamReach", "Beam Reach" | replace: "BroadReach", "Broad Reach" | replace: "CloseHaul", "Close Haul" | replace: "CloseHaulReefed", "Close Haul Reefed" | replace: "GooseWing", "Goose Wing" }}</h4>
    <p style="font-size: 0.9em; color: #666;">
    {% if config == "Beaching" %}Beached configuration for maintenance{% endif %}
    {% if config == "BeamReach" %}Cross-wind sailing{% endif %}
    {% if config == "BroadReach" %}Downwind sailing{% endif %}
    {% if config == "CloseHaul" %}Upwind sailing{% endif %}
    {% if config == "CloseHaulReefed" %}Reefed for heavy weather{% endif %}
    {% if config == "GooseWing" %}Running downwind{% endif %}
    </p>
  </div>
{% endfor %}
</div>

---

## 3D Renders

*Automatically generated from parametric CAD models*

{% assign render_files = site.static_files | where_exp: "file", "file.path contains 'renders'" | where_exp: "file", "file.path contains 'RP2'" | where_exp: "file", "file.extname == '.png'" %}

{% for config in rp2_configs %}
  <h3>{{ config | replace: "BeamReach", "Beam Reach" | replace: "BroadReach", "Broad Reach" | replace: "CloseHaul", "Close Haul" | replace: "CloseHaulReefed", "Close Haul Reefed" | replace: "GooseWing", "Goose Wing" }}</h3>
  
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  {% assign config_files = render_files | where_exp: "file", "file.basename contains config" | sort: "basename" %}
  {% for file in config_files %}
    <div>
      <img src="{{ file.path | relative_url }}" alt="{{ file.basename }}" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
      <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">
        {{ file.basename | replace: "RotiProa_RP2_", "" | replace: config, "" | replace: "_", "" | replace: "Front", "Front View" | replace: "Isometric", "Isometric View" | replace: "Right", "Right View" | replace: "Top", "Top View" }}
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

## Download CAD Files

*Coming soon: Access to parametric FreeCAD models and construction documentation*

---

[← Back to Home]({{ '/' | relative_url }}) | [View RP1 →]({{ '/rp1.html' | relative_url }}) | [View RP3 →]({{ '/rp3.html' | relative_url }})
