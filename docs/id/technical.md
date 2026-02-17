---
layout: default
title: Di Balik Layar - Detail Teknis
description: Kapal Hibrida Bertenaga Angin-Surya untuk Daerah Tropis
lang: id
---

# Di Balik Layar

Bagaimana sistem CAD Solar Proa bekerja.

[← Kembali ke Beranda]({{ '/id/' | relative_url }})

---

## Desain Parametrik

Semua desain kapal dibuat menggunakan **pemodelan CAD parametrik** - geometri didefinisikan oleh parameter (dimensi, sudut, posisi) daripada bentuk tetap. Ini berarti:

- **Ubah satu parameter, perbarui seluruh model** - Menyesuaikan panjang lambung secara otomatis menskalakan tiang, balok silang, dan tali-temali
- **Beberapa konfigurasi dari satu sumber** - Model dasar yang sama menghasilkan konfigurasi beaching, close-haul, broad reach, dan pelayaran lainnya
- **Transparansi desain** - Setiap dimensi dapat dilacak ke nilai parameter

Sistem menggunakan [FreeCAD](https://www.freecad.org/) (CAD sumber terbuka) dengan skrip Python yang membaca file parameter, membangun geometri 3D, dan mengekspor render dan file CAD.

---

## Pipeline Build

Proses build mengubah file parameter menjadi output siap-website melalui serangkaian tahap:

<div style="text-align: center; margin: 2em 0;">
  <img src="{{ '/dependency_graph.png' | relative_url }}" alt="Grafik Ketergantungan Pipeline Build" style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px; padding: 1em; background: white;">
  <p style="color: #666; font-size: 0.9em; margin-top: 0.5em;">Grafik ketergantungan dihasilkan otomatis dari Makefile</p>
</div>

**Deskripsi tahap:**

| Tahap | Input | Output | Deskripsi |
|-------|-------|--------|-----------|
| **parameter** | JSON Kapal + JSON Konfigurasi | Parameter gabungan | Menggabungkan dimensi kapal dengan konfigurasi layar (shipshape + plugin proyek) |
| **design** | Parameter | Model FreeCAD (.FCStd) | Membangun geometri 3D dari parameter |
| **mass** | Design (FreeCAD) | JSON properti massa | Menghitung volume, massa, dan daya apung (shipshape) |
| **color** | Design (FreeCAD) | Design berwarna | Menerapkan material dan warna untuk rendering |
| **buoyancy** | Design (FreeCAD), Properti massa | Properti daya apung | Mencari pose keseimbangan menggunakan iterasi Newton-Raphson (shipshape) |
| **gz** | Design (FreeCAD), Daya apung | JSON kurva GZ + PNG | Menghitung kurva lengan pemulih pada berbagai sudut kemiringan (shipshape) |
| **render** | Design berwarna (FreeCAD) | Gambar PNG | Menghasilkan tampilan isometrik, atas, depan, kanan |
| **step** | Model FreeCAD | File STEP | Mengekspor format CAD universal |
| **validate** | Parameter, Massa, GZ | JSON validasi | Validasi struktural: aka, tiang, tulang belakang, analisis terbalik |

---

## Konfigurasi

Setiap konfigurasi pelayaran didefinisikan oleh file JSON yang menentukan sudut layar, rotasi rig, dan parameter dinamis lainnya:

```
constant/configuration/
├── beaching.json      # Layar turun, di pantai
├── beamreach.json     # Berlayar melintang angin
├── broadreach.json    # Berlayar searah angin
├── closehaul.json     # Berlayar melawan angin
├── closehaulreefed.json  # Cuaca buruk
└── goosewing.json     # Berlari searah angin
```

Sistem build menghasilkan semua kombinasi kapal × konfigurasi secara otomatis.

**Konfigurasi saat ini:**

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; margin: 1em 0;">
{% for config in site.data.configurations %}
  <div style="border: 1px solid #ddd; padding: 1em; border-radius: 4px;">
    <strong>{{ config.display_name_id }}</strong>
    <p style="font-size: 0.85em; color: #666; margin: 0.5em 0 0 0;">{{ config.description_id }}</p>
  </div>
{% endfor %}
</div>

---

## Otomatisasi

Setiap push ke branch utama memicu workflow GitHub Actions yang:

1. **Membangun semua model FreeCAD** untuk setiap kombinasi kapal × konfigurasi
2. **Menghasilkan render** (gambar PNG dari berbagai sudut kamera)
3. **Mengekspor file STEP** untuk pertukaran CAD
4. **Menghitung properti massa** dan memvalidasi daya apung
5. **Membangun situs Jekyll** dengan semua aset yang dihasilkan
6. **Mendeploy ke GitHub Pages** di [solarproa.org](https://solarproa.org)

Ini memastikan website selalu mencerminkan kondisi terkini dari model CAD - render, spesifikasi, dan unduhan tidak pernah tidak sinkron.

---

## Struktur Repositori

Kode spesifik desain berada di repo ini. Analisis yang tidak bergantung pada desain kapal tertentu (penggabungan parameter, massa, daya apung, kurva GZ) disediakan oleh pustaka [shipshape](https://github.com/shipshape-marine/shipshape). Validasi struktural berada di `src/structural/`.

```
solar-proa/
├── constant/
│   ├── boat/              # File parameter kapal (rp1.json, rp2.json, rp3.json)
│   ├── configuration/     # Konfigurasi pelayaran
│   └── material/          # Properti material (densitas, warna)
├── src/
│   ├── parameter/         # Perhitungan parameter turunan khusus SolarProa
│   ├── design/            # Pembangun model FreeCAD (central, mirror, rotation)
│   ├── color/             # Aplikasi material dan warna
│   ├── render/            # Generasi render
│   ├── step/              # Ekspor STEP
│   ├── lines/             # Generasi rencana garis
│   ├── structural/        # Validasi struktural (aka, tiang, tulang belakang, capsize)
│   └── buoyancy_design/   # Penempatan keseimbangan di FreeCAD
├── artifact/              # Output yang dihasilkan (model, render, data)
├── docs/                  # Sumber website Jekyll
└── Makefile               # Orkestrasi build
```

---

## Alat & Teknologi

- **[FreeCAD 1.0](https://www.freecad.org/)** - CAD parametrik sumber terbuka
- **Python 3** - Scripting dan otomatisasi
- **[shipshape](https://github.com/shipshape-marine/shipshape)** - Pustaka rekayasa kelautan independen (parameter, massa, daya apung, GZ)
- **GNU Make** - Orkestrasi build dan pelacakan ketergantungan
- **Jekyll** - Generasi situs statis
- **GitHub Actions** - Pipeline CI/CD
- **Graphviz** - Visualisasi grafik ketergantungan

---

## Sumber Terbuka

Seluruh proyek adalah sumber terbuka di bawah [Lisensi Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0).

**Repositori GitHub:** [github.com/shipshape-marine/solar-proa](https://github.com/shipshape-marine/solar-proa)

Kontribusi, umpan balik, dan fork sangat diterima.

---

[← Kembali ke Beranda]({{ '/id/' | relative_url }}) | [Lihat RP1 →]({{ '/id/rp1.html' | relative_url }}) | [Lihat RP2 →]({{ '/id/rp2.html' | relative_url }}) | [Lihat RP3 →]({{ '/id/rp3.html' | relative_url }})
