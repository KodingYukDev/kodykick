# Panduan rakit KodyKick (prototipe nyata)

Versi CAD: `cad/kodykick_cad.py` 9 Nov 2026 sore (BASE_W 120, komponen STEP asli). Semua ukuran dari STEP komponen asli; **toleransi cetak belum diuji** → cetak tray dulu, cek pas-tidaknya motor/servo/PCB, baru cetak cangkang.

## 1. Cetak 3D (PLA, nozzle 0,4, layer 0,2, 3 perimeter, infill 20 %)
| Part STL (`out/parts/`) | Orientasi | Support | Catatan |
|---|---|---|---|
| `robot_base_tray` | dasar di bed | tidak | lubang sekrup M3 countersink di bawah; rel ESP32 & klip DRV tipis 1,2–2 mm → cetak pelan (30 mm/s) |
| `robot_top_shell` | terbalik (atap di bed) | ya, di bawah lengan scoop & jendela kicker | boss M3 & rusuk motor menggantung → support tree |
| `robot_kicker` | rebah (paddle di bed) | tidak | lubang hub Ø2 untuk sekrup horn |
| `robot_fin` | rebah | tidak | warna tim (merah/teal) |
| `robot_number_card` | rebah | tidak | boleh diganti kertas laminasi 43×43 |
| `robot_eye_l/r` | berdiri | tidak | PLA transparan/putih, LED 5 mm di belakangnya |

Berat total ±200 g PLA. Clearance tray ke lantai 18 mm, roda Ø65.

## 2. Komponen (lihat `costing/BOM-kodykick.csv`)
ESP32 DevKit V1 30-pin · DRV8833 · 2× TT motor 1:48 poros ganda · 2× roda TT 65 mm · SG90 + horn 1 lengan · holder 4×AA 2×2 **dengan saklar** · 4× AA · bola baja ½" · 2× LED 5 mm + 2× 220 Ω · buzzer pasif · Dupont F-F · sekrup: 4× M3×16 self-tapping, 2× M2×8, 1× M2×6 (horn) · double tape busa · stik PS3 wireless.

## 3. Urutan rakit
1. **Caster**: masukkan bola baja ½" ke cup di bawah tray belakang (tekan, snap). Bola harus berputar bebas; kalau seret, amplas lubang cup Ø13,2.
2. **Motor TT**: masukkan motor ke cradle (gearbox ke depan, kaleng ke belakang, poros panjang keluar lewat slot U dinding samping). Muka dalam motor menempel tiang dalam; klem depan (y +17) & belakang (y −57,6) menahan geser. Motor baru terkunci sepenuhnya oleh **rusuk cangkang** saat cangkang dipasang (langkah 9).
3. **Servo SG90** (kicker): masukkan dari atas ke slot lantai kiri-depan (badan menggantung 7 mm di bawah tray), telinga duduk di 2 boss → sekrup **M2×8** ×2. Poros menghadap atas. Set servo ke posisi tengah (90°) **sebelum** pasang horn.
4. **Horn + kicker**: pasang horn 1 lengan menghadap +X (ke kanan robot), kencangkan sekrup horn bawaan. Pasang kicker cetak di atas horn (lubang hub) dengan **M2×6**; paddle harus berada tepat di belakang bola (celah 2 mm ke dinding scoop).
5. **DRV8833**: selipkan modul ke 2 klip ujung di tengah tray (di bawah posisi ESP32), lip klip mengunci tepi PCB. Pin header modul menghadap atas.
6. **ESP32 DevKit V1**: masukkan dari atas di antara 2 rel penjepit (lip 1,2 mm menahan tepi PCB), USB menghadap belakang, antena ke depan. Header pin berada 8,5 mm di atas lantai → ruang untuk kabel Dupont ke DRV di bawahnya.
7. **Holder 4×AA**: tempel double tape busa di dasar holder, letakkan di antara 4 nub (saklar menghadap ke lubang dinding belakang kiri). Kabel merah/hitam ke VIN & GND ESP32 **dan** VM/GND DRV8833.
8. **Wiring** (lihat tabel §4), rapikan dengan kabel Dupont 10 cm.
9. **LED mata**: LED 5 mm + resistor 220 Ω di belakang lensa cangkang (lem tetes), kabel ke GPIO4 & GND.
10. **Cangkang**: turunkan dari atas; rusuk penekan harus menyentuh atap gearbox (kalau menekan terlalu keras → amplas rusuk 0,3 mm). Pasang **4× M3×16** dari bawah tray ke boss cangkang. Pasang sirip ke slot atap, kartu nomor ke recess.
11. **Roda**: tekan roda TT ke poros D (keras, pakai telapak tangan). Cek jarak roda–cangkang ±2 mm.

