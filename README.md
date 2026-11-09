# KodyKick — robot soccer untuk anak (KodingYuk)

Robot bola 2 roda yang dirakit anak SD–SMP, dikendalikan remote **KodyPad** (dirakit sendiri, ESP-NOW) atau stik PS3/PS4 (Bluepad32), main 1-lawan-1 di **KodyArena** dari 2 lembar triplek 122×244 cm. Dimulai 9 Nov 2026.

| | |
|---|---|
| Robot | 160 × 158 × 86 mm (termasuk sirip), roda TT 65 mm, ESP32 DevKit V1, DRV8833, 2 TT motor 1:48, SG90 kicker, 4×AA, caster bola baja 12,7 mm |
| KodyPad | 150 × 85 × 31 mm, ESP32-C3 Super Mini, joystick KY-023, 3 tombol (TENDANG/TURBO/KLAKSON), 3×AAA |
| Arena | 244 × 122 cm, dinding 12 cm, gawang 40 × 12 cm, bola floorball 72 mm |
| Harga usulan | Kit Rp549.000 · Arena Rp799.000 · Paket Kelas (2 robot + arena) Rp1.999.000 — lihat `costing/HPP-KODYKICK.md` |

## Isi folder
- `cad/kodykick_cad.py` — CAD parametrik FreeCAD 1.1 headless (robot, pad, arena, bola). `cad/check_clash.py` — cek tabrakan antar part (harus `CLASH-CHECK OK`).
- `out/` — hasil CAD: `parts/*.stl` (65 part), `parts.json` (warna, grup, bbox, volume cetak), `kodykick.step`, `kodypad.step`, `kodyarena.step`, `renders/` (foto + video Blender).
- `render/blender_kodykick.py` — foto hero/pad/kit/arena + video spin/match (Blender 4.5 EEVEE). `render/run_all.sh` render semua.
- `costing/BOM-kodykick.csv` + `HPP-KODYKICK.md` — BOM lengkap robot/pad/arena, HPP, harga, margin.
- `docs/RISET-REMOTE.md` — riset remote (KodyPad vs stik PS3 vs BLE), keputusan.
- `docs/ARENA-TRIPLEK.md` + `arena-cutplan.svg` — rencana potong 2 lembar triplek.
- `docs/NASKAH-VIDEO.md` — naskah reel 21 s, VO, caption feed.
- `firmware/kodykick_robot/` — Arduino ESP32: ESP-NOW + opsi Bluepad32, failsafe, kicker. `firmware/kodypad/` — ESP32-C3 pad.
- Video iklan: `Shared Libraries/kodingyuk-social-kit` komposisi `KodyKick-Ad` (`src/ads/KodyKickAd.tsx`).

## Alur kerja
```bash
# CAD -> STL/STEP/parts.json
"C:/Users/tunas/AppData/Local/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/kodykick_cad.py
"C:/Users/tunas/AppData/Local/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/check_clash.py
# Foto + video
SAMPLES=48 bash render/run_all.sh          # out/renders/{hero,pad,kit,arena}.png, {spin,match}.mp4
# Reel 9:16
cd "../../Shared Libraries/kodingyuk-social-kit" && cp ../../Robotics/KodyKick/out/renders/* public/media/kodykick/ && bash scripts/finish.sh KodyKick-Ad kodykick-ad
```

## Cetak 3D
7 part robot (121 cm³, ±150 g PLA) + 2 part pad (58 cm³). Tray & shell dicetak terbalik tidak perlu (dasar datar); shell dicetak tegak dengan support di bawah lengan scoop. Dinding 2 mm, snap pilar Ø6 ke shell. Lihat `out/parts.json` → `printed: true`.

## Belum / keputusan Owner
- Gambar produk di Odoo belum terpasang: upload attachment gagal (`Oh snap! odoo-files/...`, filestore prod menolak tulis) — cek filestore/S3 server Odoo.
- Harga jual & tanggal pre-order (placeholder `[...]` di video/caption).
- VO ElevenLabs (key MCP invalid 9 Nov 2026) — naskah siap di `docs/NASKAH-VIDEO.md`.
- Prototipe fisik belum dicetak; toleransi slot motor/servo perlu uji 1 cetakan.
- Firmware belum diuji di hardware; web-joystick fallback belum ditulis.
- Nama final: **KodyKick** (alternatif yang dipertimbangkan: KodyGoal, KodyBall).
