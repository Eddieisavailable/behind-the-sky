"""The Rattan Bull: mini-boss at the foot of the new bele tree.

A bull woven of rattan cane by the demons, echoing the bull Yele-lawo stole: an N'Dama-style
humpless body with great lyre horns of bound cane, thorns down the spine, loose strands,
ember eyes deep in a hollow wicker skull and an iron ring through the nose.
It charges, stuns itself on a tree, falls apart, and weaves itself back together.

Faces -Y. Clips: Idle, Walk, Windup (paws the ground), Charge, Stunned, Collapse, Rebuild.

    python blender/rattan_bull.py            # build + export public/models/rattan_bull.glb
    python blender/rattan_bull.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Vector, add_action, aim, aim_camera, build_armature, contact_sheet,
                 export_glb, glow_material, hexcol, jitter, mat_at, pose_at, render_to, reset_scene, rest_pose,
                 setup_preview, skin_to, turned, vertex_color_material)

CANE = hexcol("#b8894f")
CANE_DARK = hexcol("#8a6234")
CANE_PALE = hexcol("#d2aa6c")
BINDING = hexcol("#4f3a22")
THORN = hexcol("#3a2b1a")
VINE = hexcol("#4d6a2a")
HOLLOW = hexcol("#1c120a")
IRON = hexcol("#5a5f66")
EMBER = hexcol("#ffbf3a")

BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "body": ((0, 0.75, 1.12), (0, -0.2, 1.16), "root"),
    "chest": ((0, -0.2, 1.16), (0, -0.78, 1.22), "body"),
    "neck": ((0, -0.78, 1.25), (0, -1.12, 1.32), "chest"),
    "head": ((0, -1.12, 1.32), (0, -1.55, 0.98), "neck"),
    "tail": ((0, 0.82, 1.18), (0, 1.25, 0.6), "body"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"front_up.{side}"] = ((0.27 * sx, -0.6, 1.0), (0.29 * sx, -0.62, 0.52), "chest")
    BONES[f"front_low.{side}"] = ((0.29 * sx, -0.62, 0.52), (0.29 * sx, -0.64, 0.02), f"front_up.{side}")
    BONES[f"back_up.{side}"] = ((0.27 * sx, 0.52, 1.0), (0.29 * sx, 0.62, 0.52), "body")
    BONES[f"back_low.{side}"] = ((0.29 * sx, 0.62, 0.52), (0.29 * sx, 0.58, 0.02), f"back_up.{side}")


def weave(i):
    return lambda f: (CANE if (int((math.atan2(f.calc_center_median().z - 1.15, f.calc_center_median().x) + math.pi) * 7 / math.pi) + i) % 2 else CANE_PALE)


def woven_barrel(b, bone, y0, y1, r0, r1, z, rings):
    """A horizontal section of woven rings along Y with dark bindings and thorns along the top."""
    for i in range(rings):
        t0, t1 = i / rings, (i + 1) / rings
        ya, yb = y0 + (y1 - y0) * t0, y0 + (y1 - y0) * t1
        ra, rb = r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1
        b.cone(bone, weave(i), mat_at((0, (ya + yb) / 2, z), rot=(90, i * 17, 0), scale=(1, 1.1, 1)), ra, rb, abs(yb - ya) * 0.96, segments=9)
        b.cone(bone, BINDING, mat_at((0, yb, z), rot=(90, 0, 0), scale=(1, 1.1, 1)), rb * 1.06, rb * 1.06, 0.035, segments=9)
        b.cone(bone, THORN, mat_at((0, (ya + yb) / 2, z + rb * 1.05), rot=(-15, 0, 0)), 0.04, 0.0, 0.2, segments=4)
        for sx in (1, -1):
            b.cone(bone, THORN, mat_at((rb * 0.95 * sx, (ya + yb) / 2, z + rb * 0.3), rot=(0, 70 * sx, 0)), 0.025, 0.0, 0.12, segments=4)
            for h in (-0.35, 0.25):   # cane strips woven diagonally across the ring
                up = (i % 2) * 2 - 1
                a = Vector((rb * 1.02 * sx, ya, z + rb * (h - 0.18 * up)))
                c = Vector((rb * 1.02 * sx, yb, z + rb * (h + 0.18 * up)))
                b.limb(bone, CANE_DARK, tuple(a), tuple(c), 0.022, segments=4)


def leg(b, up, low, top, knee, hoof, r):
    b.limb(up, CANE_DARK, top, knee, r, r * 0.8, segments=7)
    for k in range(3):  # bundled canes
        off = Vector((math.cos(k * 2.1) * r * 0.5, math.sin(k * 2.1) * r * 0.5, 0))
        b.limb(up, CANE, tuple(Vector(top) + off), tuple(Vector(knee) + off * 0.7), r * 0.4, r * 0.3, segments=5)
    b.limb(up, BINDING, tuple(Vector(knee) + Vector((0, 0, 0.06))), tuple(Vector(knee) - Vector((0, 0, 0.0))), r * 0.9, segments=7)
    b.limb(low, CANE, knee, hoof, r * 0.7, r * 0.5, segments=7)
    b.limb(low, BINDING, tuple(Vector(hoof) + Vector((0, 0, 0.16))), tuple(Vector(hoof) + Vector((0, 0, 0.1))), r * 0.62, segments=7)
    b.cone(low, HOLLOW, mat_at(tuple(Vector(hoof) + Vector((0, -0.02, 0.05)))), r * 0.75, r * 0.6, 0.1, segments=6)  # hoof


def build_body():
    b = Body("RattanBull")
    woven_barrel(b, "body", 0.8, -0.2, 0.42, 0.5, 1.12, 5)
    woven_barrel(b, "chest", -0.2, -0.82, 0.52, 0.46, 1.16, 3)
    # dewlap of hanging vines under the chest
    for k in range(5):
        x = (k - 2) * 0.08
        b.limb("chest", VINE, (x, -0.7 + k * 0.05, 0.75), (x * 1.3, -0.72 + k * 0.05, 0.45 - (k % 2) * 0.08), 0.025, 0.01, segments=4)
    # neck and skull
    b.limb("neck", CANE_DARK, (0, -0.76, 1.24), (0, -1.12, 1.32), 0.36, 0.3, segments=9)
    for k in range(3):
        b.limb("neck", BINDING, (0, -0.84 - k * 0.1, 1.26 + k * 0.02), (0, -0.86 - k * 0.1, 1.265 + k * 0.02), 0.37 - k * 0.02, segments=9)
    skull = lambda f: CANE_PALE if int(f.calc_center_median().z * 18) % 2 else CANE
    b.cone("head", skull, mat_at((0, -1.3, 1.18), rot=(128, 0, 0), scale=(1, 0.85, 1)), 0.27, 0.15, 0.55, segments=8)
    b.cone("head", CANE_DARK, mat_at((0, -1.16, 1.36), rot=(100, 0, 0), scale=(1, 0.7, 1)), 0.25, 0.22, 0.14, segments=8)  # brow
    b.box("head", HOLLOW, mat_at((0, -1.52, 0.97), rot=(-38, 0, 0)), (0.2, 0.06, 0.14))            # muzzle hollow
    b.limb("head", IRON, (-0.06, -1.56, 0.92), (0.06, -1.56, 0.92), 0.035, segments=6)              # nose ring
    for sx in (1, -1):
        b.ball("head", HOLLOW, mat_at((0.165 * sx, -1.26, 1.24), scale=(0.7, 1, 1)), 0.075, segs=(7, 5))
        b.gem("head", EMBER, mat_at((0.17 * sx, -1.33, 1.235)), 0.048, mat=1)                         # ember eyes in the hollows
        b.cone("head", CANE, mat_at((0.25 * sx, -1.15, 1.3), rot=(0, 80 * sx, -20 * sx), scale=(1, 0.4, 1)), 0.07, 0.01, 0.2, segments=4)  # ears
        # lyre horns: out, up, then in, three bound sections, thorns at the tips
        pts = [Vector((0.16 * sx, -1.12, 1.42)), Vector((0.62 * sx, -1.16, 1.48)), Vector((0.88 * sx, -1.28, 1.76)), Vector((0.72 * sx, -1.46, 2.02))]
        for k, (a, c) in enumerate(zip(pts, pts[1:])):
            b.limb("head", CANE_DARK if k % 2 else CANE, tuple(a), tuple(c), 0.11 - k * 0.028, 0.085 - k * 0.028, segments=6)
            b.limb("head", BINDING, tuple(c + (a - c) * 0.1), tuple(c), 0.075 - k * 0.025, segments=6)
        b.cone("head", THORN, mat_at(tuple(pts[-1]), rot=(-20, -25 * sx, 0)), 0.03, 0.0, 0.18, segments=4)
    # loose strands springing out of the weave: it's barely holding together
    for k, (bone, y, z, a) in enumerate((("body", 0.5, 1.5, 30), ("body", 0.1, 1.58, -40), ("chest", -0.4, 1.62, 20), ("body", 0.7, 1.35, -70), ("chest", -0.6, 1.55, 60))):
        base = Vector((0.1 * (1 if k % 2 else -1), y, z))
        tip = base + Vector((math.sin(math.radians(a)) * 0.35, 0.15, 0.25))
        b.limb(bone, CANE_PALE, tuple(base), tuple(tip), 0.015, 0.006, segments=3)
    # tail of twisted vine with a leafy tuft
    b.limb("tail", CANE_DARK, (0, 0.82, 1.18), (0, 1.25, 0.6), 0.05, 0.03, segments=5)
    for k in range(4):
        a = k * 1.6
        b.cone("tail", VINE, mat_at((math.cos(a) * 0.04, 1.27, 0.52), rot=(180 + math.cos(a) * 20, math.sin(a) * 20, 0), scale=(1, 0.4, 1)), 0.05, 0.0, 0.24, segments=4)
    for side, sx in (("L", 1), ("R", -1)):
        leg(b, f"front_up.{side}", f"front_low.{side}", (0.27 * sx, -0.6, 1.0), (0.29 * sx, -0.62, 0.52), (0.29 * sx, -0.64, 0.02), 0.13)
        leg(b, f"back_up.{side}", f"back_low.{side}", (0.27 * sx, 0.52, 1.0), (0.29 * sx, 0.62, 0.52), (0.29 * sx, 0.58, 0.02), 0.14)
    return b


def clips(arm):
    A = {}
    # legs swing about X: negative = forward for these downward bones
    def legs(fl, fr, bl, br, knee=0):
        p = {}
        for s, a in (("L", fl), ("R", fr)):
            p[f"front_up.{s}"] = (a, 0, 0)
            p[f"front_low.{s}"] = (max(0, a) * 0.0 + (35 if a < -10 else 0) + knee, 0, 0)
        for s, a in (("L", bl), ("R", br)):
            p[f"back_up.{s}"] = (a, 0, 0)
            p[f"back_low.{s}"] = (-(25 if a < -5 else 0) - knee, 0, 0)
        return p
    head = lambda pitch, yaw=0: {"neck": turned(arm, "neck", yaw=yaw * 0.5, pitch=pitch * 0.5), "head": turned(arm, "head", yaw=yaw * 0.5, pitch=pitch * 0.5)}
    tail = lambda k: {"tail": turned(arm, "tail", yaw=25 * k, pitch=10 * abs(k))}
    lift = lambda z: {"root": {"rot": (0, 0, 0), "loc": (0, z, 0)}}

    A["Idle"] = add_action(arm, "Idle", [(1, {**head(0), **tail(0.3)}), (25, {**head(-6, 10), **tail(-0.5), **lift(0.02)}),
                                         (40, {**head(14, -6), **tail(0.6)}), (60, {**head(0), **tail(0.3)})])
    A["Walk"] = add_action(arm, "Walk", [
        (1, {**legs(-22, 18, 18, -22), **head(-4), **tail(0.3)}), (9, {**legs(0, 0, 0, 0, 15), **lift(0.03)}),
        (17, {**legs(18, -22, -22, 18), **head(-4), **tail(-0.3)}), (25, {**legs(0, 0, 0, 0, 15), **lift(0.03)}),
        (33, {**legs(-22, 18, 18, -22), **head(-4), **tail(0.3)}),
    ])
    # Windup: head low, horns forward, a front hoof scraping the ground twice
    low = {**head(-34), "chest": turned(arm, "chest", pitch=-8), **tail(0.8)}
    A["Windup"] = add_action(arm, "Windup", [
        (1, {**low, **legs(0, 0, 0, 0)}), (6, {**low, **legs(-30, 0, 0, 0)}), (11, {**low, **legs(25, 0, 0, 0)}),
        (16, {**low, **legs(-30, 0, 0, 0)}), (21, {**low, **legs(25, 0, 0, 0)}), (26, {**low, **legs(0, 0, -10, -10, 10), **lift(-0.06)}),
    ], loop=False)
    # Charge: a gallop with the horns levelled
    A["Charge"] = add_action(arm, "Charge", [
        (1, {**head(-30), **legs(-45, -35, 40, 30), "body": turned(arm, "body", pitch=5), **tail(1)}),
        (5, {**head(-26), **legs(10, 20, -30, -40, 20), **lift(0.18), "body": turned(arm, "body", pitch=-6), **tail(1.2)}),
        (9, {**head(-30), **legs(-45, -35, 40, 30), "body": turned(arm, "body", pitch=5), **tail(1)}),
    ])
    # Stunned: head hangs and sways, legs splayed, swaying on its feet
    daze = lambda k: {**head(-40, 22 * k), "body": turned(arm, "body", yaw=0, tilt=6 * k), "front_up.L": (0, 0, 10), "front_up.R": (0, 0, -10),
                      "back_up.L": (0, 0, 8), "back_up.R": (0, 0, -8), **tail(-0.2), **lift(-0.05)}
    A["Stunned"] = add_action(arm, "Stunned", [(1, daze(1)), (20, daze(-1)), (40, daze(1))])
    # Collapse: the weave gives, legs splay out, body drops to the ground
    heap = {**head(-55, 25), "body": turned(arm, "body", tilt=-12), "chest": turned(arm, "chest", pitch=-10),
            "front_up.L": (-40, 0, 55), "front_up.R": (-40, 0, -55), "front_low.L": (60, 0, 0), "front_low.R": (60, 0, 0),
            "back_up.L": (35, 0, 50), "back_up.R": (35, 0, -50), "back_low.L": (-50, 0, 0), "back_low.R": (-50, 0, 0),
            "tail": turned(arm, "tail", yaw=40, pitch=-20), **lift(-0.72)}
    A["Collapse"] = add_action(arm, "Collapse", [(1, {}), (5, {**head(-30), **lift(-0.25), "front_up.L": (-20, 0, 25), "front_up.R": (-20, 0, -25)}), (14, heap)], loop=False)
    A["Rebuild"] = add_action(arm, "Rebuild", [(1, {}), (5, {**head(-30), **lift(-0.25), "front_up.L": (-20, 0, 25), "front_up.R": (-20, 0, -25)}), (30, heap)],
                              loop=False, reverse=True)
    return A


def main():
    reset_scene()
    arm = build_armature("RattanBullRig", BONES)
    body = build_body().to_object(vertex_color_material("RattanBull", roughness=0.85), extra_materials=[glow_material("Glow", EMBER, 6.0)])
    skin_to(body, arm)
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "rattan_bull.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(600, 520))
        views = [("Idle", 1, 30, 2.0, 6.0), ("Idle", 1, 100, 1.6, 6.0), ("Walk", 1, 90, 1.6, 6.0), ("Windup", 11, 30, 1.8, 6.0),
                 ("Charge", 5, 70, 1.8, 6.5), ("Stunned", 1, 25, 2.0, 6.0), ("Collapse", 14, 30, 2.4, 6.0), ("Rebuild", 20, 30, 2.2, 6.0)]
        shots = []
        for i, (act, fr, ang, h, dist) in enumerate(views):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0, 0.95), dist=dist, height=h)
            p = PREVIEWS_OUT / f"_rb{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "rattan-bull.png", cols=4,
                      labels=["Idle", "Side", "Walk", "Windup: pawing", "Charge", "Stunned", "Collapsed", "Rebuilding"])


if __name__ == "__main__":
    main()
