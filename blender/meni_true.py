"""Meni-maa-fa in his true form: what drops out of the lizard when its plates are broken.

A tall, gaunt man of ash, taller than the heroes, with the agama's orange crest running over
his skull, ember eyes and ember cracks in his skin, a mantle of indigo lizard scales, a skirt of
dried raffia and leaves, a necklace of teeth and cowries, and a stub of lizard tail. He carries a
black iron cutlass (the duel) and the stolen seed rice tied in country cloth (the bargain); the
game shows the rice only while he offers it.

Same skeleton layout as Korto (scaled up), so he shares her run and cutlass moves.
Clips: Idle, Run, Slash1-3, Hurt, Death, plus Offer, Taunt, Block and Flee (leaps behind the sky).

    python blender/meni_true.py            # build + export public/models/meni_true.glb
    python blender/meni_true.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import korto
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, add_action, aim_camera, attach_to_bone, build_armature,
                 contact_sheet, export_glb, glow_material, hexcol, jitter, mat_at, pose_at, render_to, reset_scene,
                 rest_pose, setup_preview, skin_to, vertex_color_material)

ASH = hexcol("#8f8a84")
ASH_DARK = hexcol("#5e5955")
CREST = hexcol("#d9542a")
CREST_LIGHT = hexcol("#ef8a3c")
SCALE = hexcol("#27306e")
SCALE_LIGHT = hexcol("#3d4b98")
RAFFIA = hexcol("#a88a52")
RAFFIA_DARK = hexcol("#7a6238")
LEAF = hexcol("#4a5a2a")
COWRIE = hexcol("#ece3cc")
TOOTH = hexcol("#d8cdb0")
MOUTH = hexcol("#2a0e0a")
IRON_BLACK = hexcol("#26282c")
EMBER = hexcol("#ff5a1f")
CLOTH = korto.CLOTH
RICE = hexcol("#efe6cf")

K = 1.22   # taller than Korto by this much
BONES = {n: (tuple(v * K for v in h), tuple(v * K for v in t), p) for n, (h, t, p) in korto.BONES.items()}


def P(x, y, z):
    return (x * K, y * K, z * K)


def build_body():
    b = Body("MeniTrue")
    # head: long gaunt skull of ash, orange crest of spines from brow to nape, ember eyes, a lipless grin
    b.ball("head", ASH, mat_at(P(0, -0.005, 1.59), scale=(0.88, 1.05, 1.18)), 0.125 * K, segs=(10, 8))
    b.box("head", ASH_DARK, mat_at(P(0, -0.06, 1.5)), (0.14 * K, 0.1 * K, 0.06 * K))      # narrow jaw
    b.box("head", MOUTH, mat_at(P(0, -0.112, 1.525)), (0.07 * K, 0.015 * K, 0.016 * K))
    for k in range(4):
        b.cone("head", TOOTH, mat_at(P(-0.022 + k * 0.015, -0.117, 1.53), rot=(180, 0, 0)), 0.005 * K, 0.0, 0.018 * K, segments=3)
    for sx in (1, -1):
        b.gem("head", EMBER, mat_at(P(0.042 * sx, -0.112, 1.6)), 0.017 * K, mat=1)
        b.box("head", ASH_DARK, mat_at(P(0.044 * sx, -0.106, 1.627), rot=(0, 18 * sx, 0)), (0.055 * K, 0.02 * K, 0.014 * K))  # hooded brow
        b.box("head", EMBER, mat_at(P(0.07 * sx, -0.09, 1.56), rot=(0, 0, 20 * sx)), (0.006 * K, 0.004 * K, 0.06 * K), mat=1)  # cheek crack
    for k in range(9):  # the crest
        t = k / 8
        y = -0.09 + t * 0.22
        z = 1.7 + math.sin(t * math.pi) * 0.03
        b.cone("head", CREST_LIGHT if k % 2 else CREST, mat_at(P(0, y, z + 0.03), rot=(-5 - 45 * t, 0, 0), scale=(0.45, 1, 1)), 0.04 * K, 0.0, (0.16 + 0.1 * math.sin(t * math.pi)) * K, segments=4)
    for sx in (1, -1):  # crest frills over the temples
        b.cone("head", CREST, mat_at(P(0.11 * sx, 0.0, 1.64), rot=(0, 65 * sx, 0), scale=(1, 0.3, 1)), 0.05 * K, 0.0, 0.16 * K, segments=4)
        b.cone("head", CREST_LIGHT, mat_at(P(0.09 * sx, 0.04, 1.7), rot=(-20, 40 * sx, 0), scale=(1, 0.3, 1)), 0.04 * K, 0.0, 0.14 * K, segments=4)
    b.limb("neck", ASH, P(0, 0, 1.38), P(0, 0, 1.49), 0.042 * K)
    # bare ash chest with ember seams, mantle of lizard scales over the shoulders
    seams = lambda f: ASH_DARK if int(f.calc_center_median().z * 40) % 5 == 0 else ASH
    b.cone("chest", seams, mat_at(P(0, 0.005, 1.28), scale=(1, 0.65, 1)), 0.13 * K, 0.17 * K, 0.26 * K, segments=8)
    b.cone("spine", ASH, mat_at(P(0, 0.005, 1.08), scale=(1, 0.7, 1)), 0.12 * K, 0.13 * K, 0.22 * K, segments=8)
    for k in range(3):
        b.box("chest", EMBER, mat_at(P(0.05 - k * 0.05, -0.115, 1.2 + k * 0.05), rot=(0, 25 - k * 20, 0)), (0.006 * K, 0.004 * K, 0.08 * K), mat=1)
    scale_col = lambda f: SCALE_LIGHT if (int(f.calc_center_median().x * 60) + int(f.calc_center_median().z * 60)) % 4 == 0 else SCALE
    for sx in (1, -1):
        for k in range(3):
            b.ball("chest", scale_col, mat_at(P(0.13 * sx, 0.02, 1.4 - k * 0.04), scale=(1.2, 1.1, 0.5)), (0.09 - k * 0.012) * K, segs=(7, 4))
    b.ball("chest", scale_col, mat_at(P(0, 0.06, 1.38), scale=(1.6, 0.9, 0.55)), 0.11 * K, segs=(8, 5))
    # necklace of teeth and cowries
    for k in range(9):
        a = math.radians(-70 + k * 17.5)
        p = P(math.sin(a) * 0.12, -math.cos(a) * 0.09 + 0.01, 1.36 - math.cos(a) * 0.04)
        if k % 2:
            b.ball("chest", COWRIE, mat_at(p, scale=(0.8, 0.5, 1)), 0.014 * K, segs=(5, 4))
        else:
            b.cone("chest", TOOTH, mat_at(p, rot=(180, 0, 0)), 0.01 * K, 0.0, 0.04 * K, segments=3)
    # raffia and dried-leaf skirt to the shin, with strands that hang loose
    def raffia(f):
        c = f.calc_center_median()
        return RAFFIA_DARK if int((math.atan2(c.y, c.x) + math.pi) * 20) % 3 == 0 else RAFFIA
    b.cone("hips", ASH_DARK, mat_at(P(0, 0.005, 0.98), scale=(1, 0.78, 1)), 0.15 * K, 0.14 * K, 0.06 * K, segments=8)
    b.cone("hips", raffia, mat_at(P(0, 0.01, 0.7), scale=(1, 0.86, 1)), 0.28 * K, 0.15 * K, 0.52 * K, segments=18)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        top = Vector(P(math.cos(a) * 0.2, math.sin(a) * 0.17, 0.62))
        bot = top + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, -0.32 * K))
        b.limb("hips", LEAF if k % 3 == 0 else RAFFIA_DARK, tuple(top), tuple(bot), 0.012 * K, 0.004 * K, segments=3)
    # a stub of lizard tail dragging behind, banded like the lizard's
    for k, (a, c, r1, r2, col) in enumerate(((P(0, 0.12, 0.85), P(0, 0.3, 0.5), 0.06, 0.045, SCALE), (P(0, 0.3, 0.5), P(0.04, 0.42, 0.14), 0.045, 0.028, SCALE_LIGHT),
                                              (P(0.04, 0.42, 0.14), P(0.14, 0.62, 0.04), 0.028, 0.006, CREST))):
        b.limb("hips", col, a, c, r1 * K, r2 * K, segments=6)
    # long gaunt arms, clawed fingers; thin legs, bare clawed feet
    for side, sx in (("L", 1), ("R", -1)):
        b.ball(f"upperarm.{side}", ASH, mat_at(P(0.19 * sx, 0, 1.36)), 0.05 * K, segs=(7, 5))
        b.limb(f"upperarm.{side}", ASH, P(0.195 * sx, 0, 1.36), P(0.205 * sx, 0, 1.11), 0.045 * K, 0.036 * K)
        b.limb(f"upperarm.{side}", SCALE, P(0.198 * sx, 0, 1.3), P(0.2 * sx, 0, 1.27), 0.05 * K)     # armlet of scale
        b.ball(f"forearm.{side}", ASH_DARK, mat_at(P(0.205 * sx, 0, 1.11)), 0.038 * K, segs=(6, 5))
        b.limb(f"forearm.{side}", ASH, P(0.205 * sx, 0, 1.11), P(0.215 * sx, 0, 0.9), 0.036 * K, 0.028 * K)
        b.box(f"forearm.{side}", EMBER, mat_at(P(0.23 * sx, -0.02, 1.0), rot=(0, 0, 10 * sx)), (0.004 * K, 0.004 * K, 0.08 * K), mat=1)
        b.ball(f"hand.{side}", ASH_DARK, mat_at(P(0.215 * sx, -0.005, 0.86), scale=(0.75, 1, 1.1)), 0.04 * K, segs=(6, 5))
        for f in range(4):
            b.cone(f"hand.{side}", TOOTH, mat_at(P(0.215 * sx + (f - 1.5) * 0.012, -0.02, 0.8), rot=(170, 0, 0)), 0.007 * K, 0.0, 0.06 * K, segments=3)
        b.limb(f"thigh.{side}", ASH, P(0.097 * sx, 0, 0.8), P(0.1 * sx, 0, 0.49), 0.058 * K, 0.045 * K)
        b.limb(f"shin.{side}", ASH, P(0.1 * sx, 0, 0.49), P(0.1 * sx, 0, 0.1), 0.045 * K, 0.03 * K)
        b.box(f"foot.{side}", ASH_DARK, mat_at(P(0.1 * sx, -0.05, 0.03)), (0.08 * K, 0.2 * K, 0.05 * K))
        for f in range(3):
            b.cone(f"foot.{side}", TOOTH, mat_at(P(0.1 * sx + (f - 1) * 0.025, -0.16, 0.02), rot=(-90, 0, 0)), 0.008 * K, 0.0, 0.05 * K, segments=3)
    return b


def build_cutlass():
    """Black iron, long and hooked at the tip, an ember edge."""
    b = Body("DarkCutlass")
    hand = Vector(P(-0.215, -0.01, 0.85))
    down_fwd = Vector((0, -0.55, -1)).normalized()
    grip = hand + down_fwd * 0.08 * K
    b.limb("x", ASH_DARK, tuple(hand - down_fwd * 0.07 * K), tuple(grip), 0.018 * K, 0.02 * K)
    p1 = grip + down_fwd * 0.34 * K
    hook = (down_fwd + Vector((0, -0.45, 0.25))).normalized()
    p2 = p1 + hook * 0.26 * K
    for a, c in ((grip, p1), (p1, p2)):
        mid = (a + c) / 2
        rot = (c - a).normalized().to_track_quat("Z", "X").to_matrix().to_4x4()
        b.box("x", IRON_BLACK, Matrix.Translation(mid) @ rot, (0.01 * K, 0.065 * K, (c - a).length))
        b.box("x", EMBER, Matrix.Translation(mid + Vector((0, -0.03, -0.02)) * K) @ rot, (0.011 * K, 0.008 * K, (c - a).length * 0.9), mat=1)
    return b


def build_rice():
    """The stolen seed rice, tied in country cloth, held out in his left hand."""
    b = Body("SeedRice")
    hand = Vector(P(0.215, -0.04, 0.82))
    stripes = lambda f: CLOTH[int((math.atan2(f.calc_center_median().y - hand.y, f.calc_center_median().x - hand.x) + math.pi) * 3 / math.pi) % len(CLOTH)]
    b.ball("x", stripes, mat_at(tuple(hand + Vector((0, 0, -0.12)) * K), scale=(1, 1, 0.85)), 0.13 * K, segs=(9, 6))
    b.cone("x", CLOTH[3], mat_at(tuple(hand + Vector((0, 0, 0.0)) * K)), 0.025 * K, 0.06 * K, 0.08 * K, segments=6)
    b.ball("x", RICE, mat_at(tuple(hand + Vector((0, -0.09, -0.06)) * K), scale=(1, 0.6, 0.5)), 0.05 * K, segs=(5, 4))
    return b


def clips(arm):
    A = korto.clips(arm)
    for name in ("Roll", "Draw", "Burn", "Climb"):   # moves he never makes
        bpy.data.actions.remove(A.pop(name))
    L = korto.L
    # Offer: steps in, left hand out low with the rice, head cocked, the cutlass held back
    offer = {"chest": (0, 12, 0), "head": (-6, 0, 12), "spine": (6, 0, 0),
             **L("L", upperarm=(-80, 0, 12), forearm=(-8, 0, 0)), **L("R", upperarm=(15, 0, 15), forearm=(-25, 0, 0)),
             **L("L", thigh=(-12, 0, 0), shin=(10, 0, 0)), **L("R", thigh=(8, 0, 0))}
    A["Offer"] = add_action(arm, "Offer", [(1, offer), (30, {**offer, "head": (-2, 0, 18), "chest": (2, 8, 0)}), (60, offer)])
    # Taunt: arms spread wide, chin up, a slow sway
    spread = lambda s: {"chest": (-8, s * 6, 0), "head": (-14, 0, s * 6), **L("L", upperarm=(-10, 0, -70), forearm=(-15, 0, 0)),
                        **L("R", upperarm=(-10, 0, 70), forearm=(-15, 0, 0)), "hips": {"loc": (0, 0, 0)}}
    A["Taunt"] = add_action(arm, "Taunt", [(1, spread(1)), (24, spread(-1)), (48, spread(1))])
    # Block: cutlass across, braced
    block = {"spine": (8, 0, 0), "chest": (0, -20, 0), **L("R", upperarm=(-80, 30, 0), forearm=(-70, 0, 0)), **L("L", upperarm=(-30, 0, -20), forearm=(-60, 0, 0)),
             **L("L", thigh=(-25, 0, 0), shin=(30, 0, 0)), **L("R", thigh=(15, 0, 0), shin=(20, 0, 0))}
    A["Block"] = add_action(arm, "Block", [(1, {}), (4, block), (14, block)], loop=False)
    # Flee: crouch, then a leap straight up, behind the sky
    crouch = {"spine": (25, 0, 0), **L("L", thigh=(-70, 0, 0), shin=(90, 0, 0), upperarm=(30, 0, -10)), **L("R", thigh=(-70, 0, 0), shin=(90, 0, 0), upperarm=(30, 0, 10)),
              "hips": {"loc": (0, -0.3, 0)}}
    up = {"spine": (-10, 0, 0), "head": (-30, 0, 0), **L("L", upperarm=(-170, 0, -10)), **L("R", upperarm=(-170, 0, 10)), **L("L", foot=(40, 0, 0)), **L("R", foot=(40, 0, 0))}
    A["Flee"] = add_action(arm, "Flee", [(1, {}), (8, crouch), (12, {**up, "root": {"rot": (0, 0, 0), "loc": (0, 1.2, 0)}}),
                                         (24, {**up, "root": {"rot": (0, 0, 0), "loc": (0, 7.0, 0)}})], loop=False)
    return A


def main():
    reset_scene()
    arm = build_armature("MeniTrueRig", BONES)
    mats = [vertex_color_material("MeniTrue", roughness=0.7), glow_material("Glow", EMBER, 6.0)]
    body = build_body().to_object(mats[0], extra_materials=mats[1:])
    skin_to(body, arm)
    blade = build_cutlass().to_object(mats[0], extra_materials=mats[1:])
    blade.vertex_groups.clear(); blade.name = "DarkCutlass"
    attach_to_bone(blade, arm, "hand.R", Matrix.Identity(4))
    rice = build_rice().to_object(mats[0])
    rice.vertex_groups.clear(); rice.name = "SeedRice"
    attach_to_bone(rice, arm, "hand.L", Matrix.Identity(4))
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "meni_true.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(520, 640))
        views = [("Idle", 1, 0), ("Idle", 1, 35), ("Idle", 1, 160), ("Offer", 1, 30), ("Taunt", 1, 20), ("Slash1", 8, 30), ("Block", 8, 30), ("Flee", 8, 30)]
        shots = []
        for i, (act, fr, ang) in enumerate(views):
            pose_at(arm, actions[act], fr)
            rice.hide_render = act != "Offer"
            aim_camera(cam, ang, target=(0, 0, 1.1), dist=5.2, height=1.6)
            p = PREVIEWS_OUT / f"_mt{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "meni-true.png", cols=4,
                      labels=["Front", "Three-quarter", "Back", "Offer (the bargain)", "Taunt", "Slash", "Block", "Flee: crouch"])


if __name__ == "__main__":
    main()
