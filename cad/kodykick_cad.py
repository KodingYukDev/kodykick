# KodyKick — robot soccer 2WD untuk anak (KodingYuk). CAD parametrik FreeCAD 1.1 headless.
#   "C:/Users/tunas/AppData/Local/Programs/FreeCAD 1.1/bin/freecadcmd.exe" kodykick_cad.py
# Satuan mm, Z ke atas, +Y = depan robot. Origin robot = titik tanah di bawah tengah poros roda.
# Output -> ../out/parts/*.stl, ../out/parts.json (warna, grup, bbox, sumber), ../out/kodykick.step,
#           ../out/kodypad.step, ../out/kodyarena.step
# Komponen beli dipakai model ASLI (STEP) dari ../components/ (lihat components/LICENSES.md):
#   TT motor, holder 4xAA, holder 3xAAA, joystick, tactile 12 mm, saklar geser = Adafruit_CAD_Parts (MIT)
#   SG90 + horn = FreeCAD-library (CC-BY 3.0) · modul ESP32-WROOM-32E = espressif/kicad-libraries (CC-BY-SA 4.0)
# Yang masih dimodelkan dari dimensi datasheet (tidak ada STEP publik): PCB DevKit V1 30-pin (modul WROOM asli),
#   PCB KY-023 (joystick asli), modul DRV8833, roda TT 65 mm, bola floorball, bola baja caster.
import json
import math
import os

import FreeCAD as App
import MeshPart
import Part

V = App.Vector
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
PARTS = os.path.join(OUT, "parts")
COMP = os.path.join(HERE, "..", "components")
os.makedirs(PARTS, exist_ok=True)

C = {  # warna sRGB hex -> Blender
    "yellow": "#FFDE00", "navy": "#22303A", "red": "#E6232A", "paper": "#F7F9F9", "ink": "#232323",
    "teal": "#0C7A89", "sun": "#F99007", "pcb": "#1b5e3a", "pcb_blue": "#1f3f8f", "pcb_red": "#9b1c1c",
    "metal": "#b9bdc2", "black": "#16181a", "tt_yellow": "#f2c230", "tire": "#2b2b2b", "rim": "#f2e26b",
    "white": "#fafafa", "wood": "#d9b98a", "green": "#2e8b3c", "line": "#f5f5f5", "glass": "#9fd8ff",
    "servo_blue": "#2a62c9", "orange": "#ff7a1a", "shield": "#c9ccd1",
}

# ------------------------------------------------------------------ parameter utama
WHEEL_D, WHEEL_W = 65.0, 26.0          # roda TT 65 mm
AXLE_Z = WHEEL_D / 2                   # 32.5
MOTOR_LEN_BACK, MOTOR_LEN_FRONT = 54.6, 16.0   # dari STEP Adafruit 3777: badan -54.6..+16 relatif poros
MOTOR_T_IN, MOTOR_T_OUT = 9.3, 11.3    # tebal sepanjang poros: 9.3 ke dalam, 11.3 ke luar (asimetris)
MOTOR_H = 22.4                         # tinggi gearbox
BASE_W, BASE_FRONT, BASE_REAR = 120.0, 80.0, -86.0
BASE_T = 3.0
BASE_TOP = AXLE_Z - MOTOR_H / 2        # 21.3 -> motor duduk di atas pelat, poros tepat di tengah
BASE_BOT = BASE_TOP - BASE_T           # 18.3 ground clearance
WALL = 2.0
SHELL_TOP = 72.0
BALL_D = 72.0                          # bola plastik berlubang (floorball) 72 mm
SCOOP_R = BALL_D / 2 + 4
SCOOP_CY = 92.0
WHEEL_X = BASE_W / 2 + 2 + WHEEL_W / 2   # 75 -> lebar total 176 mm
SERVO_XY = (-22.0, 50.0)               # poros servo kicker (vertikal), kiri-depan
SERVO_BOT = 11.3                       # dasar badan servo (menggantung lewat slot lantai)
MOTOR_GAP = 4.0                        # celah motor ke dinding (rusuk penekan cangkang)
MOTOR_X = BASE_W / 2 - WALL - MOTOR_GAP - MOTOR_T_OUT   # 42.7 -> pusat poros motor
ESP_Z = BASE_TOP + 8.5 + 2.5           # dasar PCB ESP32 (di atas header 8,5 + rel)
ESP_XY = (-1.0, 15.0)                  # pusat PCB ESP32 DevKit V1
DRV_XY = (-1.0, 15.0)                  # modul DRV8833 di bawah PCB ESP32, di antara dua baris header
HOLDER_Y = -48.0
SHELL_SCREWS = ((-52.0, -80.0), (52.0, -80.0), (-52.0, 44.0), (52.0, 44.0))
PARTS_META = []
SHAPES = {}
_STEP = {}


# ------------------------------------------------------------------ primitif
def vertical_edges(shape):
    return [e for e in shape.Edges if len(e.Vertexes) == 2
            and abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) < 1e-6
            and abs(e.Vertexes[0].Point.y - e.Vertexes[1].Point.y) < 1e-6]


