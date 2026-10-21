"""Sii the spider: Woi's glutton drummer, who beat the slit-drum while the iron was forged.

Stands on top of the slit-drum in the game and beats it with his two front legs.
Exports public/models/sii.glb with "Idle" and "Drum" (one beat per front leg, 100 bpm).

    python blender/sii.py            # build + export
    python blender/sii.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Euler, Vector, add_action, aim_camera, build_armature, contact_sheet,
                 export_glb, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose, setup_preview, simple_material,
                 skin_to, vertex_color_material)

BODY = hexcol("#2a1d14")
BODY_LIGHT = hexcol("#4a3424")
OCHRE = hexcol("#d18a2c")
EYE = hexcol("#0c0a08")
SHINE = hexcol("#f2ead8")
LEG = hexcol("#3a281b")
JOINT = hexcol("#d18a2c")
FANG = hexcol("#e9dcc0")

# legs: front (0) to back (3); (shoulder y, knee reach, foot reach) in metres
LEGS = [(-0.16, (0.32, -0.36), (0.5, -0.62)), (-0.07, (0.4, -0.16), (0.66, -0.26)),
        (0.02, (0.4, 0.1), (0.66, 0.22)), (0.1, (0.32, 0.3), (0.5, 0.56))]

BONES = {
    "root": ((0, 0, 0), (0, 0, 0.1), None),
    "body": ((0, 0.02, 0.36), (0, -0.2, 0.4), "root"),
    "abdomen": ((0, 0.05, 0.4), (0, 0.45, 0.52), "body"),
}
for side, sx in (("L", 1), ("R", -1)):
    for i, (sy, (kx, ky), (fx, fy)) in enumerate(LEGS):
        BONES[f"femur{i}.{side}"] = ((0.11 * sx, sy, 0.36), (kx * sx, ky, 0.62 - i * 0.03), "body")
        BONES[f"tibia{i}.{side}"] = ((kx * sx, ky, 0.62 - i * 0.03), (fx * sx, fy, 0.02), f"femur{i}.{side}")


def build_body():
    b = Body("Sii")
    # a big round glutton's belly with ochre chevrons
    def belly(f):
        c = f.calc_center_median()
        return OCHRE if (int((c.y - 0.05) * 14) % 3 == 0 and abs(c.x) < 0.2 and c.z > 0.45) else BODY_LIGHT if c.z < 0.38 else BODY
    b.ball("abdomen", belly, mat_at((0, 0.3, 0.5), scale=(1, 1.1, 0.95)), 0.3, segs=(12, 8))
    b.ball("body", BODY, mat_at((0, -0.08, 0.4), scale=(1, 1.15, 0.85)), 0.17, segs=(10, 7))
    # eyes: two big glossy ones and four small
    for sx in (1, -1):
        b.ball("body", EYE, mat_at((0.06 * sx, -0.25, 0.47)), 0.05, segs=(8, 6))
        b.ball("body", SHINE, mat_at((0.072 * sx, -0.29, 0.49)), 0.014, segs=(5, 4))
        for k in range(2):
            b.ball("body", EYE, mat_at((0.11 * sx, -0.2 + k * 0.05, 0.5 + k * 0.02)), 0.022, segs=(5, 4))
        b.cone("body", FANG, mat_at((0.035 * sx, -0.26, 0.34), rot=(15, 0, 0)), 0.022, 0.0, 0.08, segments=4)  # fangs
    # legs: a joint ball at each knee
    for side, sx in (("L", 1), ("R", -1)):
        for i, (sy, (kx, ky), (fx, fy)) in enumerate(LEGS):
            knee = (kx * sx, ky, 0.62 - i * 0.03)
            b.limb(f"femur{i}.{side}", LEG, (0.11 * sx, sy, 0.36), knee, 0.035, 0.028, segments=5)
            b.ball(f"femur{i}.{side}", JOINT, mat_at(knee), 0.034, segs=(5, 4))
            b.limb(f"tibia{i}.{side}", LEG, knee, (fx * sx, fy, 0.02), 0.026, 0.012, segments=5)
    return b


def raising_rotation(arm, femur, tibia, deg=30):
    """Find the euler rotation on a femur that lifts its foot highest (rigs differ; this keeps clips honest)."""
    pb = arm.pose.bones[femur]
    def foot_z():
        bpy.context.view_layer.update()
        return (arm.matrix_world @ arm.pose.bones[tibia].tail).z
    base = foot_z()
    best, best_dz = None, -1
    for ax in range(3):
        for sgn in (1, -1):
            e = [0, 0, 0]
            e[ax] = sgn * deg
            pb.rotation_euler = Euler([math.radians(a) for a in e])
            dz = foot_z() - base
            if dz > best_dz:
                best, best_dz = (ax, sgn), dz
    pb.rotation_euler = Euler((0, 0, 0))
    return best


def lift(axis_sign, deg):
    ax, sgn = axis_sign
    e = [0, 0, 0]
    e[ax] = sgn * deg
    return tuple(e)


def clips(arm):
    up = {side: raising_rotation(arm, f"femur0.{side}", f"tibia0.{side}") for side in ("L", "R")}
    knee = {side: raising_rotation(arm, f"tibia0.{side}", f"tibia0.{side}") for side in ("L", "R")}
    A = {}
    breathe = lambda k: {"abdomen": (k * 3, 0, 0), "body": {"loc": (0, 0, 0)}, "root": {"loc": (0, k * 0.01, 0)}}
    A["Idle"] = add_action(arm, "Idle", [(1, breathe(1)), (31, breathe(-1)), (61, breathe(1))])
    # 100 bpm: one beat every 18 frames at 30 fps; left leg on the beat, right leg on the next
    raised = lambda side: {f"femur0.{side}": lift(up[side], 55), f"tibia0.{side}": lift(knee[side], 25)}
    struck = lambda side: {f"femur0.{side}": lift(up[side], -8), f"tibia0.{side}": lift(knee[side], -5)}
    def pose(l, r, bob):
        p = {"root": {"loc": (0, bob, 0)}, "abdomen": (-bob * 60, 0, 0)}
        p.update(l("L"))
        p.update(r("R"))
        return p
    A["Drum"] = add_action(arm, "Drum", [
        (1, pose(struck, raised, -0.02)), (10, pose(raised, raised, 0.02)),
        (19, pose(raised, struck, -0.02)), (28, pose(raised, raised, 0.02)), (37, pose(struck, raised, -0.02)),
    ])
    return A


def main():
    reset_scene()
    arm = build_armature("SiiRig", BONES)
    body = build_body().to_object(vertex_color_material("Sii", roughness=0.5))
    skin_to(body, arm)
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "sii.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(560, 560))
        shots = []
        for i, (ang, act, fr) in enumerate(((0, "Idle", 1), (40, "Idle", 1), (40, "Drum", 10), (40, "Drum", 19), (100, "Drum", 1))):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0, 0.35), dist=2.4, height=1.1)
            p = PREVIEWS_OUT / f"_s{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "sii.png", cols=5, labels=["Front", "Three-quarter", "Drum: both up", "Drum: right strikes", "Drum: left strikes"])


if __name__ == "__main__":
    main()
