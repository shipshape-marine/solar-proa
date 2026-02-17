---
layout: default
title: Roti Proa II - Laporan Keselamatan Struktural
description: Kapal Hibrida Bertenaga Angin-Surya untuk Daerah Tropis
lang: id
---

# Laporan Keselamatan Struktural: Roti Proa II

Laporan ini mendokumentasikan analisis validasi struktural untuk Roti Proa II (RP2), kapal wisata harian surya-listrik 9 meter. Semua analisis menggunakan **konfigurasi beaching** (layar digulung, kemudi diangkat) yang mewakili kapal dalam kondisi diam paling umum.

**Tanggal Validasi:** Dihasilkan secara otomatis dari model CAD
**Faktor Keamanan yang Diperlukan:** {{ site.data.rp2_beaching_validate_structure.min_safety_factor_required }}
**Hasil Keseluruhan:** {% if site.data.rp2_beaching_validate_structure.passed %}**LULUS**{% else %}**GAGAL**{% endif %}

[← Kembali ke Ringkasan RP2]({{ '/id/rp2.html' | relative_url }})

---

## Daftar Isi

1. [Ringkasan Eksekutif](#ringkasan-eksekutif)
2. [Ama Tergantung (Lentur Aka)](#1-ama-tergantung-lentur-aka)
3. [Beban Titik Aka (Kru Berdiri)](#2-beban-titik-aka-kru-berdiri)
4. [Satu Ujung Ditopang (Lentur Spine)](#3-satu-ujung-ditopang-lentur-spine)
5. [Beban Angin Tiang](#4-beban-angin-tiang)
6. [Penopang Diagonal (Beban Lateral)](#5-penopang-diagonal-beban-lateral)
7. [Hantaman Gelombang (Vertikal)](#6-hantaman-gelombang-vertikal)
8. [Hantaman Gelombang Frontal](#7-hantaman-gelombang-frontal)
9. [Hantaman Gelombang Samping](#8-hantaman-gelombang-samping)
10. [Sling Pengangkat (Operasi Crane)](#9-sling-pengangkat-operasi-crane)
11. [Distribusi Beban Gunwale](#10-distribusi-beban-gunwale)
12. [Kecepatan Angin Angkat Ama](#11-kecepatan-angin-angkat-ama-informasional)
13. [Ringkasan Penilaian Keselamatan](#ringkasan-penilaian-keselamatan)

---

## Ringkasan Eksekutif

Rangkaian validasi struktural RP2 menganalisis kapal di bawah sebelas skenario beban yang mencakup beban statis, dampak gelombang dinamis, gaya angin, dan kondisi operasional. Semua tes struktural lulus dengan faktor keamanan melebihi minimum yang diperlukan yaitu 2,0.

| Tes | Deskripsi | Faktor Keamanan | Hasil |
|-----|-----------|-----------------|-------|
| Ama Tergantung | Lentur kantilever aka | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.result }} |
| Beban Titik Aka | Kru berdiri di aka | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[1].summary.result }} |
| Satu Ujung Ditopang | Lentur spine | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[2].summary.result }} |
| Beban Angin Tiang | Angin 25 knot pada layar | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[3].summary.result }} |
| Penopang Diagonal | Beban lateral (miring) | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[4].summary.result }} |
| Hantaman Gelombang (Vertikal) | Dampak 3 m/s, dinamis 2,5× | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[5].summary.result }} |
| Hantaman Gelombang Frontal | Dampak depan-belakang | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[6].summary.result }} |
| Hantaman Gelombang Samping | Dampak lateral | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[7].summary.result }} |
| Sling Pengangkat | Angkat crane V-sling | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[8].summary.result }} |
| Beban Gunwale | Distribusi beban ke lambung | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.min_safety_factor }} | {{ site.data.rp2_beaching_validate_structure.tests[9].summary.result }} |
| Kecepatan Angin Angkat Ama | Batas stabilitas | {{ site.data.rp2_beaching_validate_structure.tests[10].summary.ama_lift_windspeed_knots }} knot | INFO |

