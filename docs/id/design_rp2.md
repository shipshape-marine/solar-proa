---
layout: default
title: Roti Proa II - Spesifikasi Desain dan Render
lang: id
---

[← Kembali ke Ikhtisar Roti Proa II]({{ '/id/rp2.html' | relative_url }})

---

## Spesifikasi

**Panjang Keseluruhan:** {{ site.data.rp2_closehaul_parameter.vaka_length }} mm  
**Lebar:** {{ site.data.rp2_closehaul_parameter.beam }} mm (dengan cadik)  
**Massa total (tanpa muatan):** {{ site.data.rp2_beaching_mass.total_mass_kg }} kg  
**Volume total tidak tenggelam:** {{ site.data.rp2_beaching_mass.total_unsinkable_volume_liters }} liter  
**Perpindahan volume tidak tenggelam di air asin:** {{ site.data.rp2_beaching_mass.total_unsinkable_displacement_saltwater_kg }} kg  
**Kapasitas:** 4 penumpang + 2 kru  
**Daya Surya:** 4 kW puncak (8 panel)  
**Daya Motor:** 4 kW listrik  
**Kecepatan Jelajah:** 10 knot  
**Jangkauan Harian:** 50 mil laut (surya-listrik saja)  
**Tipe Baterai:** LiFePO₄  
**Waktu Operasi Motor:** 5 jam (baterai saja)  
**Tiang:** Dua tiang tanpa stay yang dapat diputar, pipa aluminium silinder dengan diameter {{ site.data.rp2_broadreach_parameter.mast_diameter }} mm dan ketebalan dinding {{ site.data.rp2_broadreach_parameter.mast_thickness }} mm; tinggi tiang dari sole vaka: {{ site.data.rp2_broadreach_parameter.mast_height }} mm  
**Rig:** Setiap tiang membawa satu layar tanja, masing-masing berbentuk persegi panjang {{ site.data.rp2_broadreach_parameter.sail_width }} mm x {{ site.data.rp2_broadreach_parameter.sail_height }} mm; total luas layar: {{ site.data.rp2_broadreach_parameter.sail_area_m2 }} meter persegi  

---

## Rencana Garis

**[Lihat Rencana Garis Lengkap →]({{ '/lines/rp2.goosewing.lines.pdf' | relative_url }})**

### Profil (potongan vaka, kemudi, dan ama)

  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/lines/rp2.goosewing.lines.summary.profile.svg' | relative_url }}" alt="Profil Roti Proa II" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>

### Rencana Lebar Penuh

  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/lines/rp2.goosewing.lines.fullbreadth.svg' | relative_url }}" alt="Lebar Penuh Roti Proa II" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>

### Rencana Badan (semua potongan)

  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/lines/rp2.goosewing.lines.summary.bodyplan.svg' | relative_url }}" alt="Rencana Badan Roti Proa II" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>

---

## Render 3D

{% assign render_files = site.static_files | where_exp: "file", "file.path contains 'renders'" | where_exp: "file", "file.path contains 'rp2'" | where_exp: "file", "file.extname == '.png'" %}

{% for config in site.data.configurations %}
  {% assign config_pattern = config.name | append: ".render" %}
  <h3>{{ config.display_name_id }}</h3>

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

## Unduh Model CAD

Akses model CAD untuk semua konfigurasi layar dalam format FreeCAD (.FCStd) dan STEP (.step). File-file ini mencakup geometri 3D lengkap dan dapat dimodifikasi untuk kebutuhan spesifik Anda.

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in site.data.rp2_downloads.configuration %}
  {% assign config_trans = site.data.configurations | where: "name", config.name | first %}
  <div style="padding: 1em; border: 1px solid #ddd; border-radius: 4px;">
    <div style="font-weight: bold; margin-bottom: 0.5em;">
      {{ config_trans.display_name_id | default: config.name }}
    </div>
    {% if config_trans.description_id %}
    <div style="font-size: 0.85em; color: #666; margin-bottom: 0.75em;">
      {{ config_trans.description_id }}
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

**Format:**
- **FreeCAD (.FCStd):** Model parametrik untuk [FreeCAD](https://www.freecad.org/) (gratis dan sumber terbuka)
- **STEP (.step):** Format CAD universal yang kompatibel dengan sebagian besar perangkat lunak CAD

**Lisensi:** Model dibagikan di bawah [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) - bebas digunakan, dimodifikasi, dan dibagikan dengan atribusi.

---

[← Kembali ke Ikhtisar RP2]({{ '/id/rp2.html' | relative_url }}) | [Lihat Analisis Stabilitas dan Daya Apung →]({{ '/id/stability_rp2.html' | relative_url }})
