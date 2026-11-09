# HPP & Harga — KodyKick (robot soccer + stik PS3) · KodyArena

Disusun 9 Nov 2026. Sumber: `BOM-kodykick.csv` (delimiter `;`), harga Tokopedia yang dilihat Nov 2026 + BOM Michi (Okt 2026). Baris tanpa sumber ditandai `[ESTIMASI]`.

## Ringkasan

| Item | BOM @1 | HPP @1 | HPP @50 | Harga jual usulan | Margin @50 |
|---|---:|---:|---:|---:|---:|
| **KodyKick Kit** (1 robot + 1 stik PS3 OP + bola + kemasan + buku) | 319.900 | 366.000 | 315.000 | **Rp549.000** | 43 % |
| **KodyArena** flat-pack (2 lembar triplek, dicat, gawang, lakban) | 340.000 | 490.000 | 426.000 | **Rp799.000** | 47 % |
| **Paket Kelas** (2 robot + 2 stik + 2 bola + arena) | — | 1.212.000 | 1.046.000 | **Rp1.999.000** | 48 % |
| Paket Lomba Sekolah (4 robot + 4 stik + arena + 4 bola) | — | 1.934.000 | 1.666.000 | Rp2.999.000 | 44 % |

Harga jual di bawah Rp600.000 supaya sejajar Michi (Rp599.000) dan di bawah kit robot soccer marketplace (kit ESP32 car lengkap Rp849.000, Cytron Soccer:bit ≈ Rp900.000+ belum termasuk micro:bit).

## Robot (BOM Rp231.900)

Komponen termahal: ESP32 DevKit V1 Rp75.000 (35 %), cetak PLA Rp55.000 (24 %), motor+roda Rp33.000.

- **Kenapa ESP32 classic, bukan C3?** Hanya ESP32 classic punya Bluetooth Classic (BR/EDR). Stik PS3/PS4/8BitDo/Android gamepad murah semuanya BR/EDR → Bluepad32 di C3/S3 **tidak bisa** (docs Bluepad32). Stik PS = keputusan Owner, jadi ESP32 classic wajib.
- **Holder 4×AA 2×2 dengan saklar** (model asli Adafruit 830, Rp12.000) — saklar terpisah tidak perlu. **Baterai 4×AA (6 V)**, bukan LiPo: aman untuk anak, orang tua bisa beli di warung, tanpa charger/sertifikasi baterai. TT motor 3–6 V, DRV8833 2,7–10,8 V, ESP32 VIN 5–12 V → semua langsung dari 6 V (motor via DRV8833, ESP32 via VIN; servo dari 6 V lewat pin VIN — SG90 toleran sampai 6 V).
- **Cetak 3D in-house Rp55.000** (±200 g PLA, 163 cm³). Kalau cetak di jasa luar jadi Rp100.000–165.000 → BOM robot naik ke ±Rp300.000; jangan.
- Pengurangan biaya kalau perlu: hilangkan servo kicker + buzzer (−Rp20.000, scoop pasif tetap bisa dorong bola), beli motor+roda paket (−Rp6.000).

## Remote: stik PS3 (keputusan Owner 9 Nov 2026)
KodyPad DIY dibatalkan — remote = **stik PS3 wireless OP Rp59.900–75.000** (Tokopedia, 500+ terjual) lewat library Bluepad32 di ESP32 classic. Konsekuensi: pairing sekali pakai SixaxisPairTool di PC (MAC ESP32 ditulis ke stik), clone kadang gagal autentikasi → stok 1 stik cadangan per 10 kit; alternatif tanpa pairing USB: stik PS4 DualShock bekas Rp150–250rb (Bluepad32 langsung). Tombol: stik kiri = gerak, X = TENDANG, R2 = TURBO, O = KLAKSON. Riset lengkap: `docs/RISET-REMOTE.md`.

## Arena (HPP Rp490.000)

Dua lembar triplek 9 mm 122×244: lembar 1 = lantai utuh, lembar 2 = 4 strip 12 cm (2 dinding panjang, 2 dinding pendek, 4 sisi gawang, 2 atap gawang, 4 pojok 45°). Sisa 5 strip 12×244 → cadangan / Arena Mini 122×122. Detail potong: `docs/ARENA-TRIPLEK.md` + `docs/arena-cutplan.svg`.

Harga triplek paling tidak pasti (Rp97.000–200.000/lembar tergantung grade & kota). Upah potong dihitung tukang 2 jam; sekolah bisa potong sendiri → HPP turun ke Rp340.000.

## Modal & catatan

- Tidak ada komponen custom (PCB/cetakan) → modal awal hanya stok komponen + waktu printer. 10 kit pertama ≈ Rp3,8 juta BOM + 50 jam cetak 3D (±5 jam/kit, bisa 2 printer paralel).
- Sertifikasi: tidak ada radio custom (modul ESP32 sudah bersertifikat SDPPI oleh importir), tanpa LiPo → beban sertifikasi jauh lebih kecil dari Michi. SNI mainan tetap perlu dicek kalau dijual ritel umum (bukan ke sekolah).
- Belum dihitung: ongkir komponen (±Rp15.000/kit kalau beli eceran), fee marketplace 8 %, PPN.
