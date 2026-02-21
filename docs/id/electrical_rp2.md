---
layout: default
title: Roti Proa II - Simulasi Kelistrikan
description: Kapal Hibrida Bertenaga Angin-Surya untuk Daerah Tropis
lang: id
---

[← Kembali ke Ikhtisar Roti Proa II]({{ '/id/rp2.html' | relative_url }})

---

## Konfigurasi Rangkaian

### Pengaturan Panel Surya & MPPT

Konfigurasi: **{{ site.data.rp2_electrical_simulation_operating_point.mppt_result.array_count }}× array MPPT** diparalelkan.

{% for entry in site.data.boat_rp2_circuit_setup.mppt_panel %}{% if entry[0] contains "config_" %}{% assign cfg = entry[1] %}
{% if cfg.count == 0 %}{% continue %}{% endif %}
{% assign panel_choice = cfg.panel_info.choice %}
{% assign panel = site.data.components.Panel[panel_choice] %}
{% assign mppt_choice = cfg.mppt_info.choice %}
{% assign mppt = site.data.components.MPPT[mppt_choice] %}

#### {{ entry[0] | replace: "_", " " | capitalize }}

| Parameter | Nilai |
|-----------|-------|
| Jumlah Array | {{ cfg.count }} |
| Panel | {{ panel_choice | replace: "_", " " }} |
| Daya Panel | {{ panel.power }} W |
| Tegangan Panel | {{ panel.voltage }} V |
| Panel dalam Seri | {{ cfg.panel_info.in_series }} |
| Panel dalam Paralel | {{ cfg.panel_info.in_parallel }} |
| Daya Surya | {{ cfg.panel_info.solar_power | times: 100 }}% |
| MPPT | {{ mppt_choice | replace: "_", " " }} |
| Tegangan Input Maks MPPT | {{ mppt.max_input_voltage }} V |
| Arus Input Maks MPPT | {{ mppt.max_input_current }} A |
| Tegangan Keluaran Maks MPPT | {{ mppt.max_output_voltage }} V |
| Arus Keluaran Maks MPPT | {{ mppt.max_output_current }} A |
| Efisiensi MPPT | {{ mppt.efficiency | times: 100 }}% |

{% endif %}{% endfor %}

### Pengaturan Baterai

{% assign bat_choice = site.data.boat_rp2_circuit_setup.battery.choice %}
{% assign bat = site.data.components.Battery[bat_choice] %}
{% assign bat_setup = site.data.boat_rp2_circuit_setup.battery %}

Kimia baterai: **{{ bat_choice }}**

| Parameter | Nilai |
|-----------|-------|
| Tegangan Nominal Baterai | {{ bat.battery_voltage }} V |
| Tegangan Minimum | {{ bat.min_voltage }} V |
| Tegangan Maksimum | {{ bat.max_voltage }} V |
| Baterai dalam Seri | {{ bat_setup.battery_in_series }} |
| Baterai dalam Paralel | {{ bat_setup.battery_in_parallel }} |
| Tegangan Sistem (seri) | {{ bat.min_voltage | times: bat_setup.battery_in_series }} V – {{ bat.max_voltage | times: bat_setup.battery_in_series }} V |
| Arus Pengisian Maks | {{ bat.max_charge_current }} A |
| Arus Pelepasan Maks | {{ bat.max_discharge_current }} A |
| Kapasitas | {{ bat.capacity_ah }} Ah |
| SOC Awal | {{ bat_setup.current_soc | times: 100 }}% |

### Pengaturan Beban

{% for load_entry in site.data.boat_rp2_circuit_setup.load %}{% assign load_cfg = load_entry[1] %}{% assign load_choice = load_cfg.choice %}{% assign load_spec = site.data.components.Load[load_choice] %}

| Parameter | Nilai |
|-----------|-------|
| Motor | {{ load_choice | replace: "_", " " }} |
| Daya Total | {{ load_spec.total_power }} W |
| Tegangan Nominal | {{ load_spec.nominal_voltage }} V |

{% endfor %}

---

<br>

## Titik Operasi

Titik operasi keadaan tunak berdasarkan konfigurasi pengaturan rangkaian.

{% assign op = site.data.rp2_electrical_simulation_operating_point %}

### Ringkasan Bus DC

| Parameter | Nilai |
|-----------|-------|
| Tegangan Bus DC | {{ op.summary.data[0].voltage.total_dc_bus_voltage | round: 2 }} V |
| Total Arus Keluaran MPPT | {{ op.summary.data[0].current.total_mppt_output_current | round: 2 }} A |
| Arus Baterai (negatif = mengosongkan) | {{ op.summary.data[0].current.total_battery_input_current | round: 2 }} A |

### Keluaran MPPT

| Array MPPT | Tegangan Keluaran (V) | Arus Keluaran (A) | Daya Keluaran (W) |
|------------|------------------------|-------------------|-------------------|
{% for mppt in op.mppt_result.data %}| Array {{ mppt.array_index }} | {{ mppt.voltage.mppt_output | round: 2 }} | {{ mppt.current.mppt_output | round: 2 }} | {{ mppt.voltage.mppt_output | times: mppt.current.mppt_output | round: 0 }} |
{% endfor %}

