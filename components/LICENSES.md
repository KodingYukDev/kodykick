# Model komponen pihak ketiga (STEP) — sumber & lisensi

Diunduh 9 Nov 2026. Semua boleh dipublikasikan ulang dengan atribusi di bawah; `LICENSE-*.txt/md` = salinan lisensi asli.

| File | Komponen | Sumber | Lisensi |
|---|---|---|---|
| `tt_motor_adafruit3777.step` | TT gear motor kuning 1:48, poros ganda (Adafruit #3777) | https://github.com/adafruit/Adafruit_CAD_Parts | MIT © 2016 Adafruit Industries |
| `battery_holder_4xAA_adafruit830.step` | holder 4×AA 2×2 dengan saklar (Adafruit #830) | idem | MIT |
| `battery_holder_3xAAA_adafruit727.step` | holder 3×AAA + JST (Adafruit #727) | idem | MIT |
| `joystick_adafruit512.step` | joystick analog 2 sumbu (Adafruit #512; joystick yang sama dengan modul KY-023) — PCB Adafruit dibuang, hanya joystick | idem | MIT |
| `tactile12_adafruit1119.step` | tactile switch 12×12 mm Omron B3F (Adafruit #1119) | idem | MIT |
| `slide_switch_adafruit805.step` | saklar geser SPDT (Adafruit #805) | idem | MIT |
| `sg90_freecadlib.step`, `sg90_horn1_freecadlib.step` | micro servo SG90 + horn 1 lengan | https://github.com/FreeCAD/FreeCAD-library (Electrical Parts/Servos/SG-90) | CC-BY 3.0 — atribusi ke kontributor FreeCAD-library (lihat riwayat commit repo) |
| `esp32_wroom_32e_espressif.step` | modul ESP32-WROOM-32E | https://github.com/espressif/kicad-libraries | CC-BY-SA 4.0 (dengan pengecualian KiCad) |

## Yang BELUM model asli (dimodelkan dari dimensi datasheet/listing)
- PCB ESP32 DevKit V1 30-pin (DOIT) 51,5×28,3 mm — tidak ada STEP publik; modul WROOM di atasnya asli.
- PCB modul KY-023 34×26 mm — joystick di atasnya asli.
- Modul DRV8833 18×20 mm (versi generik marketplace; Adafruit #3297 bentuknya beda).
- Roda TT 65×26 mm, bola floorball 72 mm, bola baja 12,7 mm.
- ESP32-C3 Super Mini 22,5×18 mm (di KodyPad).

Kalau Owner punya STEP dari supplier untuk item di atas, taruh di folder ini dan ganti fungsi terkait di `cad/kodykick_cad.py`.