def edges_at_z(shape, z):
    return [e for e in shape.Edges if abs(e.BoundBox.ZMax - z) < 1e-6 and abs(e.BoundBox.ZMin - z) < 1e-6]


def rbox(w, d, h, r=0.0, z0=0.0, x=0.0, y=0.0, top=0.0, bot=0.0):
    b = Part.makeBox(w, d, h, V(x - w / 2, y - d / 2, z0))
    if r > 0:
        b = b.makeFillet(min(r, w / 2 - 0.01, d / 2 - 0.01), vertical_edges(b))
    if top > 0:
        try:
            b = b.makeFillet(top, edges_at_z(b, z0 + h))
        except Exception:
            pass
    if bot > 0:
        try:
            b = b.makeFillet(bot, edges_at_z(b, z0))
        except Exception:
            pass
    return b


def cyl(r, h, x=0.0, y=0.0, z=0.0, axis=V(0, 0, 1)):
    return Part.makeCylinder(r, h, V(x, y, z), axis)


def fuse(*shapes):
    s = shapes[0]
    for t in shapes[1:]:
        s = s.fuse(t)
    return s.removeSplitter()


def cut(s, *tools):
    for t in tools:
        s = s.cut(t)
    return s


def step(name):
    """Baca STEP dari components/ (cache)."""
    if name not in _STEP:
        _STEP[name] = Part.read(os.path.join(COMP, name))
    return _STEP[name].copy()


def solids(shape, idx):
    return Part.makeCompound([shape.Solids[i] for i in idx]) if len(idx) > 1 else shape.Solids[idx[0]]


def xform(shape, matrix=None, move=(0, 0, 0)):
    s = shape.copy()
    if matrix is not None:
        s = s.transformShape(matrix)
    s.translate(V(*move))
    return s


def add(name, shape, color, group, note="", printed=False, qty=1, mesh_dev=0.08, source="dimodelkan dari datasheet"):
    path = os.path.join(PARTS, name + ".stl")
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=mesh_dev, AngularDeflection=0.3, Relative=False)
    m.write(path)
    bb = shape.BoundBox
    PARTS_META.append(dict(name=name, color=color, group=group, note=note, printed=printed, qty=qty, source=source,
                           volume_cm3=round(shape.Volume / 1000, 2) if printed else None,
                           bbox=[round(v, 2) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)]))
    SHAPES.setdefault(group, []).append((name, shape))
    return shape


SRC_ADA = "Adafruit_CAD_Parts (MIT)"
SRC_FC = "FreeCAD-library (CC-BY 3.0)"
SRC_ESP = "espressif/kicad-libraries (CC-BY-SA 4.0)"

# matriks: X' = y, Y' = z, Z' = x  (poros TT motor native Y -> X robot; panjang native Z -> Y robot)
M_TT = App.Matrix(0, 1, 0, 0,
                  0, 0, 1, 0,
                  1, 0, 0, 0,
                  0, 0, 0, 1)
# tactile: sumbu tombol native +Y -> +Z  (rotasi +90 deg sekitar X: y->z, z->-y)
M_ROTX90 = App.Matrix(1, 0, 0, 0,
                      0, 0, -1, 0,
                      0, 1, 0, 0,
                      0, 0, 0, 1)


# ================================================================== ROBOT: komponen beli (STEP asli)
def tt_motor(side):
    """Adafruit 3777 TT motor. Native: poros sepanjang Y di origin, badan Z -54.6..16, tebal Y -11.3..9.3.
    Setelah M_TT: poros sepanjang X, badan Y -54.6..16, tebal X -11.3..9.3 (sisi -X = sisi 11.3)."""
    s = xform(step("tt_motor_adafruit3777.step"), M_TT)
    if side > 0:                                    # kanan: cermin supaya sisi tebal (11.3) ke luar (+X)
        s = s.mirror(V(0, 0, 0), V(1, 0, 0))
    s.translate(V(side * MOTOR_X, 0, AXLE_Z))
    gear = solids(s, [0, 5, 6, 7])
    can = solids(s, [2, 3, 4])
    shaft = s.Solids[1]
    return gear, can, shaft


def wheel(side):
    x_in = side * (BASE_W / 2 + 2.0)
    x0 = min(x_in, x_in + side * WHEEL_W)
    outer = cyl(WHEEL_D / 2, WHEEL_W, x0, 0, AXLE_Z, V(1, 0, 0))
    tire = outer.cut(cyl(WHEEL_D / 2 - 6, WHEEL_W, x0, 0, AXLE_Z, V(1, 0, 0)))
    rim = cyl(WHEEL_D / 2 - 6, WHEEL_W, x0, 0, AXLE_Z, V(1, 0, 0))
    for k in range(6):
        a = k * math.pi / 3
        rim = rim.cut(cyl(6.5, WHEEL_W, x0, 16 * math.cos(a), AXLE_Z + 16 * math.sin(a), V(1, 0, 0)))
    for k in range(12):
        a = k * math.pi / 6
        groove = Part.makeBox(WHEEL_W, 3.0, 2.5, V(x0, -1.5, WHEEL_D / 2 - 2.5))
        groove.rotate(V(x0, 0, 0), V(1, 0, 0), math.degrees(a))
        groove.translate(V(0, 0, AXLE_Z))
        tire = tire.cut(groove)
    return tire, rim