---

## 1. Ama Tergantung (Lentur Aka)

### Skenario

Cadik (ama) kehilangan semua dukungan daya apung—misalnya, ketika kapal miring sehingga ama terangkat sepenuhnya keluar dari air, atau selama transportasi di trailer. Seluruh berat struktur cadik tergantung dari aka (balok silang), yang bertindak sebagai kantilever yang memanjang dari vaka (lambung utama).

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/suspended_ama.png' | relative_url }}" alt="ama tergantung" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Setiap aka dimodelkan sebagai balok kantilever yang terjepit di gunwale vaka. Massa cadik dibagi menjadi:
- **Beban ujung**: Massa terkonsentrasi di ujung aka (ujung ama, tepi panel surya, dasar pilar)
- **Beban terdistribusi**: Massa tersebar sepanjang panjang aka (panel surya, kabel, elemen struktural)

Momen lentur pada sambungan vaka adalah:

$$M = F_{ujung} \times L + F_{terdistribusi} \times \frac{L}{2}$$

di mana *L* adalah panjang kantilever dari vaka ke pilar. Tegangan lentur dihitung menggunakan teori balok:

$$\sigma = \frac{M}{S}$$

di mana *S* adalah modulus penampang dari penampang berongga persegi panjang (RHS) aka.

### Asumsi

- Penampang aka: {{ site.data.rp2_beaching_validate_structure.tests[0].summary.aka_dimensions }}
- Material: Aluminium 6061-T6 (kekuatan luluh 240 MPa)
- Empat aka berbagi beban secara merata
- Tumpuan terjepit di vaka (konservatif—sambungan aktual memiliki beberapa kelenturan)
- Sumbu kuat (tinggi 101,6 mm) menahan lentur vertikal

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Massa cadik | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.outrigger_mass_kg }} kg |
| Panjang kantilever | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.cantilever_length_m }} m |
| Tegangan lentur maksimum | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.max_stress_mpa }} MPa |
| Defleksi maksimum | {{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.max_deflection_mm }} mm |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[0].summary.strong_axis.safety_factor }}** |

---

## 2. Beban Titik Aka (Kru Berdiri)

### Skenario

Selama naik kapal, pemeliharaan, atau situasi darurat, anggota kru mungkin perlu berdiri di aka. Tes ini memvalidasi kapasitas aka untuk menopang berat kru terkonsentrasi di lokasi terburuk (tengah bentang).

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/aka_point_load.png' | relative_url }}" alt="beban titik aka" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Aka dimodelkan sebagai balok dengan tumpuan sederhana dengan:
- Tumpuan di gunwale vaka (dalam)
- Tumpuan di pilar (luar, di ama)

Beban titik di tengah bentang menghasilkan momen lentur maksimum:

$$M_{max} = \frac{P \times L}{4}$$

di mana *P* adalah berat kru dan *L* adalah bentang antara tumpuan.

### Asumsi

- Massa kru: {{ site.data.rp2_beaching_validate_structure.tests[1].crew_mass_kg }} kg (sekitar dua orang)
- Posisi beban: tengah bentang (kasus terburuk)
- Kondisi tumpuan sederhana (konservatif untuk perhitungan momen)

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Bentang (vaka ke pilar) | {{ site.data.rp2_beaching_validate_structure.tests[1].geometry.span_mm | divided_by: 1000.0 | round: 2 }} m |
| Beban titik | {{ site.data.rp2_beaching_validate_structure.tests[1].loading.point_load_n | round: 0 }} N |
| Tegangan lentur maksimum | {{ site.data.rp2_beaching_validate_structure.tests[1].analysis.max_stress_mpa }} MPa |
| Defleksi maksimum | {{ site.data.rp2_beaching_validate_structure.tests[1].analysis.max_deflection_mm }} mm |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[1].summary.safety_factor }}** |

---

