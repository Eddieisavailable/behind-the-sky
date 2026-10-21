"""The Hornbill Genie: the bush spirit that lends Korto its far sight, for a price.

Modelled on the yellow-casqued hornbill of Liberia's forests (black plumage, white tail
tips, a great yellow casque, a blue throat wattle), grown to spirit size, with ember eyes
and gold spirit marks along the wings and tail (second material, "Glow").
Faces -Y. Rest pose: perched upright, wings spread (so the wing shapes are easy to read).
Clips: Perch (wings folded, looking about), Call (beak open, wings half up), Fly, Glide.

    python blender/hornbill.py            # build + export public/models/hornbill.glb
    python blender/hornbill.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Quaternion, Vector, add_action, aim, aim_camera, build_armature,
                 contact_sheet, export_glb, glow_material, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose,
                 setup_preview, skin_to, turned, vertex_color_material)

BLACK = hexcol("#16171b")
BLACK_SHEEN = hexcol("#232a31")
CHARCOAL = hexcol("#2d2c2e")
WHITE = hexcol("#e8e4da")
CASQUE = hexcol("#e8b931")
CASQUE_DARK = hexcol("#b8851e")
BILL = hexcol("#d9c79a")
BILL_DARK = hexcol("#3a3328")
FACE = hexcol("#3a6fb0")       # bare blue skin round the eye
WATTLE = hexcol("#2f5fb3")     # cobalt throat
LEG = hexcol("#2b2622")
CLAW = hexcol("#d8cdb4")
GOLD = hexcol("#ffc35a")       # spirit marks (glow)

# ---------- skeleton (metres; faces -Y, its left is +X) ----------
SHOULDER = (0.17, -0.06, 0.92)
ELBOW = (0.8, 0.02, 0.92)
TIP = (1.55, 0.12, 0.92)
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.15), None),
    "body": ((0, 0.18, 0.7), (0, -0.16, 0.9), "root"),
    "tail": ((0, 0.22, 0.66), (0, 0.95, 0.38), "body"),
    "neck": ((0, -0.16, 0.92), (0, -0.24, 1.12), "body"),
    "head": ((0, -0.24, 1.12), (0, -0.36, 1.2), "neck"),
    "jaw": ((0, -0.36, 1.14), (0, -0.8, 1.06), "head"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"wing.{side}"] = ((SHOULDER[0] * sx, SHOULDER[1], SHOULDER[2]), (ELBOW[0] * sx, ELBOW[1], ELBOW[2]), "body")
    BONES[f"hand.{side}"] = ((ELBOW[0] * sx, ELBOW[1], ELBOW[2]), (TIP[0] * sx, TIP[1], TIP[2]), f"wing.{side}")
    BONES[f"leg.{side}"] = ((0.09 * sx, 0.02, 0.58), (0.09 * sx, -0.02, 0.1), "body")
    BONES[f"foot.{side}"] = ((0.09 * sx, -0.02, 0.1), (0.09 * sx, -0.14, 0.02), f"leg.{side}")


def build_body():
    b = Body("Hornbill")
    # body: a deep, nose-up barrel of black feathers, sooty belly
    belly = lambda f: CHARCOAL if f.calc_center_median().z < 0.66 and f.calc_center_median().y < 0.1 else BLACK
    b.ball("body", belly, mat_at((0, 0.04, 0.76), rot=(-28, 0, 0), scale=(0.82, 1.3, 0.92)), 0.27, segs=(12, 8))
    for k in range(5):  # shaggy breast feathers
        x = (k - 2) * 0.07
        b.cone("body", BLACK_SHEEN, mat_at((x, -0.2, 0.86 - abs(k - 2) * 0.03), rot=(160, 0, 0), scale=(1, 0.4, 1)), 0.06, 0.0, 0.2, segments=4)
    for sx in (1, -1):  # white feathered thighs
        b.ball("body", WHITE, mat_at((0.1 * sx, 0.04, 0.6), scale=(0.8, 1, 1)), 0.09, segs=(7, 5))
    # neck and head
    b.limb("neck", BLACK, (0, -0.14, 0.9), (0, -0.25, 1.13), 0.11, 0.095, segments=8)
    for k in range(4):  # ruff at the nape
        a = (k - 1.5) * 0.5
        b.cone("neck", BLACK_SHEEN, mat_at((math.sin(a) * 0.08, -0.12, 1.08), rot=(-120, 0, math.degrees(a) * 0.6), scale=(1, 0.4, 1)), 0.05, 0.0, 0.18, segments=4)
    b.ball("head", BLACK, mat_at((0, -0.27, 1.19), scale=(0.88, 1.1, 1.0)), 0.115, segs=(10, 7))
    for sx in (1, -1):
        b.ball("head", FACE, mat_at((0.075 * sx, -0.32, 1.205), scale=(0.5, 1, 0.9)), 0.045, segs=(6, 5))
        b.gem("head", GOLD, mat_at((0.093 * sx, -0.325, 1.21)), 0.022, mat=1)            # ember eye
        b.box("head", BLACK, mat_at((0.085 * sx, -0.325, 1.245), rot=(0, -12 * sx, 0)), (0.05, 0.03, 0.012))  # lash ridge
    # great curved bill (upper) and the casque on top of it
    bill = lambda f: BILL_DARK if f.calc_center_median().y > -0.42 else BILL
    b.cone("head", bill, mat_at((0, -0.6, 1.14), rot=(98, 0, 0), scale=(0.75, 1, 1)), 0.075, 0.012, 0.52, segments=6)
    stripe = lambda f: CASQUE_DARK if int(-f.calc_center_median().y * 22) % 4 == 0 else CASQUE
    b.ball("head", stripe, mat_at((0, -0.47, 1.25), rot=(-6, 0, 0), scale=(0.42, 1.55, 0.62)), 0.15, segs=(10, 7))
    b.cone("head", CASQUE, mat_at((0, -0.67, 1.24), rot=(95, 0, 0), scale=(0.42, 0.62, 1)), 0.08, 0.02, 0.16, segments=6)
    # lower bill and cobalt wattle (jaw bone: opens when it calls)
    b.cone("jaw", BILL, mat_at((0, -0.58, 1.09), rot=(96, 0, 0), scale=(0.7, 0.55, 1)), 0.06, 0.01, 0.46, segments=6)
    b.ball("jaw", WATTLE, mat_at((0, -0.37, 1.07), scale=(0.7, 1.1, 0.8)), 0.06, segs=(7, 5))
    # wings, modelled spread: a broad arm wing and a hand of long fingered primaries
    for side, sx in (("L", 1), ("R", -1)):
        sh = Vector((SHOULDER[0] * sx, SHOULDER[1], SHOULDER[2]))
        el = Vector((ELBOW[0] * sx, ELBOW[1], ELBOW[2]))
        tp = Vector((TIP[0] * sx, TIP[1], TIP[2]))
        mid = (sh + el) / 2
        b.box(f"wing.{side}", BLACK, mat_at(tuple(mid + Vector((0, 0.2, 0))), rot=(0, 0, 7 * sx)), (0.66, 0.46, 0.05))         # secondaries
        b.box(f"wing.{side}", BLACK_SHEEN, mat_at(tuple(mid + Vector((0, 0.03, 0.03))), rot=(0, 0, 7 * sx)), (0.66, 0.16, 0.06))  # coverts
        b.limb(f"wing.{side}", BLACK, tuple(sh), tuple(el), 0.06, 0.045, segments=6)                                           # leading edge
        for k in range(6):  # primaries fan out from the hand
            t = k / 5
            root = el + (tp - el) * (0.15 + 0.7 * t)
            a = math.radians(15 + 55 * t) * sx
            d = Vector((math.cos(a) * sx * sx, math.sin(abs(a)), 0)).normalized()
            d = Vector((sx * math.cos(math.radians(15 + 55 * (1 - t))), math.sin(math.radians(15 + 55 * (1 - t))), 0))
            length = 0.5 + 0.15 * math.sin(t * math.pi)
            c = root + d * (length / 2)
            rot = d.to_track_quat("Y", "Z").to_matrix().to_4x4()
            b.box(f"hand.{side}", BLACK if k % 2 else BLACK_SHEEN, Matrix.Translation(c) @ rot, (0.11, length, 0.03))
        b.limb(f"hand.{side}", BLACK, tuple(el), tuple(tp), 0.045, 0.02, segments=5)
        # spirit marks: a dotted gold line along each wing
        for k in range(7):
            p = sh + (tp - sh) * (0.12 + k * 0.12) + Vector((0, 0.08, 0.035))
            b.gem(f"wing.{side}" if k < 3 else f"hand.{side}", GOLD, mat_at(tuple(p)), 0.022, mat=1)
    # tail: long black feathers with white tips, gold-marked
    for k in range(5):
        x = (k - 2) * 0.07
        tilt = (k - 2) * 4
        root = Vector((x * 0.6, 0.22, 0.66))
        tip = Vector((x * 1.4, 0.98, 0.38))
        c = (root + tip) / 2
        d = (tip - root).normalized()
        rot = d.to_track_quat("Y", "Z").to_matrix().to_4x4()
        tipped = lambda f, tip=tip: WHITE if (f.calc_center_median() - tip).length < 0.2 else BLACK
        b.box("tail", tipped, Matrix.Translation(c) @ rot @ mat_at(rot=(0, tilt, 0)), (0.085, (tip - root).length, 0.025))
        b.gem("tail", GOLD, mat_at(tuple(tip + (root - tip) * 0.32 + Vector((0, 0, 0.02)))), 0.018, mat=1)
    # legs and gripping feet
    for side, sx in (("L", 1), ("R", -1)):
        b.limb(f"leg.{side}", LEG, (0.09 * sx, 0.02, 0.55), (0.09 * sx, -0.02, 0.1), 0.03, 0.022)
        for a in (-25, 0, 25):
            d = Vector((math.sin(math.radians(a)), -math.cos(math.radians(a)), 0))
            base = Vector((0.09 * sx, -0.02, 0.06))
            b.limb(f"foot.{side}", LEG, tuple(base), tuple(base + d * 0.13), 0.018, 0.014)
            b.cone(f"foot.{side}", CLAW, mat_at(tuple(base + d * 0.15 + Vector((0, 0, -0.02))), rot=(math.degrees(math.atan2(-1, 1)), 0, a)), 0.012, 0.0, 0.05, segments=4)
        b.limb(f"foot.{side}", LEG, (0.09 * sx, -0.02, 0.06), (0.09 * sx, 0.1, 0.03), 0.016, 0.012)  # hind toe
    return b


def folded(arm, side, sx):
    """Wing folded back along the flank, turned on edge so it hangs like a cloak."""
    d = Vector((0.18 * sx, 1, -0.22))
    R = arm.data.bones[f"wing.{side}"].matrix_local.to_3x3()
    chord = R.inverted() @ Vector((0, 1, 0))
    best, best_z = 0, 9
    for tw in range(-180, 180, 10):  # pick the twist that turns the trailing edge down
        q = Vector((0, 1, 0)).rotation_difference((R.inverted() @ d).normalized()) @ Quaternion((0, 1, 0), math.radians(tw))
        z = (R @ (q @ chord)).z
        if z < best_z:
            best, best_z = tw, z
    return {f"wing.{side}": aim(arm, f"wing.{side}", d, best), f"hand.{side}": hand_fold(arm, side)}


def hand_fold(arm, side):
    """Flip the hand over onto the arm wing (a turn about the wing's chord), so the primaries
    lie back along the folded wing instead of fanning out."""
    R = arm.data.bones[f"hand.{side}"].matrix_local.to_3x3()
    q = Quaternion((R.inverted() @ Vector((0, 1, 0))).normalized(), math.radians(170))
    return tuple(math.degrees(a) for a in q.to_euler("XYZ"))


def clips(arm):
    A = {}
    wings_in = {**folded(arm, "L", 1), **folded(arm, "R", -1)}

    def perch(yaw, pitch, tail, breathe):
        return {**wings_in, "neck": turned(arm, "neck", yaw * 0.4, pitch * 0.5), "head": turned(arm, "head", yaw * 0.6, pitch),
                "tail": turned(arm, "tail", tail, 0), "body": {"rot": (0, 0, 0), "loc": (0, breathe, 0)}}
    A["Perch"] = add_action(arm, "Perch", [
        (1, perch(0, 0, 0, 0)), (20, perch(35, -5, 4, 0.01)), (34, perch(35, 10, 4, 0.0)),
        (52, perch(-30, 0, -4, 0.01)), (70, perch(-30, -8, -4, 0.0)), (90, perch(0, 0, 0, 0)),
    ])
    open_jaw = {"jaw": turned(arm, "jaw", 0, -24)}
    half_up = {f"wing.{s}": aim(arm, f"wing.{s}", (sx, 0.5, 0.55)) for s, sx in (("L", 1), ("R", -1))}
    half_up.update({f"hand.{s}": aim(arm, f"hand.{s}", (sx, 0.3, -0.35)) for s, sx in (("L", 1), ("R", -1))})
    A["Call"] = add_action(arm, "Call", [
        (1, perch(0, 0, 0, 0)),
        (6, {**half_up, **open_jaw, "neck": turned(arm, "neck", 0, 10), "head": turned(arm, "head", 0, 10), "tail": turned(arm, "tail", 0, 10)}),
        (12, {**half_up, "neck": turned(arm, "neck", 0, 6), "head": turned(arm, "head", 0, 6)}),
        (16, {**half_up, **open_jaw, "neck": turned(arm, "neck", 0, 10), "head": turned(arm, "head", 0, 10)}),
        (26, perch(0, 0, 0, 0)),
    ], loop=False)
    # flight: body levelled, legs tucked back, wings beat; the hand lags the arm wing
    level = {"root": aim(arm, "root", (0, -0.5, 0.87)),
             "neck": turned(arm, "neck", 0, 12), "head": turned(arm, "head", 0, 8),
             "leg.L": aim(arm, "leg.L", (0, 0.9, -0.3)), "leg.R": aim(arm, "leg.R", (0, 0.9, -0.3)),
             "foot.L": aim(arm, "foot.L", (0, 0.4, -1)), "foot.R": aim(arm, "foot.R", (0, 0.4, -1))}
    def beat(arm_z, hand_z, bob):
        p = dict(level)
        for s, sx in (("L", 1), ("R", -1)):
            p[f"wing.{s}"] = aim(arm, f"wing.{s}", (sx, 0.08, arm_z))
            p[f"hand.{s}"] = aim(arm, f"hand.{s}", (sx, 0.05, hand_z))
        p["body"] = {"rot": (0, 0, 0), "loc": (0, bob, 0)}
        return p
    A["Fly"] = add_action(arm, "Fly", [
        (1, beat(0.75, -0.2, -0.04)), (7, beat(0.0, 0.25, 0.0)), (13, beat(-0.7, 0.3, 0.05)), (19, beat(0.0, -0.35, 0.0)), (25, beat(0.75, -0.2, -0.04)),
    ])
    A["Glide"] = add_action(arm, "Glide", [
        (1, beat(0.14, -0.06, 0.0)), (30, beat(0.2, -0.1, 0.03)), (60, beat(0.14, -0.06, 0.0)),
    ])
    return A


def main():
    reset_scene()
    arm = build_armature("HornbillRig", BONES)
    body = build_body().to_object(vertex_color_material("Hornbill", roughness=0.45), extra_materials=[glow_material("Glow", GOLD, 5.0)])
    skin_to(body, arm)
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "hornbill.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(560, 560))
        shots = []
        views = [("Perch", 1, 0, 0.9, 4.0, 1.3), ("Perch", 20, 40, 0.9, 4.0, 1.3), ("Call", 6, 30, 0.9, 4.0, 1.3),
                 ("Fly", 1, 25, 0.8, 5.0, 2.2), ("Fly", 13, 25, 0.8, 5.0, 2.2), ("Glide", 1, 150, 0.8, 5.0, 2.6)]
        for i, (act, fr, ang, tz, dist, h) in enumerate(views):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0, tz), dist=dist, height=h)
            p = PREVIEWS_OUT / f"_h{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "hornbill.png", cols=6,
                      labels=["Perch", "Perch, looking", "Call", "Fly: wings up", "Fly: wings down", "Glide, from behind"])


if __name__ == "__main__":
    main()
