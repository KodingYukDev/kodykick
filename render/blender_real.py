# Render REALISTIS KodyKick (Cycles CPU + OpenImageDenoise, Nishita sky + sun, material PBR prosedural, DOF).
#   blender -b -P blender_real.py -- --shot hero|inside|arena|breakdown|match [--samples 48] [--pct 100]
# Foto -> ../out/real/<shot>.png ; video -> ../out/real/<shot>.mp4 (H.264, 30 fps)
# breakdown = exploded view animasi (rakit -> terurai -> orbit -> rakit lagi), 150 frame.
# match     = robot menyerbu bola & menendang ke gawang, 144 frame.
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
OUT = os.path.join(ROOT, "real")
FONT = os.path.join(HERE, "..", "..", "Michi", "render", "fonts", "Bricolage.ttf")
MM = 0.001
META = json.load(open(os.path.join(ROOT, "parts.json")))
COL = META["colors"]
P = META["params"]
os.makedirs(OUT, exist_ok=True)
FPS = 30


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


# ------------------------------------------------------------------ material PBR
_M = {}


def _base(name, color, rough, metal=0.0, coat=0.0, emit=0.0, spec=0.5, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Specular IOR Level"].default_value = spec
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.3, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.004
    if emit:
        b.inputs["Emission Color"].default_value = srgb(color)
        b.inputs["Emission Strength"].default_value = emit
    return m, nt, b


def _bump(nt, b, scale=400.0, detail=2.0, strength=0.08, distortion=0.0):
    """Tekstur noise -> Bump halus (permukaan cetak/plastik/karet)."""
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = detail
    tex.inputs["Distortion"].default_value = distortion
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.0005
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return tex


def _rough_var(nt, b, base=0.4, span=0.15, scale=120.0):
    """Variasi roughness (bercak sidik jari / debu)."""
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.3
    ramp.inputs["From Max"].default_value = 0.7
    ramp.inputs["To Min"].default_value = base - span
    ramp.inputs["To Max"].default_value = base + span
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], b.inputs["Roughness"])


def mat_pla(key, color):
    m, nt, b = _base("pla_" + key, color, 0.38, coat=0.15)
    # garis layer cetak 3D halus: wave horizontal (0,2 mm) + noise
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 2500.0      # 0.2 mm layer (objek dalam meter)
    wave.inputs["Distortion"].default_value = 0.3
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.035
    bump.inputs["Distance"].default_value = 0.0002
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    _rough_var(nt, b, 0.38, 0.1)
    return m


def mat_rubber(key, color):
    m, nt, b = _base("rubber_" + key, color, 0.85, spec=0.35)
    _bump(nt, b, scale=900.0, detail=3.0, strength=0.25)
    return m


def mat_plastic(key, color, rough=0.45, coat=0.0):
    m, nt, b = _base("plastic_" + key, color, rough, coat=coat)
    _bump(nt, b, scale=600.0, detail=2.0, strength=0.05)
    _rough_var(nt, b, rough, 0.08)
    return m


def mat_metal(key, color, rough=0.3):
    m, nt, b = _base("metal_" + key, color, rough, metal=1.0)
    b.inputs["Anisotropic"].default_value = 0.6
    _rough_var(nt, b, rough, 0.1, scale=60.0)
    return m


def mat_pcb(key, color):
    m, nt, b = _base("pcb_" + key, color, 0.45, coat=0.4)
    _bump(nt, b, scale=300.0, detail=1.0, strength=0.03)
    return m


def mat_emit(key, color, strength):
    m, nt, b = _base("emit_" + key, color, 0.2, emit=strength)
    b.inputs["Transmission Weight"].default_value = 0.6
    return m


def mat_wood(key, color):
    m, nt, b = _base("wood_" + key, color, 0.55)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 45.0
    wave.inputs["Distortion"].default_value = 1.5
    wave.inputs["Detail"].default_value = 2.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = srgb("#d4b588")
    ramp.color_ramp.elements[1].color = srgb("#e3cba0")
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    _bump(nt, b, scale=200.0, detail=3.0, strength=0.06)
    return m