## 3. Satu Ujung Ditopang (Lentur Spine)

### Skenario

Ama ditopang di satu ujung saja (misalnya, beristirahat di pantai atau dermaga) sementara ujung lainnya menggantung bebas. Ini menciptakan lentur pada spine (balok longitudinal yang menghubungkan bagian ama) saat aka memberikan dukungan perantara dengan kekakuan bervariasi.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/one_end_supported.png' | relative_url }}" alt="satu ujung ditopang" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Ama dimodelkan sebagai balok kontinu dengan:
- Tumpuan terjepit di satu ujung (kontak pantai/dermaga)
- Tumpuan elastis di setiap lokasi aka (fleksibilitas aka dimodelkan sebagai pegas)
- Beban terdistribusi dari struktur cadik

Kekakuan pegas aka diturunkan dari defleksi balok kantilever:

$$k_{aka} = \frac{3EI}{L^3}$$

Analisis distribusi momen menentukan reaksi di setiap tumpuan dan momen lentur maksimum pada spine.

### Asumsi

- Penampang spine: SHS 76,2×76,2×4,5 mm aluminium
- Empat aka dengan jarak sama sepanjang spine
- Satu ujung sepenuhnya terjepit (konservatif)
- Kekakuan aka dihitung dari properti kantilever

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Panjang spine | {{ site.data.rp2_beaching_validate_structure.tests[2].geometry.spine_length_mm | divided_by: 1000.0 | round: 2 }} m |
| Total massa cadik | {{ site.data.rp2_beaching_validate_structure.tests[2].ama_analysis.total_outrigger_mass_kg }} kg |
| Tegangan spine maksimum | {{ site.data.rp2_beaching_validate_structure.tests[2].spine_analysis.max_stress_mpa }} MPa |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[2].summary.safety_factor }}** |

---

## 4. Beban Angin Tiang

### Skenario

Tiang mengalami beban lentur yang signifikan saat berlayar dalam angin kencang. Gaya layar bekerja pada pusat usaha (CE), menciptakan momen terhadap mast partner (tumpuan setingkat dek).

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/mast_wind.png' | relative_url }}" alt="angin tiang" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Gaya angin pada layar diestimasi menggunakan:

$$F = \frac{1}{2} \rho V^2 C_d A$$

di mana *ρ* adalah kerapatan udara, *V* adalah kecepatan angin, *C_d* adalah koefisien hambatan, dan *A* adalah luas layar. Tiang dianalisis untuk:
- Tegangan lentur di partner
- Tegangan geser di partner
- Interaksi aksial-lentur gabungan (tekuk kolom)
- Tekuk lokal (pemeriksaan rasio D/t)

### Asumsi

- Kecepatan angin: {{ site.data.rp2_beaching_validate_structure.tests[3].wind_speed_knots }} knot
- Layar tegak lurus terhadap angin (gaya maksimum)
- Penampang tiang: diameter {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.mast_diameter_mm }} mm × dinding {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.mast_thickness_mm }} mm
- Material: Aluminium 6061-T6
- Tiang tanpa stay (tanpa shroud atau stay)

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Luas layar | {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.sail_area_m2 }} m² |
| Gaya angin | {{ site.data.rp2_beaching_validate_structure.tests[3].wind_force_n | round: 0 }} N |
| Tegangan lentur di partner | {{ site.data.rp2_beaching_validate_structure.tests[3].checks.bending_at_partner.stress_mpa }} MPa |
| Rasio D/t | {{ site.data.rp2_beaching_validate_structure.tests[3].geometry.d_over_t }} (< 50 OK) |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[3].summary.safety_factor }}** |

---

## 5. Penopang Diagonal (Beban Lateral)

### Skenario

Ketika kapal miring (di sisinya selama beaching, atau terbalik setelah capsize), berat cadik menciptakan gaya lateral pada penopang diagonal yang menghubungkan pilar ke aka. Penopang ini harus menahan kompresi dan tarik tergantung pada orientasi.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/diagonal_braces.png' | relative_url }}" alt="penopang diagonal" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Gaya lateral sama dengan berat cadik ketika kapal sepenuhnya di sisinya:

