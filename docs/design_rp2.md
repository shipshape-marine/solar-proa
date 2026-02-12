---
layout: default
title: Roti Proa II - Design Specification and Renderings
---

<div style="display: flex; align-items: center; gap: 2em; margin-bottom: 2em; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 400px; max-width: 600px;">
    <img src="{{ '/renders/rp2.closehaul.render.isometric.png' | relative_url }}" alt="Roti Proa II" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <p style="font-size: 0.9em; color: #666; margin-top: 0.5em; font-style: italic;">Roti Proa II, sailing close-haul, isometric view generated from FreeCAD design</p>
  </div>
</div>

[← Back to Roti Proa II Overview]({{ '/rp2.html' | relative_url }})

---

## Specifications

**Overall Length:** {{ site.data.rp2_closehaul_parameter.vaka_length }} mm  
**Beam:** {{ site.data.rp2_closehaul_parameter.beam }} mm (with outrigger)  
**Total mass (unloaded):** {{ site.data.rp2_beaching_mass.total_mass_kg }} kg  
**Total unsinkable volume:** {{ site.data.rp2_beaching_mass.total_unsinkable_volume_liters }} liters  
**Displacement of unsinkable volume in saltwater:** {{ site.data.rp2_beaching_mass.total_unsinkable_displacement_saltwater_kg }} kg  
**Capacity:** 4 passengers + 2 crew  
**Solar Power:** 4 kW peak (8 panels)  
**Motor Power:** 4 kW electric  
**Cruising Speed:** 10 knots  
**Daily Range:** 50 nautical miles (solar-electric only)  
**Battery Type:** LiFePO₄  
**Motor Runtime:** 5 hours (battery only)  
**Masts:** Two unstayed rotatable masts, cylindrical aluminium pipes with diameter {{ site.data.rp2_broadreach_parameter.mast_diameter }} mm and wall thickness {{ site.data.rp2_broadreach_parameter.mast_thickness }} mm; mast height from vaka sole: {{ site.data.rp2_broadreach_parameter.mast_height }} mm  
**Rig:** Each mast carries one tanja sail, each rectangular-shaped {{ site.data.rp2_broadreach_parameter.sail_width }} mm x {{ site.data.rp2_broadreach_parameter.sail_height }} mm; total sail area: {{ site.data.rp2_broadreach_parameter.sail_area_m2 }} square meters

---

## Lines Plan

**[View Full Lines Plan →]({{ '/lines/rp2.goosewing.lines.pdf' | relative_url }})**

### Profile (vaka, rudder and ama sections)

  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/lines/rp2.goosewing.lines.summary.profile.svg' | relative_url }}" alt="Roti Proa II Profile" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>

### Full Breadth Plan

  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/lines/rp2.goosewing.lines.fullbreadth.svg' | relative_url }}" alt="Roti Proa II Full Breadth" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>

### Body Plan (all sections)

  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/lines/rp2.goosewing.lines.summary.bodyplan.svg' | relative_url }}" alt="Roti Proa II Body Plan" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>

---

## 3D Renders

{% assign render_files = site.static_files | where_exp: "file", "file.path contains 'renders'" | where_exp: "file", "file.path contains 'rp2'" | where_exp: "file", "file.extname == '.png'" %}

{% for config in site.data.configurations %}
  {% assign config_pattern = config.name | append: ".render" %}
  <h3>{{ config.display_name }}</h3>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  {% assign config_files = render_files | where_exp: "file", "file.basename contains config_pattern" | sort: "basename" %}
  {% for file in config_files %}
    {% assign view_name = file.basename | split: ".render." | last %}
    <div>
      <img src="{{ file.path | relative_url }}" alt="{{ file.basename }}" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
      <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">
        {{ site.data.views[view_name].display_name }}
      </p>
    </div>
  {% endfor %}
  </div>
{% endfor %}

## Download CAD Models

Access CAD models for all sail configurations in FreeCAD (.FCStd) and STEP (.step) formats. These files include the complete 3D geometry and can be modified for your specific requirements.

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in site.data.rp2_downloads.configuration %}
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

[← Back to RP2 Overview]({{ '/rp2.html' | relative_url }}) | [View Stability and Buoyancy Analysis →]({{ '/stability_rp2.html' | relative_url }})
