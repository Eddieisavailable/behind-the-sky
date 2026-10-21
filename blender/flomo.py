"""Flomo: Korto's older brother, apprenticed at the forge.

Slower and stronger than Korto, quick to anger. Same skeleton layout and the same
ten animations as Korto (so the game drives both heroes the same way), with wider
shoulders and hips, a forge apron, a heavier cutlass and a smith's hammer at the belt.
Exports public/models/flomo.glb.

    python blender/flomo.py            # build + export
    python blender/flomo.py --preview  # also render turnaround and pose sheets
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korto
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, aim_camera, attach_to_bone, build_armature, contact_sheet,
                 export_glb, hexcol, mat_at, pose_at, prop_object, render_to, reset_scene, rest_pose, setup_preview,
                 skin_to, vertex_color_material)

SKIN = hexcol("#4f3221")
SKIN_DARK = hexcol("#3f281a")
LIPS = hexcol("#35201a")
HAIR = hexcol("#17110d")
EYE = korto.EYE
EYE_WHITE = korto.EYE_WHITE
INDIGO = hexcol("#26315c")
INDIGO_DARK = hexcol("#1b2343")
COTTON = hexcol("#e3d6b8")
RUST = hexcol("#9a4a26")
APRON = hexcol("#5a3b22")
APRON_DARK = hexcol("#432b18")
SCORCH = hexcol("#2a1a10")
LEATHER = korto.LEATHER
IRON = korto.IRON
WOOD = korto.WOOD
RATTAN = korto.RATTAN
FLETCH = korto.FLETCH

ARM_X = 1.17   # shoulders this much wider than Korto's
LEG_X = 1.12

# ---------- skeleton: Korto's, broadened ----------
BONES = {}
for name, (head, tail, parent) in korto.BONES.items():
    k = ARM_X if name.split(".")[0] in ("upperarm", "forearm", "hand") else LEG_X if name.split(".")[0] in ("thigh", "shin", "foot") else 1
    BONES[name] = ((head[0] * k, head[1], head[2]), (tail[0] * k, tail[1], tail[2]), parent)

SH = 0.19 * ARM_X     # shoulder
EL = 0.205 * ARM_X    # elbow
HA = 0.215 * ARM_X    # wrist / hand
HX = 0.1 * LEG_X      # hip, knee, ankle


def build_body():
    b = Body("Flomo")
    # head: broader jaw, cropped hair, short beard, heavy brows
    b.ball("head", SKIN, mat_at((0, -0.005, 1.585), scale=(1.02, 1.0, 1.1)), 0.13, segs=(10, 8))
    b.box("head", SKIN, mat_at((0, -0.045, 1.5)), (0.17, 0.12, 0.07))                       # jaw
    b.cone("head", SKIN_DARK, mat_at((0, -0.118, 1.575), rot=(-90, 0, 0)), 0.03, 0.01, 0.05, segments=4)  # nose
    b.box("head", LIPS, mat_at((0, -0.108, 1.522)), (0.056, 0.02, 0.016))
    b.box("head", HAIR, mat_at((0, -0.085, 1.485), rot=(-10, 0, 0)), (0.13, 0.05, 0.05))    # beard
    b.box("head", HAIR, mat_at((0, -0.11, 1.545)), (0.07, 0.012, 0.014))                     # moustache
    for sx in (1, -1):
        b.box("head", EYE_WHITE, mat_at((0.047 * sx, -0.116, 1.6)), (0.042, 0.014, 0.024))
        b.box("head", EYE, mat_at((0.047 * sx, -0.122, 1.6)), (0.02, 0.012, 0.024))
        b.box("head", HAIR, mat_at((0.047 * sx, -0.118, 1.627), rot=(0, -10 * sx, 0)), (0.06, 0.016, 0.016))  # brow, a scowl
        b.ball("head", SKIN_DARK, mat_at((0.127 * sx, 0, 1.575), scale=(0.5, 1, 1)), 0.032, segs=(6, 4))
        b.box("head", HAIR, mat_at((0.112 * sx, -0.03, 1.53), rot=(0, 0, 0)), (0.03, 0.07, 0.08))  # beard along the jaw
    b.ball("head", HAIR, mat_at((0, 0.025, 1.675), scale=(1.02, 1.05, 0.55)), 0.137, segs=(10, 6))  # cropped hair
    # thick neck
    b.limb("neck", SKIN, (0, 0, 1.38), (0, 0, 1.49), 0.06)
    # sleeveless country-cloth gown: indigo and cotton strips, wider in the chest
    def gown(f):
        c = f.calc_center_median()
        if c.z < 1.0:
            return INDIGO_DARK
        i = int(((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi)) * 14) % 3
        return (INDIGO, COTTON, INDIGO)[i]
    b.cone("chest", gown, mat_at((0, 0.005, 1.28), scale=(1, 0.72, 1)), 0.17, 0.235, 0.27, segments=10)
    b.cone("spine", gown, mat_at((0, 0.005, 1.08), scale=(1, 0.74, 1)), 0.175, 0.17, 0.2, segments=10)
    # leather forge apron over the front, scorched at the hem; neck strap and belt
    scorched = lambda f: SCORCH if f.calc_center_median().z < 0.62 else APRON_DARK if f.calc_center_median().z < 0.75 else APRON
    b.box("chest", APRON, mat_at((0, -0.17, 1.24), rot=(-6, 0, 0)), (0.27, 0.025, 0.22))
    b.box("hips", scorched, mat_at((0, -0.2, 0.8), rot=(4, 0, 0)), (0.32, 0.025, 0.44))
    b.limb("chest", LEATHER, (0.11, -0.16, 1.35), (0.05, -0.02, 1.47), 0.012, segments=4)
    b.limb("chest", LEATHER, (-0.11, -0.16, 1.35), (-0.05, -0.02, 1.47), 0.012, segments=4)
    b.cone("hips", LEATHER, mat_at((0, 0.005, 0.985), scale=(1, 0.78, 1)), 0.19, 0.185, 0.07, segments=10)
    b.box("hips", IRON, mat_at((0, -0.15, 0.985)), (0.07, 0.02, 0.06))                     # buckle
    # smith's hammer hanging at the left hip
    b.limb("hips", WOOD, (0.21, -0.02, 1.0), (0.24, -0.04, 0.72), 0.016)
    b.box("hips", IRON, mat_at((0.24, -0.04, 0.7), rot=(0, 0, 10)), (0.11, 0.05, 0.05))
    # knee-length trousers: one wide leg per thigh so they stride with him
    for side, sx in (("L", 1), ("R", -1)):
        b.cone(f"thigh.{side}", INDIGO_DARK, mat_at((HX * sx, 0.0, 0.7)), 0.095, 0.115, 0.36, segments=8)
        b.cone(f"thigh.{side}", RUST, mat_at((HX * sx, 0.0, 0.53)), 0.098, 0.098, 0.03, segments=8)  # hem band
    b.cone("hips", INDIGO_DARK, mat_at((0, 0.005, 0.9), scale=(1, 0.8, 1)), 0.2, 0.19, 0.12, segments=10)
    # quiver on the back
    b.limb("chest", RATTAN, (0.07, 0.19, 1.05), (-0.04, 0.2, 1.43), 0.05, 0.055, segments=6)
    for dx in (-0.025, 0.0, 0.025):
        b.limb("chest", WOOD, (-0.03 + dx, 0.2, 1.41), (-0.06 + dx, 0.205, 1.51), 0.006)
        b.cone("chest", FLETCH, mat_at((-0.062 + dx, 0.205, 1.51), rot=(0, -12, 0)), 0.018, 0.0, 0.05, segments=3)
    b.limb("chest", LEATHER, (0.2, -0.1, 1.36), (-0.17, 0.12, 1.04), 0.013, segments=4)
    # heavy bare arms; iron armlet, leather wrist wraps
    for side, sx in (("L", 1), ("R", -1)):
        b.ball(f"upperarm.{side}", SKIN, mat_at((SH * sx, 0, 1.355)), 0.072, segs=(8, 6))
        b.limb(f"upperarm.{side}", SKIN, (SH * sx, 0, 1.36), (EL * sx, 0, 1.11), 0.07, 0.056)
        b.limb(f"upperarm.{side}", IRON, (SH * sx * 1.02, 0, 1.25), (SH * sx * 1.03, 0, 1.22), 0.07)
        b.ball(f"forearm.{side}", SKIN, mat_at((EL * sx, 0, 1.11)), 0.055, segs=(6, 5))
        b.limb(f"forearm.{side}", SKIN, (EL * sx, 0, 1.11), (HA * sx, 0, 0.9), 0.058, 0.042)
        b.limb(f"forearm.{side}", LEATHER, (HA * sx, 0, 0.96), (HA * sx, 0, 0.9), 0.045)
        b.ball(f"hand.{side}", SKIN, mat_at((HA * sx, -0.005, 0.85), scale=(0.85, 1, 1.15)), 0.057, segs=(6, 5))
        b.ball(f"shin.{side}", SKIN, mat_at((HX * sx, 0, 0.49)), 0.064, segs=(6, 5))
        b.limb(f"shin.{side}", SKIN, (HX * sx, 0, 0.49), (HX * sx, 0, 0.1), 0.064, 0.045)
        b.box(f"foot.{side}", LEATHER, mat_at((HX * sx, -0.045, 0.03)), (0.095, 0.23, 0.05))
        b.box(f"foot.{side}", SKIN_DARK, mat_at((HX * sx, -0.05, 0.065)), (0.08, 0.16, 0.03))
        b.limb(f"foot.{side}", LEATHER, (HX * sx - 0.04, -0.06, 0.07), (HX * sx + 0.04, -0.06, 0.07), 0.01, segments=4)  # sandal strap
    return b


def main():
    reset_scene()
    arm = build_armature("FlomoRig", BONES)
    mat = vertex_color_material("Flomo")
    body = build_body().to_object(mat)
    skin_to(body, arm)
    # a heavier, broader cutlass: Flomo hits harder
    cutlass = prop_object("Cutlass", korto.build_cutlass(hand=(-HA, -0.01, 0.85), width=0.068, length=1.12), mat)
    attach_to_bone(cutlass, arm, "hand.R", Matrix.Identity(4))
    bow = prop_object("Bow", korto.build_bow(hand=(HA, -0.005, 0.85)), mat)
    attach_to_bone(bow, arm, "hand.L", Matrix.Identity(4))
    actions = korto.clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "flomo.glb")

    if "--preview" in sys.argv:
        cam = setup_preview()
        bow.hide_render = True
        shots = []
        for i, ang in enumerate((0, 35, 90, 180)):
            aim_camera(cam, ang)
            p = PREVIEWS_OUT / f"_f{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "flomo-turnaround.png", cols=4, labels=["Front", "Three-quarter", "Side", "Back"])
        poses = [("Idle", 1), ("Run", 1), ("Slash1", 8), ("Slash3", 12), ("Draw", 12), ("Burn", 5)]
        shots = []
        aim_camera(cam, 30, dist=4.6, height=1.5)
        for i, (name, frame) in enumerate(poses):
            pose_at(arm, actions[name], frame)
            bow.hide_render = name != "Draw"
            p = PREVIEWS_OUT / f"_fp{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "flomo-poses.png", cols=6, labels=[f"{n} {f}" for n, f in poses])


if __name__ == "__main__":
    main()
