# Gambar rencana potong KodyArena dari triplek 9 mm 122 x 244 cm -> arena-cutplan.svg (+ daftar potong di ARENA-TRIPLEK.md)
import os

HERE = os.path.dirname(os.path.abspath(__file__))
S = 0.25  # px per mm
W, H = 2440, 1220
KERF = 3
STRIP = 120

pieces = [  # (label, panjang mm, warna)
    ("Dinding panjang A 2440", 2440, "#d9b98a"),
    ("Dinding panjang B 2440", 2440, "#d9b98a"),
    ("Dinding pendek A 1202 | Dinding pendek B 1202", [1202, 1202], "#e8c99a"),
    ("Sisi gawang 4 x 120 | Atap gawang 2 x 418 | Pojok 2 kotak 120 (belah diagonal = 4 segitiga)", [120, 120, 120, 120, 418, 418, 120, 120], "#f1d9ad"),
]


def svg():
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S+40}" height="{2*H*S+160}" font-family="Instrument Sans, Arial" font-size="13">']
    out.append('<rect width="100%" height="100%" fill="#F7F9F9"/>')
    # lembar 1: lantai
    ox, oy = 20, 30
    out.append(f'<text x="{ox}" y="{oy-10}" font-weight="700" font-size="16">Lembar 1 — LANTAI utuh 122 x 244 cm (cat hijau, garis lakban putih 2 cm)</text>')
    out.append(f'<rect x="{ox}" y="{oy}" width="{W*S}" height="{H*S}" fill="#2e8b3c" stroke="#232323" stroke-width="2"/>')
    cx, cy = ox + W * S / 2, oy + H * S / 2
    out.append(f'<line x1="{cx}" y1="{oy}" x2="{cx}" y2="{oy+H*S}" stroke="#fff" stroke-width="4"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{300*S}" fill="none" stroke="#fff" stroke-width="4"/>')
    for sx in (-1, 1):
        x0 = cx + sx * (W / 2 - 9 - 250) * S
        out.append(f'<rect x="{min(x0, cx + sx*(W/2-9)*S)}" y="{cy-400*S}" width="{250*S}" height="{800*S}" fill="none" stroke="#fff" stroke-width="4"/>')
        gx = cx + sx * (W / 2 - 9 - 120) * S
        out.append(f'<rect x="{min(gx, cx + sx*(W/2-9)*S)}" y="{cy-200*S}" width="{120*S}" height="{400*S}" fill="#d9b98a" opacity=".9" stroke="#232323"/>')
        out.append(f'<text x="{(gx + cx + sx*(W/2-9)*S)/2}" y="{cy+4}" text-anchor="middle" font-size="11">GAWANG 40x12</text>')
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * (W / 2 - 9) * S, cy + sy * (H / 2 - 9) * S
            out.append(f'<polygon points="{px},{py} {px-sx*100*S},{py} {px},{py-sy*100*S}" fill="#d9b98a" stroke="#232323"/>')
    out.append(f'<text x="{ox+8}" y="{oy+H*S-8}" fill="#fff" font-size="12">dinding 12 cm di atas lantai, tepi dalam 120,2 x 242,2 cm</text>')
    # lembar 2: strip
    oy2 = oy + H * S + 60
    out.append(f'<text x="{ox}" y="{oy2-10}" font-weight="700" font-size="16">Lembar 2 — DINDING & GAWANG: 4 strip 12 cm dipakai, 5 strip sisa (kerf 3 mm)</text>')
    out.append(f'<rect x="{ox}" y="{oy2}" width="{W*S}" height="{H*S}" fill="#efe6d4" stroke="#232323" stroke-width="2"/>')
    y = oy2
    for i in range(9):
        used = i < len(pieces)
        col = pieces[i][2] if used else "#efe6d4"
        out.append(f'<rect x="{ox}" y="{y}" width="{W*S}" height="{STRIP*S}" fill="{col}" stroke="#232323" stroke-dasharray="{"" if used else "6 4"}"/>')
        if used:
            lens = pieces[i][1] if isinstance(pieces[i][1], list) else [pieces[i][1]]
            x = ox
            for L in lens:
                out.append(f'<rect x="{x}" y="{y}" width="{L*S}" height="{STRIP*S}" fill="none" stroke="#232323" stroke-width="1.5"/>')
                out.append(f'<text x="{x+L*S/2}" y="{y+STRIP*S/2+4}" text-anchor="middle" font-size="11">{L}</text>')
                x += (L + KERF) * S
            out.append(f'<text x="{ox+W*S+6}" y="{y+STRIP*S/2+4}" font-size="11">{pieces[i][0]}</text>' if False else "")
            out.append(f'<text x="{ox+6}" y="{y+12}" font-size="10" font-weight="700">{pieces[i][0]}</text>')
        else:
            out.append(f'<text x="{ox+6}" y="{y+STRIP*S/2+4}" font-size="11" fill="#777">sisa strip 12 x 244 (cadangan / Arena Mini 122 x 122)</text>')
        y += (STRIP + KERF) * S
    out.append(f'<text x="{ox+6}" y="{oy2+H*S-6}" font-size="11" fill="#777">sisa bawah {H - 9*STRIP - 8*KERF} mm</text>')
    out.append("</svg>")
    open(os.path.join(HERE, "arena-cutplan.svg"), "w", encoding="utf-8").write("\n".join(out))
    print("OK arena-cutplan.svg")


svg()