def mat_felt(key, color):
    """Lantai arena: cat hijau di atas triplek -> sedikit tekstur."""
    m, nt, b = _base("felt_" + key, color, 0.9, spec=0.3)
    _bump(nt, b, scale=250.0, detail=4.0, strength=0.12)
    return m


def mat_floor():
    m, nt, b = _base("floor_studio", "#e9e6e0", 0.6, spec=0.4)
    _bump(nt, b, scale=40.0, detail=4.0, strength=0.04)
    _rough_var(nt, b, 0.6, 0.1, scale=8.0)
    return m


KIND = {  # kunci warna -> pembuat material
    "yellow": mat_pla, "navy": mat_pla, "red": mat_pla, "paper": mat_pla, "ink": lambda k, c: mat_plastic(k, c, 0.5),
    "tire": mat_rubber, "rim": lambda k, c: mat_plastic(k, c, 0.5), "tt_yellow": lambda k, c: mat_plastic(k, c, 0.45),
    "metal": mat_metal, "shield": lambda k, c: mat_metal(k, c, 0.4), "black": lambda k, c: mat_plastic(k, c, 0.55),
    "pcb": mat_pcb, "pcb_blue": mat_pcb, "white": lambda k, c: mat_plastic(k, c, 0.4, 0.2), "servo_blue": lambda k, c: mat_plastic(k, c, 0.5),
    "glass": lambda k, c: mat_emit(k, c, 4.0), "line": lambda k, c: mat_plastic(k, c, 0.7), "green": mat_felt, "wood": mat_wood,
    "teal": mat_pla, "sun": mat_pla,
}


def material_for(key):
    if key not in _M:
        _M[key] = KIND.get(key, mat_plastic)(key, COL[key])
    return _M[key]


# ------------------------------------------------------------------ scene helpers
def import_group(group, prefix="", fin_color=None, parent=None, exclude=()):
    objs = []
    for p in META["parts"]:
        if p["group"] != group or p["name"] in exclude:
            continue
        bpy.ops.wm.stl_import(filepath=os.path.join(PARTS, p["name"] + ".stl"), global_scale=MM)
        o = bpy.context.selected_objects[0]
        o.name = prefix + p["name"]
        col = fin_color if (fin_color and p["name"] == "robot_fin") else p["color"]
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


def text(body, size, loc, rot=(0, 0, 0), color="ink", parent=None, extrude=0.0003):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.data.body = body
    t.data.size = size
    t.data.extrude = extrude
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    if os.path.exists(FONT):
        t.data.font = bpy.data.fonts.load(FONT)
    t.data.materials.append(material_for(color))
    if parent:
        t.parent = parent
    return t


def robot(name, loc=(0, 0, 0), yaw=0.0, fin="red", number="10", with_ball=False, exclude=()):
    e = empty(name, loc, (0, 0, yaw))
    objs = import_group("robot", name + "_", fin_color=fin, parent=e, exclude=exclude)
    if "robot_number_card" not in exclude:
        text(number, 0.030, (0, -0.005, (P["shell_top"] - 0.2) * MM + 0.0002), (0, 0, math.radians(180)), "ink", e, extrude=0.0002)
    if with_ball:
        import_group("ball", name + "_", parent=e)
    return e, objs


def ball(name, loc):
    e = empty(name, loc)
    for o in import_group("ball", name + "_", parent=e):
        o.location = (0, -P["scoop_cy"] * MM, 0)
    return e