### Keluaran Array Surya

| Array Surya | Tegangan Keluaran (V) | Arus Keluaran (A) | Daya Keluaran (W) |
|-------------|------------------------|-------------------|-------------------|
{% for solar in op.solar_result.data %}| Array {{ solar.array_index }} | {{ solar.voltage.solar_array_output | round: 2 }} | {{ solar.current.solar_array_output | round: 2 }} | {{ solar.voltage.solar_array_output | times: solar.current.solar_array_output | round: 0 }} |
{% endfor %}

### Status Baterai

| Parameter | Nilai |
|-----------|-------|
| Arus Baterai (per string) | {{ op.battery_result.data[0].current.p0_s0_battery | round: 2 }} A |
| Status | {% if op.battery_result.data[0].current.p0_s0_battery < 0 %}Mengosongkan{% else %}Mengisi{% endif %} |

### Beban

| Beban | Tegangan (V) | Arus (A) | Daya (W) |
|-------|--------------|----------|----------|
{% for load in op.load_result.data %}{% for v in load.voltage %}{% assign load_name = v[0] %}{% assign load_v = v[1] %}{% assign load_i = load.current[load_name] %}| {{ load_name }} | {{ load_v | round: 2 }} | {{ load_i | round: 2 }} | {{ load_v | times: load_i | round: 0 }} |
{% endfor %}{% endfor %}

### Konfigurasi Throttle

| Beban | Throttle |
|-------|----------|
{% for load_entry in site.data.boat_rp2_circuit_setup.load %}{% assign load_cfg = load_entry[1] %}| {{ load_cfg.choice | replace: "_", " " }} | {{ load_cfg.throttle | times: 100 }}% |
{% endfor %}