$$F_{lateral} = m_{cadik} \times g$$

Gaya ini didistribusikan di antara semua penopang diagonal. Setiap penopang diperiksa untuk:
- **Kompresi**: Tekuk Euler dan luluh tekan
- **Tarik**: Luluh tarik

Mode kritis adalah tekuk Euler untuk elemen kompresi langsing:

$$\sigma_{cr} = \frac{\pi^2 E}{(L/r)^2}$$

di mana *L/r* adalah rasio kelangsingan.

### Asumsi

- Penampang penopang: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.section }}
- Panjang penopang: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.length_mm | round: 0 }} mm
- Sudut penopang: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.angle_deg }}° dari horizontal
- Jumlah penopang: {{ site.data.rp2_beaching_validate_structure.tests[4].brace_geometry.num_braces }}
- Sambungan berujung pin (konservatif untuk tekuk)

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Massa cadik | {{ site.data.rp2_beaching_validate_structure.tests[4].loading.outrigger_mass_kg }} kg |
| Gaya per penopang | {{ site.data.rp2_beaching_validate_structure.tests[4].compression_check.force_per_brace_n | round: 0 }} N |
| Rasio kelangsingan | {{ site.data.rp2_beaching_validate_structure.tests[4].compression_check.slenderness_ratio | round: 0 }} |
| Mode dominan | {{ site.data.rp2_beaching_validate_structure.tests[4].compression_check.governing_mode }} |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[4].summary.min_safety_factor }}** |

---

## 6. Hantaman Gelombang (Vertikal)

### Skenario

Saat berlayar dalam gelombang, ama dapat menghantam permukaan air dengan kecepatan signifikan, menciptakan beban hidrodinamik impulsif. Tes ini menganalisis hantaman gelombang vertikal—ama menghantam air dari atas.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/wave_slam_vertical.png' | relative_url }}" alt="hantaman gelombang vertikal" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Tekanan hantaman diestimasi menggunakan rumus palu air:

$$P = \frac{1}{2} \rho V^2 C_p$$

di mana *V* adalah kecepatan dampak dan *C_p* adalah koefisien tekanan. Faktor amplifikasi dinamis memperhitungkan respons struktural terhadap pembebanan impulsif.

Jalur beban adalah: **gelombang → pilar → penopang diagonal → aka → vaka**

Aka dimodelkan sebagai kantilever yang ditopang dengan:
- Tumpuan terjepit di vaka
- Tumpuan pegas elastis di sambungan penopang diagonal

### Asumsi

- Kecepatan dampak: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.impact_velocity_ms }} m/s
- Faktor dinamis: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.dynamic_factor }}×
- Koefisien hantaman: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.slam_coefficient }}
- Luas efektif ama: {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.effective_area_m2 }} m² (perendaman parsial)
- Penopang memberikan dukungan elastis ke aka

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Tekanan hantaman | {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.slam_pressure_kpa }} kPa |
| Total gaya hantaman | {{ site.data.rp2_beaching_validate_structure.tests[5].wave_slam.dynamic_slam_force_n | round: 0 }} N |
| Tegangan aka | {{ site.data.rp2_beaching_validate_structure.tests[5].checks.aka.combined_stress_mpa }} MPa (SF={{ site.data.rp2_beaching_validate_structure.tests[5].checks.aka.safety_factor }}) |
| Tegangan penopang | {{ site.data.rp2_beaching_validate_structure.tests[5].checks.diagonal_braces.compressive_stress_mpa }} MPa (SF={{ site.data.rp2_beaching_validate_structure.tests[5].checks.diagonal_braces.safety_factor }}) |
| Tegangan spine | {{ site.data.rp2_beaching_validate_structure.tests[5].checks.spine.max_stress_mpa }} MPa (SF={{ site.data.rp2_beaching_validate_structure.tests[5].checks.spine.safety_factor }}) |
| **Komponen Dominan** | **{{ site.data.rp2_beaching_validate_structure.tests[5].summary.governing_component }}** |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[5].summary.min_safety_factor }}** |

