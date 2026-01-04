# Using Statistics in Jekyll Pages

## Overview

The build process automatically generates YAML files in `docs/_data/` containing statistics for each boat configuration. These are available in Jekyll templates as `site.data.<filename>`.

## Example Generated File

`docs/_data/rp2_closehaul.yml`:
```yaml
boat: RP2
configuration: CloseHaul
total_mass_kg: 487.32
total_volume_liters: 1245.67
materials:
  Aluminum:
    mass_kg: 125.60
    volume_liters: 46.52
  Solar panels:
    mass_kg: 72.00
    volume_liters: 15.20
top_components:
  - name: Main Hull
    mass_kg: 156.80
    volume_liters: 580.00
    material: Aluminum
component_count: 45
```

## Usage in Markdown Pages

### Display Total Mass

```markdown
**Total Mass:** {{ site.data.rp2_closehaul.total_mass_kg }} kg
```

### Materials Table

```markdown
| Material | Mass (kg) | Volume (L) |
|----------|-----------|------------|
{% for material in site.data.rp2_closehaul.materials %}
| {{ material[0] }} | {{ material[1].mass_kg }} | {{ material[1].volume_liters }} |
{% endfor %}
```

### Top Components List

```markdown
### Heaviest Components

{% for comp in site.data.rp2_closehaul.top_components limit:5 %}
- **{{ comp.name }}**: {{ comp.mass_kg }} kg ({{ comp.material }})
{% endfor %}
```

### Complete Stats Section

```markdown
## Technical Specifications - {{ site.data.rp2_closehaul.configuration }}

**Total Mass:** {{ site.data.rp2_closehaul.total_mass_kg }} kg  
**Total Volume:** {{ site.data.rp2_closehaul.total_volume_liters }} L  
**Components:** {{ site.data.rp2_closehaul.component_count }}

### Materials Breakdown

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em;">
{% for material in site.data.rp2_closehaul.materials %}
  <div style="padding: 1em; border: 1px solid #ddd; border-radius: 4px;">
    <strong>{{ material[0] }}</strong><br>
    Mass: {{ material[1].mass_kg }} kg<br>
    Volume: {{ material[1].volume_liters }} L
  </div>
{% endfor %}
</div>

### Major Components

| Component | Mass (kg) | Material |
|-----------|-----------|----------|
{% for comp in site.data.rp2_closehaul.top_components %}
| {{ comp.name }} | {{ comp.mass_kg }} | {{ comp.material }} |
{% endfor %}
```

## Conditional Loading

Check if data exists before using:

```markdown
{% if site.data.rp2_closehaul %}
  Total mass: {{ site.data.rp2_closehaul.total_mass_kg }} kg
{% else %}
  Statistics not yet generated
{% endif %}
```

## Comparing Configurations

```markdown
| Configuration | Mass (kg) |
|---------------|-----------|
| Close Haul | {{ site.data.rp2_closehaul.total_mass_kg }} |
| Beam Reach | {{ site.data.rp2_beamreach.total_mass_kg }} |
| Broad Reach | {{ site.data.rp2_broadreach.total_mass_kg }} |
```
