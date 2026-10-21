"""The Driver-Ant Genie: the bush genie whose gift is the swarm.

A soldier driver ant (the column ants that march through Liberian bush and clear everything in
their path) the size of a cow: a blind, heavy red-brown head with great sickle jaws, a narrow
waist, a shining gaster, and the genii's gold marks: a crown of gold beads on its head and gold
bands round its gaster.

Faces -Y, about 2.6 m long. Clips: Idle (feelers sweep, jaws work), Walk (tripod gait),
Grant (rears up, jaws wide), Swarm (shivers, jaws snapping: calling the column).

    python blender/genie_ant.py            # build + export public/models/genie_ant.glb
    python blender/genie_ant.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Vector, add_action, aim_camera, build_armature, contact_sheet,
                 export_glb, glow_material, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose, setup_preview,
                 skin_to, turned, vertex_color_material)

CHITIN = hexcol("#6a2a14")
CHITIN_DARK = hexcol("#3a160a")
CHITIN_SHINE = hexcol("#8e4424")
JAW = hexcol("#24120a")
GOLD = hexcol("#ffc35a")

LEGS = [(-0.3, -0.35, -0.45), (0.0, 0.0, 0.0), (0.22, 0.35, 0.5)]   # (hip y on thorax, knee y offset, foot y offset)
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "thorax": ((0, 0.25, 0.78), (0, -0.38, 0.84), "root"),
    "head": ((0, -0.38, 0.86), (0, -0.9, 0.8), "thorax"),
    "gaster": ((0, 0.25, 0.78), (0, 1.3, 0.66), "thorax"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"jaw.{side}"] = ((0.13 * sx, -0.82, 0.72), (0.06 * sx, -1.32, 0.68), "head")
    BONES[f"feeler.{side}"] = ((0.12 * sx, -0.66, 0.98), (0.45 * sx, -1.0, 1.38), "head")
    BONES[f"feeler2.{side}"] = ((0.45 * sx, -1.0, 1.38), (0.62 * sx, -1.5, 1.22), f"feeler.{side}")
    for i, (hy, ky, fy) in enumerate(LEGS):
        BONES[f"femur{i}.{side}"] = ((0.16 * sx, hy, 0.74), (0.62 * sx, hy + ky, 1.02), "thorax")
        BONES[f"tibia{i}.{side}"] = ((0.62 * sx, hy + ky, 1.02), (0.98 * sx, hy + fy, 0.02), f"femur{i}.{side}")


def build_body():
    b = Body("GenieAnt")
    shine = lambda f: CHITIN_SHINE if f.calc_center_median().z > 0.95 and abs(f.calc_center_median().x) < 0.2 else CHITIN
    # head: blind, broad, heavy; a crown of gold beads
    b.ball("head", shine, mat_at((0, -0.62, 0.86), scale=(1.15, 1.0, 0.82)), 0.3, segs=(10, 7))
    b.box("head", CHITIN_DARK, mat_at((0, -0.86, 0.78), rot=(-10, 0, 0)), (0.28, 0.08, 0.1))      # clypeus
    for k in range(7):
        a = math.radians(-60 + k * 20)
        b.gem("head", GOLD, mat_at((math.sin(a) * 0.22, -0.55 + math.cos(a) * 0.06 - 0.06, 1.1 - abs(a) * 0.05)), 0.03, mat=1)
    b.gem("head", GOLD, mat_at((0, -0.72, 1.05)), 0.045, mat=1)
    # sickle jaws, each in two pieces curving in, dark with a sharp tip
    for side, sx in (("L", 1), ("R", -1)):
        p0 = Vector((0.13 * sx, -0.82, 0.72))
        p1 = Vector((0.16 * sx, -1.08, 0.7))
        p2 = Vector((0.04 * sx, -1.34, 0.68))
        b.limb(f"jaw.{side}", JAW, tuple(p0), tuple(p1), 0.05, 0.04, segments=5)
        b.limb(f"jaw.{side}", JAW, tuple(p1), tuple(p2), 0.04, 0.008, segments=5)
        for k in range(3):  # teeth on the inner edge
            t = p0 + (p1 - p0) * (0.3 + k * 0.3)
            b.cone(f"jaw.{side}", JAW, mat_at(tuple(t), rot=(0, -90 * sx, 0)), 0.015, 0.0, 0.06, segments=3)
        # feelers, elbowed
        b.limb(f"feeler.{side}", CHITIN_DARK, (0.12 * sx, -0.66, 0.98), (0.45 * sx, -1.0, 1.38), 0.025, 0.018, segments=4)
        b.limb(f"feeler2.{side}", CHITIN_DARK, (0.45 * sx, -1.0, 1.38), (0.62 * sx, -1.5, 1.22), 0.018, 0.01, segments=4)
    # thorax and the narrow waist
    b.ball("thorax", shine, mat_at((0, -0.08, 0.82), scale=(0.75, 1.5, 0.75)), 0.24, segs=(9, 6))
    b.ball("gaster", CHITIN_DARK, mat_at((0, 0.3, 0.8)), 0.1, segs=(6, 5))                          # petiole node
    # gaster with gold bands
    def gaster(f):
        c = f.calc_center_median()
        return CHITIN_SHINE if c.z > 0.98 else CHITIN
    b.ball("gaster", gaster, mat_at((0, 0.8, 0.74), scale=(0.95, 1.4, 0.85)), 0.4, segs=(12, 8))
    for k in range(3):
        y = 0.55 + k * 0.25
        b.cone("gaster", GOLD, mat_at((0, y, 0.74), rot=(90, 0, 0), scale=(0.95, 0.85, 1)), 0.4 * math.sqrt(max(0.05, 1 - ((y - 0.8) / 0.56) ** 2)) * 1.01,
               0.4 * math.sqrt(max(0.05, 1 - ((y - 0.8) / 0.56) ** 2)) * 1.01, 0.025, segments=12, mat=1)
    # six legs: femur up and out, tibia down to the ground
    for side, sx in (("L", 1), ("R", -1)):
        for i, (hy, ky, fy) in enumerate(LEGS):
            hip = (0.16 * sx, hy, 0.74)
            knee = (0.62 * sx, hy + ky, 1.02)
            foot = (0.98 * sx, hy + fy, 0.02)
            b.limb(f"femur{i}.{side}", CHITIN, hip, knee, 0.05, 0.04, segments=5)
            b.ball(f"femur{i}.{side}", CHITIN_DARK, mat_at(knee), 0.045, segs=(5, 4))
            b.limb(f"tibia{i}.{side}", CHITIN_DARK, knee, foot, 0.035, 0.015, segments=5)
    return b


def leg(arm, i, side, sx, fwd=0.0, lift=0.0):
    return {f"femur{i}.{side}": turned(arm, f"femur{i}.{side}", yaw=-fwd * sx, tilt=-lift * sx)}


def clips(arm):
    A = {}
    feel = lambda a, b_: {"feeler.L": turned(arm, "feeler.L", yaw=a, pitch=b_), "feeler.R": turned(arm, "feeler.R", yaw=-a, pitch=b_)}
    jaws = lambda o: {"jaw.L": turned(arm, "jaw.L", yaw=o), "jaw.R": turned(arm, "jaw.R", yaw=-o)}
    A["Idle"] = add_action(arm, "Idle", [(1, {**feel(0, 0), **jaws(0)}), (15, {**feel(20, -10), **jaws(18)}), (30, {**feel(-15, 8), **jaws(0)}),
                                         (45, {**feel(10, -5), **jaws(14), "gaster": turned(arm, "gaster", pitch=-4)}), (60, {**feel(0, 0), **jaws(0)})])
    def tripod(k):
        p = {**feel(8 * k, 0), "gaster": turned(arm, "gaster", yaw=4 * k)}
        for i, (side, sx) in enumerate((("L", 1), ("R", -1))):
            pass
        a = [("L", 1, 0), ("R", -1, 1), ("L", 1, 2)]
        b_ = [("R", -1, 0), ("L", 1, 1), ("R", -1, 2)]
        for side, sx, i in a:
            p.update(leg(arm, i, side, sx, 22 * k, 14 * max(0, k)))
        for side, sx, i in b_:
            p.update(leg(arm, i, side, sx, -22 * k, 14 * max(0, -k)))
        return p
    A["Walk"] = add_action(arm, "Walk", [(1, tripod(1)), (6, tripod(0)), (11, tripod(-1)), (16, tripod(0)), (21, tripod(1))])
    rear = {"thorax": turned(arm, "thorax", pitch=28), "head": turned(arm, "head", pitch=-10), "gaster": turned(arm, "gaster", pitch=-22),
            **feel(25, 20), **jaws(32), **leg(arm, 0, "L", 1, 40, 45), **leg(arm, 0, "R", -1, 40, 45)}
    A["Grant"] = add_action(arm, "Grant", [(1, {}), (12, rear), (30, {**rear, **jaws(10)}), (42, rear)], loop=False)
    shiver = lambda k: {"gaster": turned(arm, "gaster", yaw=6 * k, pitch=-8), **jaws(30 if k > 0 else 0), **feel(-10, 15 * k),
                        "root": {"rot": (0, 0, 0), "loc": (0, 0.02 * k, 0)}}
    A["Swarm"] = add_action(arm, "Swarm", [(1, shiver(1)), (3, shiver(-1)), (5, shiver(1)), (7, shiver(-1)), (9, shiver(1))])
    return A


def main():
    reset_scene()
    arm = build_armature("GenieAntRig", BONES)
    body = build_body().to_object(vertex_color_material("GenieAnt", roughness=0.35), extra_materials=[glow_material("Glow", GOLD, 5.0)])
    skin_to(body, arm)
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "genie_ant.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(600, 480))
        views = [("Idle", 1, 30, 2.2), ("Idle", 15, 90, 1.4), ("Walk", 1, 60, 2.6), ("Grant", 30, 35, 1.6), ("Swarm", 1, 150, 2.4)]
        shots = []
        for i, (act, fr, ang, h) in enumerate(views):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0.1, 0.75), dist=4.6, height=h)
            p = PREVIEWS_OUT / f"_ga{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "genie-ant.png", cols=5, labels=["Idle", "Side, jaws open", "Walk", "Grant", "Swarm"])


if __name__ == "__main__":
    main()