---

## 7. Hantaman Gelombang Frontal

### Skenario

Ama menghadapi gelombang secara langsung, menciptakan gaya dampak depan-belakang. Beban ini ditahan oleh penopang silang bentuk-X antara pilar bersebelahan.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/frontal_wave_slam.png' | relative_url }}" alt="hantaman gelombang frontal" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Gaya hantaman frontal dihitung dari luas penampang melintang ama. Penopang-X bekerja sebagai sistem tarik-saja: saat dibebani, diagonal kompresi tekuk (karena kelangsingan ekstrem), dan diagonal tarik membawa beban penuh.

Rasio kelangsingan penopang menentukan perilaku:

$$\lambda = \frac{L}{r} > 100 \implies \text{perilaku tarik-saja}$$

### Asumsi

- Luas frontal ama: {{ site.data.rp2_beaching_validate_structure.tests[6].frontal_slam.frontal_area_m2 }} m² (penampang lingkaran)
- Diameter penopang silang: {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.geometry.brace_diameter_mm }} mm (batang solid)
- Panjang penopang: {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.geometry.brace_length_mm | round: 0 }} mm
- Jumlah pasangan penopang-X: {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.geometry.num_x_brace_pairs }}
- Koefisien hantaman: {{ site.data.rp2_beaching_validate_structure.tests[6].frontal_slam.slam_coefficient }} (badan tumpul)

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Gaya hantaman frontal | {{ site.data.rp2_beaching_validate_structure.tests[6].frontal_slam.dynamic_slam_force_n | round: 0 }} N |
| Rasio kelangsingan | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.slenderness_ratio | round: 0 }} |
| Mode | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.governing_mode }} |
| Tarik per penopang | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.tension_force_per_brace_n | round: 0 }} N |
| Tegangan | {{ site.data.rp2_beaching_validate_structure.tests[6].checks.cross_braces.stress_mpa }} MPa |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[6].summary.min_safety_factor }}** |

---

## 8. Hantaman Gelombang Samping

### Skenario

Gelombang menghantam ama dari samping (melintang kapal), menciptakan gaya lateral. Penopang pilar diagonal menahan beban ini dalam kompresi.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/sideways_wave_slam.png' | relative_url }}" alt="hantaman gelombang samping" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Gaya hantaman lateral dihitung dari luas sisi proyeksi ama (panjang × diameter). Penopang diagonal mengambil komponen horizontal dari gaya ini.

### Asumsi

- Parameter hantaman sama dengan hantaman gelombang vertikal
- Penopang diagonal pada 45° mengambil beban horizontal
- Tekuk dominan untuk penopang kompresi

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Gaya hantaman samping | {{ site.data.rp2_beaching_validate_structure.tests[7].sideways_slam.dynamic_slam_force_n | round: 0 }} N |
| Gaya per penopang | {{ site.data.rp2_beaching_validate_structure.tests[7].checks.diagonal_braces.axial_force_per_brace_n | round: 0 }} N |
| Beban tekuk Euler | {{ site.data.rp2_beaching_validate_structure.tests[7].checks.diagonal_braces.euler_buckling_load_n | round: 0 }} N |
| **Faktor Keamanan** | **{{ site.data.rp2_beaching_validate_structure.tests[7].summary.min_safety_factor }}** |

---

## 9. Sling Pengangkat (Operasi Crane)

### Skenario

Kapal diangkat dengan crane untuk peluncuran, pengangkatan keluar, atau transportasi. Konfigurasi V-sling menggunakan 4 kait, masing-masing terhubung dengan dua tali ke aka bersebelahan, mendistribusikan beban ke seluruh elemen struktural.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/lifting_sling.png' | relative_url }}" alt="sling pengangkat" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

