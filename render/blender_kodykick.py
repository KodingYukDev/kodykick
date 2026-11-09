# Foto & video KodyKick dari part CAD (../out/parts, mm, Z up) dengan Blender 4.5 (EEVEE Next; --cycles untuk Cycles).
#   blender -b -P blender_kodykick.py -- --shot hero|pad|kit|arena|spin|match [--samples 48] [--pct 100] [--cycles]
# Output -> ../out/renders/<shot>.png  (spin/match -> .mp4)
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "out")
PARTS = os.path.join(ROOT, "parts")
OUT = os.path.join(ROOT, "renders")
FONT = os.path.join(HERE, "..", "..", "Michi", "render", "fonts", "Bricolage.ttf")
MM = 0.001
META = json.load(open(os.path.join(ROOT, "parts.json")))
COL = META["colors"]
P = META["params"]
os.makedirs(OUT, exist_ok=True)


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


_M = {}


def mat(key, color, rough=0.45, metal=0.0, emit=0.0, alpha=1.0, coat=0.0):
    k = (key, color, rough, metal, emit, alpha, coat)
    if k in _M:
        return _M[k]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = srgb(color)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    _M[k] = m
    return m


LOOK = {  # nama warna -> (rough, metal, emit, alpha, coat)
    "yellow": (0.35, 0, 0, 1, 0.3), "navy": (0.4, 0, 0, 1, 0.2), "red": (0.35, 0, 0, 1, 0.3), "paper": (0.6, 0, 0, 1, 0),
    "metal": (0.3, 1.0, 0, 1, 0), "tire": (0.9, 0, 0, 1, 0), "rim": (0.4, 0, 0, 1, 0), "glass": (0.1, 0, 6.0, 1, 0),
    "line": (0.7, 0, 0.3, 1, 0), "green": (0.85, 0, 0, 1, 0), "wood": (0.7, 0, 0, 1, 0), "white": (0.5, 0, 0, 1, 0.2),
    "teal": (0.35, 0, 0, 1, 0.3), "sun": (0.35, 0, 0, 1, 0.3), "tt_yellow": (0.5, 0, 0, 1, 0), "shield": (0.35, 0.9, 0, 1, 0),
    "servo_blue": (0.5, 0, 0, 1, 0), "black": (0.6, 0, 0, 1, 0), "ink": (0.6, 0, 0, 1, 0),
}


def material_for(color_key):
    r, mt, e, a, c = LOOK.get(color_key, (0.5, 0, 0, 1, 0))
    return mat(color_key, COL[color_key], r, mt, e, a, c)


def import_group(group, prefix="", fin_color=None, parent=None, exclude=()):
    objs = []
    for p in META["parts"]:
        if p["group"] != group or p["name"] in exclude:
            continue
        path = os.path.join(PARTS, p["name"] + ".stl")
        bpy.ops.wm.stl_import(filepath=path, global_scale=MM)
        o = bpy.context.selected_objects[0]
        o.name = prefix + p["name"]
        col = p["color"]
        if fin_color and p["name"] == "robot_fin":
            col = fin_color
        o.data.materials.clear()
        o.data.materials.append(material_for(col))
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
        if parent:
            o.parent = parent
        objs.append(o)
    return objs


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    return e


def text(body, size, loc, rot=(0, 0, 0), color="ink", parent=None, extrude=0.0003, align="CENTER"):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.data.body = body
    t.data.size = size
    t.data.extrude = extrude
    t.data.align_x = align
    t.data.align_y = "CENTER"
    if os.path.exists(FONT):
        t.data.font = bpy.data.fonts.load(FONT)
    t.data.materials.append(material_for(color))
    if parent:
        t.parent = parent
    return t


def robot(name, loc=(0, 0, 0), yaw=0.0, fin="red", number="10", with_ball=False):
    """Robot lengkap sebagai anak dari empty; +Y CAD = depan."""
    e = empty(name, loc, (0, 0, yaw))
    objs = import_group("robot", name + "_", fin_color=fin, parent=e)
    # nomor punggung di kartu (z=71.8), teks menghadap atas, "atas" teks ke arah depan (+y)
    text(number, 0.030, (0, -0.005, (P["shell_top"] - 0.2) * MM + 0.0002), (0, 0, math.radians(180)), "ink", e, extrude=0.0002)
    text("KodyKick", 0.0075, (0, (P["base"][1] + 2) * MM - 0.0002, 0.050), (math.radians(90), 0, math.radians(180)), "yellow", e, extrude=0.0003)
    if with_ball:
        import_group("ball", name + "_", parent=e)
    return e, objs