def esp32_devkit(x, y, z):
    """ESP32 DevKit V1 30 pin: PCB 51.5x28.3 (datasheet DOIT) + modul ESP32-WROOM-32E ASLI (Espressif).
    Antena modul menghadap +Y (depan), micro-USB di -Y."""
    pcb = rbox(28.3, 51.5, 1.6, 1.5, z, x, y)
    mod = step("esp32_wroom_32e_espressif.step")            # 18 x 25.5 x 3.1, origin pojok
    mod.translate(V(x - 9.0, y + 25.75 - 25.5 - 1.0, z + 1.6 - 0.1))
    usb = Part.makeBox(7.5, 5.6, 2.8, V(x - 3.75, y - 25.75 - 1.5, z + 1.6))
    hdr = fuse(Part.makeBox(2.54, 38.1, 8.5, V(x - 14.15 + 1.0, y - 19.05, z - 8.5)),
               Part.makeBox(2.54, 38.1, 8.5, V(x + 14.15 - 3.54, y - 19.05, z - 8.5)))
    return pcb, mod, usb, hdr


def drv8833(x, y, z):
    pcb = rbox(18.0, 20.0, 1.6, 1.0, z, x, y)
    chip = Part.makeBox(5.0, 6.5, 1.0, V(x - 2.5, y - 3.25, z + 1.6))
    return pcb, chip


def aa_holder(x, y, z):
    """Adafruit 830: holder 4xAA 2x2 dengan saklar, 64.6 x 70 x 22.3. Pojok native (0,0,0) -> pusat (x,y)."""
    s = step("battery_holder_4xAA_adafruit830.step")
    s.translate(V(x - 32.3, y - 35.0, z + 0.2))
    return s.Solids[1], s.Solids[0]


def sg90(x, y, z_bot):
    """FreeCAD-library SG90: tegak, poros Z di (0,16.6), dasar z=0, atas poros z=29.9, telinga sepanjang Y.
    (x,y) = pusat poros robot; z_bot = dasar badan."""
    body = step("sg90_freecadlib.step")
    body.translate(V(x, y - 16.6, z_bot))
    horn = step("sg90_horn1_freecadlib.step")             # hub di (27,36.3), dasar z 25.7, lengan ke +X
    horn.translate(V(x - 27.0, y - 36.3, z_bot + 29.9 - 3.0 - 25.7))   # hub turun 3 mm ke spline poros
    return body, horn


def slide_switch(x, y, z, rot_z=0.0):
    """Adafruit 805 saklar geser 11.7 x 4 x 8 (z -6.3..1.7). (x,y,z) = pusat bawah badan."""
    s = step("slide_switch_adafruit805.step")
    if rot_z:
        s.rotate(V(0, 0, 0), V(0, 0, 1), rot_z)
    s.translate(V(x - 5.85, y + 2.0, z + 6.3))
    return s