V-sling menciptakan 8 titik sambungan. Setiap tali membawa sebagian dari beban vertikal, dengan tegangan yang meningkat karena sudut-V:

$$T = \frac{F_{vertikal}}{\cos(\theta)}$$

Pemeriksaan meliputi:
- Lentur aka (semua 4 aka berpartisipasi)
- Tegangan lokal di titik sambungan sling
- Kapasitas tegangan tali/sling
- Lentur kapal global antara tumpuan

### Asumsi

- Total massa kapal: {{ site.data.rp2_beaching_validate_structure.tests[8].summary.total_mass_kg }} kg
- Sudut-V dari vertikal: {{ site.data.rp2_beaching_validate_structure.tests[8].sling_geometry.v_angle_deg }}°
- Tipe sling: Sling datar polyester 50mm (WLL 2000 kg)
- Jarak aka: {{ site.data.rp2_beaching_validate_structure.tests[8].sling_geometry.aka_spacing_m }} m

### Hasil

| Komponen | Tegangan/Beban | Faktor Keamanan |
|----------|---------------|-----------------|
| Lentur aka | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.aka_bending.max_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.aka_bending.safety_factor }} |
| Sambungan sling | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.sling_point.combined_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.sling_point.safety_factor }} |
| Tegangan tali | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.rope_tension.rope_tension_n | round: 0 }} N | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.rope_tension.safety_factor }} |
| Lentur global | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.global_bending.max_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[8].checks.global_bending.safety_factor }} |
| **Dominan** | **{{ site.data.rp2_beaching_validate_structure.tests[8].summary.governing_component }}** | **{{ site.data.rp2_beaching_validate_structure.tests[8].summary.min_safety_factor }}** |

---

## 10. Distribusi Beban Gunwale

### Skenario

Aka mentransfer semua beban cadik ke vaka melalui gunwale. Tes ini memvalidasi bahwa gunwale kayu (3" × 2", diikat fiberglass ke lambung) dapat membawa dan mendistribusikan beban aka yang terkonsentrasi.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/gunwale_loads.png' | relative_url }}" alt="beban gunwale" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Gunwale dimodelkan sebagai balok pada pondasi elastis. Panjang karakteristik di mana beban menyebar adalah:

$$\lambda = \left(\frac{4EI}{k}\right)^{0.25}$$

di mana *k* adalah kekakuan pondasi (kulit lambung menopang gunwale).

Pemeriksaan meliputi:
- Tegangan lentur gunwale
- Tegangan tumpu (kayu tegak lurus serat)
- Geser ikatan (sambungan fiberglass ke lambung)

### Asumsi

- Penampang gunwale: {{ site.data.rp2_beaching_validate_structure.tests[9].gunwale_section.width_mm | round: 1 }} × {{ site.data.rp2_beaching_validate_structure.tests[9].gunwale_section.height_mm }} mm
- Material: Douglas fir atau sejenisnya (lentur izin 50 MPa, tumpu 10 MPa)
- Geser ikatan fiberglass izin: 5 MPa
- Beban desain: hantaman gelombang (dominan atas ama tergantung statis)

### Hasil

| Pemeriksaan | Tegangan | Izin | Faktor Keamanan |
|-------------|----------|------|-----------------|
| Lentur gunwale | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bending.bending_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bending.allowable_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bending.safety_factor }} |
| Tumpu (tegak lurus serat) | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bearing.bearing_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bearing.allowable_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bearing.safety_factor }} |
| Geser ikatan | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bond_shear.shear_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bond_shear.allowable_stress_mpa }} MPa | {{ site.data.rp2_beaching_validate_structure.tests[9].checks.bond_shear.safety_factor }} |

**Distribusi Beban**: Jarak aka ({{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.aka_spacing_mm | round: 0 }} mm) adalah {{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.spacing_ratio }}× dari panjang distribusi ({{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.distribution_length_mm | round: 0 }} mm), sehingga beban **{{ site.data.rp2_beaching_validate_structure.tests[9].aka_spacing.interaction }}**.

