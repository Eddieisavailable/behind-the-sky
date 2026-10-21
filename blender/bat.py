"""Night bat: the swarm Meni-maa-fa calls, and the swamp's night hunters.

Modelled on the hammer-headed fruit bat of Liberia's forests (Africa's largest bat: a big,
blunt, horse-like head, lipped muzzle, round ears), darkened and given red ember eyes.
Kept small and light (one mesh, few faces) because the game flies 8 to 12 at once.

Faces -Y, flying level with wings spread at rest; origin at the body's centre.
Clips: Fly (fast flapping), Dive (wings swept back), Fall (struck down, tumbling).

    python blender/bat.py            # build + export public/models/bat.glb
    python blender/bat.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Vector, add_action, aim, aim_camera, build_armature, contact_sheet,
                 export_glb, glow_material, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose, setup_preview,
                 skin_to, turned, vertex_color_material)

FUR = hexcol("#3a2e26")
FUR_LIGHT = hexcol("#5a4636")
MUZZLE = hexcol("#4a3a30")
LIP = hexcol("#6a4a3e")
MEMBRANE = hexcol("#241a16")
MEMBRANE_EDGE = hexcol("#3e2c24")
BONE = hexcol("#4a3a30")
EYE = hexcol("#ff2a1a")

SH = Vector((0.045, -0.04, 0.0))
EL = Vector((0.2, -0.02, 0.01))
TIPS = [Vector((0.44, 0.04, 0.0)), Vector((0.42, 0.17, 0.0)), Vector((0.31, 0.23, 0.0))]
BONES = {
    "root": ((0, 0, -0.05), (0, 0, 0.05), None),
    "body": ((0, 0.1, 0), (0, -0.08, 0.005), "root"),
    "head": ((0, -0.08, 0.005), (0, -0.2, 0.0), "body"),
    "feet": ((0, 0.1, -0.005), (0, 0.2, -0.02), "body"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"wing.{side}"] = ((SH.x * sx, SH.y, SH.z), (EL.x * sx, EL.y, EL.z), "body")
    BONES[f"hand.{side}"] = ((EL.x * sx, EL.y, EL.z), (TIPS[0].x * sx, TIPS[0].y, TIPS[0].z), f"wing.{side}")


def build_body():
    b = Body("Bat")
    b.ball("body", lambda f: FUR_LIGHT if f.calc_center_median().z > 0.02 else FUR, mat_at((0, 0.0, 0), scale=(0.75, 1.55, 0.7)), 0.062, segs=(7, 5))
    # the big blunt head: long box muzzle with heavy lips, round ears
    b.ball("head", FUR, mat_at((0, -0.11, 0.012), scale=(0.85, 1.0, 0.9)), 0.045, segs=(7, 5))
    b.box("head", MUZZLE, mat_at((0, -0.165, 0.0), rot=(-8, 0, 0)), (0.05, 0.08, 0.045))
    b.box("head", LIP, mat_at((0, -0.2, -0.008)), (0.056, 0.02, 0.03))
    for sx in (1, -1):
        b.gem("head", EYE, mat_at((0.024 * sx, -0.135, 0.028)), 0.009, mat=1)
        b.cone("head", MUZZLE, mat_at((0.03 * sx, -0.095, 0.05), rot=(-15, 20 * sx, 0), scale=(1, 0.5, 1)), 0.02, 0.008, 0.04, segments=5)  # ears
    # hind feet trailing
    for sx in (1, -1):
        b.limb("feet", FUR, (0.025 * sx, 0.1, -0.01), (0.03 * sx, 0.17, -0.02), 0.008, 0.005, segments=3)
    # wings: arm bones and fingers, membrane panels between them
    for side, sx in (("L", 1), ("R", -1)):
        m = lambda v, sx=sx: (v.x * sx, v.y, v.z)
        b.limb(f"wing.{side}", BONE, m(SH), m(EL), 0.012, 0.009, segments=4)
        b.panel(f"wing.{side}", MEMBRANE, [m(SH), m(EL), m(Vector((0.19, 0.21, 0.005))), m(Vector((0.04, 0.15, 0.0)))])
        for t in TIPS:
            b.limb(f"hand.{side}", BONE, m(EL), m(t), 0.006, 0.003, segments=3)
        b.panel(f"hand.{side}", MEMBRANE_EDGE, [m(EL), m(TIPS[0]), m(TIPS[1]), m(TIPS[2]), m(Vector((0.19, 0.21, 0.005)))])
        b.cone(f"wing.{side}", BONE, mat_at(m(EL + Vector((0, -0.012, 0.01))), rot=(-80, 0, 0)), 0.008, 0.0, 0.03, segments=3)  # thumb claw
    return b


def clips(arm):
    A = {}
    def flap(up, hand, head=0.0, bob=0.0):
        p = {"head": turned(arm, "head", pitch=head), "root": {"rot": (0, 0, 0), "loc": (0, bob, 0)}}
        for s, sx in (("L", 1), ("R", -1)):
            p[f"wing.{s}"] = aim(arm, f"wing.{s}", (sx, 0.12 * abs(up), up))
            p[f"hand.{s}"] = aim(arm, f"hand.{s}", (sx, 0.25, hand))
        return p
    # 10 frames a beat (3 beats a second): bats flap fast
    A["Fly"] = add_action(arm, "Fly", [(1, flap(0.9, -0.2, 0, -0.02)), (4, flap(0.0, 0.3, 4)), (6, flap(-0.85, 0.35, 0, 0.03)), (9, flap(0.1, -0.4)), (11, flap(0.9, -0.2, 0, -0.02))])
    # Dive: wings swept back half-folded, head down
    swept = {"head": turned(arm, "head", pitch=-10), "body": turned(arm, "body", pitch=-20)}
    for s, sx in (("L", 1), ("R", -1)):
        swept[f"wing.{s}"] = aim(arm, f"wing.{s}", (0.6 * sx, 0.8, 0.2))
        swept[f"hand.{s}"] = aim(arm, f"hand.{s}", (-0.2 * sx, 1.0, 0.0))
    A["Dive"] = add_action(arm, "Dive", [(1, swept), (6, {**swept, "head": turned(arm, "head", pitch=-4)}), (12, swept)])
    # Fall: a broken tumble, one wing limp
    A["Fall"] = add_action(arm, "Fall", [
        (1, flap(0.3, 0.0)),
        (6, {**flap(-0.6, -0.5, 25), "root": {"rot": turned(arm, "root", tilt=90), "loc": (0, 0, 0)}}),
        (12, {**flap(0.7, -0.7, 30), "root": {"rot": turned(arm, "root", tilt=200), "loc": (0, 0, 0)}}),
        (18, {**flap(-0.8, -0.9, 30), "root": {"rot": turned(arm, "root", tilt=300), "loc": (0, 0, 0)}}),
    ], loop=False)
    return A


def main():
    reset_scene()
    arm = build_armature("BatRig", BONES)
    body = build_body().to_object(vertex_color_material("Bat", roughness=0.9), extra_materials=[glow_material("Glow", EYE, 6.0)])
    skin_to(body, arm)
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "bat.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(560, 440))
        views = [("Fly", 1, 20, 0.35, 1.3), ("Fly", 6, 20, 0.35, 1.3), ("Fly", 4, 0, 0.05, 1.0), ("Dive", 1, 60, 0.4, 1.2), ("Fall", 12, 40, 0.3, 1.3)]
        shots = []
        for i, (act, fr, ang, h, dist) in enumerate(views):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0, 0), dist=dist, height=h)
            p = PREVIEWS_OUT / f"_bt{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "bat.png", cols=5, labels=["Fly: wings up", "Fly: wings down", "Face on", "Dive", "Fall"])


if __name__ == "__main__":
    main()