# ================================================================== ROBOT: part cetak
def base_tray():
    d = BASE_FRONT - BASE_REAR
    yc = (BASE_FRONT + BASE_REAR) / 2
    outer = rbox(BASE_W, d, 10.0, 12.0, BASE_BOT, 0, yc)
    inner = rbox(BASE_W - 2 * WALL, d - 2 * WALL, 10.0, 10.0, BASE_TOP, 0, yc)
    tray = outer.cut(inner)
    for s in (-1, 1):
        xw = s * BASE_W / 2
        tray = tray.cut(Part.makeBox(WALL + 1.0, 7.0, 20.0, V(xw - (WALL + 1.0) / 2, -3.5, AXLE_Z - 3.5)))
        tray = tray.cut(cyl(3.5, WALL + 1.0, xw - (WALL + 1.0) / 2, 0, AXLE_Z, V(1, 0, 0)))
    x_in_motor = MOTOR_X - MOTOR_T_IN                     # 33.4 = muka dalam motor
    for s in (-1, 1):
        for yy, xin in ((MOTOR_LEN_FRONT + 1.0, x_in_motor - 2.0), (-MOTOR_LEN_BACK - 3.0, x_in_motor + 0.6)):
            xa, xb = sorted((s * (BASE_W / 2 - WALL), s * xin))        # klem depan gearbox & belakang kaleng
            tray = tray.fuse(Part.makeBox(xb - xa, 2.0, 14.0, V(xa, yy, BASE_TOP)))
        rx = min(s * x_in_motor, s * (x_in_motor - 2.0))
        for yy in (-11.0,):                               # tiang pendek sisi dalam motor
            tray = tray.fuse(Part.makeBox(2.0, 3.0, 12.0, V(rx, yy, BASE_TOP)))
    cup_x, cup_y = 0.0, BASE_REAR + 10.0                  # caster di belakang holder baterai
    cup = cyl(9.5, BASE_TOP - 6.0, cup_x, cup_y, 6.0)
    cup = cup.cut(Part.makeSphere(6.6, V(cup_x, cup_y, 6.6)))
    cup = cup.cut(cyl(5.0, 8.0, cup_x, cup_y, 0.0))
    tray = tray.fuse(cup)
    # pilar sekrup cangkang: M3x16 self-tapping dari bawah tray ke boss cangkang (4 titik)
    for sx, sy in SHELL_SCREWS:
        tray = tray.fuse(cyl(3.5, 10.0, sx, sy, BASE_TOP))
        tray = tray.cut(cyl(1.7, 20.0, sx, sy, BASE_BOT - 1.0))
        tray = tray.cut(cyl(3.2, 2.0, sx, sy, BASE_BOT - 0.5))           # countersink dangkal kepala sekrup
    # rel penjepit PCB ESP32 DevKit V1 (lebar 28.3, tebal 1.6): rel berlip di kedua sisi, PCB diselipkan dari atas
    ex, ey, ez = ESP_XY[0], ESP_XY[1], ESP_Z
    for sx in (-1, 1):
        xr = ex + sx * (14.15 + 0.3)
        rail = Part.makeBox(2.0, 40.0, ez + 1.6 + 1.2 - BASE_TOP, V(min(xr, xr + sx * 2.0), ey - 20.0, BASE_TOP))
        lip = Part.makeBox(1.2, 40.0, 1.2, V(min(xr, xr - sx * 1.2), ey - 20.0, ez + 1.6 + 0.2))
        tray = tray.fuse(rail).fuse(lip)
    for sy in (ey - 25.75 - 2.0, ey + 25.75):                             # stopper ujung PCB
        tray = tray.fuse(Part.makeBox(28.3 + 4.6, 2.0, ez + 1.6 - BASE_TOP, V(ex - 14.15 - 2.3, sy, BASE_TOP)))
    # klip modul DRV8833 (18 x 20): 4 sudut L
    dx, dy, dz = DRV_XY[0], DRV_XY[1], BASE_TOP + 1.0
    for sy in (-1, 1):                                                   # 2 klip ujung (depan/belakang) + lip
        cy = dy + sy * 10.3
        tray = tray.fuse(Part.makeBox(12.0, 1.5, dz + 1.6 + 1.2 - BASE_TOP, V(dx - 6.0, min(cy, cy + sy * 1.5), BASE_TOP)))
        tray = tray.fuse(Part.makeBox(12.0, 1.2, 1.0, V(dx - 6.0, min(cy, cy - sy * 1.2), dz + 1.6 + 0.2)))
    # slot servo + 2 boss sekrup M2x8 di telinga (lubang telinga SG90 asli: y -19.0 dan +8.3 relatif poros, z 27.2)
    tray = tray.cut(Part.makeBox(12.8, 23.7, 10.0, V(SERVO_XY[0] - 6.4, SERVO_XY[1] - 17.1, BASE_BOT)))
    for dy_ in (-19.0, 8.3):
        bx, by = SERVO_XY[0], SERVO_XY[1] + dy_
        tray = tray.fuse(cyl(2.6, SERVO_BOT + 15.9 - BASE_TOP, bx, by, BASE_TOP).cut(cyl(0.8, 8.0, bx, by, SERVO_BOT + 15.9 - 6.0)))
    # penahan holder baterai 4xAA 2x2 (64.6 x 70): 4 nub sudut + ditempel double tape / velcro
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * 32.6, HOLDER_Y + sy * 35.3
            tray = tray.fuse(Part.makeBox(1.5, 8.0, 6.0, V(min(cx, cx + sx * 1.5), min(cy, cy - sy * 8.0), BASE_TOP)))
            tray = tray.fuse(Part.makeBox(8.0, 1.5, 6.0, V(min(cx, cx - sx * 8.0), min(cy, cy + sy * 1.5), BASE_TOP)))
    for sx in (-20, 0, 20):
        for sy in (-50, 30):
            tray = tray.cut(cyl(5.0, 10.0, sx, sy, BASE_BOT))
    tray = tray.cut(Part.makeBox(14.0, WALL + 1.0, 8.0, V(-46.0, BASE_REAR - 0.5, BASE_TOP)))  # kabel/saklar
    return tray.removeSplitter()