def ground(size=4.0, z=0.0, mat=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    g = bpy.context.object
    g.name = "Ground"
    g.data.materials.append(mat or mat_floor())
    return g


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def world_sky(sun_elev=38.0, sun_rot=-50.0, strength=0.35, sun_strength=1.6, warm=True):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Sky")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(sun_elev)
    sky.sun_rotation = math.radians(sun_rot)
    sky.sun_intensity = 0.0          # matahari dipisah jadi lampu Sun supaya bayangan terkontrol
    sky.altitude = 200
    sky.air_density = 1.2
    sky.dust_density = 1.5
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    # Sun
    sd = bpy.data.lights.new("Sun", "SUN")
    sd.energy = sun_strength
    sd.angle = math.radians(2.5)
    sd.color = (1.0, 0.95, 0.88) if warm else (1, 1, 1)
    so = bpy.data.objects.new("Sun", sd)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(90 - sun_elev), 0, math.radians(sun_rot + 180))
    # softbox fill besar (studio)
    ad = bpy.data.lights.new("Softbox", "AREA")
    ad.energy = 55
    ad.size = 1.6
    ad.shape = "RECTANGLE"
    ad.size_y = 1.0
    ao = bpy.data.objects.new("Softbox", ad)
    sc.collection.objects.link(ao)
    ao.location = (-0.8, -0.6, 1.1)
    look_at(ao, (0, 0, 0.03))
    rd = bpy.data.lights.new("Rim", "AREA")
    rd.energy = 35
    rd.size = 0.8
    ro = bpy.data.objects.new("Rim", rd)
    sc.collection.objects.link(ro)
    ro.location = (0.5, 1.0, 0.6)
    look_at(ro, (0, 0, 0.03))


def camera(loc, target, fov=30.0, fstop=4.0):
    c = bpy.data.cameras.new("Cam")
    c.angle = math.radians(fov)
    c.dof.use_dof = True
    c.dof.aperture_fstop = fstop
    c.dof.focus_distance = (Vector(target) - Vector(loc)).length
    o = bpy.data.objects.new("Cam", c)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    look_at(o, target)
    bpy.context.scene.camera = o
    return o


def setup_render(a, w, h, video=False):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = a.pct
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = a.samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.max_bounces = 6
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.use_light_tree = True
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.view_settings.exposure = -0.75
    sc.render.film_transparent = False
    if video:
        sc.render.image_settings.file_format = "FFMPEG"
        sc.render.ffmpeg.format = "MPEG4"
        sc.render.ffmpeg.codec = "H264"
        sc.render.ffmpeg.constant_rate_factor = "HIGH"
        sc.render.fps = FPS
    else:
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_depth = "8"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def linear(ob):
    for fc in ob.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"


# ------------------------------------------------------------------ shots
def shot_hero(a):
    clear()
    ground(4.0)
    world_sky()
    robot("R", yaw=math.radians(20), with_ball=True)
    camera((0.27, 0.36, 0.17), (0.0, 0.035, 0.040), 30, 5.6)
    setup_render(a, 1440, 1800)


HIDE_SHELL = ("robot_top_shell", "robot_fin", "robot_number_card", "robot_eye_l", "robot_eye_r")


def shot_inside(a):
    clear()
    ground(4.0)
    world_sky(sun_elev=50)
    e, _ = robot("R", yaw=math.radians(35), with_ball=True, exclude=HIDE_SHELL)
    camera((0.26, -0.30, 0.30), (0.0, -0.01, 0.03), 32, 6.3)
    setup_render(a, 1440, 1800)


def arena_scene():
    import_group("arena")
    world_sky(sun_elev=45, sun_rot=-30, strength=0.6, sun_strength=3.0, warm=False)
    for n in ("Softbox", "Rim"):
        o = bpy.data.objects[n]
        o.location = (o.location.x * 3.5, o.location.y * 3.5, o.location.z * 3.0 + 1.0)
        o.data.energy *= 12
        o.data.size *= 3
    ground(12.0, -0.001, mat_plastic("gym", "#5a6670", 0.7))
    ra, _ = robot("RA", (-0.55, 0.12, 0.009), math.radians(-70), "red", "10")
    rb, _ = robot("RB", (0.62, -0.18, 0.009), math.radians(105), "teal", "7")
    b = ball("B", (-0.22, 0.0, 0.009 + P["ball_d"] / 2 * MM))
    return ra, rb, b


def shot_arena(a):
    clear()
    arena_scene()
    camera((-1.9, -2.3, 1.45), (0.0, 0.0, 0.05), 42, 8.0)
    setup_render(a, 1920, 1200)


