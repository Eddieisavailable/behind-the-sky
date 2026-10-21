"""Gelengol: Woi's first wife, mother of all living things, banished to the fork in the road.

She sits at the crossroads on a carved stool among stacks of wooden bowls, and her singing carves
new ones; she sells Korto the offering bowls. Old and regal: a tall indigo head-tie with white
circles, grey hair at the temples, strings of beads and cowries, an ochre and black wrapper, a
shawl, brass bangles. The stool and her bowls are part of the model. The bowl she offers
(the Bowl part) is shown only while offering.

Same skeleton layout as Korto. Clips (all seated): Sit (sways, humming), Sing (head up, palms up),
Offer (leans forward, holds out a bowl).

    python blender/gelengol.py            # build + export public/models/gelengol.glb
    python blender/gelengol.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korto
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, add_action, aim_camera, attach_to_bone, build_armature,
                 contact_sheet, export_glb, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose, setup_preview,
                 skin_to, vertex_color_material)

SKIN = hexcol("#4a2f20")
SKIN_DARK = hexcol("#3a2418")
HAIR = hexcol("#c9c4ba")
LIPS = hexcol("#33201a")
EYE = korto.EYE
EYE_WHITE = korto.EYE_WHITE
INDIGO = hexcol("#232c5a")
WHITE = hexcol("#e8e0cc")
OCHRE = hexcol("#c08a32")
BLACK = hexcol("#1c1814")
SHAWL = hexcol("#7a2f22")
BRASS = hexcol("#c9a24a")
BEADS = [hexcol("#b8352a"), hexcol("#e0a83a"), hexcol("#e8e0cc"), hexcol("#2d6a8a")]
COWRIE = hexcol("#ece3cc")
WOOD = hexcol("#6b4426")
WOOD_DARK = hexcol("#4a2e18")
WOOD_PALE = hexcol("#9a6a3e")

BONES = korto.BONES
L = korto.L


def wrapper(f):
    """Ochre wrapper with black zigzag bands."""
    c = f.calc_center_median()
    return BLACK if int(c.z * 14 + abs(math.atan2(c.y, c.x)) * 2) % 5 == 0 else OCHRE


def bowl(b, bone, loc, r, depth, col=WOOD):
    x, y, z = loc
    b.cone(bone, col, mat_at((x, y, z + depth / 2)), r * 0.6, r, depth, segments=10)
    b.cone(bone, WOOD_DARK, mat_at((x, y, z + depth)), r * 0.9, r * 0.9, 0.012, segments=10)   # the hollow
    b.cone(bone, WOOD_PALE, mat_at((x, y, z + depth * 0.45)), r * 0.82, r * 0.82, 0.012, segments=10)  # carved band


def build_body():
    b = Body("Gelengol")
    # head: an old face, grey hair at the temples, a tall indigo head-tie with white circles
    b.ball("head", SKIN, mat_at((0, -0.005, 1.58), scale=(0.95, 1.0, 1.1)), 0.12, segs=(10, 8))
    b.cone("head", SKIN_DARK, mat_at((0, -0.11, 1.57), rot=(-90, 0, 0)), 0.024, 0.008, 0.04, segments=4)
    b.box("head", LIPS, mat_at((0, -0.1, 1.52)), (0.045, 0.02, 0.012))
    for sx in (1, -1):
        b.box("head", EYE_WHITE, mat_at((0.043 * sx, -0.107, 1.595)), (0.036, 0.012, 0.016))
        b.box("head", EYE, mat_at((0.043 * sx, -0.112, 1.592)), (0.018, 0.01, 0.014))
        b.box("head", SKIN_DARK, mat_at((0.043 * sx, -0.108, 1.578)), (0.04, 0.01, 0.006))   # the lines under her eyes
        b.ball("head", HAIR, mat_at((0.1 * sx, 0.0, 1.61), scale=(0.5, 1, 1)), 0.045, segs=(6, 4))
        b.ball("head", SKIN_DARK, mat_at((0.118 * sx, 0, 1.57), scale=(0.5, 1, 1)), 0.028, segs=(6, 4))
        b.gem("head", BRASS, mat_at((0.12 * sx, -0.01, 1.52)), 0.016)                       # earrings
    dots = lambda f: WHITE if (int(f.calc_center_median().z * 50) + int((math.atan2(f.calc_center_median().y, f.calc_center_median().x) + 3.2) * 4)) % 4 == 0 else INDIGO
    b.cone("head", INDIGO, mat_at((0, 0.01, 1.66)), 0.125, 0.14, 0.07, segments=12)
    b.cone("head", dots, mat_at((0, 0.03, 1.8), rot=(-12, 0, 0)), 0.15, 0.1, 0.24, segments=12)
    b.ball("head", dots, mat_at((0, 0.05, 1.93), rot=(-12, 0, 0), scale=(1, 1, 0.5)), 0.11, segs=(10, 5))
    b.cone("head", INDIGO, mat_at((0.07, 0.1, 1.76), rot=(0, 0, 30), scale=(1, 0.35, 1)), 0.05, 0.1, 0.12, segments=6)  # knot
    b.limb("neck", SKIN, (0, 0, 1.39), (0, 0, 1.49), 0.045)
    # strings of beads and cowries, longest lowest
    for k in range(4):
        r = 0.1 + k * 0.025
        for j in range(14):
            a = math.radians(-80 + j * (160 / 13))
            p = (math.sin(a) * r, -math.cos(a) * r * 0.72 + 0.01, 1.4 - k * 0.04 - math.cos(a) * 0.05 * (k + 1))
            if k == 3 and j % 2:
                b.ball("chest", COWRIE, mat_at(p, scale=(0.8, 0.5, 1)), 0.014, segs=(5, 4))
            else:
                b.gem("chest", BEADS[(j + k) % len(BEADS)], mat_at(p), 0.012)
    # body: dress top, red shawl across the shoulders
    b.cone("chest", wrapper, mat_at((0, 0.005, 1.28), scale=(1, 0.72, 1)), 0.14, 0.18, 0.24, segments=10)
    b.cone("spine", wrapper, mat_at((0, 0.005, 1.08), scale=(1, 0.75, 1)), 0.16, 0.14, 0.22, segments=10)
    b.cone("chest", SHAWL, mat_at((0, 0.02, 1.33), scale=(1, 0.8, 1)), 0.2, 0.19, 0.1, segments=10)
    # wrapper: round the hips, over the thighs and down the shins to the ankle (so it sits with her)
    b.cone("hips", wrapper, mat_at((0, 0.01, 0.9), scale=(1, 0.85, 1)), 0.22, 0.17, 0.18, segments=12)
    for side, sx in (("L", 1), ("R", -1)):
        b.cone(f"thigh.{side}", wrapper, mat_at((0.1 * sx, 0.0, 0.66)), 0.11, 0.12, 0.36, segments=10)
        b.cone(f"shin.{side}", wrapper, mat_at((0.1 * sx, 0.0, 0.3)), 0.13, 0.11, 0.42, segments=10)
        b.cone(f"shin.{side}", BLACK, mat_at((0.1 * sx, 0.0, 0.1)), 0.132, 0.132, 0.03, segments=10)  # hem
    # arms, thin, brass bangles stacked; bare feet
    for side, sx in (("L", 1), ("R", -1)):
        b.ball(f"upperarm.{side}", SHAWL, mat_at((0.19 * sx, 0, 1.35)), 0.06, segs=(8, 6))
        b.limb(f"upperarm.{side}", SKIN, (0.195 * sx, 0, 1.33), (0.205 * sx, 0, 1.11), 0.042, 0.036)
        b.limb(f"forearm.{side}", SKIN, (0.205 * sx, 0, 1.11), (0.215 * sx, 0, 0.9), 0.036, 0.03)
        for k in range(3):
            b.limb(f"forearm.{side}", BRASS, (0.214 * sx, 0, 0.94 - k * 0.022), (0.215 * sx, 0, 0.93 - k * 0.022), 0.034)
        b.ball(f"hand.{side}", SKIN, mat_at((0.215 * sx, -0.005, 0.85), scale=(0.8, 1, 1.15)), 0.042, segs=(6, 5))
        b.box(f"foot.{side}", SKIN_DARK, mat_at((0.1 * sx, -0.05, 0.03)), (0.075, 0.19, 0.045))
    # her carved stool (rests on the ground under her when seated) and her bowls
    b.cone("root", WOOD, mat_at((0, 0.05, 0.42)), 0.24, 0.24, 0.05, segments=12)
    b.cone("root", WOOD_DARK, mat_at((0, 0.05, 0.25)), 0.08, 0.16, 0.3, segments=8)
    b.cone("root", WOOD, mat_at((0, 0.05, 0.05)), 0.22, 0.2, 0.1, segments=12)
    for k in range(4):
        a = k / 4 * 2 * math.pi
        b.box("root", WOOD_PALE, mat_at((math.cos(a) * 0.12, 0.05 + math.sin(a) * 0.12, 0.25), rot=(0, 0, math.degrees(a))), (0.03, 0.03, 0.22))
    for (x, y, rs) in ((0.6, -0.1, (0.22, 0.19, 0.16)), (-0.62, 0.15, (0.2, 0.17)), (0.45, 0.45, (0.26,))):
        z = 0.0
        for r in rs:
            bowl(b, "root", (x, y, z), r, r * 0.55)
            z += r * 0.42
    bowl(b, "root", (-0.4, -0.45, 0.0), 0.14, 0.08, WOOD_PALE)
    return b


def build_bowl():
    b = Body("Bowl")
    bowl(b, "x", (-0.215, -0.1, 0.78), 0.13, 0.08, WOOD_PALE)
    return b


SEAT = {"hips": {"rot": (0, 0, 0), "loc": (0, -0.4, 0)}, **L("L", thigh=(-88, 0, -4), shin=(88, 0, 0)), **L("R", thigh=(-88, 0, 4), shin=(88, 0, 0))}


def seated(**extra):
    p = dict(SEAT)
    p.update(extra)
    return p


def clips(arm):
    A = {}
    rest_arms = {**L("L", upperarm=(-25, 0, -8), forearm=(-60, 0, 0)), **L("R", upperarm=(-25, 0, 8), forearm=(-60, 0, 0))}
    A["Sit"] = add_action(arm, "Sit", [(1, seated(**rest_arms, chest=(2, 0, 0))), (30, seated(**rest_arms, chest=(-2, 4, 0), head=(-6, 0, 6))),
                                       (60, seated(**rest_arms, chest=(2, -4, 0), head=(4, 0, -6))), (90, seated(**rest_arms, chest=(2, 0, 0)))])
    sing = lambda s: seated(chest=(-10, 6 * s, 0), head=(-22, 0, 8 * s), spine=(-4, 0, 0),
                            **L("L", upperarm=(-70, 0, -45), forearm=(-30, 0, 0)), **L("R", upperarm=(-70, 0, 45), forearm=(-30, 0, 0)))
    A["Sing"] = add_action(arm, "Sing", [(1, sing(1)), (24, sing(-1)), (48, sing(1))])
    offer = seated(spine=(18, 0, 0), chest=(8, 0, 0), head=(-10, 0, 0),
                   **L("L", upperarm=(-62, 0, 18), forearm=(-25, 0, 0)), **L("R", upperarm=(-62, 0, -18), forearm=(-25, 0, 0)))
    A["Offer"] = add_action(arm, "Offer", [(1, seated(**rest_arms)), (14, offer), (40, {**offer, "head": (-14, 0, 6)})], loop=False)
    return A


def main():
    reset_scene()
    arm = build_armature("GelengolRig", BONES)
    mat = vertex_color_material("Gelengol")
    body = build_body().to_object(mat)
    skin_to(body, arm)
    held = build_bowl().to_object(mat)
    held.vertex_groups.clear(); held.name = "Bowl"
    attach_to_bone(held, arm, "hand.R", Matrix.Identity(4))
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "gelengol.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(520, 560))
        views = [("Sit", 1, 0), ("Sit", 30, 40), ("Sing", 1, 25), ("Offer", 40, 30), ("Sit", 1, 150)]
        shots = []
        for i, (act, fr, ang) in enumerate(views):
            pose_at(arm, actions[act], fr)
            held.hide_render = act != "Offer"
            aim_camera(cam, ang, target=(0, 0, 0.75), dist=3.6, height=1.3)
            p = PREVIEWS_OUT / f"_gl{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "gelengol.png", cols=5, labels=["Sitting", "Humming", "Sing", "Offer a bowl", "Back"])


if __name__ == "__main__":
    main()
