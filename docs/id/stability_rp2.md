---
layout: default
title: Analisis Stabilitas & Daya Apung - Roti Proa II
lang: id
---

[← Kembali ke Ikhtisar Roti Proa II]({{ '/id/rp2.html' | relative_url }})

---

## Analisis Daya Apung

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1em; margin: 2em 0;">
  <div>
    <img src="{{ '/renders/rp2.beaching.buoyancy_design.render.front.png' | relative_url }}" alt="Kesetimbangan daya apung - tampak depan" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Tampak depan pada kesetimbangan</p>
  </div>
  <div>
    <img src="{{ '/renders/rp2.beaching.buoyancy_design.render.right.png' | relative_url }}" alt="Kesetimbangan daya apung - tampak samping" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
    <p style="text-align: center; font-size: 0.9em; color: #666; margin-top: 0.5em;">Tampak samping pada kesetimbangan</p>
  </div>
</div>

Kesetimbangan daya apung dihitung menggunakan metode Newton, secara iteratif menyesuaikan roll/pitch/z-offset kapal sampai pusat dan jumlah daya apung sesuai dengan pusat dan jumlah massa. Analisis menggunakan konfigurasi beaching (tanpa layar, kemudi diangkat).

### Posisi Kesetimbangan

| Parameter | Nilai |
|-----------|-------|
| Z-offset (sarat) | {{ site.data.rp2_beaching_buoyancy.equilibrium.z_offset_mm }} mm |
| Pitch | {{ site.data.rp2_beaching_buoyancy.equilibrium.pitch_deg }}° |
| Roll | {{ site.data.rp2_beaching_buoyancy.equilibrium.roll_deg }}° |
| Iterasi untuk konvergen | {{ site.data.rp2_beaching_buoyancy.iterations }} |

### Vaka (Lambung Utama)

| Parameter | Nilai |
|-----------|-------|
| Volume terendam | {{ site.data.rp2_beaching_buoyancy.vaka.submerged_volume_liters }} liter |
| Volume total | {{ site.data.rp2_beaching_buoyancy.vaka.total_volume_liters }} liter |
| Persentase terendam | {{ site.data.rp2_beaching_buoyancy.vaka.submerged_percent }}% |
| Posisi Z (dunia) | {{ site.data.rp2_beaching_buoyancy.vaka.z_world_mm }} mm |

### Ama (Pelampung Cadik)

| Parameter | Nilai |
|-----------|-------|
| Volume terendam | {{ site.data.rp2_beaching_buoyancy.ama.submerged_volume_liters }} liter |
| Volume total | {{ site.data.rp2_beaching_buoyancy.ama.total_volume_liters }} liter |
| Persentase terendam | {{ site.data.rp2_beaching_buoyancy.ama.submerged_percent }}% |
| Posisi Z (dunia) | {{ site.data.rp2_beaching_buoyancy.ama.z_world_mm }} mm |

### Pusat Massa dan Daya Apung

| Titik | X (mm) | Y (mm) | Z (mm) |
|-------|--------|--------|--------|
| Pusat Gravitasi | {{ site.data.rp2_beaching_buoyancy.center_of_gravity_world.x }} | {{ site.data.rp2_beaching_buoyancy.center_of_gravity_world.y }} | {{ site.data.rp2_beaching_buoyancy.center_of_gravity_world.z }} |
| Pusat Daya Apung | {{ site.data.rp2_beaching_buoyancy.center_of_buoyancy.x }} | {{ site.data.rp2_beaching_buoyancy.center_of_buoyancy.y }} | {{ site.data.rp2_beaching_buoyancy.center_of_buoyancy.z }} |

