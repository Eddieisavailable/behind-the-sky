"""Korto: the blacksmith's daughter of Gbelewala.

Builds the model, rig and animations and exports public/models/korto.glb.
Faces -Y in Blender (Blender's front view); the game turns it to face its own forward.

    python blender/korto.py            # build + export
    python blender/korto.py --preview  # also render turnaround and pose sheets
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, add_action, aim_camera, attach_to_bone,
                 build_armature, contact_sheet, export_glb, hexcol, mat_at, pose_at, prop_object,
                 render_to, reset_scene, rest_pose, setup_preview, skin_to, vertex_color_material)

# ---------- palette ----------
SKIN = hexcol("#5b3a26")
SKIN_DARK = hexcol("#4a2f1f")
LIPS = hexcol("#3d241a")
EYE = hexcol("#16100c")
EYE_WHITE = hexcol("#e9e2d2")
WRAP = hexcol("#b8352a")          # headwrap red
WRAP_GOLD = hexcol("#e0a83a")
TUNIC = hexcol("#c8862f")         # ochre top
TUNIC_DARK = hexcol("#a86c22")
SASH = hexcol("#7a3a1e")
# country cloth: Kpelle hand-woven cotton, strip-woven in stripes
CLOTH = [hexcol("#2d3a6b"), hexcol("#e9dcc0"), hexcol("#2d3a6b"), hexcol("#a4532c"), hexcol("#e9dcc0"), hexcol("#2d3a6b")]
LEATHER = hexcol("#3a2a1c")
IRON = hexcol("#7d868f")
STEEL = hexcol("#c9d1d8")
STEEL_EDGE = hexcol("#eef2f5")
WOOD = hexcol("#5e3d22")
RATTAN = hexcol("#b08454")
FLETCH = hexcol("#e9dcc0")

# ---------- skeleton (metres; character faces -Y, her left is +X) ----------
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.15), None),
    "hips": ((0, 0, 0.88), (0, 0, 1.0), "root"),
    "spine": ((0, 0, 1.0), (0, 0, 1.2), "hips"),
    "chest": ((0, 0, 1.2), (0, 0, 1.4), "spine"),
    "neck": ((0, 0, 1.4), (0, 0, 1.48), "chest"),
    "head": ((0, 0, 1.48), (0, 0, 1.75), "neck"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES.update({
        f"upperarm.{side}": ((0.19 * sx, 0, 1.37), (0.205 * sx, 0, 1.11), "chest"),
        f"forearm.{side}": ((0.205 * sx, 0, 1.11), (0.215 * sx, 0, 0.88), f"upperarm.{side}"),
        f"hand.{side}": ((0.215 * sx, 0, 0.88), (0.215 * sx, 0, 0.79), f"forearm.{side}"),
        f"thigh.{side}": ((0.095 * sx, 0, 0.88), (0.1 * sx, 0, 0.49), "hips"),
        f"shin.{side}": ((0.1 * sx, 0, 0.49), (0.1 * sx, 0, 0.09), f"thigh.{side}"),
        f"foot.{side}": ((0.1 * sx, 0, 0.09), (0.1 * sx, -0.13, 0.03), f"shin.{side}"),
    })


def build_body():
    b = Body("Korto")
    # head
    b.ball("head", SKIN, mat_at((0, -0.005, 1.585), scale=(0.97, 1.0, 1.12)), 0.125, segs=(10, 8))
    b.cone("head", SKIN_DARK, mat_at((0, -0.112, 1.575), rot=(-90, 0, 0)), 0.026, 0.008, 0.045, segments=4)  # nose
    b.box("head", LIPS, mat_at((0, -0.104, 1.525)), (0.05, 0.02, 0.014))
    for sx in (1, -1):
        b.box("head", EYE_WHITE, mat_at((0.045 * sx, -0.111, 1.6)), (0.042, 0.014, 0.026))
        b.box("head", EYE, mat_at((0.045 * sx, -0.117, 1.6)), (0.02, 0.012, 0.026))
        b.box("head", EYE, mat_at((0.045 * sx, -0.112, 1.625), rot=(0, 8 * sx, 0)), (0.05, 0.012, 0.01))  # brow
        b.ball("head", SKIN_DARK, mat_at((0.122 * sx, 0, 1.575), scale=(0.5, 1, 1)), 0.03, segs=(6, 4))  # ears
    # head tie: a lappa cloth wrapped high and round, tilted back, with a fanned knot on top
    stripe = lambda f: WRAP_GOLD if int(f.calc_center_median().z * 60) % 3 == 0 else WRAP
    b.cone("head", WRAP, mat_at((0, 0.01, 1.665)), 0.135, 0.15, 0.07, segments=12)
    b.ball("head", stripe, mat_at((0, 0.035, 1.745), rot=(-18, 0, 0), scale=(1.12, 1.02, 0.62)), 0.15, segs=(12, 7))
    b.ball("head", WRAP, mat_at((0.06, 0.0, 1.705), rot=(0, 0, 20), scale=(0.9, 1.1, 0.5)), 0.11, segs=(8, 5))
    b.cone("head", WRAP_GOLD, mat_at((-0.05, 0.08, 1.83), rot=(-30, -25, 0), scale=(1, 0.35, 1)), 0.03, 0.09, 0.09, segments=6)
    b.cone("head", WRAP, mat_at((0.05, 0.1, 1.82), rot=(-40, 30, 0), scale=(1, 0.35, 1)), 0.025, 0.075, 0.08, segments=6)
    # neck
    b.limb("neck", SKIN, (0, 0, 1.39), (0, 0, 1.49), 0.048)
    # torso: ochre top, darker hem
    hem = lambda f: TUNIC_DARK if f.calc_center_median().z < 1.06 else TUNIC
    b.cone("chest", TUNIC, mat_at((0, 0.005, 1.29), scale=(1, 0.72, 1)), 0.145, 0.19, 0.24, segments=8)
    b.cone("spine", hem, mat_at((0, 0.005, 1.1), scale=(1, 0.74, 1)), 0.155, 0.145, 0.2, segments=8)
    b.cone("hips", SASH, mat_at((0, 0.005, 0.985), scale=(1, 0.78, 1)), 0.168, 0.162, 0.06, segments=8)
    # wrap skirt in striped country cloth, to the knee; wide hem so the legs can stride inside it
    def cloth(f):
        c = f.calc_center_median()
        if c.z < 0.53:
            return SASH
        i = int(((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi)) * 16) % len(CLOTH)
        return CLOTH[i]
    b.cone("hips", cloth, mat_at((0, 0.01, 0.74), scale=(1, 0.86, 1)), 0.255, 0.168, 0.44, segments=16)
    # quiver on the back
    b.limb("chest", RATTAN, (0.06, 0.16, 1.05), (-0.04, 0.17, 1.42), 0.045, 0.05, segments=6)
    for dx in (-0.025, 0.0, 0.025):
        b.limb("chest", WOOD, (-0.03 + dx, 0.17, 1.4), (-0.06 + dx, 0.175, 1.5), 0.006)
        b.cone("chest", FLETCH, mat_at((-0.062 + dx, 0.175, 1.5), rot=(0, -12, 0)), 0.018, 0.0, 0.05, segments=3)
    b.limb("chest", LEATHER, (0.17, -0.09, 1.36), (-0.15, 0.1, 1.05), 0.012, segments=4)  # strap
    # arms and legs
    for side, sx in (("L", 1), ("R", -1)):
        b.ball(f"upperarm.{side}", SKIN, mat_at((0.19 * sx, 0, 1.36)), 0.058, segs=(8, 6))
        b.limb(f"upperarm.{side}", SKIN, (0.195 * sx, 0, 1.36), (0.205 * sx, 0, 1.11), 0.056, 0.046)
        b.ball(f"forearm.{side}", SKIN, mat_at((0.205 * sx, 0, 1.11)), 0.046, segs=(6, 5))  # elbow
        b.limb(f"forearm.{side}", SKIN, (0.205 * sx, 0, 1.11), (0.215 * sx, 0, 0.9), 0.046, 0.036)
        b.limb(f"forearm.{side}", IRON, (0.214 * sx, 0, 0.935), (0.215 * sx, 0, 0.905), 0.037)  # iron bangle
        b.ball(f"hand.{side}", SKIN, mat_at((0.215 * sx, -0.005, 0.85), scale=(0.8, 1, 1.15)), 0.05, segs=(6, 5))
        b.ball(f"thigh.{side}", SKIN, mat_at((0.1 * sx, 0, 0.62)), 0.078, segs=(8, 5))
        b.limb(f"thigh.{side}", SKIN, (0.097 * sx, 0, 0.8), (0.1 * sx, 0, 0.49), 0.076, 0.058)
        b.ball(f"shin.{side}", SKIN, mat_at((0.1 * sx, 0, 0.49)), 0.057, segs=(6, 5))  # knee
        b.limb(f"shin.{side}", SKIN, (0.1 * sx, 0, 0.49), (0.1 * sx, 0, 0.1), 0.058, 0.04)
        b.limb(f"shin.{side}", IRON, (0.1 * sx, 0, 0.14), (0.1 * sx, 0, 0.115), 0.04)  # anklet
        b.box(f"foot.{side}", LEATHER, mat_at((0.1 * sx, -0.045, 0.03)), (0.085, 0.21, 0.05))
        b.box(f"foot.{side}", SKIN_DARK, mat_at((0.1 * sx, -0.05, 0.065)), (0.07, 0.15, 0.03))
    return b


def build_cutlass(hand=(-0.215, -0.01, 0.85), width=0.05, length=1.0):
    """Held in the right hand, blade forward and down at rest."""
    b = Body("Cutlass")
    hand = Vector(hand)
    down_fwd = Vector((0, -0.55, -1)).normalized()
    grip_end = hand + down_fwd * 0.07
    b.limb("x", WOOD, hand - down_fwd * 0.06, grip_end, 0.016, 0.018)
    b.box("x", IRON, Matrix.Translation(grip_end) @ down_fwd.to_track_quat("Z", "Y").to_matrix().to_4x4(), (0.11, 0.025, 0.02))
    # a broad, slightly curved blade in two pieces, then a clipped tip
    p1 = grip_end + down_fwd * 0.25 * length
    curve = (down_fwd + Vector((0, -0.25, 0.1))).normalized()
    p2 = p1 + curve * 0.25 * length
    for a, c in ((grip_end, p1), (p1, p2)):
        mid = (a + c) / 2
        rot = (c - a).normalized().to_track_quat("Z", "X").to_matrix().to_4x4()
        b.box("x", STEEL, Matrix.Translation(mid) @ rot, (0.008, width, (c - a).length))
    rot = curve.to_track_quat("Z", "X").to_matrix().to_4x4()
    b.cone("x", STEEL_EDGE, Matrix.Translation(p2 + curve * 0.04) @ rot @ Matrix.Diagonal((0.16, 1, 1, 1)), 0.7 * width, 0.002, 0.08, segments=4)
    return b


def build_bow(hand=(0.215, -0.005, 0.85)):
    """Lies along Y through the left hand (bulging down) so it stands upright when the arm is raised to shoot."""
    b = Body("Bow")
    hand = Vector(hand)
    pts = []
    for i in range(9):
        t = -1 + i / 4
        pts.append(hand + Vector((0, t * 0.55, -0.12 * (1 - t * t) + 0.02)))
    for a, c in zip(pts, pts[1:]):
        b.limb("x", WOOD, a, c, 0.014)
    b.limb("x", LEATHER, hand + Vector((0, -0.05, -0.1)), hand + Vector((0, 0.05, -0.1)), 0.02)  # grip wrap
    b.limb("x", FLETCH, pts[0] + Vector((0, 0, 0.0)), pts[-1], 0.003, segments=3)                 # string
    return b


# ---------- animations ----------
def L(side, **kw):
    return {f"{k}.{side}": v for k, v in kw.items()}


def clips(arm):
    A = {}
    # Idle: breathing, a slight weight shift
    A["Idle"] = add_action(arm, "Idle", [
        (1, {"chest": (1, 0, 0), "upperarm.L": (0, 0, -4), "upperarm.R": (0, 0, 4), "forearm.L": (-8, 0, 0), "forearm.R": (-8, 0, 0)}),
        (31, {"chest": (-2, 0, 0), "spine": (0, 2, 0), "head": (2, 0, 0), "upperarm.L": (2, 0, -5), "upperarm.R": (2, 0, 5), "forearm.L": (-12, 0, 0), "forearm.R": (-12, 0, 0),
              "hips": {"loc": (0, -0.006, 0)}}),
        (61, {"chest": (1, 0, 0), "upperarm.L": (0, 0, -4), "upperarm.R": (0, 0, 4), "forearm.L": (-8, 0, 0), "forearm.R": (-8, 0, 0)}),
    ])
    # Run: 0.7 s cycle at 30 fps; legs swing (negative X = forward), arms counter-swing
    def run_pose(lead, trail, bob):
        p = {"spine": (10, 0, 0), "chest": (2, 0, 0), "head": (-8, 0, 0), "hips": {"loc": (0, bob, 0)}}
        p.update(L(lead, thigh=(-40, 0, 0), shin=(20, 0, 0), foot=(10, 0, 0), upperarm=(35, 0, 0), forearm=(-25, 0, 0)))
        p.update(L(trail, thigh=(30, 0, 0), shin=(65, 0, 0), foot=(-15, 0, 0), upperarm=(-40, 0, 0), forearm=(-60, 0, 0)))
        return p
    def pass_pose(up, down, bob):
        p = {"spine": (10, 0, 0), "head": (-8, 0, 0), "hips": {"loc": (0, bob, 0)}}
        p.update(L(up, thigh=(-10, 0, 0), shin=(95, 0, 0), upperarm=(5, 0, 0), forearm=(-45, 0, 0)))
        p.update(L(down, thigh=(5, 0, 0), shin=(5, 0, 0), upperarm=(-5, 0, 0), forearm=(-45, 0, 0)))
        return p
    A["Run"] = add_action(arm, "Run", [
        (1, run_pose("L", "R", -0.02)), (6, pass_pose("R", "L", 0.03)),
        (11, run_pose("R", "L", -0.02)), (16, pass_pose("L", "R", 0.03)), (21, run_pose("L", "R", -0.02)),
    ])
    # Three cutlass blows: right-to-left forehand, left-to-right backhand, overhead chop
    stance = {"thigh.L": (-18, 0, 0), "shin.L": (20, 0, 0), "thigh.R": (12, 0, 0), "shin.R": (14, 0, 0), "spine": (6, 0, 0)}
    def blow(chest_y, arm_x, arm_y, fore_x, extra=None):
        p = dict(stance)
        p.update({"chest": (0, chest_y, 0), "upperarm.R": (arm_x, arm_y, 0), "forearm.R": (fore_x, 0, 0),
                  "upperarm.L": (-25, 0, -15), "forearm.L": (-55, 0, 0)})
        if extra:
            p.update(extra)
        return p
    A["Slash1"] = add_action(arm, "Slash1", [(1, blow(-35, -75, 75, -50)), (4, blow(10, -85, 0, -10)), (8, blow(35, -70, -65, -20))], loop=False)
    A["Slash2"] = add_action(arm, "Slash2", [(1, blow(35, -70, -65, -40)), (4, blow(-5, -85, 10, -10)), (8, blow(-35, -75, 70, -25))], loop=False)
    A["Slash3"] = add_action(arm, "Slash3", [
        (1, blow(-10, -165, 10, -40, {"spine": (-6, 0, 0), "head": (-10, 0, 0)})),
        (6, blow(0, -95, 0, -5, {"spine": (18, 0, 0), "chest": (10, 0, 0)})),
        (12, blow(0, -40, 0, -10, {"spine": (24, 0, 0), "chest": (12, 0, 0), "thigh.L": (-35, 0, 0), "shin.L": (40, 0, 0)})),
    ], loop=False)
    # Roll: a forward tumble, curled up
    tuck = {**L("L", thigh=(-110, 0, 0), shin=(130, 0, 0), upperarm=(-60, 0, 0), forearm=(-90, 0, 0)),
            **L("R", thigh=(-110, 0, 0), shin=(130, 0, 0), upperarm=(-60, 0, 0), forearm=(-90, 0, 0)),
            "spine": (35, 0, 0), "chest": (25, 0, 0), "head": (30, 0, 0)}
    A["Roll"] = add_action(arm, "Roll", [
        (1, {"spine": (20, 0, 0)}),
        (3, {**tuck, "root": (90, 0, 0), "hips": {"loc": (0, -0.35, 0)}}),
        (6, {**tuck, "root": (200, 0, 0), "hips": {"loc": (0, -0.45, 0)}}),
        (8, {**tuck, "root": (300, 0, 0), "hips": {"loc": (0, -0.3, 0)}}),
        (10, {"root": (360, 0, 0), "spine": (12, 0, 0)}),
    ], loop=False)
    # Draw: bow arm up and forward, string hand to the chin
    draw = {"chest": (0, -30, 0), "head": (0, 28, 0), "spine": (4, 0, 0),
            "upperarm.L": (-88, -30, 0), "forearm.L": (0, 0, 0), "hand.L": (0, 0, 0),
            "upperarm.R": (-80, 55, 0), "forearm.R": (-120, 0, 0),
            "thigh.L": (-12, 0, -6), "thigh.R": (10, 0, 6), "shin.R": (8, 0, 0)}
    A["Draw"] = add_action(arm, "Draw", [(1, {"upperarm.L": (-40, 0, 0), "upperarm.R": (-40, 0, 0), "forearm.R": (-40, 0, 0)}), (8, draw), (12, draw)], loop=False)
    # Hurt: knocked back a step
    A["Hurt"] = add_action(arm, "Hurt", [
        (1, {}),
        (3, {"spine": (-14, 0, 0), "chest": (-8, 0, 0), "head": (-15, 0, 0), "upperarm.L": (10, 0, -25), "upperarm.R": (10, 0, 25), "forearm.L": (-30, 0, 0), "forearm.R": (-30, 0, 0)}),
        (9, {}),
    ], loop=False)
    # Death: falls backward and stays down
    A["Death"] = add_action(arm, "Death", [
        (1, {}),
        (6, {"spine": (-20, 0, 0), "head": (-20, 0, 0), "thigh.L": (-15, 0, 0), "shin.L": (40, 0, 0), "thigh.R": (-10, 0, 0), "shin.R": (35, 0, 0), "upperarm.L": (0, 0, -30), "upperarm.R": (0, 0, 30)}),
        (16, {"root": (-88, 0, 0), "spine": (-6, 0, 0), "head": (-10, 0, 10), "thigh.L": (-25, 0, 0), "shin.L": (35, 0, 0), "thigh.R": (5, 0, 0), "shin.R": (10, 0, 0),
              "upperarm.L": (-10, 0, -60), "upperarm.R": (-20, 0, 70), "forearm.L": (-20, 0, 0), "forearm.R": (-10, 0, 0)}),
    ], loop=False)
    # Burn: a quick crouch, fire thrust down at the pile
    A["Burn"] = add_action(arm, "Burn", [
        (1, {}),
        (5, {"spine": (25, 0, 0), "chest": (10, -15, 0), "thigh.L": (-50, 0, 0), "shin.L": (70, 0, 0), "thigh.R": (20, 0, 0), "shin.R": (60, 0, 0),
             "upperarm.R": (-70, 25, 0), "forearm.R": (-10, 0, 0), "hips": {"loc": (0, -0.12, 0)}}),
        (12, {}),
    ], loop=False)
    # Climb: hand over hand up a rattan rope, knees drawn up, leaning into it
    def reach(up):
        dn = "R" if up == "L" else "L"
        return {"spine": (12, 0, 0), "chest": (6, 0, 0), "head": (-18, 0, 0),
                **L(up, upperarm=(-168, 0, 0), forearm=(-20, 0, 0), thigh=(-70, 0, 0), shin=(85, 0, 0)),
                **L(dn, upperarm=(-120, 0, 0), forearm=(-75, 0, 0), thigh=(-20, 0, 0), shin=(40, 0, 0))}
    A["Climb"] = add_action(arm, "Climb", [(1, reach("L")), (13, reach("R")), (25, reach("L"))])
    return A


def main():
    reset_scene()
    arm = build_armature("KortoRig", BONES)
    mat = vertex_color_material("Korto")
    body = build_body().to_object(mat)
    skin_to(body, arm)
    cutlass = prop_object("Cutlass", build_cutlass(), mat)
    attach_to_bone(cutlass, arm, "hand.R", Matrix.Identity(4))
    bow = prop_object("Bow", build_bow(), mat)
    attach_to_bone(bow, arm, "hand.L", Matrix.Identity(4))
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "korto.glb")

    if "--preview" in sys.argv:
        cam = setup_preview()
        bow.hide_render = True
        shots = []
        for i, ang in enumerate((0, 35, 90, 180)):
            aim_camera(cam, ang)
            p = PREVIEWS_OUT / f"_k{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "korto-turnaround.png", cols=4, labels=["Front", "Three-quarter", "Side", "Back"])
        poses = [("Idle", 1), ("Run", 1), ("Run", 6), ("Slash1", 1), ("Slash1", 8), ("Slash3", 1), ("Slash3", 12), ("Roll", 6), ("Draw", 12), ("Burn", 5), ("Hurt", 3), ("Death", 16)]
        shots = []
        aim_camera(cam, 30, dist=4.6, height=1.5)
        for i, (name, frame) in enumerate(poses):
            pose_at(arm, actions[name], frame)
            bow.hide_render = name != "Draw"   # in the game the bow only shows while aiming
            p = PREVIEWS_OUT / f"_p{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "korto-poses.png", cols=6, labels=[f"{n} {f}" for n, f in poses])


if __name__ == "__main__":
    main()