{% if op.error.data.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Kesalahan ({{ op.error.data.size }})</strong> — masalah ini dapat menyebabkan kerusakan pada sistem dan harus diselesaikan.
</div>

<details markdown="1">
<summary><strong>Kesalahan Titik Operasi ({{ op.error.data.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

| Pesan Kesalahan |
|----------------|
{% for e in op.error.data %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if op.warning.data.size > 0 %}
<details markdown="1">
<summary><strong>Peringatan Titik Operasi ({{ op.warning.data.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

| # | Peringatan |
|---|------------|
{% for w in op.warning.data %}{% for warning in w %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

{% if op.error.data.size == 0 and op.warning.data.size == 0 %}
> **✓** Tidak ada kesalahan atau peringatan pada titik operasi ini.
{% endif %}

---

<br> 

## Sapuan: Throttle vs Respons Kelistrikan (Tanpa Surya)

Simulasi menyapu throttle dari 0% hingga 100% tanpa masukan surya, menunjukkan bagaimana sistem kelistrikan merespons variasi beban motor hanya dengan daya baterai.

<div style="max-width: 800px; margin: 2em auto;">
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_throttle.Voltage vs Throttle Input (%).png' | relative_url }}" alt="Tegangan vs Throttle" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Tegangan vs Masukan Throttle</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_throttle.Current vs Throttle Input (%).png' | relative_url }}" alt="Arus vs Throttle" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Arus vs Masukan Throttle</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_throttle.Power vs Throttle Input (%).png' | relative_url }}" alt="Daya vs Throttle" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Daya vs Masukan Throttle</p>
  </div>
</div>

{% assign throttle_errors = site.data.rp2_electrical_simulation_sweep_throttle_sweep_simulation_errors %}
{% assign throttle_warnings = site.data.rp2_electrical_simulation_sweep_throttle_sweep_simulation_warnings %}

{% if throttle_errors.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Kesalahan ({{ throttle_errors.size }})</strong> — masalah ini dapat menyebabkan kerusakan pada sistem dan harus diselesaikan.
</div>

<details markdown="1">
<summary><strong>Kesalahan Sapuan Throttle ({{ throttle_errors.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

| Pesan Kesalahan |
|----------------|
{% for e in throttle_errors %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if throttle_warnings.size == 0 and throttle_errors.size == 0 %}
> **✓** Tidak ada kesalahan atau peringatan yang dihasilkan selama sapuan throttle.
{% elsif throttle_warnings.size > 0 %}
<details markdown="1">
<summary><strong>Peringatan Sapuan Throttle ({{ throttle_warnings.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

| Masukan Throttle | Peringatan |
|------------------|------------|
{% for w in throttle_warnings %}{% for warning in w.warnings %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

---

<br>

## Sapuan: Daya Panel vs Respons Kelistrikan (Throttle Penuh)

Simulasi menyapu keluaran panel surya dari 0% hingga 100% pada throttle penuh, menunjukkan bagaimana peningkatan kontribusi surya mengurangi pelepasan baterai.

<div style="max-width: 800px; margin: 2em auto;">
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_panel_power.Voltage vs Panel Power (%).png' | relative_url }}" alt="Tegangan vs Daya Panel" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Tegangan vs Daya Panel</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_panel_power.Current vs Panel Power (%).png' | relative_url }}" alt="Arus vs Daya Panel" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Arus vs Daya Panel</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.sweep_panel_power.Power vs Panel Power (%).png' | relative_url }}" alt="Daya vs Daya Panel" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Daya vs Daya Panel</p>
  </div>
</div>

{% assign panel_errors = site.data.rp2_electrical_simulation_sweep_panel_power_sweep_simulation_errors %}
{% assign panel_warnings = site.data.rp2_electrical_simulation_sweep_panel_power_sweep_simulation_warnings %}

{% if panel_errors.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Kesalahan ({{ panel_errors.size }})</strong> — masalah ini dapat menyebabkan kerusakan pada sistem dan harus diselesaikan.
</div>

<details markdown="1">
<summary><strong>Kesalahan Sapuan Daya Panel ({{ panel_errors.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

| Pesan Kesalahan |
|----------------|
{% for e in panel_errors %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if panel_warnings.size > 0 %}
<details markdown="1">
<summary><strong>Peringatan Sapuan Daya Panel ({{ panel_warnings.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

Pada tingkat daya surya rendah, arus pelepasan baterai melebihi batas maksimum yang dikonfigurasikan. Simulasi secara otomatis membatasi throttle motor untuk melindungi baterai:

| Daya Surya | Peringatan |
|------------|------------|
{% for w in panel_warnings %}{% for warning in w.warnings %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

---

<br>

## Simulasi Pelayaran

{% assign voyage = site.data.voyage_setup %}

### Profil Pelayaran: {{ voyage.voyage_info.name }}

SOC awal baterai: **{{ voyage.initial_battery_soc | times: 100 }}%**

| Segmen | Durasi | Throttle | Daya Surya |
|--------|--------|----------|------------|
{% for seg in voyage.segments %}| {{ seg.name }} | {{ seg.duration_minutes }} min | {{ seg.throttle | times: 100 }}% | {{ seg.solar_power | times: 100 }}% |
{% endfor %}

{% assign total_min = 0 %}{% for seg in voyage.segments %}{% assign total_min = total_min | plus: seg.duration_minutes %}{% endfor %}
**Durasi total pelayaran: {{ total_min }} menit ({{ total_min | divided_by: 60 }} jam {{ total_min | modulo: 60 }} min)**

<div style="max-width: 800px; margin: 2em auto;">
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Voltage vs Time (minutes).png' | relative_url }}" alt="Tegangan vs Waktu" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Tegangan vs Waktu</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Current vs Time (minutes).png' | relative_url }}" alt="Arus vs Waktu" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Arus vs Waktu</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Power vs Time (minutes).png' | relative_url }}" alt="Daya vs Waktu" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Daya vs Waktu</p>
  </div>
  <div style="margin-bottom: 2em;">
    <img src="{{ '/renders/rp2.electrical_simulation.voyage.Battery Capacity vs Time (minutes).png' | relative_url }}" alt="Kapasitas Baterai vs Waktu" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Kapasitas Baterai vs Waktu</p>
  </div>
</div>

{% assign voyage_errors = site.data.rp2_electrical_simulation_voyage_sweep_simulation_errors %}
{% assign voyage_warnings = site.data.rp2_electrical_simulation_voyage_sweep_simulation_warnings %}

{% if voyage_errors.size > 0 %}
<div style="background: #fdd; border-left: 4px solid #d00; padding: 0.5em 1em; margin: 1em 0;">
<strong>⛔ Kesalahan ({{ voyage_errors.size }})</strong> — masalah ini dapat menyebabkan kerusakan pada sistem dan harus diselesaikan.
</div>

<details markdown="1">
<summary><strong>Kesalahan Pelayaran ({{ voyage_errors.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

| Pesan Kesalahan |
|----------------|
{% for e in voyage_errors %}| {{ e }} |
{% endfor %}

</details>
{% endif %}

{% if voyage_warnings.size > 0 %}
<details markdown="1">
<summary><strong>Peringatan Pelayaran ({{ voyage_warnings.size }})</strong> - Klik untuk tampilkan/sembunyikan</summary>

Selama pelayaran, batas pelepasan baterai terlampaui pada beberapa titik karena throttle tinggi dengan masukan surya terbatas atau tidak ada. Throttle motor secara otomatis dibatasi:

| Waktu (min) | Peringatan |
|-------------|------------|
{% for w in voyage_warnings %}{% for warning in w.warnings %}| {{ w.x | round: 1 }} | {{ warning }} |
{% endfor %}{% endfor %}

</details>
{% endif %}

---

[← Kembali ke Ikhtisar RP2]({{ '/id/rp2.html' | relative_url }}) | [Lihat Analisis Stabilitas dan Daya Apung →]({{ '/id/stability_rp2.html' | relative_url }})
