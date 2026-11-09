# Riset remote KodyKick — cetak sendiri vs stik PS murah

Tanggal: 9 Nov 2026. Pertanyaan Owner: "murahan cetak controller sendiri atau pake stik PS yang murah yang bluetooth itu".

## Jawaban singkat
Stik PS3 OP (Rp60–75 rb) **sedikit lebih murah** dari KodyPad DIY (Rp84,5 rb eceran, Rp75 rb @50), tapi KodyPad menang di pairing, multi-robot, dan nilai edukasi. **Kit standar = KodyPad. Stik PS3/PS4 didukung sebagai opsi.**

## Fakta teknis yang menentukan
1. **Bluepad32** (library gamepad Bluetooth untuk ESP32) mendukung DualShock 3/4, DualSense, Switch, Xbox, 8BitDo, gamepad Android. Hampir semua stik murah pakai **BR/EDR (Bluetooth Classic)**. Chip **ESP32 classic** mendukung BR/EDR; **ESP32-S3/C3/C6/H2 tidak**. → Robot wajib ESP32 classic (DevKit V1 Rp75 rb) kalau mau opsi stik PS. Sumber: https://bluepad32.readthedocs.io/en/latest/supported_gamepads/
2. **DualShock 3 tidak punya discovery standar**: harus di-pair lewat USB dulu dengan **SixaxisPairTool**, menulis MAC ESP32 ke stik. Clone murah sering gagal autentikasi (laporan forum DroneBot Workshop, Elektroda). Sumber: https://bluepad32.readthedocs.io/en/latest/pair_ds3/ , https://dronebotworkshop.com/ps3-esp32/
3. Harga Tokopedia Nov 2026: stik PS3 OP wireless Rp59.900–75.000 (500+ terjual), "bisa connect ESP32" dijual Rp219.000; gamepad X3 BT 3.0 Rp90.000; Ipega PG-9129 Rp210.000; 8BitDo Micro Rp299.000. Sumber: https://www.tokopedia.com/find/stik-ps3-bluetooth , https://www.tokopedia.com/find/stik-ps-bluetooth
4. **ESP-NOW** (KodyPad → robot): tanpa pairing Bluetooth, latensi ±2–5 ms, 1 pad terkunci ke 1 MAC robot → 4–6 robot di satu arena tanpa saling ganggu. Jalan di C3 (pad) dan ESP32 classic (robot).

## Opsi yang dibandingkan
| Opsi | Biaya | Plus | Minus |
|---|---|---|---|
| A. KodyPad DIY (C3 Super Mini + KY-023 + 3 tombol + 3xAAA, casing PLA) | Rp84.500 | pairing 1 tombol, multi-robot, anak merakit sendiri, bentuk/branding KodingYuk | perlu solder perfboard (guru/kakak kelas), 2 part cetak 58 cm³ |
| B. Stik PS3 OP clone | Rp65.000 | murah, nyaman, getar | SixaxisPairTool via PC, clone bisa gagal, perlu ESP32 classic, 1 stik = 1 robot harus di-pair ulang |
| C. Stik BLE/Android (X3, Ipega) | Rp90–210 rb | tanpa USB pairing | profil HID beragam, BT 3.0 tidak ketemu, mahal |
| D. HP Android via WiFi AP (web joystick) | Rp0 | gratis | HP anak dipakai, latensi WiFi 30–80 ms, tidak "mainan" |

## Keputusan desain
- Kit: **A** (KodyPad). Firmware robot punya `#define USE_BLUEPAD32` untuk **B** sebagai upgrade; manual memuat langkah SixaxisPairTool.
- D dijadikan fallback gratis di firmware (AP `KodyKick-xx`, halaman web joystick) supaya kelas tetap jalan kalau pad rusak.
- KodyPad: joystick kiri = gerak (arcade drive), tombol merah besar = TENDANG (servo), teal = TURBO (PWM 100 %), oranye = KLAKSON (buzzer). Tombol PAIR = tekan joystick.
