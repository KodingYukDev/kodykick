# Cek tabrakan antar part robot & pad (volume irisan > 2 mm3). Pasangan yang memang bersentuhan dikecualikan.
#   freecadcmd.exe check_clash.py
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kodykick_cad as K  # noqa: E402  (membangun ulang semua part)

ALLOW = {  # pasangan yang boleh beririsan (sengaja menempel / masuk)
    ("tt_shaft", "wheel_rim"), ("tt_shaft", "tt_gearbox"), ("tt_shaft", "tt_can"), ("tt_shaft", "robot_base_tray"),
    ("tt_gearbox", "tt_can"), ("tt_gearbox", "robot_base_tray"), ("tt_can", "robot_base_tray"),
    ("aa_holder", "aa_holder_inner"), ("sg90_body", "sg90_horn"), ("sg90_horn", "robot_kicker"), ("sg90_body", "robot_base_tray"),
    ("esp32_pcb", "esp32_headers"), ("esp32_pcb", "esp32_module"), ("esp32_pcb", "esp32_usb"), ("esp32_module", "esp32_usb"),
    ("esp32_headers", "robot_base_tray"), ("drv8833_pcb", "drv8833_chip"), ("robot_number_card", "robot_top_shell"),
    ("robot_fin", "robot_top_shell"), ("robot_eye", "robot_top_shell"), ("caster_ball", "robot_base_tray"),
    ("wheel_tire", "wheel_rim"), ("robot_base_tray", "robot_top_shell"), ("switch_body", "robot_base_tray"),
    ("pad_joy_pcb", "pad_joy_body"), ("pad_joy_body", "pad_joy_cap"), ("pad_joy_cap", "pad_shell_top"), ("pad_joy_pcb", "pad_shell_bottom"),
    ("pad_tact", "pad_main_pcb"), ("pad_tact", "pad_cap"), ("pad_cap", "pad_shell_top"), ("pad_main_pcb", "pad_shell_bottom"),
    ("pad_aaa", "pad_shell_bottom"), ("pad_aaa", "pad_c3"), ("pad_c3", "pad_shell_top"), ("pad_led", "pad_shell_top"),
    ("pad_switch", "pad_shell_top"), ("pad_shell_top", "pad_shell_bottom"),
}


def base(n):
    for suf in ("_l", "_r"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    for pre in ("pad_tact_", "pad_cap_"):
        if n.startswith(pre):
            n = pre[:-1]
    return n


def allowed(a, b):
    a, b = base(a), base(b)
    return (a, b) in ALLOW or (b, a) in ALLOW or a == b


bad = 0
for group in ("robot", "pad"):
    parts = K.SHAPES.get(group, [])
    for (na, sa), (nb, sb) in itertools.combinations(parts, 2):
        if allowed(na, nb):
            continue
        if not sa.BoundBox.intersect(sb.BoundBox):
            continue
        try:
            v = sa.common(sb).Volume
        except Exception:
            continue
        if v > 2.0:
            bad += 1
            print(f"CLASH {group}: {na} x {nb} = {v:.1f} mm3")
print("CLASH-CHECK", "OK" if bad == 0 else f"{bad} masalah")
