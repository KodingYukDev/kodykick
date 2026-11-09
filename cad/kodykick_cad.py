# KodyKick — robot soccer 2WD untuk anak (KodingYuk). CAD parametrik FreeCAD 1.1 headless.
#   "C:/Users/tunas/AppData/Local/Programs/FreeCAD 1.1/bin/freecadcmd.exe" kodykick_cad.py
# Satuan mm, Z ke atas, +Y = depan robot. Origin robot = titik tanah di bawah tengah poros roda.
# Output -> ../out/parts/*.stl, ../out/parts.json (warna, grup, bbox), ../out/kodykick.step,
#           ../out/kodypad.step, ../out/kodyarena.step
# Grup part: robot (cetak 3D + komponen beli), pad (remote DIY), arena (triplek 9 mm 122x244), ball.
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
os.makedirs(PARTS, exist_ok=True)

C = {  # warna sRGB hex -> Blender
    "yellow": "#FFDE00", "navy": "#22303A", "red": "#E6232A", "paper": "#F7F9F9", "ink": "#232323",
    "teal": "#0C7A89", "sun": "#F99007", "pcb": "#1b5e3a", "pcb_blue": "#1f3f8f", "pcb_red": "#9b1c1c",
    "metal": "#b9bdc2", "black": "#16181a", "tt_yellow": "#f2c230", "tire": "#2b2b2b", "rim": "#f2e26b",
    "white": "#fafafa", "wood": "#d9b98a", "green": "#2e8b3c", "line": "#f5f5f5", "glass": "#9fd8ff",
    "servo_blue": "#2a62c9", "orange": "#ff7a1a",
}

# ------------------------------------------------------------------ parameter utama
WHEEL_D, WHEEL_W = 65.0, 26.0          # roda TT kuning 65 mm
AXLE_Z = WHEEL_D / 2                   # 32.5
MOTOR_L, MOTOR_T, MOTOR_H = 70.0, 18.5, 22.5   # TT gear motor (panjang y, tebal x, tinggi z)
SHAFT_FROM_FRONT = 11.0                # poros 11 mm dari ujung depan gearbox
BASE_W, BASE_FRONT, BASE_REAR = 108.0, 80.0, -78.0
BASE_T = 3.0
BASE_TOP = AXLE_Z - MOTOR_H / 2        # 21.25 -> motor duduk di atas pelat, poros tepat di tengah
BASE_BOT = BASE_TOP - BASE_T           # 18.25 ground clearance
WALL = 2.0
SHELL_TOP = 72.0
BALL_D = 72.0                          # bola plastik berlubang (floorball) 72 mm
SCOOP_R = BALL_D / 2 + 4               # radius cekungan penangkap bola
SCOOP_CY = 92.0                        # pusat cekungan (y) -> bola nyangkut di depan robot
WHEEL_X = BASE_W / 2 + 2 + WHEEL_W / 2   # 67 -> lebar total 160 mm
SERVO_XY = (-22.0, 50.0)                # servo kicker (poros vertikal), kiri-depan
PARTS_META = []
SHAPES = {}


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


def add(name, shape, color, group, note="", printed=False, qty=1, mesh_dev=0.08):
    path = os.path.join(PARTS, name + ".stl")
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=mesh_dev, AngularDeflection=0.3, Relative=False)
    m.write(path)
    bb = shape.BoundBox
    PARTS_META.append(dict(name=name, color=color, group=group, note=note, printed=printed, qty=qty,
                           volume_cm3=round(shape.Volume / 1000, 2) if printed else None,
                           bbox=[round(v, 2) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)]))
    SHAPES.setdefault(group, []).append((name, shape))
    return shape