# offset exploded view per part (x, y, z) dalam mm
EXPLODE = {
    "robot_top_shell": (0, 0, 75), "robot_fin": (0, 0, 118), "robot_number_card": (0, 0, 104),
    "robot_eye_l": (0, 28, 88), "robot_eye_r": (0, 28, 88),
    "wheel_tire_l": (-70, 0, 0), "wheel_rim_l": (-70, 0, 0), "wheel_tire_r": (70, 0, 0), "wheel_rim_r": (70, 0, 0),
    "tt_gearbox_l": (-28, 0, 40), "tt_can_l": (-28, 0, 40), "tt_shaft_l": (-28, 0, 40),
    "tt_gearbox_r": (28, 0, 40), "tt_can_r": (28, 0, 40), "tt_shaft_r": (28, 0, 40),
    "esp32_pcb": (0, 0, 60), "esp32_module": (0, 0, 60), "esp32_usb": (0, 0, 60), "esp32_headers": (0, 0, 60),
    "drv8833_pcb": (0, 0, 30), "drv8833_chip": (0, 0, 30),
    "aa_holder": (0, -20, 55), "aa_holder_inner": (0, -20, 55),
    "sg90_body": (-20, 10, 70), "sg90_horn": (-20, 10, 85), "robot_kicker": (-20, 10, 105),
    "switch_body": (-15, -15, 35), "caster_ball": (0, 0, -22),
}


def ease(t):
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def shot_breakdown(a):
    """Exploded view: 0-20 rakit, 20-80 terurai (bertahap), 80-120 orbit, 120-150 rakit lagi."""
    clear()
    ground(4.0)
    world_sky(sun_elev=45)
    rig = empty("Rig", (0, 0, 0), (0, 0, math.radians(25)))
    _, objs = robot("R", yaw=0.0, exclude=())
    bpy.data.objects["R"].parent = rig
    # kartu nomor teks ikut kartu
    sc = bpy.context.scene
    n = 150
    sc.frame_start, sc.frame_end = 1, n
    order = ["robot_fin", "robot_number_card", "robot_eye_l", "robot_eye_r", "robot_top_shell", "robot_kicker", "sg90_horn",
             "wheel_tire_l", "wheel_rim_l", "wheel_tire_r", "wheel_rim_r", "esp32_module", "esp32_pcb", "esp32_usb", "esp32_headers",
             "sg90_body", "aa_holder", "aa_holder_inner", "tt_gearbox_l", "tt_can_l", "tt_shaft_l", "tt_gearbox_r", "tt_can_r", "tt_shaft_r",
             "drv8833_pcb", "drv8833_chip", "switch_body", "caster_ball"]
    for o in objs:
        key = o.name[2:]
        if key not in EXPLODE:
            continue
        off = Vector(EXPLODE[key]) * MM
        i = order.index(key) if key in order else 10
        start = 20 + i * 1.6
        base = o.location.copy()
        for f in range(1, n + 1):
            if f < start - 1 and f > 2:
                continue
            t_out = ease((f - start) / 40.0)
            t_in = ease((f - 118) / 28.0) if f >= 118 else 0.0
            k = t_out * (1 - t_in)
            o.location = base + off * k
            o.keyframe_insert("location", frame=f)
    # teks nomor ikut kartu
    card = bpy.data.objects.get("R_robot_number_card")
    for ob in bpy.data.objects:
        if ob.type == "FONT" and ob.parent and ob.parent.name == "R" and card:
            ob.parent = card
            ob.matrix_parent_inverse = card.matrix_world.inverted()
    # orbit kamera lewat rig
    rig.rotation_euler = (0, 0, math.radians(25))
    rig.keyframe_insert("rotation_euler", frame=1)
    rig.rotation_euler = (0, 0, math.radians(25 + 70))
    rig.keyframe_insert("rotation_euler", frame=n)
    linear(rig)
    camera((0.46, -0.50, 0.42), (0.0, 0.0, 0.095), 33, 6.3)
    setup_render(a, 1080, 1350, video=True)


