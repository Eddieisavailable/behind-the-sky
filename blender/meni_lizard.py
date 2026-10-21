"""Meni-maa-fa as the Male-Lizard: the boss on the bele tree.

A giant male rainbow agama (the orange-headed, indigo-bodied lizard that does push-ups on every
wall in Liberia) grown monstrous: ember eyes, ash cracks glowing along the flanks, and six hard
back plates. The plates are separate parts named Plate1..Plate6 so the game can knock them off
one at a time with iron arrows (boss phase 2).

Faces -Y, lying flat; the game turns him to cling to the trunk.
Clips: Idle (agama head-bob push-ups), Crawl, Bite, Heal (rears, breathes on a cut branch),
Call (rears high and screams for the bats), Hurt, Fall (drops out of lizard form).

    python blender/meni_lizard.py            # build + export public/models/meni_lizard.glb
    python blender/meni_lizard.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Vector, add_action, aim, aim_camera, build_armature, contact_sheet,
                 export_glb, glow_material, hexcol, jitter, mat_at, pose_at, render_to, reset_scene, rest_pose,
                 setup_preview, skin_to, static_part, turned, vertex_color_material)

HEAD = hexcol("#d9542a")        # agama orange-red
HEAD_LIGHT = hexcol("#ef8a3c")
INDIGO = hexcol("#27306e")
INDIGO_DARK = hexcol("#1a2050")
INDIGO_LIGHT = hexcol("#3d4b98")
BELLY = hexcol("#8c90a6")
CREAM = hexcol("#e6dcc4")
TAIL_ORANGE = hexcol("#d8702c")
TAIL_TIP = hexcol("#3a1c12")
MOUTH = hexcol("#4a1410")
TOOTH = hexcol("#e9dfc8")
CLAW = hexcol("#cfc2a4")
PLATE = hexcol("#35303a")
PLATE_RIM = hexcol("#a8752e")
EMBER = hexcol("#ff5a1f")

BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, 0.5, 0.55), (0, 0.1, 0.6), "root"),
    "spine": ((0, 0.1, 0.6), (0, -0.35, 0.62), "hips"),
    "chest": ((0, -0.35, 0.62), (0, -0.8, 0.66), "spine"),
    "neck": ((0, -0.8, 0.66), (0, -1.1, 0.8), "chest"),
    "head": ((0, -1.1, 0.8), (0, -1.62, 0.76), "neck"),
    "jaw": ((0, -1.16, 0.7), (0, -1.56, 0.64), "head"),
    "tail1": ((0, 0.5, 0.55), (0, 1.15, 0.45), "hips"),
    "tail2": ((0, 1.15, 0.45), (0, 1.85, 0.3), "tail1"),
    "tail3": ((0, 1.85, 0.3), (0, 2.6, 0.17), "tail2"),
    "tail4": ((0, 2.6, 0.17), (0, 3.4, 0.08), "tail3"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"upperarm.{side}"] = ((0.26 * sx, -0.68, 0.56), (0.62 * sx, -0.74, 0.36), "chest")
    BONES[f"forearm.{side}"] = ((0.62 * sx, -0.74, 0.36), (0.66 * sx, -0.86, 0.06), f"upperarm.{side}")
    BONES[f"hand.{side}"] = ((0.66 * sx, -0.86, 0.06), (0.74 * sx, -1.02, 0.02), f"forearm.{side}")
    BONES[f"thigh.{side}"] = ((0.26 * sx, 0.36, 0.5), (0.68 * sx, 0.3, 0.36), "hips")
    BONES[f"shin.{side}"] = ((0.68 * sx, 0.3, 0.36), (0.74 * sx, 0.46, 0.06), f"thigh.{side}")
    BONES[f"foot.{side}"] = ((0.74 * sx, 0.46, 0.06), (0.86 * sx, 0.26, 0.02), f"shin.{side}")

PLATES = [(-0.72, 0.92, "chest", 0.26), (-0.42, 0.98, "chest", 0.3), (-0.1, 1.0, "spine", 0.32),
          (0.22, 0.98, "spine", 0.3), (0.52, 0.9, "hips", 0.27), (0.82, 0.78, "tail1", 0.22)]


def body_colour(f):
    c = f.calc_center_median()
    if c.z < 0.42:
        return BELLY
    # scattered pale scales over the indigo back
    return INDIGO_LIGHT if (int(c.x * 23) + int(c.y * 17)) % 7 == 0 else INDIGO


def build_body():
    b = Body("MeniLizard")
    # trunk in three masses so it can bend
    jitter(b.ball("chest", body_colour, mat_at((0, -0.58, 0.64), scale=(0.82, 1.15, 0.6)), 0.42, segs=(12, 8)), 0.012, 1)
    jitter(b.ball("spine", body_colour, mat_at((0, -0.12, 0.62), scale=(0.88, 1.2, 0.6)), 0.44, segs=(12, 8)), 0.012, 2)
    jitter(b.ball("hips", body_colour, mat_at((0, 0.36, 0.58), scale=(0.76, 1.05, 0.56)), 0.4, segs=(12, 8)), 0.012, 3)
    # ash cracks: ember seams glowing along both flanks
    for sx in (1, -1):
        for k in range(7):
            y = -0.75 + k * 0.22
            b.box("chest" if y < -0.35 else "spine" if y < 0.15 else "hips", EMBER,
                  mat_at((0.33 * sx, y, 0.6 + (k % 2) * 0.05), rot=(0, 20 * sx, 25 * ((k % 3) - 1))), (0.02, 0.16, 0.025), mat=1)
    # neck and the orange agama head, wedge-shaped, with a spiny crest at the nape
    b.limb("neck", HEAD, (0, -0.82, 0.68), (0, -1.12, 0.8), 0.27, 0.22, segments=9)
    jitter(b.ball("head", HEAD, mat_at((0, -1.3, 0.83), scale=(0.9, 1.3, 0.62)), 0.26, segs=(10, 7)), 0.01, 4)
    b.cone("head", HEAD_LIGHT, mat_at((0, -1.5, 0.79), rot=(96, 0, 0), scale=(1, 0.6, 1)), 0.17, 0.07, 0.26, segments=7)  # snout
    for k in range(6):
        b.cone("neck" if k > 2 else "head", HEAD_LIGHT if k % 2 else HEAD, mat_at((0, -1.15 + k * 0.08, 1.0 - k * 0.025), rot=(-20, 0, 0), scale=(0.4, 1, 1)), 0.05, 0.0, 0.16, segments=4)
    for sx in (1, -1):
        b.gem("head", EMBER, mat_at((0.17 * sx, -1.36, 0.9)), 0.05, mat=1)                       # ember eyes
        b.box("head", INDIGO_DARK, mat_at((0.16 * sx, -1.36, 0.95), rot=(0, -15 * sx, 0)), (0.1, 0.09, 0.025))  # brow ridge
        b.ball("head", HEAD_LIGHT, mat_at((0.2 * sx, -1.2, 0.76), scale=(0.4, 1, 1)), 0.06, segs=(6, 4))      # ear opening
        for k in range(4):  # upper teeth
            b.cone("head", TOOTH, mat_at((0.11 * sx, -1.42 - k * 0.05, 0.69), rot=(180, 0, 0)), 0.018, 0.0, 0.06, segments=4)
    # lower jaw, mouth, and a throat pouch
    b.cone("jaw", HEAD_LIGHT, mat_at((0, -1.38, 0.66), rot=(96, 0, 0), scale=(1, 0.42, 1)), 0.2, 0.08, 0.38, segments=7)
    b.box("jaw", MOUTH, mat_at((0, -1.38, 0.71)), (0.24, 0.32, 0.02))
    b.ball("jaw", HEAD, mat_at((0, -1.2, 0.6), scale=(0.8, 1, 0.8)), 0.14, segs=(8, 5))
    for sx in (1, -1):
        for k in range(3):
            b.cone("jaw", TOOTH, mat_at((0.1 * sx, -1.42 - k * 0.05, 0.72)), 0.016, 0.0, 0.05, segments=4)
    # tail: blue at the base, a pale band, orange to a dark tip
    tail = [("tail1", INDIGO, (0, 0.55, 0.55), (0, 1.15, 0.45), 0.3, 0.22), ("tail2", CREAM, (0, 1.15, 0.45), (0, 1.85, 0.3), 0.22, 0.15),
            ("tail3", TAIL_ORANGE, (0, 1.85, 0.3), (0, 2.6, 0.17), 0.15, 0.08), ("tail4", TAIL_TIP, (0, 2.6, 0.17), (0, 3.4, 0.08), 0.08, 0.015)]
    for bone, col, a, c, r1, r2 in tail:
        ring = lambda f, col=col: INDIGO_DARK if col is INDIGO and int(f.calc_center_median().y * 9) % 3 == 0 else col
        b.limb(bone, ring, a, c, r1, r2, segments=8)
    # legs: thick upper limbs, splayed, long-toed clawed feet
    for side, sx in (("L", 1), ("R", -1)):
        for up, low, ft, a, k, f, r in (("upperarm", "forearm", "hand", (0.26, -0.68, 0.56), (0.62, -0.74, 0.36), (0.66, -0.86, 0.06), 0.11),
                                        ("thigh", "shin", "foot", (0.26, 0.36, 0.5), (0.68, 0.3, 0.36), (0.74, 0.46, 0.06), 0.13)):
            A = (a[0] * sx, a[1], a[2]); K = (k[0] * sx, k[1], k[2]); F = (f[0] * sx, f[1], f[2])
            b.limb(f"{up}.{side}", INDIGO, A, K, r, r * 0.8, segments=7)
            b.ball(f"{low}.{side}", INDIGO_DARK, mat_at(K), r * 0.85, segs=(7, 5))
            b.limb(f"{low}.{side}", INDIGO, K, F, r * 0.8, r * 0.55, segments=7)
            fwd = -1 if up == "upperarm" else 1
            for t in range(5):
                ang = math.radians(-60 + t * 30) * sx
                d = Vector((math.sin(ang) * sx * sx, -math.cos(ang) * fwd, 0))
                d = Vector((sx * abs(math.sin(math.radians(-60 + t * 30))) * 0.9 + 0.1 * sx, -math.cos(math.radians(-60 + t * 30)) * fwd * 0.9, 0)).normalized()
                base = Vector(F) + Vector((0, 0, -0.02))
                tip = base + d * (0.2 + 0.05 * (t == 2))
                b.limb(f"{ft}.{side}", INDIGO_DARK, tuple(base), tuple(tip), 0.03, 0.02, segments=4)
                b.cone(f"{ft}.{side}", CLAW, mat_at(tuple(tip + d * 0.03), rot=(0, 0, 0)) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4(), 0.018, 0.0, 0.07, segments=4)
    return b


def build_plate(i, y, z, size):
    """One back plate: a dark ridged shield with a bronze rim, a spike and an ember rune."""
    b = Body(f"Plate{i}")
    jitter(b.cone("x", PLATE, mat_at((0, y, z), rot=(-8, 0, 0), scale=(1.0, 1.3, 1)), size, size * 0.55, 0.12, segments=6), size * 0.05, i)
    b.cone("x", PLATE_RIM, mat_at((0, y, z - 0.05), rot=(-8, 0, 0), scale=(1.0, 1.3, 1)), size * 1.08, size * 1.08, 0.03, segments=6)
    b.cone("x", PLATE, mat_at((0, y + 0.02, z + 0.16), rot=(-25, 0, 0)), size * 0.3, 0.0, size * 0.75, segments=5)
    b.gem("x", EMBER, mat_at((0, y - size * 0.45, z + 0.05)), size * 0.12, mat=1)
    return b


# ---------- animation ----------
def swing(arm, side, sx, up, low, fwd, lift, bend=0.0):
    """A splayed leg: fwd swings the foot forward (+), lift raises it, bend folds the lower leg."""
    return {f"{up}.{side}": turned(arm, f"{up}.{side}", yaw=-fwd * sx, tilt=-lift * sx),
            f"{low}.{side}": turned(arm, f"{low}.{side}", tilt=-bend * sx)}


def clips(arm):
    A = {}
    tail = lambda k: {"tail1": turned(arm, "tail1", yaw=8 * k), "tail2": turned(arm, "tail2", yaw=12 * k),
                      "tail3": turned(arm, "tail3", yaw=16 * k), "tail4": turned(arm, "tail4", yaw=20 * k)}
    legs_rest = {}

    # Idle: the agama push-up display, three bobs then a pause, tail swishing
    def push(up, k):
        p = {"chest": turned(arm, "chest", pitch=10 * up), "neck": turned(arm, "neck", pitch=14 * up), "head": turned(arm, "head", pitch=-12 * up),
             "root": {"rot": (0, 0, 0), "loc": (0, 0.1 * up, 0)}, **tail(k)}
        for s, sx in (("L", 1), ("R", -1)):
            p.update(swing(arm, s, sx, "upperarm", "forearm", 0, -14 * up, -10 * up))
        return p
    A["Idle"] = add_action(arm, "Idle", [(1, push(0, 0)), (7, push(1, 0.5)), (12, push(0, 0.6)), (17, push(1, 0.4)), (22, push(0, 0)),
                                         (27, push(1, -0.4)), (33, push(0, -0.6)), (60, push(0, 0))])

    # Crawl: diagonal pairs, the spine snakes, the tail counter-swings
    def stride(k):
        p = {"hips": turned(arm, "hips", yaw=-10 * k), "chest": turned(arm, "chest", yaw=14 * k), "head": turned(arm, "head", yaw=-10 * k), **tail(-k)}
        p.update(swing(arm, "L", 1, "upperarm", "forearm", 30 * k, 12 * max(0, k)))
        p.update(swing(arm, "R", -1, "thigh", "shin", 30 * k, 12 * max(0, k)))
        p.update(swing(arm, "R", -1, "upperarm", "forearm", -30 * k, 12 * max(0, -k)))
        p.update(swing(arm, "L", 1, "thigh", "shin", -30 * k, 12 * max(0, -k)))
        return p
    A["Crawl"] = add_action(arm, "Crawl", [(1, stride(1)), (7, stride(0)), (13, stride(-1)), (19, stride(0)), (25, stride(1))])

    # Bite: draw back, lunge with the jaw wide, snap shut
    A["Bite"] = add_action(arm, "Bite", [
        (1, {}),
        (6, {"chest": turned(arm, "chest", pitch=8), "neck": turned(arm, "neck", pitch=25), "head": turned(arm, "head", pitch=10), "jaw": turned(arm, "jaw", pitch=-10),
             "root": {"rot": (0, 0, 0), "loc": (0, 0.05, 0)}}),
        (10, {"neck": turned(arm, "neck", pitch=-10), "head": turned(arm, "head", pitch=-8), "jaw": turned(arm, "jaw", pitch=-40),
              "root": {"rot": (0, 0, 0), "loc": (0, 0, 0)}, "hips": {"rot": (0, 0, 0), "loc": (0, 0.25, 0)}}),
        (13, {"neck": turned(arm, "neck", pitch=-12), "head": turned(arm, "head", pitch=-8), "hips": {"rot": (0, 0, 0), "loc": (0, 0.25, 0)}}),
        (22, {}),
    ], loop=False)

    # rearing up on the hind legs, front legs off the ground (shared by Heal and Call)
    def rear(height, jaw, headp):
        p = {"spine": turned(arm, "spine", pitch=22 * height), "chest": turned(arm, "chest", pitch=18 * height),
             "neck": turned(arm, "neck", pitch=10 * height), "head": turned(arm, "head", pitch=headp), "jaw": turned(arm, "jaw", pitch=-jaw),
             "tail1": turned(arm, "tail1", pitch=12 * height), "tail2": turned(arm, "tail2", pitch=-6 * height)}
        for s, sx in (("L", 1), ("R", -1)):
            p[f"upperarm.{s}"] = aim(arm, f"upperarm.{s}", (0.7 * sx, -0.4, -0.55))
            p[f"forearm.{s}"] = turned(arm, f"forearm.{s}", tilt=-30 * sx)
        return p
    A["Heal"] = add_action(arm, "Heal", [(1, rear(0.8, 25, -15)), (15, rear(0.9, 35, -20)), (30, rear(0.8, 25, -15))])
    A["Call"] = add_action(arm, "Call", [(1, {}), (8, rear(1.3, 20, 25)), (14, rear(1.5, 55, 40)), (26, rear(1.5, 55, 40)), (36, {})], loop=False)

    A["Hurt"] = add_action(arm, "Hurt", [
        (1, {}),
        (3, {"chest": turned(arm, "chest", yaw=-15, pitch=8), "neck": turned(arm, "neck", yaw=-20, pitch=15), "head": turned(arm, "head", pitch=20),
             "jaw": turned(arm, "jaw", pitch=-30), **tail(1.5)}),
        (10, {}),
    ], loop=False)

    # Fall: rolls onto his side, legs limp, head down: the lizard form gives out
    limp = {}
    for s, sx in (("L", 1), ("R", -1)):
        limp.update(swing(arm, s, sx, "upperarm", "forearm", 10, 25, 30))
        limp.update(swing(arm, s, sx, "thigh", "shin", -10, 25, 30))
    A["Fall"] = add_action(arm, "Fall", [
        (1, {}),
        (6, {"root": {"rot": turned(arm, "root", tilt=-25), "loc": (0, 0.15, 0)}, "neck": turned(arm, "neck", pitch=20), "jaw": turned(arm, "jaw", pitch=-35)}),
        (16, {**limp, "root": {"rot": turned(arm, "root", tilt=-95), "loc": (0, 0.2, 0)}, "neck": turned(arm, "neck", pitch=-15), "head": turned(arm, "head", pitch=-10),
              "jaw": turned(arm, "jaw", pitch=-20), **tail(-1)}),
    ], loop=False)
    return A


def main():
    reset_scene()
    arm = build_armature("MeniLizardRig", BONES)
    mats = [vertex_color_material("MeniLizard", roughness=0.55), glow_material("Glow", EMBER, 6.0)]
    body = build_body().to_object(mats[0], extra_materials=mats[1:])
    skin_to(body, arm)
    plates = [static_part(f"Plate{i + 1}", build_plate(i + 1, y, z, s), mats, arm, bone) for i, (y, z, bone, s) in enumerate(PLATES)]
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "meni_lizard.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(640, 480))
        views = [("Idle", 1, 35, 1.6, 6.5), ("Idle", 7, 300, 2.2, 6.0), ("Crawl", 1, 90, 3.5, 6.5), ("Bite", 10, 30, 1.6, 6.0),
                 ("Heal", 15, 60, 1.6, 6.5), ("Call", 14, 40, 1.8, 7.0), ("Fall", 16, 20, 2.5, 6.5)]
        shots = []
        for i, (act, fr, ang, h, dist) in enumerate(views):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0.6, 0.6), dist=dist, height=h)
            p = PREVIEWS_OUT / f"_ml{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "meni-lizard.png", cols=4,
                      labels=["Idle", "Push-up, from above", "Crawl (side)", "Bite", "Heal", "Call the bats", "Fall"])


if __name__ == "__main__":
    main()