def top_shell():
    z0 = BASE_BOT + 10.0
    body_front = 46.0
    d = body_front - BASE_REAR
    yc = (body_front + BASE_REAR) / 2
    body = rbox(BASE_W, d, SHELL_TOP - z0, 22.0, z0, 0, yc, top=10.0)
    arm_h = 26.0
    arms = rbox(BASE_W, BASE_FRONT - 20.0, arm_h, 10.0, z0, 0, (BASE_FRONT + 20.0) / 2, top=4.0)
    shell = fuse(body, arms)
    shell = shell.cut(cyl(SCOOP_R, 200.0, 0, SCOOP_CY, 0))
    cav_body = rbox(BASE_W - 2 * WALL, d - 2 * WALL, SHELL_TOP - z0 - WALL, 20.0, z0 - 0.01, 0, yc, top=8.0)
    cav_arms = rbox(BASE_W - 2 * WALL, BASE_FRONT - 20.0 - 2 * WALL, arm_h - WALL, 8.0, z0 - 0.01, 0, (BASE_FRONT + 20.0) / 2)
    cav_arms = cav_arms.cut(cyl(SCOOP_R + WALL, 200.0, 0, SCOOP_CY, 0))
    shell = cut(shell, cav_body, cav_arms)
    shell = shell.cut(rbox(44.0, 44.0, 1.0, 4.0, SHELL_TOP - 1.0, 0, -5.0))
    for sx in (-20, 20):
        shell = shell.cut(cyl(5.0, 30.0, sx, body_front - 15.0, 55.0, V(0, 1, 0)))
    shell = shell.cut(Part.makeBox(2.6, 32.0, 3.0, V(-1.3, -66.0, SHELL_TOP - 3.0)))
    shell = shell.cut(Part.makeBox(14.0, 10.0, 9.0, V(-46.0, BASE_REAR - 5.0, z0)))
    for s in (-1, 1):
        shell = shell.cut(Part.makeBox(WALL + 3.0, 8.0, 8.0, V(s * BASE_W / 2 - (WALL + 3.0) / 2, -4.0, z0 - 0.1)))
    shell = shell.cut(Part.makeBox(56.0, 30.0, 26.0, V(-30.0, 40.0, 28.0)))     # jendela kicker
    # boss sekrup M3 (self-tapping) turun dari langit-langit ke pilar tray (z 31.3)
    for sx, sy in SHELL_SCREWS:
        ceil = SHELL_TOP - WALL if sy < 30 else z0 + arm_h - WALL
        shell = shell.fuse(cyl(4.5, ceil - 31.3 + 0.5, sx, sy, 31.3 - 0.5).cut(cyl(1.4, 12.0, sx, sy, 31.3 - 0.5)))
    # rusuk penekan motor: 2 rusuk per motor dari langit-langit ke atas gearbox (z 44.0), lebar motor + celah
    for s in (-1, 1):
        xa = min(s * (MOTOR_X - MOTOR_T_IN - 1.0), s * (BASE_W / 2 - WALL))
        xb = max(s * (MOTOR_X - MOTOR_T_IN - 1.0), s * (BASE_W / 2 - WALL))
        for yy in (-30.0, 2.0):
            shell = shell.fuse(Part.makeBox(xb - xa, 2.5, SHELL_TOP - WALL - 44.0 + 0.5, V(xa, yy, 44.0)))
    return shell.removeSplitter()


def fin():
    f = Part.makeBox(2.4, 32.0, 3.0, V(-1.2, -66.0, SHELL_TOP - 3.0))
    blade = Part.makeBox(2.4, 28.0, 14.0, V(-1.2, -64.0, SHELL_TOP))
    try:
        blade = blade.makeFillet(5.0, [e for e in blade.Edges if abs(e.BoundBox.ZMax - (SHELL_TOP + 14.0)) < 1e-6
                                        and abs(e.BoundBox.ZMin - (SHELL_TOP + 14.0)) < 1e-6 and abs(e.Length - 2.4) < 1e-6])
    except Exception:
        pass
    return fuse(f, blade)


def number_card():
    return rbox(43.0, 43.0, 0.8, 4.0, SHELL_TOP - 1.0, 0, -5.0)


def eye_lens(sx):
    return cyl(4.8, 3.0, sx, 46.0 - 1.0, 55.0, V(0, 1, 0))


def kicker(horn_top_z):
    """Pemukul bola cetak, disekrup ke horn servo asli: cakram hub di atas horn, lengan ke +X, paddle melintang."""
    x, y = SERVO_XY
    z = horn_top_z
    hub = cyl(6.0, 2.0, x, y, z).cut(cyl(1.0, 2.0, x, y, z))
    arm = Part.makeBox(32.0, 4.0, 3.0, V(x, y + 2.0, z))
    arm2 = Part.makeBox(4.0, 5.0, 3.0, V(x + 28.0, y + 4.0, z))
    paddle = rbox(36.0, 3.0, 22.0, 1.0, 30.0, 6.0, y + 6.5)
    return fuse(hub, arm, arm2, paddle)


def ball(x=0.0, y=SCOOP_CY, z=BALL_D / 2):
    return Part.makeSphere(BALL_D / 2, V(x, y, z))


# ================================================================== KODYPAD (remote DIY ESP-NOW)
PAD_W, PAD_D, PAD_H = 150.0, 74.0, 26.0
PAD_SPLIT = 9.0
JZ = PAD_SPLIT - 2.0          # dasar PCB di pad
PCB_TOP = JZ + 1.6