# ================================================================== ROBOT: komponen beli
def tt_motor(side):
    """TT gear motor + poros ganda. side=+1 kanan. Poros di y=0, z=AXLE_Z. Body ke belakang."""
    x = side * (BASE_W / 2 - WALL - 1.0 - MOTOR_T / 2)
    y0 = SHAFT_FROM_FRONT - MOTOR_L                       # -59 .. +11
    gear = Part.makeBox(MOTOR_T, 37.0, MOTOR_H, V(x - MOTOR_T / 2, y0 + MOTOR_L - 37.0, AXLE_Z - MOTOR_H / 2))
    motor = cyl(10.0, MOTOR_L - 37.0, x, y0, AXLE_Z, V(0, 1, 0))
    xin = x - side * (MOTOR_T / 2 + 5.0)
    xout = x + side * (MOTOR_T / 2 + WHEEL_W + 4.0)
    shaft = cyl(2.6, abs(xout - xin), min(xin, xout), 0, AXLE_Z, V(1, 0, 0))
    return fuse(gear, motor), shaft, x


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
    """ESP32 DevKit V1 30 pin: PCB 51.5x28.3, modul WROOM, 2 header. USB micro di -y."""
    pcb = rbox(28.3, 51.5, 1.6, 1.5, z, x, y)
    module = Part.makeBox(18.0, 25.5, 3.2, V(x - 9, y + 25.75 - 25.5 - 2, z + 1.6))
    can = Part.makeBox(16.0, 18.0, 3.0, V(x - 8, y + 25.75 - 18.5 - 2, z + 1.8))
    usb = Part.makeBox(7.5, 5.6, 2.8, V(x - 3.75, y - 25.75 - 1.5, z + 1.6))
    hdr = fuse(Part.makeBox(2.54, 38.1, 8.5, V(x - 14.15 + 1.0, y - 19.05, z - 8.5)),
               Part.makeBox(2.54, 38.1, 8.5, V(x + 14.15 - 3.54, y - 19.05, z - 8.5)))
    return pcb, fuse(module, can), usb, hdr


def drv8833(x, y, z):
    pcb = rbox(18.0, 20.0, 1.6, 1.0, z, x, y)
    chip = Part.makeBox(5.0, 6.5, 1.0, V(x - 2.5, y - 3.25, z + 1.6))
    return pcb, chip


def aa_holder(x, y, z):
    """Holder 4xAA 2x2 datar: 58 x 62 x 15."""
    body = rbox(58.0, 62.0, 15.0, 2.0, z, x, y)
    xs = (-21.75, -7.25, 7.25, 21.75)
    body = cut(body, *[cyl(7.3, 56.0, x + i, y - 28.0, z + 8.0, V(0, 1, 0)) for i in xs])
    cells = fuse(*[cyl(7.0, 50.0, x + i, y - 25.0, z + 8.0, V(0, 1, 0)) for i in xs])
    return body, cells


def sg90(x, y, z):
    """SG90 poros VERTIKAL. (x,y,z) = pusat atas poros. Body 22.5 x 12.2 x 22.7 menggantung ke bawah."""
    body = Part.makeBox(22.5, 12.2, 22.7, V(x - 22.5 + 6.0, y - 6.1, z - 22.7 - 4.0))
    ears = Part.makeBox(32.3, 12.2, 2.5, V(x - 22.5 + 6.0 - 4.9, y - 6.1, z - 22.7 - 4.0 + 16.0))
    boss = cyl(6.0, 4.0, x, y, z - 4.0)
    shaft = cyl(2.4, 4.0, x, y, z)
    horn = fuse(cyl(3.5, 1.6, x, y, z + 2.4), Part.makeBox(18.0, 4.0, 1.6, V(x, y - 2.0, z + 2.4)))
    return fuse(body, ears, boss), shaft, horn


def slide_switch(x, y, z):
    body = Part.makeBox(12.0, 6.0, 6.0, V(x - 6, y - 3, z))
    knob = Part.makeBox(3.5, 2.5, 4.0, V(x + 0.25, y - 1.25, z + 6))
    return body, knob