Lihat [implementasi](https://github.com/solar-proa/CAD/blob/main/src/buoyancy/__main__.py).

---

## Analisis Stabilitas (Kurva GZ)

Kurva GZ (kurva lengan penegak) menunjukkan bagaimana stabilitas kapal bervariasi dengan sudut kemiringan. Untuk setiap sudut kemiringan, kami menghitung garis air kesetimbangan (di mana daya apung sama dengan berat) dan mengukur jarak horizontal antara pusat daya apung (CoB) dan pusat gravitasi (CoG). Jarak ini—lengan penegak GZ—dikalikan dengan displacement memberikan momen penegak yang mengembalikan kapal ke kesetimbangan.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/renders/rp2.beaching.gz.png' | relative_url }}" alt="Kurva GZ" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Karakteristik Stabilitas Asimetris

Sebagai proa dengan cadik (ama), kapal ini memiliki stabilitas asimetris:

**Ke arah ama (kemiringan positif):** Ama memberikan leverage daya apung yang substansial saat terendam.

| Parameter | Nilai |
|-----------|-------|
| Lengan penegak maksimum | {{ site.data.rp2_beaching_gz.summary.max_gz_m | times: 100 | round: 0 }} cm |
| Sudut GZ maksimum | {{ site.data.rp2_beaching_gz.summary.max_gz_angle_deg }}° |
| Sudut turtle | {{ site.data.rp2_beaching_gz.summary.turtle_angle_deg }}° |

**Menjauhi ama (kemiringan negatif):** Stabilitas berasal dari berat ama yang terangkat bertindak sebagai penyeimbang.

| Parameter | Nilai |
|-----------|-------|
| Sudut capsize | {{ site.data.rp2_beaching_gz.summary.capsize_angle_deg }}° |
| Sudut engagement ama | {{ site.data.rp2_beaching_gz.summary.ama_engagement_angle_deg }}° |
| Rentang stabilitas positif | {{ site.data.rp2_beaching_gz.summary.range_of_positive_stability_deg }}° |

### Amplop Operasi

Secara tradisional, proa berlayar dengan ama di sisi angin. Gaya angin memiringkan kapal menjauhi ama, mengangkatnya (sebagian atau bahkan sepenuhnya) keluar dari air untuk mengurangi hambatan ("flying the ama"). Amplop operasi biasanya kemiringan -5° hingga -20° dalam kasus tersebut, dengan baik dalam wilayah stabil.

Proa _surya_ harus dapat berlayar dengan baik juga dengan ama di sisi bawah angin, untuk menjaga layar dari membayangi panel surya. Pada sudut kemiringan sekitar 4°, ama akan sepenuhnya terendam dan menyebabkan hambatan maksimum tetapi masih menginduksi momen penegak yang signifikan sampai sudut turtle tercapai.

---

## Periode Natural (Seakeeping)

Gerakan kapal dalam gelombang ditandai oleh periode natural untuk roll, pitch, dan heave. Ini adalah **perkiraan kasar** menggunakan rumus empiris sederhana; rumus arsitektur naval standar yang dilinearkan tidak berlaku dengan baik untuk lambung proa asimetris. Pengujian fisik direkomendasikan untuk nilai yang akurat.

| Gerakan | Periode | Rumus | Deskripsi |
|---------|---------|-------|-----------|
| Roll | {{ site.data.rp2_beaching_gz.natural_periods.roll_period_s }} s | T ≈ 0.35 × lebar | Osilasi sisi-ke-sisi terhadap sumbu longitudinal |
| Pitch | {{ site.data.rp2_beaching_gz.natural_periods.pitch_period_s }} s | T ≈ 0.4√LOA + 1.5 | Osilasi depan-belakang terhadap sumbu transversal |
| Heave | {{ site.data.rp2_beaching_gz.natural_periods.heave_period_s }} s | T = 2π√(m/ρgA<sub>wp</sub>) | Osilasi vertikal |

### Pertimbangan Kenyamanan

- **Periode roll pendek** (~2s): Mencerminkan lebar beam yang menyediakan stabilitas awal yang tinggi. Gerakan akan cepat dan tajam.
- **Periode pitch sedang** (~2.7s): Tipikal untuk multihull ringan dengan panjang ini.
- **Periode heave pendek** (~1s): Karakteristik lambung ringan dan sempit.

Untuk kenyamanan penumpang, periode roll 6-12 detik biasanya lebih disukai. Periode roll pendek kapal ini menunjukkan gerakan kaku—kapal kembali tegak dengan cepat tetapi mungkin terasa tersentak-sentak di laut melintang.

**Pertimbangan kritis:** Jika periode gelombang di area operasi adalah 3-6 detik (tipikal untuk perairan pantai), kapal mungkin mengalami resonansi pitch, yang bisa tidak nyaman bagi penumpang.

Lihat [implementasi](https://github.com/solar-proa/CAD/blob/main/src/gz/__main__.py).

---

[← Kembali ke Ikhtisar RP2]({{ '/id/rp2.html' | relative_url }}) | [Lihat Analisis Struktural →]({{ '/id/validation_rp2.html' | relative_url }})
