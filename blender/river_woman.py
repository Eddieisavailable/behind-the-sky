"""The River Woman: the water spirit who sits on the river rocks combing her long hair.

Drawn from Liberian Mammy Water belief (she brings wealth and visits in dreams; shout at her first
and she must bargain fairly). Dark skin dotted with white river clay, very long black hair to the
rock, pale glowing eyes, a shimmering blue-green wrap with scale-like folds, pearls and cowries,
silver anklets, a gold comb (the Comb part).

Same skeleton layout as Korto, seated (the game sits her on the river rocks from the swamp kit).
Clips: Comb (combing, unaware), Startled (the hero shouted first: she turns), Speak (bargaining),
Dive (slips back into the water).

    python blender/river_woman.py            # build + export public/models/river_woman.glb
    python blender/river_woman.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korto
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, add_action, aim_camera, attach_to_bone, build_armature,
                 contact_sheet, export_glb, glow_material, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose,
                 setup_preview, skin_to, vertex_color_material)

SKIN = hexcol("#3e281c")
SKIN_DARK = hexcol("#2e1d14")
CLAY = hexcol("#e9e4da")
HAIR = hexcol("#0f0d0e")
HAIR_SHEEN = hexcol("#2a2a33")
LIPS = hexcol("#2a1712")
WRAP = hexcol("#1f6e6a")
WRAP_LIGHT = hexcol("#3fa39a")
WRAP_DARK = hexcol("#164a52")
PEARL = hexcol("#f1ece0")
SILVER = hexcol("#c4c9cf")
GOLD = hexcol("#d9b048")
GLOW = hexcol("#a8f0ff")

BONES = korto.BONES
L = korto.L


def scales(f):
    c = f.calc_center_median()
    k = int(c.z * 30) + int((math.atan2(c.y, c.x) + math.pi) * 5)
    return WRAP_LIGHT if k % 4 == 0 else WRAP_DARK if k % 4 == 2 else WRAP


def build_body():
    b = Body("RiverWoman")
    # face: white clay dots over the brows and cheeks, pale glowing eyes
    b.ball("head", SKIN, mat_at((0, -0.005, 1.585), scale=(0.94, 1.0, 1.12)), 0.12, segs=(10, 8))
    b.cone("head", SKIN_DARK, mat_at((0, -0.11, 1.575), rot=(-90, 0, 0)), 0.024, 0.008, 0.04, segments=4)
    b.box("head", LIPS, mat_at((0, -0.1, 1.525)), (0.048, 0.02, 0.014))
    for sx in (1, -1):
        b.gem("head", GLOW, mat_at((0.043 * sx, -0.108, 1.6)), 0.016, mat=1)
        for k in range(3):
            b.gem("head", CLAY, mat_at((0.03 * sx + k * 0.018 * sx, -0.108, 1.635 - k * 0.004)), 0.006)
            b.gem("head", CLAY, mat_at((0.06 * sx, -0.098, 1.565 - k * 0.016)), 0.006)
        b.gem("head", PEARL, mat_at((0.12 * sx, -0.01, 1.53)), 0.014)
    # hair: a crown of hair on the head, then long locks down her back to the rock
    b.ball("head", HAIR, mat_at((0, 0.03, 1.64), scale=(1.08, 1.12, 0.85)), 0.13, segs=(10, 6))
    for k in range(9):
        a = math.radians(-80 + k * 20)
        top = Vector((math.sin(a) * 0.1, 0.06 + math.cos(a) * 0.06, 1.6))
        mid = top + Vector((math.sin(a) * 0.08, 0.08, -0.45))
        low = mid + Vector((math.sin(a) * 0.05, 0.06, -0.55))
        col = HAIR_SHEEN if k % 3 == 0 else HAIR
        b.limb("head", col, tuple(top), tuple(top + (mid - top) * 0.25), 0.032, 0.03, segments=5)
        b.limb("chest", col, tuple(top + (mid - top) * 0.25), tuple(mid), 0.03, 0.026, segments=5)
        b.limb("spine", col, tuple(mid), tuple(low), 0.026, 0.008, segments=5)
    b.limb("neck", SKIN, (0, 0, 1.39), (0, 0, 1.49), 0.045)
    # wrap tied above the breast, strings of pearls and cowries
    b.cone("chest", scales, mat_at((0, 0.005, 1.25), scale=(1, 0.72, 1)), 0.14, 0.165, 0.2, segments=12)
    b.cone("spine", scales, mat_at((0, 0.005, 1.07), scale=(1, 0.75, 1)), 0.16, 0.14, 0.2, segments=12)
    for k in range(2):
        r = 0.1 + k * 0.03
        for j in range(12):
            a = math.radians(-75 + j * (150 / 11))
            b.gem("chest", PEARL if (j + k) % 3 else GOLD, mat_at((math.sin(a) * r, -math.cos(a) * r * 0.75, 1.39 - k * 0.05 - math.cos(a) * 0.04)), 0.011)
    # long skirt: round the hips, over the thighs, down the shins in a flaring, fin-like hem
    b.cone("hips", scales, mat_at((0, 0.01, 0.9), scale=(1, 0.85, 1)), 0.21, 0.16, 0.18, segments=12)
    for side, sx in (("L", 1), ("R", -1)):
        b.cone(f"thigh.{side}", scales, mat_at((0.1 * sx, 0.0, 0.66)), 0.11, 0.12, 0.36, segments=10)
        b.cone(f"shin.{side}", scales, mat_at((0.1 * sx, 0.0, 0.3)), 0.17, 0.11, 0.42, segments=10)
        b.cone(f"shin.{side}", WRAP_LIGHT, mat_at((0.1 * sx, 0.0, 0.08), scale=(1.25, 1, 1)), 0.2, 0.17, 0.04, segments=10)
    for side, sx in (("L", 1), ("R", -1)):
        b.ball(f"upperarm.{side}", SKIN, mat_at((0.185 * sx, 0, 1.36)), 0.05, segs=(8, 6))
        b.limb(f"upperarm.{side}", SKIN, (0.19 * sx, 0, 1.36), (0.2 * sx, 0, 1.11), 0.045, 0.038)
        for k in range(3):
            b.gem(f"upperarm.{side}", CLAY, mat_at((0.235 * sx, -0.01, 1.3 - k * 0.04)), 0.006)
        b.limb(f"forearm.{side}", SKIN, (0.2 * sx, 0, 1.11), (0.21 * sx, 0, 0.9), 0.038, 0.03)
        b.limb(f"forearm.{side}", SILVER, (0.209 * sx, 0, 0.93), (0.21 * sx, 0, 0.91), 0.034)
        b.ball(f"hand.{side}", SKIN, mat_at((0.21 * sx, -0.005, 0.85), scale=(0.8, 1, 1.15)), 0.042, segs=(6, 5))
        b.box(f"foot.{side}", SKIN_DARK, mat_at((0.1 * sx, -0.05, 0.03)), (0.07, 0.19, 0.045))
        b.limb(f"foot.{side}", SILVER, (0.07 * sx, 0, 0.08), (0.13 * sx, 0, 0.08), 0.012, segments=4)
    return b


def build_comb():
    b = Body("Comb")
    hand = Vector((-0.21, -0.03, 0.82))
    b.box("x", GOLD, mat_at(tuple(hand)), (0.02, 0.12, 0.05))
    for k in range(7):
        b.box("x", GOLD, mat_at(tuple(hand + Vector((0, -0.05 + k * 0.017, -0.05)))), (0.008, 0.006, 0.06))
    b.gem("x", GLOW, mat_at(tuple(hand + Vector((0, 0, 0.03)))), 0.012, mat=1)
    return b


SEAT = {"hips": {"rot": (0, 0, 0), "loc": (0, -0.4, 0)}, **L("L", thigh=(-82, 0, -6), shin=(70, 0, 0)), **L("R", thigh=(-82, 0, 2), shin=(95, 0, 0))}


def seated(**extra):
    p = dict(SEAT)
    p.update(extra)
    return p


def clips(arm):
    A = {}
    # comb: right hand up by her head drawing the comb down through the hair; left hand holds the locks
    stroke = lambda k: seated(head=(6, 0, -14), chest=(0, 8, 0),
                              **L("R", upperarm=(-150 + 40 * k, 0, -28), forearm=(-80 + 30 * k, 0, 0)),
                              **L("L", upperarm=(-35, 0, -10), forearm=(-80, 0, 0)))
    A["Comb"] = add_action(arm, "Comb", [(1, stroke(0)), (20, stroke(1)), (26, stroke(1)), (45, stroke(0)), (60, stroke(0))])
    startled = seated(head=(-6, 0, 38), chest=(-8, -22, 0), spine=(-6, 0, 0),
                      **L("R", upperarm=(-40, 0, 20), forearm=(-60, 0, 0)), **L("L", upperarm=(-10, 0, -30), forearm=(-20, 0, 0)))
    A["Startled"] = add_action(arm, "Startled", [(1, stroke(0)), (5, startled), (20, startled)], loop=False)
    talk = lambda s: seated(head=(-4, 0, 8 * s), chest=(-4, 6 * s, 0),
                            **L("L", upperarm=(-55, 0, -20), forearm=(-50 + 15 * s, 0, 0)), **L("R", upperarm=(-20, 0, 10), forearm=(-70, 0, 0)))
    A["Speak"] = add_action(arm, "Speak", [(1, talk(1)), (30, talk(-1)), (60, talk(1))])
    dive = {"spine": (40, 0, 0), "chest": (20, 0, 0), "head": (20, 0, 0), **L("L", upperarm=(-160, 0, 10), thigh=(0, 0, 0)), **L("R", upperarm=(-160, 0, -10), thigh=(0, 0, 0)),
            "root": {"rot": (60, 0, 0), "loc": (0, -1.2, -0.6)}}
    A["Dive"] = add_action(arm, "Dive", [(1, talk(1)), (8, seated(spine=(20, 0, 0), **L("L", upperarm=(-120, 0, 10)), **L("R", upperarm=(-120, 0, -10)))), (20, dive)], loop=False)
    return A


def main():
    reset_scene()
    arm = build_armature("RiverWomanRig", BONES)
    mats = [vertex_color_material("RiverWoman", roughness=0.4), glow_material("Glow", GLOW, 4.0)]
    body = build_body().to_object(mats[0], extra_materials=mats[1:])
    skin_to(body, arm)
    comb = build_comb().to_object(mats[0], extra_materials=mats[1:])
    comb.vertex_groups.clear(); comb.name = "Comb"
    attach_to_bone(comb, arm, "hand.R", Matrix.Identity(4))
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "river_woman.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(520, 560))
        views = [("Comb", 1, 20), ("Comb", 20, 60), ("Startled", 20, 20), ("Speak", 1, 25), ("Comb", 1, 160), ("Dive", 14, 70)]
        shots = []
        for i, (act, fr, ang) in enumerate(views):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0, 0.8), dist=3.4, height=1.3)
            p = PREVIEWS_OUT / f"_rw{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "river-woman.png", cols=6, labels=["Combing", "Combing (side)", "Startled", "Speak", "Back: her hair", "Dive"])


if __name__ == "__main__":
    main()