# ================================================================== ROBOT: part cetak
def base_tray():
    d = BASE_FRONT - BASE_REAR
    yc = (BASE_FRONT + BASE_REAR) / 2
    outer = rbox(BASE_W, d, 10.0, 12.0, BASE_BOT, 0, yc)
    inner = rbox(BASE_W - 2 * WALL, d - 2 * WALL, 10.0, 10.0, BASE_TOP, 0, yc)
    tray = outer.cut(inner)
    for s in (-1, 1):
        xw = s * BASE_W / 2
        slot = Part.makeBox(WALL + 1.0, 7.0, 20.0, V(xw - (WALL + 1.0) / 2, -3.5, AXLE_Z - 3.5))
        tray = tray.cut(slot)
        tray = tray.cut(cyl(3.5, WALL + 1.0, xw - (WALL + 1.0) / 2, 0, AXLE_Z, V(1, 0, 0)))
    for s in (-1, 1):
        x_in_wall = s * (BASE_W / 2 - WALL)                     # muka dalam dinding
        x_motor_in = s * (BASE_W / 2 - WALL - 1.0 - MOTOR_T)    # sisi dalam motor
        xa, xb = sorted((x_in_wall, x_motor_in - s * 2.0))
        for yy in (SHAFT_FROM_FRONT + 1.0, SHAFT_FROM_FRONT - MOTOR_L - 2.0):
            tray = tray.fuse(Part.makeBox(xb - xa, 2.0, 14.0, V(xa, yy, BASE_TOP)))
        rx = min(x_motor_in, x_motor_in - s * 2.0)
        for yy in (-24.0, 4.0):
            tray = tray.fuse(Part.makeBox(2.0, 3.0, 12.0, V(rx, yy, BASE_TOP)))
    cup_x, cup_y = 0.0, BASE_REAR + 14.0
    cup = cyl(9.5, BASE_TOP - 6.0, cup_x, cup_y, 6.0)
    cup = cup.cut(Part.makeSphere(6.6, V(cup_x, cup_y, 6.6)))
    cup = cup.cut(cyl(5.0, 8.0, cup_x, cup_y, 0.0))
    tray = tray.fuse(cup)
    for sx, sy in ((-46, -72), (46, -72), (-46, 44), (46, 44)):
        tray = tray.fuse(cyl(3.0, 10.0, sx, sy, BASE_TOP))
    for sx, sy in ((-12 - 11.4, 16 + 24), (-12 + 11.4, 16 + 24), (-12 - 11.4, 16 - 24), (-12 + 11.4, 16 - 24)):
        tray = tray.fuse(cyl(2.6, 4.0, sx, sy, BASE_TOP).cut(cyl(1.2, 4.0, sx, sy, BASE_TOP)))
    tray = tray.cut(Part.makeBox(23.5, 12.8, 10.0, V(SERVO_XY[0] - 22.5 + 6.0 - 0.5, SERVO_XY[1] - 6.4, BASE_BOT)))
    for sx in (-20, 0, 20):
        for sy in (-40, 30):
            tray = tray.cut(cyl(5.0, 10.0, sx, sy, BASE_BOT))
    tray = tray.cut(Part.makeBox(14.0, WALL + 1.0, 8.0, V(-42.0, BASE_REAR - 0.5, BASE_TOP)))
    return tray.removeSplitter()


def top_shell():
    """Cangkang atas: badan bulat + dua lengan penangkap bola (scoop), mata LED, slot sirip tim."""
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
    shell = shell.cut(Part.makeBox(2.6, 32.0, 3.0, V(-1.3, -62.0, SHELL_TOP - 3.0)))
    shell = shell.cut(Part.makeBox(14.0, 10.0, 9.0, V(-42.0, BASE_REAR - 5.0, z0)))
    for s in (-1, 1):
        shell = shell.cut(Part.makeBox(WALL + 3.0, 8.0, 8.0, V(s * BASE_W / 2 - (WALL + 3.0) / 2, -4.0, z0 - 0.1)))
    # jendela kicker di dinding dalam scoop
    shell = shell.cut(Part.makeBox(52.0, 30.0, 26.0, V(-26.0, 40.0, 28.0)))
    return shell.removeSplitter()


def fin():
    f = Part.makeBox(2.4, 32.0, 3.0, V(-1.2, -62.0, SHELL_TOP - 3.0))
    blade = Part.makeBox(2.4, 28.0, 14.0, V(-1.2, -60.0, SHELL_TOP))
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


def kicker(servo_xyz):
    """Pemukul bola di horn servo (poros vertikal): lengan berayun horizontal, paddle menampar bola."""
    x, y, z = servo_xyz
    hub = cyl(5.0, 3.0, x, y, z + 4.0).cut(cyl(2.5, 3.0, x, y, z + 4.0))
    arm = Part.makeBox(32.0, 4.0, 3.0, V(x, y + 2.0, z + 4.0))               # ke +x sampai x=+10
    arm2 = Part.makeBox(4.0, 5.0, 3.0, V(x + 28.0, y + 4.0, z + 4.0))
    paddle = rbox(36.0, 3.0, 22.0, 1.0, z - 8.0, 6.0, y + 6.5)                   # melintang x -12..24, y 55..58
    return fuse(hub, arm, arm2, paddle)


def ball(x=0.0, y=SCOOP_CY, z=BALL_D / 2):
    return Part.makeSphere(BALL_D / 2, V(x, y, z))


# ================================================================== KODYPAD (remote DIY ESP-NOW)
PAD_W, PAD_D, PAD_H = 150.0, 74.0, 26.0
PAD_SPLIT = 9.0


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
    top = top.cut(cyl(2.0, 20.0, 0.0, 18.0, PAD_H - 10.0))
    top = top.cut(Part.makeBox(9.0, 4.0, 20.0, V(-4.5, 26.0, PAD_H - 10.0)))
    top = top.cut(rbox(30.0, 10.0, 1.0, 2.0, PAD_H - 1.0, 0, 0))
    top = top.cut(Part.makeBox(10.0, 6.0, 5.0, V(-5.0, -PAD_D / 2 - 1.0, 16.0)))
    for sx, sy in ((-58, 18), (-32, 18), (26, 16), (64, 16)):
        bottom = bottom.fuse(cyl(3.0, 6.0, sx, sy, WALL).cut(cyl(1.2, 6.0, sx, sy, WALL)))
    return top.removeSplitter(), bottom.removeSplitter()


