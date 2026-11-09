# KodyArena — arena soccer dari 2 lembar triplek 9 mm 122 × 244 cm

Prinsip: **lembar 1 utuh jadi lantai**, lembar 2 dipotong jadi strip 12 cm untuk dinding + gawang + pojok. Tanpa potongan miring selain 4 segitiga pojok. Semua bisa dipotong tukang/sekolah dengan gergaji meja; kerf 3 mm sudah dihitung.

Gambar: `arena-cutplan.svg` (dibuat `arena_cutplan.py`). Model 3D: `out/kodyarena.step`, STL per part di `out/parts/arena_*.stl`.

## Ukuran (mm)
| Bagian | Ukuran | Jumlah | Dari |
|---|---|---|---|
| Lantai | 2440 × 1220 × 9 | 1 | lembar 1 utuh |
| Dinding panjang | 2440 × 120 | 2 | lembar 2, strip 1–2 |
| Dinding pendek | 1202 × 120 (= 1220 − 2×9) | 2 | strip 3 |
| Sisi gawang | 120 × 120 | 4 | strip 4 |
| Atap gawang | 418 × 120 (= 400 + 2×9) | 2 | strip 4 |
| Pojok 45° | segitiga siku 100 × 100 (dari kotak 120 dibelah) | 4 | strip 4 |
| Sisa | strip 120 × 2440 | 5 | cadangan / Arena Mini |

Lapangan dalam: **2422 × 1202 mm**, mulut gawang **400 lebar × 120 dalam × 120 tinggi** (dinding pendek = tiang belakang gawang). Garis lakban putih 2 cm: garis tengah, lingkaran tengah R 30 cm, kotak penalti 25 × 80 cm, garis gawang, 5 titik netral.

Perbandingan RoboCupJunior Soccer: lapangan 158 × 219 cm + outer 12 cm = 182 × 243 cm, dinding 22 cm, gawang 60 × 10 cm (field_specification 2025). KodyArena sengaja **lebih kecil & gawang lebih sempit** (robot 16 cm, bola 7,2 cm) supaya pertandingan 1-lawan-1 cepat & seru di kelas.

## Rakit
1. Cat lantai hijau (2 lapis), biarkan kering 24 jam, tempel lakban garis.
2. Pasang dinding panjang di tepi lantai (sekrup 3,5 × 30 dari bawah tiap 40 cm, atau siku L di luar). Dinding pendek di antara dinding panjang.
3. Gawang: sekrup 2 sisi gawang ke dinding pendek (jarak dalam 400), pasang atap. Tempel garis gawang di lantai 12 cm dari dinding.
4. Pojok 45°: lem + paku kecil, bola tidak macet di sudut.
5. Opsional: lapisi mulut gawang dengan lakban warna tim (merah / teal).

## Arena Mini (opsional, ruang kecil)
Lantai 122 × 122 (potong lembar 1 jadi 2 → 2 arena mini) + dinding dari 5 strip sisa (2 × 1220, 2 × 1202 + gawang). Cocok untuk latihan menggiring/1 gawang.

## Biaya
Lihat `costing/BOM-kodykick.csv` baris 41–45: triplek 2 lembar ±Rp260.000, cat + lakban + sekrup ±Rp80.000, upah potong/rakit ±Rp150.000 → **HPP ±Rp490.000**, jual flat-pack Rp799.000 atau bundel Paket Kelas.