## 4. Wiring (ESP32 DevKit V1)
| Dari | Ke | Catatan |
|---|---|---|
| Holder 4×AA + (via saklar) | ESP32 VIN, DRV8833 VM | 6 V alkaline / 4,8 V NiMH |
| Holder − | ESP32 GND, DRV8833 GND, servo GND, LED/buzzer GND | GND bersama |
| ESP32 GPIO25 / 26 | DRV8833 AIN1 / AIN2 | motor kiri |
| ESP32 GPIO27 / 14 | DRV8833 BIN1 / BIN2 | motor kanan |
| DRV8833 AOUT1/2, BOUT1/2 | motor kiri, motor kanan | tukar kabel kalau arah terbalik |
| DRV8833 nSLEEP | ESP32 3V3 | wajib HIGH |
| ESP32 GPIO13 | servo sinyal (oranye) | servo + ke VIN (6 V), − ke GND |
| ESP32 GPIO15 | buzzer pasif + | − ke GND |
| ESP32 GPIO4 | 220 Ω → 2× LED mata | paralel |
Firmware: `firmware/kodykick_robot/kodykick_robot.ino` (Arduino-ESP32 3.x + board package Bluepad32, pilih "ESP32 Dev Module").

## 5. Pairing stik PS3 (sekali per stik)
1. Flash firmware, buka Serial Monitor 115200 → catat `KodyKick MAC xx:xx:...` (MAC Bluetooth = MAC WiFi + 2 di byte terakhir; Bluepad32 mencetak MAC BT di log).
2. Di PC: jalankan **SixaxisPairTool**, colok stik PS3 via USB, isi "Master" dengan MAC Bluetooth ESP32 → Update.
3. Cabut USB, nyalakan robot, tekan tombol PS → LED stik menyala stabil, robot bunyi 2 nada = tersambung.
4. Kalau clone gagal autentikasi (LED kedip terus) → coba stik lain / pakai stik PS4 (pairing: tahan Share + PS sampai kedip cepat, robot otomatis menerima).
Kontrol: stik kiri = maju/mundur/belok, **X** = tendang, **R2** = turbo, **O** = klakson. Robot berhenti otomatis 0,4 s tanpa sinyal.

## 6. Uji sebelum main
- Berat robot dengan baterai ±420 g; pastikan caster menyentuh lantai dan roda tidak menggesek cangkang.
- Tendangan: paddle harus menyentuh bola 72 mm yang berada di scoop; atur `KICK_REST`/`KICK_HIT` di firmware bila horn tidak di tengah.
- Arus: TT motor stall ±1,2 A @6 V → DRV8833 1,5 A/ch cukup; kalau DRV panas, turunkan PWM maks (180 → 150).
- Checklist toleransi yang paling mungkin perlu dikoreksi di CAD: slot poros roda di dinding (Ø7 untuk poros Ø5,2 + goyang), rel ESP32 (28,3 + 0,6), klip DRV (20 + 0,6), boss servo (lubang Ø1,6 untuk M2 self-tap).