def pad(name, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = empty(name, loc, rot)
    objs = import_group("pad", name + "_", parent=e)
    text("KodyPad", 0.006, (0, 0, (P["pad"][2] - 0.6) * MM), (0, 0, 0), "navy", e, extrude=0.0002)
    text("TENDANG!", 0.0032, (0.045, 0.0235, (P["pad"][2] + 0.2) * MM), (0, 0, 0), "navy", e, extrude=0.0001)
    return e, objs


def ball(name, loc):
    e = empty(name, loc)
    objs = import_group("ball", name + "_", parent=e)
    # bola floorball: tambah pola pentagon sederhana lewat tekstur noise? cukup putih + sedikit kilap
    for o in objs:
        o.location = (0, -P["scoop_cy"] * MM, 0)  # pusat bola ke origin empty (bola CAD ada di y=scoop_cy)
    return e


def ground(size=4.0, color="paper", z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    g = bpy.context.object
    g.name = "Ground"
    g.data.materials.append(mat("ground_" + color, COL[color], 0.7))
    return g


def lights(strength=1.0, warm=True):
    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.9, 0.92, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.12 * strength

    def area(name, loc, energy, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, "AREA")
        d.energy = energy * strength
        d.size = size
        d.color = color
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc
        look_at(o, Vector((0, 0, 0.03)))
        return o
    area("Key", (0.6, -0.7, 0.9), 130, 1.2, (1, 0.97, 0.92) if warm else (1, 1, 1))
    area("Fill", (-0.9, -0.4, 0.5), 70, 1.4, (0.9, 0.95, 1))
    area("Rim", (-0.2, 0.9, 0.7), 140, 0.6)


def look_at(obj, target):
    d = target - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(loc, target, fov=28.0, ortho=None):
    c = bpy.data.cameras.new("Cam")
    c.angle = math.radians(fov)
    if ortho:
        c.type = "ORTHO"
        c.ortho_scale = ortho
    o = bpy.data.objects.new("Cam", c)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    look_at(o, Vector(target))
    bpy.context.scene.camera = o
    return o


def setup_render(a, w, h, video=False):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = a.pct
    if a.cycles:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = a.samples
        sc.cycles.use_denoising = True
        sc.cycles.device = "CPU"
    else:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
        sc.eevee.taa_render_samples = a.samples
        sc.eevee.use_shadows = True
        sc.eevee.use_raytracing = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = -1.0
    sc.render.film_transparent = False
    if video:
        sc.render.image_settings.file_format = "FFMPEG"
        sc.render.ffmpeg.format = "MPEG4"
        sc.render.ffmpeg.codec = "H264"
        sc.render.ffmpeg.constant_rate_factor = "HIGH"
        sc.render.fps = 30
    else:
        sc.render.image_settings.file_format = "PNG"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ------------------------------------------------------------------ shots
def shot_hero(a):
    clear()
    ground(3.0)
    lights()
    robot("R", yaw=math.radians(20), with_ball=True)
    camera((0.27, 0.36, 0.17), (0.0, 0.035, 0.040), 30)
    setup_render(a, 1440, 1800)


def shot_pad(a):
    clear()
    ground(3.0, "navy")
    lights(1.1, warm=False)
    pad("Pad", rot=(math.radians(-8), 0, math.radians(14)))
    camera((0.12, -0.24, 0.20), (0.0, -0.01, 0.010), 30)
    setup_render(a, 1440, 1800)


def shot_kit(a):
    """Flat lay isi kit: robot, KodyPad, bola, dari atas."""
    clear()
    ground(3.0)
    lights(1.0)
    robot("R", (-0.10, 0.04, 0), math.radians(-100))
    pad("Pad", (0.11, -0.10, 0), (0, 0, math.radians(8)))
    ball("B", (0.13, 0.10, P["ball_d"] / 2 * MM))
    camera((0.03, -0.05, 0.92), (0.03, 0.0, 0.0), 32)
    setup_render(a, 1440, 1800)


HIDE_SHELL = ("robot_top_shell", "robot_fin", "robot_number_card", "robot_eye_l", "robot_eye_r")


def shot_inside(a):
    """Isi robot: tray + komponen asli tanpa cangkang (3/4 dari atas)."""
    clear()
    ground(3.0)
    lights()
    e = empty("R", (0, 0, 0), (0, 0, math.radians(35)))
    import_group("robot", "R_", parent=e, exclude=HIDE_SHELL)
    import_group("ball", "R_", parent=e)
    camera((0.26, -0.30, 0.30), (0.0, -0.01, 0.03), 32)
    setup_render(a, 1440, 1800)


def shot_padinside(a):
    """Isi KodyPad tanpa cangkang atas."""
    clear()
    ground(3.0, "navy")
    lights(1.1, warm=False)
    e = empty("Pad", (0, 0, 0), (0, 0, math.radians(10)))
    import_group("pad", "Pad_", parent=e, exclude=("pad_shell_top",))
    camera((0.10, -0.22, 0.24), (0.0, -0.01, 0.01), 30)
    setup_render(a, 1440, 1800)


def arena_scene(with_robots=True):
    objs = import_group("arena")
    lights(1.3, warm=False)
    for l in ("Key", "Fill", "Rim"):
        o = bpy.data.objects[l]
        o.location = (o.location.x * 3.5, o.location.y * 3.5, o.location.z * 3.0 + 1.0)
        o.data.energy *= 14
        o.data.size *= 3
    ground(12.0, "navy", -0.001)
    if with_robots:
        ra, _ = robot("RA", (-0.55, 0.12, 0.009), math.radians(-70), "red", "10")
        rb, _ = robot("RB", (0.62, -0.18, 0.009), math.radians(105), "teal", "7")
        b = ball("B", (-0.22, 0.0, 0.009 + P["ball_d"] / 2 * MM))
        return ra, rb, b
    return None


def shot_arena(a):
    clear()
    arena_scene()
    camera((-1.9, -2.3, 1.45), (0.0, 0.0, 0.05), 42)
    setup_render(a, 1920, 1200)


def shot_spin(a):
    clear()
    ground(3.0)
    lights()
    e, _ = robot("R", with_ball=True)
    camera((0.0, 0.46, 0.20), (0.0, 0.02, 0.042), 28)
    n = 120
    e.rotation_euler = (0, 0, 0)
    e.keyframe_insert("rotation_euler", frame=1)
    e.rotation_euler = (0, 0, math.radians(360))
    e.keyframe_insert("rotation_euler", frame=n + 1)
    for fc in e.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, n
    setup_render(a, 1080, 1080, video=True)


def shot_match(a):
    """Robot merah menyerbu bola & menendang ke gawang kanan, 4 s."""
    clear()
    ra, rb, b = arena_scene()
    sc = bpy.context.scene
    n = 120
    sc.frame_start, sc.frame_end = 1, n
    # robot A: dari kiri menuju bola
    ra.location, ra.rotation_euler = (-0.75, 0.25, 0.009), (0, 0, math.radians(-60))
    ra.keyframe_insert("location", frame=1)
    ra.keyframe_insert("rotation_euler", frame=1)
    ra.location, ra.rotation_euler = (-0.30, 0.0, 0.009), (0, 0, math.radians(-90))
    ra.keyframe_insert("location", frame=55)
    ra.keyframe_insert("rotation_euler", frame=55)
    ra.location = (-0.27, 0.0, 0.009)
    ra.keyframe_insert("location", frame=70)
    ra.keyframe_insert("location", frame=n)
    # kicker berayun (part RA_robot_kicker rotasi di poros servo)
    kick = bpy.data.objects["RA_robot_kicker"]
    piv = empty("KickPivot", (-0.028, 0.050, 0.0))
    piv.parent = ra
    kick.parent = piv
    kick.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler = (0, 0, 0)
    piv.keyframe_insert("rotation_euler", frame=66)
    piv.rotation_euler = (0, 0, math.radians(-55))
    piv.keyframe_insert("rotation_euler", frame=72)
    piv.rotation_euler = (0, 0, 0)
    piv.keyframe_insert("rotation_euler", frame=84)
    # bola: diam sampai frame 70, lalu meluncur ke gawang kanan
    b.location = (-0.22, 0.0, b.location.z)
    b.keyframe_insert("location", frame=70)
    b.location = (1.16, -0.03, b.location.z)
    b.keyframe_insert("location", frame=110)
    b.keyframe_insert("location", frame=n)
    bo = [o for o in b.children][0]
    bo.rotation_euler = (0, 0, 0)
    bo.keyframe_insert("rotation_euler", frame=70)
    bo.rotation_euler = (0, math.radians(-1.38 / (P["ball_d"] / 2 * MM) * 57.3 / 57.3), 0)
    bo.rotation_euler = (0, -1.38 / (P["ball_d"] / 2 * MM), 0)
    bo.keyframe_insert("rotation_euler", frame=110)
    # robot B kiper bergerak sedikit
    rb.location = (0.95, -0.15, 0.009)
    rb.keyframe_insert("location", frame=1)
    rb.location = (0.95, 0.12, 0.009)
    rb.keyframe_insert("location", frame=n)
    cam = camera((-0.9, -1.15, 0.55), (-0.3, 0.0, 0.03), 44)
    tgt = empty("CamTarget", (-0.35, 0.0, 0.03))
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    cam.keyframe_insert("location", frame=1)
    tgt.keyframe_insert("location", frame=1)
    cam.location = (0.35, -1.2, 0.5)
    tgt.location = (0.55, 0.0, 0.03)
    cam.keyframe_insert("location", frame=n)
    tgt.keyframe_insert("location", frame=n)
    for ob in (cam, tgt):
        for fc in ob.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    setup_render(a, 1080, 1360, video=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--cycles", action="store_true")
    a = ap.parse_args(argv)
    fn = globals()["shot_" + a.shot]
    fn(a)
    sc = bpy.context.scene
    video = sc.render.image_settings.file_format == "FFMPEG"
    sc.render.filepath = os.path.join(OUT, a.shot + (".mp4" if video else ".png"))
    bpy.ops.render.render(animation=video, write_still=not video)
    print("RENDERED", sc.render.filepath)


main()