def shot_match(a):
    clear()
    ra, rb, b = arena_scene()
    sc = bpy.context.scene
    n = 144
    sc.frame_start, sc.frame_end = 1, n
    ra.location, ra.rotation_euler = (-0.75, 0.25, 0.009), (0, 0, math.radians(-60))
    ra.keyframe_insert("location", frame=1)
    ra.keyframe_insert("rotation_euler", frame=1)
    ra.location, ra.rotation_euler = (-0.30, 0.0, 0.009), (0, 0, math.radians(-90))
    ra.keyframe_insert("location", frame=66)
    ra.keyframe_insert("rotation_euler", frame=66)
    ra.location = (-0.27, 0.0, 0.009)
    ra.keyframe_insert("location", frame=84)
    ra.keyframe_insert("location", frame=n)
    # roda berputar
    for tag in ("l", "r"):
        for part in ("wheel_tire", "wheel_rim"):
            w = bpy.data.objects[f"RA_{part}_{tag}"]
            piv = empty(f"Axle_{part}_{tag}", (0, 0, P["axle_z"] * MM))
            piv.parent = ra
            w.parent = piv
            w.matrix_parent_inverse = piv.matrix_world.inverted()
            piv.rotation_euler = (0, 0, 0)
            piv.keyframe_insert("rotation_euler", frame=1)
            piv.rotation_euler = (-0.50 / (P["wheel_d"] / 2 * MM), 0, 0)
            piv.keyframe_insert("rotation_euler", frame=66)
            linear(piv)
    kick = bpy.data.objects["RA_robot_kicker"]
    piv = empty("KickPivot", (-0.022, 0.050, 0.0))
    piv.parent = ra
    kick.parent = piv
    kick.matrix_parent_inverse = piv.matrix_world.inverted()
    horn = bpy.data.objects["RA_sg90_horn"]
    horn.parent = piv
    horn.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler = (0, 0, 0)
    piv.keyframe_insert("rotation_euler", frame=80)
    piv.rotation_euler = (0, 0, math.radians(-55))
    piv.keyframe_insert("rotation_euler", frame=86)
    piv.rotation_euler = (0, 0, 0)
    piv.keyframe_insert("rotation_euler", frame=98)
    b.location = (-0.22, 0.0, b.location.z)
    b.keyframe_insert("location", frame=84)
    b.location = (1.16, -0.03, b.location.z)
    b.keyframe_insert("location", frame=132)
    b.keyframe_insert("location", frame=n)
    bo = [o for o in b.children][0]
    bo.rotation_euler = (0, 0, 0)
    bo.keyframe_insert("rotation_euler", frame=84)
    bo.rotation_euler = (0, -1.38 / (P["ball_d"] / 2 * MM), 0)
    bo.keyframe_insert("rotation_euler", frame=132)
    rb.location = (0.95, -0.15, 0.009)
    rb.keyframe_insert("location", frame=1)
    rb.location = (0.95, 0.12, 0.009)
    rb.keyframe_insert("location", frame=n)
    cam = camera((-0.9, -1.15, 0.55), (-0.3, 0.0, 0.03), 44, 5.6)
    tgt = empty("CamTarget", (-0.35, 0.0, 0.03))
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    cam.keyframe_insert("location", frame=1)
    tgt.keyframe_insert("location", frame=1)
    cam.location = (-0.6, -1.15, 0.5)
    tgt.location = (-0.3, 0.0, 0.03)
    cam.keyframe_insert("location", frame=80)
    tgt.keyframe_insert("location", frame=80)
    cam.location = (0.45, -1.2, 0.5)
    tgt.location = (0.85, 0.0, 0.03)
    cam.keyframe_insert("location", frame=132)
    tgt.keyframe_insert("location", frame=132)
    cam.keyframe_insert("location", frame=n)
    tgt.keyframe_insert("location", frame=n)
    linear(cam)
    linear(tgt)
    setup_render(a, 1080, 1350, video=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--frame", type=int, default=0, help="render 1 frame saja (uji) untuk shot video")
    a = ap.parse_args(argv)
    globals()["shot_" + a.shot](a)
    sc = bpy.context.scene
    video = sc.render.image_settings.file_format == "FFMPEG"
    if video and a.frame:
        sc.frame_set(a.frame)
        sc.render.image_settings.file_format = "PNG"
        sc.render.filepath = os.path.join(OUT, f"{a.shot}_f{a.frame}.png")
        bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = os.path.join(OUT, a.shot + (".mp4" if video else ".png"))
        bpy.ops.render.render(animation=video, write_still=not video)
    print("RENDERED", sc.render.filepath)


main()