def pad_internals():
    parts = {}
    jx, jy, jz = -45.0, 4.0, PAD_SPLIT - 2.0
    parts["pad_joy_pcb"] = rbox(26.0, 34.0, 1.6, 1.0, jz, jx, jy)
    parts["pad_joy_body"] = fuse(Part.makeBox(16.0, 16.0, 9.0, V(jx - 8, jy - 8, jz + 1.6)), cyl(4.0, 8.0, jx, jy, jz + 10.6))
    parts["pad_joy_cap"] = fuse(cyl(10.0, 5.0, jx, jy, PAD_H - 1.0), cyl(7.0, 6.0, jx, jy, PAD_H - 7.0))
    for name, (bx, by, r) in {"kick": (45.0, 10.0, 9.0), "turbo": (25.0, -2.0, 6.0), "horn": (65.0, -2.0, 6.0)}.items():
        parts["pad_btn_" + name] = fuse(Part.makeBox(12.0, 12.0, 7.3, V(bx - 6, by - 6, jz + 1.6)), cyl(r, 5.0, bx, by, PAD_H - 3.0))
    parts["pad_main_pcb"] = rbox(48.0, 30.0, 1.6, 2.0, jz, 45.0, 4.0)        # PCB tombol kanan
    parts["pad_c3"] = fuse(rbox(18.0, 22.5, 1.0, 1.0, 16.0, 0.0, -24.0),       # C3 di atas holder, USB-C ke belakang
                           Part.makeBox(12.0, 13.0, 2.4, V(-6.0, -27.0, 17.0)),
                           Part.makeBox(9.0, 7.0, 3.2, V(-4.5, -36.5, 17.0)))
    parts["pad_aaa"] = rbox(38.0, 52.0, 13.0, 2.0, WALL + 0.5, 0.0, -2.0)
    parts["pad_led"] = cyl(1.6, 6.0, 0.0, 18.0, PAD_H - 6.0)
    sw_body, sw_knob = slide_switch(0.0, 26.0, PAD_H - 9.0)
    parts["pad_switch"] = fuse(sw_body, sw_knob)
    return parts


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
    add("robot_base_tray", base_tray(), "navy", "robot", "cetak PLA, tray bawah: motor, baterai, ESP32, caster", printed=True)
    add("robot_top_shell", top_shell(), "yellow", "robot", "cetak PLA, cangkang + scoop bola", printed=True)
    add("robot_fin", fin(), "red", "robot", "cetak PLA, sirip tim (warna tim)", printed=True)
    add("robot_number_card", number_card(), "paper", "robot", "kartu nomor punggung (cetak kertas/PLA)", printed=True)
    for s in (-1, 1):
        add(f"robot_eye_{'l' if s < 0 else 'r'}", eye_lens(s * 20.0), "glass", "robot", "lensa LED mata (PLA transparan)", printed=True)
    for s in (-1, 1):
        body, shaft, mx = tt_motor(s)
        tag = 'l' if s < 0 else 'r'
        add(f"tt_motor_{tag}", body, "tt_yellow", "robot", "TT gear motor 1:48 3-6 V")
        add(f"tt_shaft_{tag}", shaft, "metal", "robot", "poros motor")
        tire, rim = wheel(s)
        add(f"wheel_tire_{tag}", tire, "tire", "robot", "roda TT 65 mm karet")
        add(f"wheel_rim_{tag}", rim, "rim", "robot", "velg roda TT")
    pcb, mod, usb, hdr = esp32_devkit(-12.0, 16.0, BASE_TOP + 8.5 + 2.5)
    add("esp32_pcb", pcb, "black", "robot", "ESP32 DevKit V1 30 pin (BT classic untuk stik PS)")
    add("esp32_module", mod, "metal", "robot", "modul WROOM-32")
    add("esp32_usb", usb, "metal", "robot", "micro-USB")
    add("esp32_headers", hdr, "ink", "robot", "pin header")
    dpcb, dchip = drv8833(26.0, 26.0, BASE_TOP + 1.0)
    add("drv8833_pcb", dpcb, "pcb_blue", "robot", "driver motor DRV8833 2 ch 1,5 A")
    add("drv8833_chip", dchip, "black", "robot", "IC DRV8833")
    hb, cells = aa_holder(0.0, -44.0, BASE_TOP + 0.5)
    add("aa_holder", hb, "black", "robot", "holder 4xAA 2x2 (6 V)")
    add("aa_cells", cells, "metal", "robot", "4 baterai AA")
    sv = (SERVO_XY[0], SERVO_XY[1], BASE_TOP + 22.7 + 4.0 - 10.0)
    body, shaft, horn = sg90(*sv)
    add("sg90_body", body, "servo_blue", "robot", "servo SG90 kicker (poros vertikal)")
    add("sg90_shaft", shaft, "white", "robot", "poros servo")
    add("sg90_horn", horn, "white", "robot", "horn servo")
    add("robot_kicker", kicker(sv), "red", "robot", "cetak PLA, pemukul bola di horn servo", printed=True)
    swb, swk = slide_switch(-35.0, BASE_REAR + 2.0, BASE_TOP + 1.0)
    add("switch_body", swb, "black", "robot", "saklar geser power")
    add("switch_knob", swk, "white", "robot", "knob saklar")
    add("ball", ball(), "white", "ball", "bola plastik berlubang (floorball) 72 mm")
    add("caster_ball", Part.makeSphere(6.35, V(0.0, BASE_REAR + 14.0, 6.35)), "metal", "robot", "bola baja 1/2 inch (gotri) di cup cetak")


