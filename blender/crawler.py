"""The rattan crawler: a demon-grown creature of woven cane, thorns and vine.

Builds the model, rig and animations and exports public/models/crawler.glb.

    python blender/crawler.py            # build + export
    python blender/crawler.py --preview  # also render turnaround and pose sheets
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, add_action, aim_camera, build_armature, contact_sheet,
                 export_glb, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose, setup_preview,
                 simple_material, skin_to, vertex_color_material)

CANE = hexcol("#b8894f")
CANE_DARK = hexcol("#8a6234")
CANE_PALE = hexcol("#d2aa6c")
BINDING = hexcol("#4f3a22")
THORN = hexcol("#3a2b1a")
VINE = hexcol("#4d6a2a")
LEAF = hexcol("#6f8f34")
MAW = hexcol("#2a1408")
EYE_GLOW = hexcol("#ffbf3a")

BONES = {
    "root": ((0, 0, 0), (0, 0, 0.1), None),
    "base": ((0, 0, 0.05), (0, 0, 0.45), "root"),
    "seg1": ((0, 0, 0.45), (0, 0, 0.85), "base"),
    "seg2": ((0, 0, 0.85), (0, 0, 1.22), "seg1"),
    "head": ((0, 0, 1.22), (0, 0, 1.55), "seg2"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"arm1.{side}"] = ((0.16 * sx, 0, 1.1), (0.4 * sx, -0.05, 0.86), "seg2")
    BONES[f"arm2.{side}"] = ((0.4 * sx, -0.05, 0.86), (0.5 * sx, -0.12, 0.52), f"arm1.{side}")


def woven(z0, z1, bone, b, r0, r1, rings=3):
    """A trunk section of stacked woven rings, each a little twisted, with bindings and thorns."""
    for i in range(rings):
        t0 = i / rings
        t1 = (i + 1) / rings
        za = z0 + (z1 - z0) * t0
        zb = z0 + (z1 - z0) * t1
        ra = r0 + (r1 - r0) * t0
        rb = r0 + (r1 - r0) * t1
        weave = lambda f, i=i: (CANE if (int((math.atan2(f.calc_center_median().y, f.calc_center_median().x) + math.pi) * 7 / math.pi) + i) % 2 else CANE_PALE)
        b.cone(bone, weave, mat_at((0, 0, (za + zb) / 2), rot=(0, 0, i * 17)), ra * 1.06, rb, (zb - za) * 0.96, segments=7)
        b.cone(bone, BINDING, mat_at((0, 0, zb - 0.01)), rb * 1.08, rb * 1.08, 0.025, segments=7)
        # thorns sticking out of every ring, staggered
        for k in range(3):
            a = (k / 3) * 2 * math.pi + i * 1.1
            x, y = math.cos(a) * rb * 0.95, math.sin(a) * rb * 0.95
            b.cone(bone, THORN, mat_at((x * 1.25, y * 1.25, (za + zb) / 2), rot=(math.degrees(-math.sin(a)) * 1.2, math.degrees(math.cos(a)) * 1.2, 0)), 0.022, 0.0, 0.11, segments=4)


def build_body():
    b = Body("Crawler")
    # roots splayed on the ground
    for k in range(5):
        a = (k / 5) * 2 * math.pi + 0.3
        b.limb("base", VINE, (0, 0, 0.12), (math.cos(a) * 0.42, math.sin(a) * 0.42, 0.02), 0.05, 0.015, segments=5)
    woven(0.05, 0.45, "base", b, 0.2, 0.17)
    woven(0.45, 0.85, "seg1", b, 0.17, 0.15)
    woven(0.85, 1.22, "seg2", b, 0.15, 0.14)
    # head: a long woven snout with a dark maw and two glowing eyes
    b.cone("head", CANE_DARK, mat_at((0, -0.06, 1.36), rot=(-20, 0, 0), scale=(1, 1.35, 1)), 0.16, 0.12, 0.26, segments=7)
    b.cone("head", CANE, mat_at((0, -0.24, 1.33), rot=(-95, 0, 0)), 0.1, 0.05, 0.2, segments=6)        # snout
    b.box("head", MAW, mat_at((0, -0.27, 1.29), rot=(10, 0, 0)), (0.13, 0.17, 0.03))                   # mouth slit
    for sx in (1, -1):
        b.gem("head", EYE_GLOW, mat_at((0.075 * sx, -0.19, 1.42)), 0.032, mat=1)
        b.cone("head", THORN, mat_at((0.09 * sx, -0.12, 1.47), rot=(-25, 0, -20 * sx)), 0.03, 0.0, 0.12, segments=4)  # brow spikes
    # crown of vine leaves
    for k in range(6):
        a = (k / 6) * 2 * math.pi
        b.cone("head", LEAF, mat_at((math.cos(a) * 0.08, math.sin(a) * 0.08 + 0.03, 1.5), rot=(math.degrees(-math.sin(a)) * 0.6, math.degrees(math.cos(a)) * 0.6, 0), scale=(1, 0.35, 1)), 0.05, 0.0, 0.22, segments=4)
    # vine arms ending in hooked thorns
    for side, sx in (("L", 1), ("R", -1)):
        b.limb(f"arm1.{side}", VINE, (0.12 * sx, 0, 1.12), (0.4 * sx, -0.05, 0.86), 0.05, 0.04, segments=5)
        b.limb(f"arm2.{side}", VINE, (0.4 * sx, -0.05, 0.86), (0.5 * sx, -0.12, 0.52), 0.04, 0.025, segments=5)
        b.cone(f"arm2.{side}", THORN, mat_at((0.52 * sx, -0.16, 0.47), rot=(-120, 0, 0)), 0.03, 0.0, 0.16, segments=4)
        b.cone(f"arm2.{side}", THORN, mat_at((0.47 * sx, -0.1, 0.62), rot=(0, 70 * sx, 0)), 0.02, 0.0, 0.09, segments=4)
        b.cone(f"arm1.{side}", LEAF, mat_at((0.3 * sx, -0.02, 1.0), rot=(0, 50 * sx, 0), scale=(1, 0.35, 1)), 0.04, 0.0, 0.16, segments=4)
    return b


def clips(arm):
    A = {}
    sway = lambda s: {"base": (0, 0, 4 * s), "seg1": (0, 0, -6 * s), "seg2": (0, 0, 7 * s), "head": (0, 0, -5 * s),
                      "arm1.L": (8 * s, 0, 0), "arm1.R": (-8 * s, 0, 0), "arm2.L": (-10, 0, 0), "arm2.R": (-10, 0, 0)}
    A["Idle"] = add_action(arm, "Idle", [(1, sway(1)), (31, sway(-1)), (61, sway(1))])

    def step(s, up):
        return {"root": {"loc": (0, up, 0)}, "base": (8, 0, 10 * s), "seg1": (-4, 0, -14 * s), "seg2": (6, 0, 14 * s), "head": (-6, 0, -10 * s),
                "arm1.L": (-30 * s, 0, 0), "arm1.R": (30 * s, 0, 0), "arm2.L": (-20, 0, 0), "arm2.R": (-20, 0, 0)}
    A["Walk"] = add_action(arm, "Walk", [(1, step(1, 0.0)), (6, step(0, 0.05)), (11, step(-1, 0.0)), (16, step(0, 0.05)), (21, step(1, 0.0))])

    rear = {"base": (-8, 0, 0), "seg1": (-18, 0, 0), "seg2": (-22, 0, 0), "head": (20, 0, 0),
            "arm1.L": (110, 0, -20), "arm1.R": (110, 0, 20), "arm2.L": (-40, 0, 0), "arm2.R": (-40, 0, 0)}
    A["Windup"] = add_action(arm, "Windup", [(1, {}), (8, rear), (15, {**rear, "seg2": (-26, 0, 0)})], loop=False)
    A["Strike"] = add_action(arm, "Strike", [
        (1, rear),
        (4, {"base": (14, 0, 0), "seg1": (26, 0, 0), "seg2": (24, 0, 0), "head": (10, 0, 0),
             "arm1.L": (-85, 0, 10), "arm1.R": (-85, 0, -10), "arm2.L": (-20, 0, 0), "arm2.R": (-20, 0, 0)}),
        (10, {}),
    ], loop=False)
    # felled: lying along the ground (lifted so the cane doesn't sink in), head raised a little, arms flat
    felled = {"root": {"loc": (0, 0.14, 0)}, "base": (87, 0, 0), "seg1": (-6, 0, 8), "seg2": (8, 0, -10), "head": (-40, 0, 6),
              "arm1.L": (95, 0, -35), "arm1.R": (95, 0, 35), "arm2.L": (10, 0, 0), "arm2.R": (10, 0, 0)}
    down_keys = [(1, {}), (5, {**felled, "root": {"loc": (0, 0.05, 0)}, "base": (60, 0, 0), "seg1": (20, 0, 0)}), (12, felled)]
    A["Down"] = add_action(arm, "Down", down_keys, loop=False)
    A["Rise"] = add_action(arm, "Rise", down_keys, loop=False, reverse=True)
    return A


def main():
    reset_scene()
    arm = build_armature("CrawlerRig", BONES)
    body = build_body().to_object(vertex_color_material("Rattan"),
                                  extra_materials=[simple_material("Eyes", EYE_GLOW, emission=EYE_GLOW, strength=4)])
    skin_to(body, arm)
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "crawler.glb")

    if "--preview" in sys.argv:
        cam = setup_preview()
        shots = []
        for i, ang in enumerate((0, 35, 90, 180)):
            aim_camera(cam, ang, target=(0, 0, 0.8), dist=3.8, height=1.3)
            p = PREVIEWS_OUT / f"_c{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "crawler-turnaround.png", cols=4, labels=["Front", "Three-quarter", "Side", "Back"])
        poses = [("Idle", 1), ("Walk", 1), ("Walk", 11), ("Windup", 15), ("Strike", 4), ("Down", 12)]
        shots = []
        aim_camera(cam, 55, target=(0, -0.4, 0.6), dist=4.2, height=1.6)
        for i, (name, frame) in enumerate(poses):
            pose_at(arm, actions[name], frame)
            p = PREVIEWS_OUT / f"_cp{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "crawler-poses.png", cols=6, labels=[f"{n} {f}" for n, f in poses])


if __name__ == "__main__":
    main()
