---
layout: default
title: Roti Proa II - Kapal Wisata Harian 9m
lang: id
---

<div style="display: flex; align-items: center; gap: 2em; margin-bottom: 2em; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 300px;">
    <h1 style="margin: 0;">Roti Proa II</h1>
    <h2 style="margin-top: 0.5em; font-weight: 300;">Kapal Wisata Harian Surya-Listrik 9 Meter</h2>
  </div>
  <div style="flex: 1; min-width: 300px; max-width: 500px;">
    <img src="{{ '/renders/rp2.closehaul.render.isometric.png' | relative_url }}" alt="Roti Proa II" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  </div>
</div>

[← Kembali ke Beranda]({{ '/id/' | relative_url }})

---

## Desain

Roti Proa II adalah kapal daysailer 9m yang menggabungkan rencana badan dasar proa Pasifik dengan material fiberglass, PVC, dan aluminium untuk mencapai konsep kapal yang dapat dikonfigurasi dan diskalakan.

**[Lihat Spesifikasi Desain Lengkap →]({{ '/id/design_rp2.html' | relative_url }})**

**Konstruksi Lambung:**
- Konstruksi fiberglass profesional oleh pembuat kapal Singapura
- Dioptimalkan untuk efisiensi propulsi listrik
- Pengiriman dijadwalkan pertengahan Februari 2026

**Sistem Surya-Listrik:**
- 8 x panel surya 500W (total 4kW)
- Sistem listrik 48V
- Motor listrik 4kW yang disponsori
- Manajemen baterai terintegrasi

**Rig Layar:**
- Dua tiang aluminium tanpa stay
- Layar persegi panjang terinspirasi tanja tradisional
- Konfigurasi shunting untuk kondisi tropis
- Kemampuan propulsi cadangan

**Cadik (Ama):**
- Konstruksi balok silang aluminium (aka)
- Konstruksi pelampung pipa PVC
- Pemasangan panel surya yang dioptimalkan
- Stabilitas yang ditingkatkan untuk kenyamanan penumpang

---

## Stabilitas & Daya Apung

Stabilitas kapal telah dianalisis menggunakan perhitungan kesetimbangan daya apung otomatis dan kurva GZ.

**[Lihat Analisis Stabilitas & Daya Apung Lengkap →]({{ '/id/stability_rp2.html' | relative_url }})**

| Parameter | Nilai | Deskripsi |
|-----------|-------|-----------|
| Sarat | {{ site.data.rp2_beaching_buoyancy.equilibrium.z_offset_mm }} mm | Kedalaman di bawah garis air pada kesetimbangan |
| Lengan penegak maks | {{ site.data.rp2_beaching_gz.summary.max_gz_m | times: 100 | round: 0 }} cm | Pada kemiringan {{ site.data.rp2_beaching_gz.summary.max_gz_angle_deg }}° |
| Sudut capsize | {{ site.data.rp2_beaching_gz.summary.capsize_angle_deg }}° | Menjauhi ama |
| Sudut turtle | {{ site.data.rp2_beaching_gz.summary.turtle_angle_deg }}° | Menuju ama |
| Periode roll | {{ site.data.rp2_beaching_gz.natural_periods.roll_period_s }} s | Perkiraan kasar |
| Periode pitch | {{ site.data.rp2_beaching_gz.natural_periods.pitch_period_s }} s | Perkiraan kasar |
| Periode heave | {{ site.data.rp2_beaching_gz.natural_periods.heave_period_s }} s | Perkiraan kasar |

---

## Validasi Struktural

Integritas struktural kapal telah divalidasi di bawah beberapa skenario beban termasuk beban statis, dampak gelombang, gaya angin, dan operasi crane. Semua tes lulus dengan faktor keamanan melebihi minimum yang diperlukan yaitu 2,0.

**[Lihat Laporan Keselamatan Struktural Lengkap →]({{ '/id/validation_rp2.html' | relative_url }})**

| Tes | Faktor Keamanan | Hasil |
|-----|-----------------|-------|
| Ama tergantung (lentur aka) | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.result }} |
| Beban titik aka (kru berdiri) | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.result }} |
| Satu ujung ditopang (lentur spine) | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.result }} |
| Beban angin tiang (25 knot) | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.result }} |
| Penopang diagonal (lateral) | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.result }} |
| Hantaman gelombang (vertikal) | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.result }} |
| Hantaman gelombang frontal | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.result }} |
| Hantaman gelombang samping | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.result }} |
| Sling pengangkat (crane) | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.result }} |
| Beban gunwale | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.result }} |
| Kecepatan angin angkat ama | {{ site.data.rp2_beaching_validate_structure.tests[10].summary.ama_lift_windspeed_knots }} knot | INFO |

---

## Konfigurasi

Kapal dapat dikonfigurasi untuk berbagai kondisi pelayaran dan kasus penggunaan:

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; margin: 2em 0;">
{% for config in site.data.configurations %}
  <div style="border: 1px solid #ddd; padding: 1em; border-radius: 4px;">
    <h4>{{ config.display_name_id }}</h4>
    <p style="font-size: 0.9em; color: #666;">{{ config.description_id }}</p>
  </div>
{% endfor %}
</div>

---

## Status Proyek

**Fase Saat Ini:** Dalam Konstruksi

**Selesai:**
- ✅ Desain CAD detail dan optimasi
- ✅ Pesanan lambung ditempatkan ke pembuat kapal
- ✅ Struktur cadik sedang berlangsung
- ✅ Desain sistem listrik
- ✅ Pengadaan komponen

**Langkah Selanjutnya:**
- Pengiriman lambung (Februari 2026)
- Perakitan akhir (Maret-April 2026)
- Uji coba laut (Mei-Juni 2026)
- Validasi komersial dengan mitra (Q3 2026)

---

[← Kembali ke Beranda]({{ '/id/' | relative_url }}) | [Lihat RP1 →]({{ '/id/rp1.html' | relative_url }}) | [Lihat RP3 →]({{ '/id/rp3.html' | relative_url }})
