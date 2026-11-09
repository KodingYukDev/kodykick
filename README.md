# KodyKick — robot soccer untuk anak (KodingYuk)

Robot bola 2 roda yang dirakit anak SD–SMP, dikendalikan **stik PS3/PS4** (Bluepad32 di ESP32), main 1-lawan-1 di **KodyArena** dari 2 lembar triplek 122×244 cm. Dimulai 9 Nov 2026. Keputusan Owner 9 Nov: remote DIY KodyPad dibatalkan.

| | |
|---|---|
| Robot | 176 × 166 × 86 mm (termasuk sirip), roda TT 65 mm, ESP32 DevKit V1, DRV8833, 2 TT motor 1:48, SG90 kicker, holder 4×AA 2×2 + saklar, caster bola baja 12,7 mm |
| Remote | stik PS3 wireless (OP) via Bluepad32; stik PS4 juga bisa |
| Perakitan | motor di cradle cetak + rusuk penekan cangkang; ESP32 di rel penjepit; DRV8833 di klip (di bawah ESP32); servo 2× M2×8 ke boss; holder baterai nub + double tape; cangkang 4× M3×16 dari bawah tray |
| Arena | 244 × 122 cm, dinding 12 cm, gawang 40 × 12 cm, bola floorball 72 mm |
| Harga usulan | Kit (robot + stik PS3) Rp549.000 · Arena Rp799.000 · Paket Kelas (2 robot + 2 stik + arena) Rp1.999.000 — lihat `costing/HPP-KODYKICK.md` |

## Isi folder
- `components/` — **STEP asli komponen beli** (TT motor, holder baterai, joystick, tactile, saklar = Adafruit MIT; SG90 = FreeCAD-library CC-BY; modul ESP32-WROOM-32E = Espressif CC-BY-SA) + `LICENSES.md`. Yang masih dimodelkan dari datasheet: PCB DevKit V1, PCB KY-023, modul DRV8833, roda TT, bola.
- `cad/kodykick_cad.py` — CAD parametrik FreeCAD 1.1 headless (robot, arena, bola). `cad/check_clash.py` — cek tabrakan antar part (harus `CLASH-CHECK OK`).
- `out/` — hasil CAD: `parts/*.stl` (52 part), `parts.json` (warna, grup, bbox, volume cetak, sumber), `kodykick.step`, `kodyarena.step`, `real/` (render realistis Cycles), `renders/` (EEVEE cepat).
- `render/blender_real.py` — **render realistis** Cycles (foto hero/inside/arena + video `breakdown` exploded & `match`). `render/blender_kodykick.py` = versi cepat EEVEE lama.
- `costing/BOM-kodykick.csv` + `HPP-KODYKICK.md` — BOM lengkap robot/stik/arena, HPP, harga, margin.
- `docs/RISET-REMOTE.md` — riset remote (KodyPad vs stik PS3 vs BLE), keputusan.
- `docs/ARENA-TRIPLEK.md` + `arena-cutplan.svg` — rencana potong 2 lembar triplek.
- `docs/NASKAH-VIDEO.md` — naskah reel 21 s, VO, caption feed.
- `docs/RAKIT.md` — **panduan rakit prototipe nyata**: cetak, urutan rakit, wiring pin, pairing stik PS3, checklist toleransi.
- `firmware/kodykick_robot/` — Arduino ESP32 + Bluepad32 (stik PS3/PS4), failsafe, kicker.
- Video iklan: `Shared Libraries/kodingyuk-social-kit` komposisi `KodyKick-Ad` (`src/ads/KodyKickAd.tsx`).

## Alur kerja
```bash
# CAD -> STL/STEP/parts.json
"C:/Users/tunas/AppData/Local/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/kodykick_cad.py
"C:/Users/tunas/AppData/Local/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/check_clash.py
# Foto + video
bash render/run_real.sh                    # out/real/{hero,inside,arena}.png + breakdown.mp4 + match.mp4 (Cycles, ±2 jam CPU)
# Reel 9:16
cd "../../Shared Libraries/kodingyuk-social-kit" && cp ../../Robotics/KodyKick/out/real/* public/media/kodykick/ && bash scripts/finish.sh KodyKick-Ad kodykick-ad
```

## Cetak 3D
7 part robot (163 cm³, ±200 g PLA). Tray & shell dicetak terbalik tidak perlu (dasar datar); shell dicetak tegak dengan support di bawah lengan scoop. Dinding 2 mm, snap pilar Ø6 ke shell. Lihat `out/parts.json` → `printed: true`.

## Belum / keputusan Owner
- Gambar produk di Odoo belum terpasang: upload attachment gagal (`Oh snap! odoo-files/...`, filestore prod menolak tulis) — cek filestore/S3 server Odoo.
- Harga jual & tanggal pre-order (placeholder `[...]` di video/caption).
- VO ElevenLabs (key MCP invalid 9 Nov 2026) — naskah siap di `docs/NASKAH-VIDEO.md`.
- Prototipe fisik belum dicetak; toleransi slot motor/servo perlu uji 1 cetakan.
- Firmware belum diuji di hardware; web-joystick fallback belum ditulis.
- Nama final: **KodyKick** (alternatif yang dipertimbangkan: KodyGoal, KodyBall).
