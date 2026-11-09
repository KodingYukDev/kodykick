# HPP & Harga — KodyKick (robot soccer) · KodyPad · KodyArena

Disusun 9 Nov 2026. Sumber: `BOM-kodykick.csv` (delimiter `;`), harga Tokopedia yang dilihat Nov 2026 + BOM Michi (Okt 2026). Baris tanpa sumber ditandai `[ESTIMASI]`.

## Ringkasan

| Item | BOM @1 | HPP @1 | HPP @50 | Harga jual usulan | Margin @50 |
|---|---:|---:|---:|---:|---:|
| **KodyKick Kit** (1 robot + 1 KodyPad + bola + kemasan + buku) | 322.900 | 384.000 | 333.000 | **Rp549.000** | 39 % |
| KodyKick Kit + stik PS3 OP (tanpa KodyPad) | 303.400 | 362.000 | 313.000 | Rp549.000 | 43 % |
| **KodyArena** flat-pack (2 lembar triplek, dicat, gawang, lakban) | 340.000 | 490.000 | 426.000 | **Rp799.000** | 47 % |
| **Paket Kelas** (2 robot + 2 pad + 2 bola + arena) | — | 1.258.000 | 1.092.000 | **Rp1.999.000** | 45 % |
| Paket Lomba Sekolah (4 robot + 4 pad + arena + 4 bola) | — | 2.026.000 | 1.758.000 | Rp2.999.000 | 41 % |

Harga jual di bawah Rp600.000 supaya sejajar Michi (Rp599.000) dan di bawah kit robot soccer marketplace (kit ESP32 car lengkap Rp849.000, Cytron Soccer:bit ≈ Rp900.000+ belum termasuk micro:bit).

## Robot (BOM Rp215.400)

Komponen termahal: ESP32 DevKit V1 Rp75.000 (35 %), cetak PLA Rp45.000 (21 %), motor+roda Rp33.000.

- **Kenapa ESP32 classic, bukan C3?** Hanya ESP32 classic punya Bluetooth Classic (BR/EDR). Stik PS3/PS4/8BitDo/Android gamepad murah semuanya BR/EDR → Bluepad32 di C3/S3 **tidak bisa** (docs Bluepad32). ESP-NOW ke KodyPad jalan di semua chip. Hemat Rp40.000 kalau pakai C3 tapi kehilangan opsi stik PS.
- **Baterai 4×AA (6 V)**, bukan LiPo: aman untuk anak, orang tua bisa beli di warung, tanpa charger/sertifikasi baterai. TT motor 3–6 V, DRV8833 2,7–10,8 V, ESP32 VIN 5–12 V → semua langsung dari 6 V (motor via DRV8833, ESP32 via VIN; servo dari 6 V lewat pin VIN — SG90 toleran sampai 6 V).
- **Cetak 3D in-house Rp45.000** (165 g PLA). Kalau cetak di jasa luar jadi Rp100.000–165.000 → BOM robot naik ke ±Rp300.000; jangan.
- Pengurangan biaya kalau perlu: hilangkan servo kicker + buzzer (−Rp20.000, scoop pasif tetap bisa dorong bola), beli motor+roda paket (−Rp6.000).

## KodyPad vs stik PS3 — hasil riset remote

| | KodyPad DIY (ESP-NOW) | Stik PS3 OP clone | Stik BLE Android (X3 dkk) |
|---|---|---|---|
| Harga | Rp84.500 (Rp75.000 @50) | Rp59.900–75.000 | Rp90.000–210.000 |
| Pairing | otomatis (tekan PAIR di pad + robot, MAC tersimpan) | **wajib** SixaxisPairTool via USB, set MAC ESP32 ke stik; clone kadang gagal autentikasi | tergantung profil HID; BT 3.0 sering tidak terdeteksi |
| Banyak robot di 1 arena | ya, 1 pad ↔ 1 robot by MAC, latensi ±5 ms | ya tapi tiap stik harus di-pair ulang ke robotnya | tidak andal |
| Nilai edukasi | anak merakit remotenya sendiri (joystick, tombol, C3) → cocok jadi sesi kelas | tidak ada | tidak ada |
| Durability anak | casing PLA 2 mm + grip | bagus | bagus |
| Risiko | solder perfboard (butuh guru) | stok clone berubah-ubah, chip BT abal-abal | tidak konsisten |

**Keputusan**: kit standar pakai **KodyPad**; firmware robot tetap mendukung stik PS3/PS4/8BitDo lewat Bluepad32 sebagai *upgrade* (dokumentasi pairing di manual). Harga kit sama untuk kedua varian (selisih BOM Rp20.000).

## Arena (HPP Rp490.000)

Dua lembar triplek 9 mm 122×244: lembar 1 = lantai utuh, lembar 2 = 4 strip 12 cm (2 dinding panjang, 2 dinding pendek, 4 sisi gawang, 2 atap gawang, 4 pojok 45°). Sisa 5 strip 12×244 → cadangan / Arena Mini 122×122. Detail potong: `docs/ARENA-TRIPLEK.md` + `docs/arena-cutplan.svg`.

Harga triplek paling tidak pasti (Rp97.000–200.000/lembar tergantung grade & kota). Upah potong dihitung tukang 2 jam; sekolah bisa potong sendiri → HPP turun ke Rp340.000.

## Modal & catatan

- Tidak ada komponen custom (PCB/cetakan) → modal awal hanya stok komponen + waktu printer. 10 kit pertama ≈ Rp3,8 juta BOM + 50 jam cetak 3D (±5 jam/kit, bisa 2 printer paralel).
- Sertifikasi: tidak ada radio custom (modul ESP32 sudah bersertifikat SDPPI oleh importir), tanpa LiPo → beban sertifikasi jauh lebih kecil dari Michi. SNI mainan tetap perlu dicek kalau dijual ritel umum (bukan ke sekolah).
- Belum dihitung: ongkir komponen (±Rp15.000/kit kalau beli eceran), fee marketplace 8 %, PPN.