---

## 11. Kecepatan Angin Angkat Ama (Informasional)

### Skenario

Perhitungan informasional ini menentukan kecepatan angin di mana momen kemiringan (angin dari sisi ama) sama dengan momen penegak maksimum, menyebabkan ama terangkat sepenuhnya dari air.

<div style="max-width: 800px; margin: 2em auto;">
  <img src="{{ '/diagrams/ama_lift_wind.png' | relative_url }}" alt="kecepatan angin angkat ama" style="width: 100%; border: 1px solid #ddd; border-radius: 4px;">
</div>

### Metode

Momen kemiringan dari gaya angin adalah:

$$M_{kemiringan} = F_{angin} \times h_{CE}$$

di mana *h_CE* adalah tinggi pusat usaha layar di atas sumbu kemiringan. Ini dibandingkan dengan momen penegak maksimum dari analisis kurva GZ.

### Hasil

| Parameter | Nilai |
|-----------|-------|
| Total luas layar | {{ site.data.rp2_beaching_validate_structure.tests[10].sail_geometry.total_sail_area_m2 }} m² |
| Tinggi CE | {{ site.data.rp2_beaching_validate_structure.tests[10].sail_geometry.ce_height_m }} m |
| Momen penegak maksimum | {{ site.data.rp2_beaching_validate_structure.tests[10].stability.max_righting_moment_nm | round: 0 }} N·m |
| **Kecepatan angin angkat ama** | **{{ site.data.rp2_beaching_validate_structure.tests[10].summary.ama_lift_windspeed_knots }} knot** |

*Catatan: Ini adalah kecepatan angin teoretis dengan layar penuh dan tanpa penyesuaian berat kru. Dalam praktiknya, kru dapat bergerak ke sisi angin dan layar dapat di-reef.*

---

## Ringkasan Penilaian Keselamatan

### Integritas Struktural Keseluruhan

Desain struktural Roti Proa II **lulus semua tes validasi** dengan faktor keamanan melebihi minimum yang diperlukan yaitu 2,0. Struktur mendemonstrasikan kekuatan dan kekakuan yang memadai untuk:

- **Operasi normal**: Berlayar, bermotor, berlabuh, beaching
- **Kejadian dinamis**: Dampak hantaman gelombang dari berbagai arah
- **Operasi penanganan**: Pengangkatan crane, transportasi trailer
- **Skenario darurat**: Capsize, kru di balok silang

### Jalur Beban Kritis

1. **Cadik ke Vaka**: Beban ditransfer melalui aka → gunwale → lambung
2. **Dampak Gelombang**: Gaya didistribusikan melalui pilar → penopang → aka
3. **Beban Angin**: Gaya layar ditransfer melalui tiang → partner → lambung

### Rekomendasi

1. **Titik Inspeksi**: Inspeksi berkala sambungan aka-gunwale, las penopang diagonal, dan ikatan fiberglass
2. **Operasi Pengangkatan**: Gunakan konfigurasi V-sling dengan 4 kait ke aka bersebelahan
3. **Batas Hantaman Gelombang**: Kecepatan dampak 3 m/s mewakili kondisi moderat; hindari kondisi gelombang ekstrem
4. **Batas Angin**: Tiang divalidasi untuk 25 knot; reef layar dalam kondisi lebih kencang

### Perangkat Lunak Validasi

Laporan ini dihasilkan secara otomatis dari model CAD parametrik menggunakan modul `validate-structure`. Kode sumber: [github.com/shipshape-marine/solar-proa](https://github.com/shipshape-marine/solar-proa/tree/main/src/structural)

---

[← Kembali ke Ringkasan RP2]({{ '/id/rp2.html' | relative_url }}) | [Lihat Analisis Stabilitas & Daya Apung →]({{ '/id/stability_rp2.html' | relative_url }})