def pad_shells():
    body = rbox(PAD_W, PAD_D, PAD_H, 18.0, 0, 0, 0, top=6.0, bot=4.0)
    for s in (-1, 1):
        body = body.fuse(rbox(34.0, 40.0, PAD_H - 2.0, 14.0, 0, s * 56.0, -28.0, top=6.0, bot=4.0))
    body = body.removeSplitter()
    cav = rbox(PAD_W - 2 * WALL, PAD_D - 2 * WALL, PAD_H - 2 * WALL, 16.0, WALL, 0, 0)
    for s in (-1, 1):
        cav = cav.fuse(rbox(34.0 - 2 * WALL, 40.0 - 2 * WALL, PAD_H - 2.0 - 2 * WALL, 12.0, WALL, s * 56.0, -28.0))
    hollow = body.cut(cav)
    cutter_top = Part.makeBox(400, 400, 100, V(-200, -200, PAD_SPLIT))
    cutter_bot = Part.makeBox(400, 400, 100, V(-200, -200, PAD_SPLIT - 100))
    bottom = hollow.cut(cutter_top)
    top = hollow.cut(cutter_bot)
    top = top.cut(cyl(12.0, 20.0, -45.0, 4.0, PAD_H - 10.0))
    top = top.cut(cyl(9.5, 20.0, 45.0, 10.0, PAD_H - 10.0))
    top = top.cut(cyl(6.5, 20.0, 25.0, -2.0, PAD_H - 10.0))
    top = top.cut(cyl(6.5, 20.0, 65.0, -2.0, PAD_H - 10.0))
    top = top.cut(cyl(2.0, 20.0, 0.0, 30.0, PAD_H - 10.0))
    top = top.cut(Part.makeBox(9.0, 4.0, 20.0, V(-44.5, 26.0, PAD_H - 10.0)))       # saklar geser
    top = top.cut(rbox(30.0, 10.0, 1.0, 2.0, PAD_H - 1.0, 0, 0))
    top = top.cut(Part.makeBox(10.0, 6.0, 6.0, V(-5.0, -PAD_D / 2 - 1.0, 19.0)))     # USB-C C3 (belakang)
    for sx, sy in ((-58, 18), (-32, 18), (26, 16), (64, 16)):
        bottom = bottom.fuse(cyl(3.0, JZ - WALL, sx, sy, WALL).cut(cyl(1.2, JZ - WALL, sx, sy, WALL)))
    return top.removeSplitter(), bottom.removeSplitter()


def pad_internals():
    p = {}
    jx, jy = -45.0, 4.0
    p["pad_joy_pcb"] = (rbox(26.0, 34.0, 1.6, 1.0, JZ, jx, jy), "pcb", "PCB modul KY-023 (dimodelkan)", None)
    joy = step("joystick_adafruit512.step")                 # PCB Adafruit (solid0) dibuang, joystick asli dipakai
    joy = solids(joy, list(range(1, 9)))
    joy.translate(V(jx - 19.1, jy - 19.1, PCB_TOP - 1.6))
    p["pad_joy_body"] = (joy, "black", "joystick analog 2 sumbu + tombol (KY-023)", SRC_ADA)
    p["pad_joy_cap"] = (fuse(cyl(10.0, 5.0, jx, jy, PAD_H - 1.0), cyl(7.0, 7.0, jx, jy, PAD_H - 8.0)), "ink", "cap joystick (cetak PLA)", None)
    for name, (bx, by, r, col) in {"kick": (45.0, 10.0, 9.0, "red"), "turbo": (25.0, -2.0, 6.0, "teal"), "horn": (65.0, -2.0, 6.0, "sun")}.items():
        sw = xform(step("tactile12_adafruit1119.step"), M_ROTX90, (bx, by, PCB_TOP))   # badan z 0..3.8, aktuator ..6
        p["pad_tact_" + name] = (sw, "black", "tactile 12x12 mm B3F", SRC_ADA)
        p["pad_cap_" + name] = (cyl(r, PAD_H + 2.0 - (PCB_TOP + 5.5), bx, by, PCB_TOP + 5.5), col, "cap tombol (cetak PLA)", None)
    p["pad_main_pcb"] = (rbox(48.0, 30.0, 1.6, 2.0, JZ, 45.0, 4.0), "pcb", "perfboard tombol kanan", None)
    aaa = step("battery_holder_3xAAA_adafruit727.step")      # 37 x 63(+JST 66) x 17.3, pojok native (0,0,0)
    aaa.translate(V(-18.5, -33.0, WALL + 0.5))
    p["pad_aaa"] = (aaa, "black", "holder 3xAAA + JST", SRC_ADA)
    c3z = WALL + 0.5 + 17.3 + 0.2
    p["pad_c3"] = (fuse(rbox(18.0, 22.5, 1.0, 1.0, c3z, 0.0, -24.0),
                        Part.makeBox(12.0, 13.0, 2.2, V(-6.0, -27.0, c3z + 1.0)),
                        Part.makeBox(9.0, 7.0, 2.8, V(-4.5, -36.5, c3z + 1.0))), "black", "ESP32-C3 Super Mini (dimodelkan)", None)
    p["pad_led"] = (cyl(1.6, 6.0, 0.0, 30.0, PAD_H - 6.0), "glass", "LED 3 mm", None)
    p["pad_switch"] = (slide_switch(-40.0, 26.0, PAD_H - 8.5), "black", "saklar geser SPDT", SRC_ADA)
    return p


# ================================================================== KODYARENA (triplek 9 mm, 122 x 244 cm)
PLY = 9.0
FLOOR_X, FLOOR_Y = 2440.0, 1220.0
WALL_H = 120.0
GOAL_W, GOAL_D = 400.0, 120.0


