"""Kelema-ninga: the female firebird in beads and a red headscarf, who defeated the tyrant Gemila.

She lands at the end of the slice with news from behind the sky ("Woi is calling for you").
A tall woman with great wings of fire-coloured feathers (gold at the shoulder, orange, then red,
the tips glowing like embers), a red headscarf with gold, strings of beads everywhere, a feathered
bodice and skirt, long tail plumes, beaded anklets.

Korto's skeleton layout, a little taller, plus wing bones from the shoulder blades.
Clips: Idle (wings folded like a cloak), Fly (hovering), Land, Speak (wings half open).

    python blender/kelema.py            # build + export public/models/kelema.glb
    python blender/kelema.py --preview  # also render a preview sheet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korto
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, add_action, aim, aim_camera, aim_edge, build_armature,
                 contact_sheet, export_glb, glow_material, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose,
                 setup_preview, skin_to, vertex_color_material)

SKIN = hexcol("#5a3822")
SKIN_DARK = hexcol("#46291a")
LIPS = hexcol("#3d2219")
SCARF = hexcol("#c22a20")
SCARF_GOLD = hexcol("#e8b23a")
GOLDF = hexcol("#f0b83a")       # feathers at the shoulder
ORANGE = hexcol("#e8742a")
RED = hexcol("#b8251c")
EMBER = hexcol("#ffcf5a")
BEADS = [hexcol("#c22a20"), hexcol("#f0b83a"), hexcol("#f2ecdc"), hexcol("#2d6a8a"), hexcol("#1c1814")]
EYE = korto.EYE
EYE_WHITE = korto.EYE_WHITE

K = 1.04
BONES = {n: (tuple(v * K for v in h), tuple(v * K for v in t), p) for n, (h, t, p) in korto.BONES.items()}
SH = Vector((0.1, 0.12, 1.36)) * K
EL = Vector((0.7, 0.22, 1.55)) * K
TIP = Vector((1.45, 0.3, 1.35)) * K
for side, sx in (("L", 1), ("R", -1)):
    BONES[f"wing.{side}"] = ((SH.x * sx, SH.y, SH.z), (EL.x * sx, EL.y, EL.z), "chest")
    BONES[f"wingtip.{side}"] = ((EL.x * sx, EL.y, EL.z), (TIP.x * sx, TIP.y, TIP.z), f"wing.{side}")
L = korto.L


def P(x, y, z):
    return (x * K, y * K, z * K)


def fire(t):
    """Feather colour along a wing or plume, 0 at the root, 1 at the tip."""
    return GOLDF if t < 0.33 else ORANGE if t < 0.7 else RED


def build_body():
    b = Body("Kelema")
    b.ball("head", SKIN, mat_at(P(0, -0.005, 1.585), scale=(0.95, 1.0, 1.12)), 0.123 * K, segs=(10, 8))
    b.cone("head", SKIN_DARK, mat_at(P(0, -0.112, 1.575), rot=(-90, 0, 0)), 0.024 * K, 0.008 * K, 0.04 * K, segments=4)
    b.box("head", LIPS, mat_at(P(0, -0.103, 1.525)), (0.048 * K, 0.02 * K, 0.014 * K))
    for sx in (1, -1):
        b.box("head", EYE_WHITE, mat_at(P(0.044 * sx, -0.11, 1.6)), (0.04 * K, 0.014 * K, 0.022 * K))
        b.gem("head", EMBER, mat_at(P(0.044 * sx, -0.116, 1.6)), 0.011 * K, mat=1)
        b.box("head", EYE, mat_at(P(0.044 * sx, -0.11, 1.625), rot=(0, 10 * sx, 0)), (0.05 * K, 0.012 * K, 0.01 * K))
        for k in range(3):   # bead strings hanging from the scarf by her face
            b.gem("head", BEADS[k % 5], mat_at(P(0.125 * sx, -0.03, 1.6 - k * 0.035)), 0.012 * K)
    # red headscarf, tied high, gold-edged, with a fanned knot
    edge = lambda f: SCARF_GOLD if int(f.calc_center_median().z * 50) % 4 == 0 else SCARF
    b.cone("head", SCARF, mat_at(P(0, 0.01, 1.665)), 0.135 * K, 0.15 * K, 0.07 * K, segments=12)
    b.ball("head", edge, mat_at(P(0, 0.03, 1.75), rot=(-15, 0, 0), scale=(1.1, 1.05, 0.7)), 0.15 * K, segs=(12, 7))
    for sx in (1, -1):
        b.cone("head", SCARF, mat_at(P(0.06 * sx, 0.1, 1.84), rot=(-35, 30 * sx, 0), scale=(1, 0.35, 1)), 0.03 * K, 0.09 * K, 0.11 * K, segments=6)
    b.limb("neck", SKIN, P(0, 0, 1.39), P(0, 0, 1.49), 0.045 * K)
    # many strings of beads at the throat
    for k in range(5):
        r = 0.065 + k * 0.012
        for j in range(12):
            a = math.radians(-180 + j * 30)
            b.gem("neck" if k < 3 else "chest", BEADS[(j + k) % 5], mat_at(P(math.sin(a) * r, -math.cos(a) * r, 1.42 - k * 0.018)), 0.01 * K)
    # feathered bodice, beaded belt, layered feather skirt
    rows = lambda f: (GOLDF, ORANGE, RED)[int(f.calc_center_median().z * 25) % 3]
    b.cone("chest", rows, mat_at(P(0, 0.005, 1.28), scale=(1, 0.72, 1)), 0.14 * K, 0.17 * K, 0.24 * K, segments=10)
    b.cone("spine", SKIN, mat_at(P(0, 0.005, 1.1), scale=(1, 0.72, 1)), 0.14 * K, 0.135 * K, 0.18 * K, segments=8)
    b.cone("hips", lambda f: BEADS[int((math.atan2(f.calc_center_median().y, f.calc_center_median().x) + 3.2) * 4) % 5],
           mat_at(P(0, 0.005, 0.99), scale=(1, 0.78, 1)), 0.165 * K, 0.16 * K, 0.06 * K, segments=16)
    for layer, (z, r1, r2, d) in enumerate(((0.86, 0.24, 0.17, 0.2), (0.72, 0.27, 0.2, 0.22), (0.6, 0.29, 0.24, 0.2))):
        col = (GOLDF, ORANGE, RED)[layer]
        b.cone("hips", col, mat_at(P(0, 0.01, z), scale=(1, 0.86, 1)), r1 * K, r2 * K, d * K, segments=10)
    # long tail plumes trailing behind, ember-tipped
    for k in range(3):
        a = (k - 1) * 0.12
        root = Vector(P(a, 0.12, 0.92))
        tip = Vector(P(a * 3, 0.85, 0.15))
        mid = (root + tip) / 2
        d = (tip - root).normalized()
        b.box("hips", ORANGE if k == 1 else RED, Matrix.Translation(mid) @ d.to_track_quat("Y", "Z").to_matrix().to_4x4(), (0.07 * K, (tip - root).length, 0.015 * K))
        b.gem("hips", EMBER, mat_at(tuple(tip)), 0.03 * K, mat=1)
    for side, sx in (("L", 1), ("R", -1)):
        b.ball(f"upperarm.{side}", GOLDF, mat_at(P(0.19 * sx, 0, 1.36)), 0.055 * K, segs=(8, 6))
        b.limb(f"upperarm.{side}", SKIN, P(0.195 * sx, 0, 1.35), P(0.205 * sx, 0, 1.11), 0.046 * K, 0.04 * K)
        b.limb(f"forearm.{side}", SKIN, P(0.205 * sx, 0, 1.11), P(0.215 * sx, 0, 0.9), 0.04 * K, 0.032 * K)
        for k in range(4):
            b.gem(f"forearm.{side}", BEADS[k % 5], mat_at(P(0.215 * sx, -0.03, 0.95 - k * 0.012)), 0.01 * K)
        b.ball(f"hand.{side}", SKIN, mat_at(P(0.215 * sx, -0.005, 0.85), scale=(0.8, 1, 1.15)), 0.044 * K, segs=(6, 5))
        b.limb(f"thigh.{side}", SKIN, P(0.095 * sx, 0, 0.62), P(0.1 * sx, 0, 0.49), 0.06 * K, 0.055 * K)
        b.limb(f"shin.{side}", SKIN, P(0.1 * sx, 0, 0.49), P(0.1 * sx, 0, 0.1), 0.055 * K, 0.038 * K)
        for k in range(5):
            b.gem(f"shin.{side}", BEADS[(k + 2) % 5], mat_at(P(0.1 * sx + math.cos(k * 1.25) * 0.04, math.sin(k * 1.25) * 0.04, 0.13)), 0.011 * K)
        b.box(f"foot.{side}", SKIN_DARK, mat_at(P(0.1 * sx, -0.05, 0.03)), (0.075 * K, 0.2 * K, 0.045 * K))
        # wings: arm wing and hand wing, feathers fanning back, embers at the tips
        sh = Vector((SH.x * sx, SH.y, SH.z))
        el = Vector((EL.x * sx, EL.y, EL.z))
        tp = Vector((TIP.x * sx, TIP.y, TIP.z))
        b.limb(f"wing.{side}", GOLDF, tuple(sh), tuple(el), 0.05, 0.04, segments=6)
        b.limb(f"wingtip.{side}", ORANGE, tuple(el), tuple(tp), 0.04, 0.015, segments=5)
        for k in range(5):  # secondaries on the arm wing
            t = k / 4
            root = sh + (el - sh) * (0.1 + 0.85 * t)
            d = Vector((0.12 * sx, 1, -0.15)).normalized()
            length = 0.35 + 0.12 * t
            for j, frac in enumerate((0.33, 0.33, 0.34)):
                a = root + d * (length * sum((0.33, 0.33, 0.34)[:j]))
                c = a + d * (length * frac)
                b.box(f"wing.{side}", fire((j + 0.5) / 3 * 0.6), Matrix.Translation((a + c) / 2) @ d.to_track_quat("Y", "Z").to_matrix().to_4x4(), (0.16, (c - a).length, 0.02))
        for k in range(6):  # primaries fanning from the hand
            t = k / 5
            root = el + (tp - el) * (0.1 + 0.85 * t)
            ang = math.radians(70 - 55 * t)
            d = Vector((math.cos(ang) * sx * 0.35 + 0.15 * sx * t, math.sin(ang), -0.12)).normalized()
            length = 0.5 + 0.12 * math.sin(t * math.pi)
            for j in range(3):
                a = root + d * (length * j / 3)
                c = root + d * (length * (j + 1) / 3)
                b.box(f"wingtip.{side}", fire(0.3 + (j + 0.5) / 3 * 0.7), Matrix.Translation((a + c) / 2) @ d.to_track_quat("Y", "Z").to_matrix().to_4x4(), (0.14, (c - a).length, 0.02))
            b.gem(f"wingtip.{side}", EMBER, mat_at(tuple(root + d * length)), 0.025, mat=1)
    return b


def clips(arm):
    A = {}
    folded = {}
    for s, sx in (("L", 1), ("R", -1)):
        folded[f"wing.{s}"] = aim_edge(arm, f"wing.{s}", (0.32 * sx, 0.72, -0.62), chord=(0, 1, 0), want=(0, 0.25, -1))
        folded[f"wingtip.{s}"] = aim(arm, f"wingtip.{s}", (sx, 0.25, -0.1))
    stand = lambda k: {**folded, "chest": (k * 2, 0, 0), "head": (-k * 3, 0, k * 4), **L("L", upperarm=(0, 0, -5), forearm=(-15, 0, 0)),
                       **L("R", upperarm=(0, 0, 5), forearm=(-15, 0, 0))}
    A["Idle"] = add_action(arm, "Idle", [(1, stand(0)), (40, stand(1)), (80, stand(0))])

    def beat(z, tipz, bob):
        p = {"hips": {"rot": (0, 0, 0), "loc": (0, bob, 0)}, "spine": (8, 0, 0), "head": (-6, 0, 0),
             **L("L", thigh=(-10, 0, 0), shin=(30, 0, 0), foot=(35, 0, 0), upperarm=(-20, 0, -25), forearm=(-20, 0, 0)),
             **L("R", thigh=(-4, 0, 0), shin=(45, 0, 0), foot=(35, 0, 0), upperarm=(-20, 0, 25), forearm=(-20, 0, 0))}
        for s, sx in (("L", 1), ("R", -1)):
            p[f"wing.{s}"] = aim(arm, f"wing.{s}", (sx, 0.35, z))
            p[f"wingtip.{s}"] = aim(arm, f"wingtip.{s}", (sx, 0.1, tipz))
        return p
    A["Fly"] = add_action(arm, "Fly", [(1, beat(0.85, -0.2, 0.0)), (6, beat(0.1, 0.25, 0.04)), (11, beat(-0.55, 0.3, 0.08)), (16, beat(0.2, -0.3, 0.03)), (21, beat(0.85, -0.2, 0.0))])
    flare = beat(1.1, 0.2, 0)
    for s, sx in (("L", 1), ("R", -1)):
        flare[f"wing.{s}"] = aim(arm, f"wing.{s}", (sx, -0.35, 0.9))
    flare.update(**L("L", thigh=(-20, 0, 0), shin=(10, 0, 0), foot=(10, 0, 0)), **L("R", thigh=(-15, 0, 0), shin=(5, 0, 0), foot=(10, 0, 0)))
    touch = {**folded, "spine": (14, 0, 0), "hips": {"rot": (0, 0, 0), "loc": (0, -0.15, 0)}, **L("L", thigh=(-40, 0, 0), shin=(55, 0, 0)), **L("R", thigh=(-25, 0, 0), shin=(45, 0, 0))}
    for s, sx in (("L", 1), ("R", -1)):
        touch[f"wing.{s}"] = aim(arm, f"wing.{s}", (sx, 0.3, 0.45))
    A["Land"] = add_action(arm, "Land", [(1, {**beat(0.85, -0.2, 0), "root": {"rot": (0, 0, 0), "loc": (0, 1.4, 0)}}),
                                         (10, {**flare, "root": {"rot": (0, 0, 0), "loc": (0, 0.35, 0)}}),
                                         (15, touch), (26, stand(0))], loop=False)
    half = {}
    for s, sx in (("L", 1), ("R", -1)):
        half[f"wing.{s}"] = aim(arm, f"wing.{s}", (sx, 0.55, -0.15))
        half[f"wingtip.{s}"] = aim(arm, f"wingtip.{s}", (sx, 0.25, -0.5))
    talk = lambda k: {**half, "head": (-6, 0, 8 * k), "chest": (-4, 5 * k, 0), **L("R", upperarm=(-50, 0, 20), forearm=(-40 + 15 * k, 0, 0)),
                      **L("L", upperarm=(0, 0, -6), forearm=(-20, 0, 0))}
    A["Speak"] = add_action(arm, "Speak", [(1, talk(1)), (30, talk(-1)), (60, talk(1))])
    return A


def main():
    reset_scene()
    arm = build_armature("KelemaRig", BONES)
    body = build_body().to_object(vertex_color_material("Kelema", roughness=0.6), extra_materials=[glow_material("Glow", EMBER, 6.0)])
    skin_to(body, arm)
    actions = clips(arm)
    rest_pose(arm)
    export_glb(MODELS_OUT / "kelema.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(560, 600))
        views = [("Idle", 1, 0, 0), ("Idle", 1, 150, 0), ("Fly", 1, 25, 0), ("Fly", 11, 25, 0), ("Land", 10, 30, 0), ("Speak", 1, 30, 0)]
        shots = []
        for i, (act, fr, ang, _) in enumerate(views):
            pose_at(arm, actions[act], fr)
            aim_camera(cam, ang, target=(0, 0, 1.05), dist=5.0, height=1.6)
            p = PREVIEWS_OUT / f"_ke{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "kelema.png", cols=6, labels=["Wings folded", "Back", "Fly: wings up", "Fly: wings down", "Landing", "Speak"])


if __name__ == "__main__":
    main()
