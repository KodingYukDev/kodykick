# Naskah video & feed KodyKick

## Reel 20 s "KodyKick — Robot Bola, Kamu Pelatihnya" (9:16, social kit, tema `produk` aksen kuning)
Dirender dari `Shared Libraries/kodingyuk-social-kit` komposisi `KodyKickAd` (`src/ads/KodyKickAd.tsx`), footage Blender dari `Robotics/KodyKick/out/renders/`.

| Detik | Visual | Teks di layar | VO (ElevenLabs, suara "Kak Ceria", ceria & cepat) |
|---|---|---|---|
| 0–2,4 | arena.png push-in, hook sticker | **Robot bola buat anak?** | "Robot bola… yang kamu rakit sendiri?" |
| 2,4–6,4 | spin.mp4 (robot berputar) | *KodyKick* · robot soccer | "Kenalin, KodyKick! Robot soccer dari KodingYuk." |
| 6,4–10 | match.mp4 (serbu bola, tendang, gol) | Tendang pakai *servo* ⚽ | "Giring bolanya, pencet tombol merah… GOL!" |
| 10–13 | pad.png | Remote *KodyPad*, kamu rakit sendiri | "Remote-nya juga kamu rakit sendiri: joystick, tombol, dan otak ESP32." |
| 13–16 | kit.png flat lay + chip: ESP32 · 2 motor · servo · 4×AA | Baterai AA biasa, aman | "Pakai baterai AA biasa. Aman, gampang." |
| 16–17 | arena.png (gawang) | Arena dari *1 lembar triplek* | "Arenanya? Dua lembar triplek, jadi lapangan bola!" |
| 17–21 | End card: KodyKick by KodingYuk · "Robot bola, kamu pelatihnya" · CTA | **Daftar pre-order** · kodingyuk.id/produk/kodykick | "Ayo jadi pelatih robot pertama di sekolahmu!" |

SFX: whoosh tiap cut, pop saat chip muncul, drop saat harga, sparkle saat gol. Musik `music_energy_5.mp3` (CC0), ducking saat VO.
Harga **tidak** ditampilkan di video sampai Owner konfirmasi (placeholder `[Rp549.000]`).

## Status VO
ElevenLabs MCP mengembalikan `401 invalid_api_key` (9 Nov 2026) → VO belum dibuat. Setelah key diperbarui: generate 7 kalimat di atas dengan suara Kak Ceria (seperti unboxing Michi), simpan ke `video/vo/01..07.mp3`, lalu render ulang `bash scripts/finish.sh KodyKickAd kodykick-ad`.

## Caption feed (IG/TikTok)
**Caption 1 (launch):**
Robot bola yang kamu rakit sendiri ⚽🤖
KodyKick: robot soccer 2 roda + servo penendang + remote KodyPad yang juga dirakit sendiri. Baterai AA biasa, arena dari triplek. Main 1 lawan 1 di kelas!
Pre-order dibuka [tanggal]. Link di bio.
#KodyKick #KodingYuk #robotik #robotsoccer #STEM #belajarkoding #anakindonesia

**Caption 2 (edukasi):**
Kenapa robot soccer bagus buat belajar? 🧠
1. Motor DC + driver = belajar arah & kecepatan
2. Servo = belajar sudut & gerak mekanik
3. Remote ESP-NOW = belajar komunikasi nirkabel
4. Lomba = belajar strategi & sportivitas
KodyKick, robot bola dari KodingYuk. #KodyKick #KodingYuk

**Caption 3 (arena):**
1 lembar triplek 122×244 = lantai. 1 lembar lagi = dinding + gawang. Jadi deh KodyArena 🏟️
Sekolah bisa bikin sendiri, panduan potong lengkap ada di kit. #KodyKick #KodyArena #KodingYuk

## Foto feed (dari render)
1. `hero.png` — robot + bola, 4:5
2. `pad.png` — KodyPad, 4:5
3. `kit.png` — flat lay isi kit, 4:5
4. `arena.png` — arena 2 robot, 16:10 (crop 4:5 untuk feed)
Carousel "Apa isi kit KodyKick?" = kit.png + 4 slide komponen (ESP32, motor+roda, servo, KodyPad) — teks dari STYLE.md (Bricolage, sticker shadow).