def arena_parts():
    p = {}
    z = PLY
    p["arena_floor"] = Part.makeBox(FLOOR_X, FLOOR_Y, PLY, V(-FLOOR_X / 2, -FLOOR_Y / 2, 0))
    p["arena_wall_long_a"] = Part.makeBox(FLOOR_X, PLY, WALL_H, V(-FLOOR_X / 2, -FLOOR_Y / 2, z))
    p["arena_wall_long_b"] = Part.makeBox(FLOOR_X, PLY, WALL_H, V(-FLOOR_X / 2, FLOOR_Y / 2 - PLY, z))
    inner_y = FLOOR_Y - 2 * PLY
    p["arena_wall_short_a"] = Part.makeBox(PLY, inner_y, WALL_H, V(-FLOOR_X / 2, -inner_y / 2, z))
    p["arena_wall_short_b"] = Part.makeBox(PLY, inner_y, WALL_H, V(FLOOR_X / 2 - PLY, -inner_y / 2, z))
    for s, tag in ((-1, "a"), (1, "b")):
        x_in = s * (FLOOR_X / 2 - PLY)
        x0 = min(x_in, x_in - s * GOAL_D)
        for t, tag2 in ((-1, "l"), (1, "r")):
            p[f"arena_goal_{tag}_side_{tag2}"] = Part.makeBox(GOAL_D, PLY, WALL_H, V(x0, t * (GOAL_W / 2) - (PLY if t > 0 else 0), z))
        p[f"arena_goal_{tag}_roof"] = Part.makeBox(GOAL_D, GOAL_W + 2 * PLY, PLY, V(x0, -GOAL_W / 2 - PLY, z + WALL_H))
        xl = x_in - s * GOAL_D
        p[f"arena_line_goal_{tag}"] = Part.makeBox(20.0, GOAL_W, 1.0, V(xl - (20.0 if s > 0 else 0), -GOAL_W / 2, z))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (FLOOR_X / 2 - PLY), sy * (FLOOR_Y / 2 - PLY)
            tri = Part.makePolygon([V(cx, cy, z), V(cx - sx * 100.0, cy, z), V(cx, cy - sy * 100.0, z), V(cx, cy, z)])
            p[f"arena_corner_{'a' if sx < 0 else 'b'}{'l' if sy < 0 else 'r'}"] = Part.Face(tri).extrude(V(0, 0, WALL_H))
    p["arena_line_center"] = Part.makeBox(20.0, inner_y, 1.0, V(-10.0, -inner_y / 2, z))
    p["arena_line_circle"] = cyl(310.0, 1.0, 0, 0, z).cut(cyl(290.0, 1.0, 0, 0, z))
    for s, tag in ((-1, "a"), (1, "b")):
        x_in = s * (FLOOR_X / 2 - PLY)
        xa = min(x_in, x_in - s * 250.0)
        box = Part.makeBox(250.0, 800.0, 1.0, V(xa, -400.0, z)).cut(Part.makeBox(230.0, 760.0, 1.0, V(xa + (20.0 if s < 0 else 0), -380.0, z)))
        p[f"arena_line_pen_{tag}"] = box
    p["arena_spots"] = fuse(*[cyl(10.0, 1.0, x, y, z) for x, y in ((0, 0), (-450, -300), (-450, 300), (450, -300), (450, 300))])
    return p