def build_pad():
    top, bottom = pad_shells()
    add("pad_shell_top", top, "yellow", "pad", "cetak PLA, cangkang atas KodyPad", printed=True)
    add("pad_shell_bottom", bottom, "navy", "pad", "cetak PLA, cangkang bawah KodyPad", printed=True)
    cols = {"pad_joy_pcb": "pcb", "pad_joy_body": "black", "pad_joy_cap": "ink", "pad_btn_kick": "red", "pad_btn_turbo": "teal",
            "pad_btn_horn": "sun", "pad_main_pcb": "pcb", "pad_c3": "black", "pad_aaa": "black", "pad_led": "glass", "pad_switch": "black"}
    notes = {"pad_joy_pcb": "joystick KY-023", "pad_btn_kick": "tombol TENDANG (tactile 12 mm + cap)", "pad_btn_turbo": "tombol TURBO",
             "pad_btn_horn": "tombol KLAKSON/buzzer", "pad_main_pcb": "PCB lubang 13x3,5 cm (perfboard)", "pad_c3": "ESP32-C3 Super Mini (ESP-NOW)",
             "pad_aaa": "holder 3xAAA 4,5 V", "pad_led": "LED status 3 mm", "pad_switch": "saklar geser"}
    for k, s in pad_internals().items():
        add(k, s, cols[k], "pad", notes.get(k, ""))


def build_arena():
    col = {"floor": "green", "wall": "wood", "goal": "wood", "corner": "wood", "line": "line", "spots": "line"}
    for k, s in arena_parts().items():
        kind = k.split("_")[1]
        note = {"floor": "triplek 9 mm 122x244 utuh, cat hijau", "wall": "strip triplek 12 cm", "goal": "gawang 40 cm lebar x 12 cm dalam",
                "corner": "pojok 45 derajat segitiga 10 cm", "line": "lakban putih 2 cm", "spots": "titik netral"}.get(kind, "")
        add(k, s, col.get(kind, "wood"), "arena", note, mesh_dev=0.5)


def export_step(group, fname):
    comp = Part.makeCompound([s for _, s in SHAPES.get(group, [])])
    comp.exportStep(os.path.join(OUT, fname))


def main():
    build_robot()
    build_pad()
    build_arena()
    export_step("robot", "kodykick.step")
    export_step("pad", "kodypad.step")
    export_step("arena", "kodyarena.step")
    meta = dict(colors=C, parts=PARTS_META,
                params=dict(wheel_d=WHEEL_D, wheel_x=WHEEL_X, axle_z=AXLE_Z, base=[BASE_W, BASE_REAR, BASE_FRONT],
                            shell_top=SHELL_TOP, ball_d=BALL_D, scoop_cy=SCOOP_CY, pad=[PAD_W, PAD_D, PAD_H],
                            arena=[FLOOR_X, FLOOR_Y, WALL_H, GOAL_W, GOAL_D, PLY]))
    json.dump(meta, open(os.path.join(OUT, "parts.json"), "w"), indent=1)
    printed = [p for p in PARTS_META if p["printed"]]
    print("PARTS", len(PARTS_META), "printed cm3:", round(sum(p["volume_cm3"] for p in printed), 1))
    for p in printed:
        print(f"  {p['name']:24s} {p['volume_cm3']:7.2f} cm3  bbox {p['bbox']}")
    print("DONE")


main()
