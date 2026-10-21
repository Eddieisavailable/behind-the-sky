"""The Iron-Stone Genie: the bush genie that lends strength (stone skin, then a ground smash).

A giant of red laterite and dark iron ore, the stone Kpelle smiths smelted: boulders for a body,
iron bands round its forearms, moss and ferns grown on its shoulders, and the gold seams and eyes
that mark the genii (the Hornbill has the same gold). Flomo's first genie.

Faces -Y, about 2.7 m tall. Clips: Idle, Walk, Smash (both fists overhead, slammed down),
Grant (kneels and holds out a glowing stone: the GiftStone part, shown only then).

    python blender/genie_iron.py            # build + export public/models/genie_iron.glb
    python blender/genie_iron.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, add_action, aim_camera, attach_to_bone, build_armature,
                 contact_sheet, export_glb, glow_material, hexcol, jitter, mat_at, pose_at, render_to, reset_scene,
                 rest_pose, setup_preview, skin_to, vertex_color_material)

LATERITE = hexcol("#9a5b3a")
LATERITE_DARK = hexcol("#6e3f28")
ORE = hexcol("#3d3a3a")
ORE_RUST = hexcol("#7a4a30")
IRON = hexcol("#56595e")
MOSS = hexcol("#4f6e2a")
FERN = hexcol("#3f6a2c")
GOLD = hexcol("#ffc35a")

BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, 0, 1.05), (0, 0, 1.3), "root"),
    "chest": ((0, 0, 1.3), (0, 0, 2.05), "hips"),
    "head": ((0, -0.12, 2.18), (0, -0.16, 2.55), "chest"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"upperarm.{side}"] = ((0.72 * sx, 0, 1.95), (0.92 * sx, 0, 1.38), "chest")
    BONES[f"forearm.{side}"] = ((0.92 * sx, 0, 1.38), (0.98 * sx, -0.05, 0.78), f"upperarm.{side}")
    BONES[f"hand.{side}"] = ((0.98 * sx, -0.05, 0.78), (0.98 * sx, -0.1, 0.46), f"forearm.{side}")
    BONES[f"thigh.{side}"] = ((0.34 * sx, 0, 1.05), (0.4 * sx, 0, 0.55), "hips")
    BONES[f"shin.{side}"] = ((0.4 * sx, 0, 0.55), (0.42 * sx, -0.05, 0.05), f"thigh.{side}")


def stone(b, bone, col, loc, r, scale=(1, 1, 1), seed=1, rough=0.12):
    jitter(b.gem(bone, col, mat_at(loc, scale=scale), r), r * rough, seed)


def build_body():
    b = Body("GenieIron")
    ore = lambda f: ORE_RUST if (int(f.calc_center_median().x * 9) + int(f.calc_center_median().z * 7)) % 4 == 0 else ORE
    # hips and the great chest boulder, a second boulder hunched on the back
    stone(b, "hips", LATERITE_DARK, (0, 0.02, 1.15), 0.45, (1.3, 0.9, 0.7), 1)
    stone(b, "chest", ore, (0, 0.05, 1.72), 0.62, (1.35, 1.0, 1.0), 2, 0.08)
    stone(b, "chest", LATERITE, (0, 0.28, 2.02), 0.42, (1.2, 0.9, 0.8), 3)
    # gold seams across the chest: the genie's mark
    for a, c in (((-0.42, -0.5, 1.95), (-0.08, -0.6, 1.62)), ((0.42, -0.5, 1.95), (0.08, -0.6, 1.62)), ((-0.08, -0.6, 1.62), (0.0, -0.58, 1.35)),
                 ((0.08, -0.6, 1.62), (0.0, -0.58, 1.35)), ((-0.5, -0.4, 1.5), (-0.3, -0.55, 1.4))):
        b.limb("chest", GOLD, a, c, 0.022, segments=4, mat=1)
    # moss and ferns grown over the shoulders and back
    for sx in (1, -1):
        b.ball("chest", MOSS, mat_at((0.55 * sx, 0.05, 2.12), scale=(1.2, 1, 0.45)), 0.25, segs=(7, 4))
        for k in range(4):
            a = math.radians(-30 + k * 35)
            b.cone("chest", FERN, mat_at((0.5 * sx, 0.1 + k * 0.05, 2.2), rot=(-40 + k * 25, 25 * sx, math.degrees(a)), scale=(1, 0.3, 1)), 0.07, 0.0, 0.4, segments=4)
    b.ball("chest", MOSS, mat_at((0, 0.35, 2.3), scale=(1.3, 1, 0.4)), 0.25, segs=(7, 4))
    # small blocky head sunk between the shoulders, gold eyes under a heavy brow
    stone(b, "head", LATERITE_DARK, (0, -0.16, 2.36), 0.24, (1.0, 0.95, 1.05), 4, 0.08)
    b.box("head", ORE, mat_at((0, -0.34, 2.45), rot=(-10, 0, 0)), (0.36, 0.1, 0.09))
    for sx in (1, -1):
        b.gem("head", GOLD, mat_at((0.09 * sx, -0.37, 2.38)), 0.045, mat=1)
    b.box("head", GOLD, mat_at((0, -0.38, 2.24)), (0.14, 0.02, 0.025), mat=1)  # the mouth glows when it speaks
    # arms: shoulder boulder, upper arm, a huge forearm with iron bands, a fist
    for side, sx in (("L", 1), ("R", -1)):
        stone(b, f"upperarm.{side}", LATERITE, (0.72 * sx, 0.02, 1.98), 0.34, (1, 1, 0.9), 5 + sx)
        stone(b, f"upperarm.{side}", ore, (0.84 * sx, 0, 1.65), 0.25, (1, 1, 1.3), 7 + sx)
        stone(b, f"forearm.{side}", LATERITE_DARK, (0.95 * sx, -0.03, 1.08), 0.3, (1, 1, 1.5), 9 + sx)
        for z in (1.25, 0.95):
            b.cone(f"forearm.{side}", IRON, mat_at((0.95 * sx, -0.03, z)), 0.3, 0.3, 0.07, segments=8)
        stone(b, f"hand.{side}", ore, (0.98 * sx, -0.08, 0.6), 0.27, (1, 1, 1.1), 11 + sx)
        for k in range(3):
            b.gem(f"hand.{side}", ORE, mat_at((0.98 * sx + (k - 1) * 0.11, -0.3, 0.6)), 0.08)  # knuckles
        stone(b, f"thigh.{side}", LATERITE, (0.38 * sx, 0, 0.82), 0.3, (1, 1, 1.2), 13 + sx)
        stone(b, f"shin.{side}", ore, (0.41 * sx, -0.02, 0.33), 0.27, (1.05, 1.1, 1.2), 15 + sx)
        b.box(f"shin.{side}", LATERITE_DARK, mat_at((0.42 * sx, -0.12, 0.08)), (0.42, 0.55, 0.16))   # foot slab
    return b


def build_gift():
    b = Body("GiftStone")
    hand = Vector((-0.98, -0.32, 0.62))
    jitter(b.gem("x", ORE, mat_at(tuple(hand)), 0.13), 0.02, 3)
    for a in range(3):
        b.limb("x", GOLD, tuple(hand + Vector((math.cos(a * 2.1) * 0.1, -0.1, math.sin(a * 2.1) * 0.1))), tuple(hand + Vector((0, -0.12, 0))), 0.012, segments=3, mat=1)
    b.gem("x", GOLD, mat_at(tuple(hand + Vector((0, -0.11, 0.02)))), 0.05, mat=1)
    return b


def L(side, **kw):
    return {f"{k}.{side}": v for k, v in kw.items()}


def clips(arm):
    A = {}
    breathe = lambda k: {"chest": (k * 2, 0, 0), "head": (-k * 3, 0, 0), **L("L", upperarm=(0, 0, -6 - k * 2)), **L("R", upperarm=(0, 0, 6 + k * 2)),
                         "hips": {"rot": (0, 0, 0), "loc": (0, -0.02 * k, 0)}}
    A["Idle"] = add_action(arm, "Idle", [(1, breathe(0)), (40, breathe(1)), (80, breathe(0))])
    def step(lead, trail, bob):
        return {"chest": (6, 0, 4 if lead == "L" else -4), "hips": {"rot": (0, 0, 0), "loc": (0, bob, 0)},
                **L(lead, thigh=(-28, 0, 0), shin=(15, 0, 0), upperarm=(18, 0, 0)), **L(trail, thigh=(20, 0, 0), shin=(30, 0, 0), upperarm=(-18, 0, 0))}
    A["Walk"] = add_action(arm, "Walk", [(1, step("L", "R", -0.04)), (13, step("R", "L", -0.04)), (25, step("L", "R", -0.04))])
    up = {"chest": (-14, 0, 0), "head": (-12, 0, 0), **L("L", upperarm=(-165, 0, 15), forearm=(-30, 0, 0)), **L("R", upperarm=(-165, 0, -15), forearm=(-30, 0, 0))}
    down = {"chest": (38, 0, 0), "head": (-20, 0, 0), **L("L", upperarm=(-60, 0, 10), forearm=(-5, 0, 0), thigh=(-40, 0, 0), shin=(45, 0, 0)),
            **L("R", upperarm=(-60, 0, -10), forearm=(-5, 0, 0), thigh=(20, 0, 0), shin=(40, 0, 0)), "hips": {"rot": (0, 0, 0), "loc": (0, -0.3, 0)}}
    A["Smash"] = add_action(arm, "Smash", [(1, {}), (12, up), (17, down), (26, down), (40, {})], loop=False)
    kneel = {"chest": (14, 0, 0), "head": (10, 0, 0), **L("L", thigh=(-80, 0, 0), shin=(85, 0, 0), upperarm=(-10, 0, 8)),
             **L("R", thigh=(15, 0, 0), shin=(100, 0, 0), upperarm=(-70, 0, 0), forearm=(-25, 0, 0)), "hips": {"rot": (0, 0, 0), "loc": (0, -0.5, 0)}}
    A["Grant"] = add_action(arm, "Grant", [(1, {}), (18, kneel), (40, {**kneel, "head": (16, 0, 0)})], loop=False)
    return A


def main():
    reset_scene()
    arm = build_armature("GenieIronRig", BONES)
    mats = [vertex_color_material("GenieIron", roughness=0.9), glow_material("Glow", GOLD, 5.0)]
    body = build_body().to_object(mats[0], extra_materials=mats[1:])
    skin_to(body, arm)
    gift = build_gift().to_object(mats[0], extra_materials=mats[1:])
    gift.vertex_groups.clear(); gift.name = "GiftStone"
    attach_to_bone(gift, arm, "hand.R", Matrix.Identity(4))
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "genie_iron.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(560, 640))
        views = [("Idle", 1, 0), ("Idle", 1, 40), ("Idle", 1, 160), ("Walk", 1, 60), ("Smash", 12, 35), ("Smash", 17, 35), ("Grant", 40, 30)]
        shots = []
        for i, (act, fr, ang) in enumerate(views):
            pose_at(arm, actions[act], fr)
            gift.hide_render = act != "Grant"
            aim_camera(cam, ang, target=(0, 0, 1.3), dist=7.0, height=2.2)
            p = PREVIEWS_OUT / f"_gi{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "genie-iron.png", cols=4,
                      labels=["Front", "Three-quarter", "Back", "Walk", "Smash: up", "Smash: down", "Grant"])


if __name__ == "__main__":
    main()