# ================================================================== BUILD
def build_robot():
    add("robot_base_tray", base_tray(), "navy", "robot", "cetak PLA, tray bawah: motor, baterai, ESP32, caster", printed=True, source="desain KodingYuk")
    add("robot_top_shell", top_shell(), "yellow", "robot", "cetak PLA, cangkang + scoop bola", printed=True, source="desain KodingYuk")
    add("robot_fin", fin(), "red", "robot", "cetak PLA, sirip tim (warna tim)", printed=True, source="desain KodingYuk")
    add("robot_number_card", number_card(), "paper", "robot", "kartu nomor punggung", printed=True, source="desain KodingYuk")
    for s in (-1, 1):
        add(f"robot_eye_{'l' if s < 0 else 'r'}", eye_lens(s * 20.0), "glass", "robot", "lensa LED mata (PLA transparan)", printed=True, source="desain KodingYuk")
    for s in (-1, 1):
        tag = 'l' if s < 0 else 'r'
        gear, can, shaft = tt_motor(s)
        add(f"tt_gearbox_{tag}", gear, "tt_yellow", "robot", "TT gear motor 1:48 — gearbox", source=SRC_ADA)
        add(f"tt_can_{tag}", can, "metal", "robot", "TT gear motor — kaleng motor DC", source=SRC_ADA)
        add(f"tt_shaft_{tag}", shaft, "metal", "robot", "TT gear motor — poros ganda", source=SRC_ADA)
        tire, rim = wheel(s)
        add(f"wheel_tire_{tag}", tire, "tire", "robot", "roda TT 65 mm karet")
        add(f"wheel_rim_{tag}", rim, "rim", "robot", "velg roda TT")
    pcb, mod, usb, hdr = esp32_devkit(ESP_XY[0], ESP_XY[1], ESP_Z)
    add("esp32_pcb", pcb, "black", "robot", "PCB ESP32 DevKit V1 30 pin 51,5x28,3 (dimodelkan)")
    add("esp32_module", mod, "shield", "robot", "modul ESP32-WROOM-32E", source=SRC_ESP, mesh_dev=0.15)
    add("esp32_usb", usb, "metal", "robot", "micro-USB")
    add("esp32_headers", hdr, "ink", "robot", "pin header 2x15")
    dpcb, dchip = drv8833(DRV_XY[0], DRV_XY[1], BASE_TOP + 1.0)
    add("drv8833_pcb", dpcb, "pcb_blue", "robot", "modul DRV8833 2 ch 1,5 A (dimodelkan)")
    add("drv8833_chip", dchip, "black", "robot", "IC DRV8833")
    hb, hin = aa_holder(0.0, HOLDER_Y, BASE_TOP + 0.5)
    add("aa_holder", hb, "black", "robot", "holder 4xAA 2x2 + saklar", source=SRC_ADA)
    add("aa_holder_inner", hin, "ink", "robot", "holder 4xAA — bagian dalam/tutup", source=SRC_ADA)
    body, horn = sg90(SERVO_XY[0], SERVO_XY[1], SERVO_BOT)
    add("sg90_body", body, "servo_blue", "robot", "servo SG90 kicker (poros vertikal)", source=SRC_FC)
    add("sg90_horn", horn, "white", "robot", "horn servo 1 lengan", source=SRC_FC)
    horn_top = horn.BoundBox.ZMax
    add("robot_kicker", kicker(horn_top), "red", "robot", "cetak PLA, pemukul bola disekrup ke horn", printed=True, source="desain KodingYuk")
    add("switch_body", slide_switch(-39.0, BASE_REAR + 6.0, BASE_TOP), "black", "robot", "saklar geser power (cadangan; holder 830 sudah ada saklar)", source=SRC_ADA)
    add("ball", ball(), "white", "ball", "bola plastik berlubang (floorball) 72 mm")
    add("caster_ball", Part.makeSphere(6.35, V(0.0, BASE_REAR + 10.0, 6.35)), "metal", "robot", "bola baja 1/2 inch (gotri) di cup cetak")


def build_pad():
    top, bottom = pad_shells()
    add("pad_shell_top", top, "yellow", "pad", "cetak PLA, cangkang atas KodyPad", printed=True, source="desain KodingYuk")
    add("pad_shell_bottom", bottom, "navy", "pad", "cetak PLA, cangkang bawah KodyPad", printed=True, source="desain KodingYuk")
    for k, (s, col, note, src) in pad_internals().items():
        add(k, s, col, "pad", note, printed=k.startswith("pad_cap") or k == "pad_joy_cap",
            source=src or ("desain KodingYuk" if "cetak" in note else "dimodelkan dari datasheet"))


def build_arena():
    col = {"floor": "green", "wall": "wood", "goal": "wood", "corner": "wood", "line": "line", "spots": "line"}
    for k, s in arena_parts().items():
        kind = k.split("_")[1]
        note = {"floor": "triplek 9 mm 122x244 utuh, cat hijau", "wall": "strip triplek 12 cm", "goal": "gawang 40 cm lebar x 12 cm dalam",
                "corner": "pojok 45 derajat segitiga 10 cm", "line": "lakban putih 2 cm", "spots": "titik netral"}.get(kind, "")
        add(k, s, col.get(kind, "wood"), "arena", note, mesh_dev=0.5, source="desain KodingYuk")


def export_step(group, fname):
    comp = Part.makeCompound([s for _, s in SHAPES.get(group, [])])
    comp.exportStep(os.path.join(OUT, fname))


def main():
    build_robot()
    build_arena()
    export_step("robot", "kodykick.step")
    export_step("arena", "kodyarena.step")
    meta = dict(colors=C, parts=PARTS_META,
                params=dict(wheel_d=WHEEL_D, wheel_x=WHEEL_X, axle_z=AXLE_Z, base=[BASE_W, BASE_REAR, BASE_FRONT],
                            shell_top=SHELL_TOP, ball_d=BALL_D, scoop_cy=SCOOP_CY,
                            arena=[FLOOR_X, FLOOR_Y, WALL_H, GOAL_W, GOAL_D, PLY]))
    json.dump(meta, open(os.path.join(OUT, "parts.json"), "w"), indent=1)
    printed = [p for p in PARTS_META if p["printed"]]
    print("PARTS", len(PARTS_META), "printed cm3:", round(sum(p["volume_cm3"] for p in printed), 1))
    for p in printed:
        print(f"  {p['name']:24s} {p['volume_cm3']:7.2f} cm3  bbox {p['bbox']}")
    for p in PARTS_META:
        if p["group"] in ("robot", "pad") and not p["printed"]:
            print(f"  [{p['source'][:22]:22s}] {p['name']:22s} bbox {p['bbox']}")
    print("DONE")


main()
