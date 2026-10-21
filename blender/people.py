"""The people of Gbelewala: the storyteller-singer, the Chief, Korto's father the blacksmith, and villagers.

One builder makes every person from a short description (height, build, skin, hair or head-tie,
top, wrapper or trousers, props), all on Korto's skeleton layout so they share movements.

Every person can stand, walk, talk, sit, clap and answer "wese" (so any of them can be the
storyteller's audience round the fire), and some have their own work:

  storyteller    fly whisk and seed rattle      Tell, Sing         (the cold open and each "wese")
  chief          carved staff of office         Worry, Speak       ("The seed rice is gone...")
  blacksmith     Korto and Flomo's father       Hammer
  villager_woman baby on her back, pestle       Pound              (pounding rice in a mortar)
  villager_man   rice farmer, short hoe         Hoe
  elder          old woman with a stick
  child

    python blender/people.py            # build + export public/models/<name>.glb for each
    python blender/people.py --preview  # also render preview sheets
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import korto
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, add_action, aim_camera, attach_to_bone, build_armature,
                 contact_sheet, export_glb, hexcol, mat_at, pose_at, render_to, reset_scene, rest_pose, setup_preview,
                 skin_to, vertex_color_material)

L = korto.L
EYE = korto.EYE
EYE_WHITE = korto.EYE_WHITE
H = hexcol
SKINS = {"deep": H("#3e2719"), "brown": H("#5b3a26"), "warm": H("#6b4430"), "old": H("#4a2f20")}
GREY = H("#c9c4ba")
BLACK_HAIR = H("#17110d")
LEATHER = H("#3a2a1c")
WOOD = H("#5e3d22")
WOOD_DARK = H("#3e2716")
IRON = H("#56595e")
BRASS = H("#c9a24a")
COWRIE = H("#ece3cc")
BEADS = [H("#b8352a"), H("#e0a83a"), H("#e8e0cc"), H("#2d6a8a")]
GOURD = H("#c09a52")
RAFFIA = H("#d8c8a0")


def stripes(colors, n=12):
    """Country cloth: strip-woven, so the pattern runs in vertical bands round the body."""
    return lambda f: colors[int(((math.atan2(f.calc_center_median().y, f.calc_center_median().x) + math.pi) / (2 * math.pi)) * n) % len(colors)]


def bands(colors, k=14):
    """Lappa print: horizontal bands."""
    return lambda f: colors[int(f.calc_center_median().z * k) % len(colors)]


PEOPLE = {
    "storyteller": dict(K=1.03, W=1.05, skin="old", hair="cap", hat=[H("#e8e0cc"), H("#2d3a6b")], beard="grey",
                        top="gown", top_cols=[H("#e8e0cc"), H("#2d3a6b"), H("#e8e0cc"), H("#a4532c")], bottom="trousers", bottom_cols=[H("#2d3a6b")],
                        feet="sandals", extras=["necklace"], props=[("Whisk", "whisk", "hand.R"), ("Rattle", "rattle", "hand.L")], special=["Tell", "Sing"]),
    "chief": dict(K=1.08, W=1.12, skin="deep", hair="chief_hat", hat=[H("#7a1f1a"), H("#e0a83a")], beard="grey",
                  top="gown", top_cols=[H("#e0a83a"), H("#1c1814"), H("#7a1f1a"), H("#1c1814")], bottom="trousers", bottom_cols=[H("#1c1814")],
                  feet="sandals", extras=["necklace", "bangles"], props=[("Staff", "staff", "hand.R")], special=["Worry", "Speak"]),
    "blacksmith": dict(K=1.1, W=1.22, skin="deep", hair="short", beard="black", top="apron", bottom="shorts", bottom_cols=[H("#2a2420")],
                       feet="bare", extras=["armbands"], props=[("Hammer", "hammer", "hand.R")], special=["Hammer"]),
    "villager_woman": dict(K=0.98, W=1.0, skin="brown", hair="headtie", hat=[H("#2d6a8a"), H("#e8e0cc")], top="blouse",
                           top_cols=[H("#e0a83a"), H("#2d6a8a"), H("#b8352a")], bottom="wrapper", bottom_cols=[H("#2d6a8a"), H("#e0a83a"), H("#2d6a8a"), H("#e8e0cc")],
                           feet="bare", extras=["baby", "bangles"], props=[("Pestle", "pestle", "hand.R")], special=["Pound"]),
    "villager_man": dict(K=1.03, W=1.08, skin="warm", hair="short", top="shirt", top_cols=[H("#a4532c")], bottom="shorts", bottom_cols=[H("#6a6a52")],
                         feet="bare", extras=[], props=[("Hoe", "hoe", "hand.R")], special=["Hoe"]),
    "elder": dict(K=0.95, W=0.98, skin="old", hair="headtie", hat=[H("#e8e0cc"), H("#7a1f1a")], top="blouse",
                  top_cols=[H("#7a1f1a"), H("#e8e0cc")], bottom="wrapper", bottom_cols=[H("#3a2a1c"), H("#c08a32"), H("#3a2a1c")],
                  feet="bare", extras=["necklace"], props=[("Stick", "stick", "hand.R")], special=[], stoop=True),
    "child": dict(K=0.66, W=1.0, skin="brown", hair="short", top="shirt", top_cols=[H("#e0a83a")], bottom="shorts", bottom_cols=[H("#2d3a6b")],
                  feet="bare", extras=[], props=[], special=[]),
}


class Person:
    def __init__(self, name, spec):
        self.name, self.s = name, spec
        self.K, self.W = spec["K"], spec["W"]
        self.skin = SKINS[spec["skin"]]
        self.dark = tuple(c * 0.8 for c in self.skin[:3]) + (1.0,)
        self.b = Body(name)

    def P(self, x, y, z, arm=False):
        k = self.K
        return (x * k * (self.W if arm else 1), y * k, z * k)

    def R(self, r):
        return r * self.K

    # ---------- body ----------
    def head(self):
        b, P, R, s = self.b, self.P, self.R, self.s
        b.ball("head", self.skin, mat_at(P(0, -0.005, 1.585), scale=(0.96, 1.0, 1.1)), R(0.122), segs=(10, 8))
        b.cone("head", self.dark, mat_at(P(0, -0.112, 1.575), rot=(-90, 0, 0)), R(0.026), R(0.009), R(0.045), segments=4)
        b.box("head", H("#33201a"), mat_at(P(0, -0.104, 1.525)), (R(0.05), R(0.02), R(0.014)))
        brow = GREY if s.get("beard") == "grey" else BLACK_HAIR
        for sx in (1, -1):
            b.box("head", EYE_WHITE, mat_at(P(0.045 * sx, -0.111, 1.6)), (R(0.04), R(0.014), R(0.022)))
            b.box("head", EYE, mat_at(P(0.045 * sx, -0.117, 1.6)), (R(0.019), R(0.012), R(0.022)))
            b.box("head", brow, mat_at(P(0.045 * sx, -0.112, 1.626)), (R(0.05), R(0.012), R(0.011)))
            b.ball("head", self.dark, mat_at(P(0.122 * sx, 0, 1.575), scale=(0.5, 1, 1)), R(0.03), segs=(6, 4))
        hair = s.get("hair")
        col = GREY if s.get("beard") == "grey" else BLACK_HAIR
        if hair in ("short", "chief_hat", "cap"):
            b.ball("head", col, mat_at(P(0, 0.025, 1.675), scale=(1.02, 1.05, 0.55)), R(0.135), segs=(10, 6))
        if hair == "cap":   # a round embroidered cap
            hc = s["hat"]
            b.cone("head", bands(hc, 60), mat_at(P(0, 0.01, 1.71)), R(0.128), R(0.12), R(0.09), segments=12)
        if hair == "chief_hat":   # a tall embroidered chief's cap, folded to one side
            hc = s["hat"]
            b.cone("head", bands(hc, 40), mat_at(P(0, 0.01, 1.74), rot=(0, -8, 0)), R(0.13), R(0.115), R(0.17), segments=12)
            b.cone("head", hc[1], mat_at(P(-0.03, 0.01, 1.83), rot=(0, -25, 0)), R(0.115), R(0.06), R(0.08), segments=12)
        if hair == "headtie":
            hc = s["hat"]
            b.cone("head", hc[0], mat_at(P(0, 0.01, 1.665)), R(0.132), R(0.145), R(0.07), segments=12)
            b.ball("head", bands(hc, 60), mat_at(P(0, 0.03, 1.74), rot=(-15, 0, 0), scale=(1.1, 1.02, 0.62)), R(0.148), segs=(12, 7))
            b.cone("head", hc[0], mat_at(P(0.05, 0.09, 1.82), rot=(-35, 25, 0), scale=(1, 0.35, 1)), R(0.025), R(0.08), R(0.09), segments=6)
        if s.get("beard"):
            b.box("head", col, mat_at(P(0, -0.085, 1.485), rot=(-10, 0, 0)), (R(0.12), R(0.05), R(0.05 if s["beard"] == "black" else 0.08)))
            for sx in (1, -1):
                b.box("head", col, mat_at(P(0.108 * sx, -0.03, 1.53)), (R(0.028), R(0.07), R(0.075)))
        b.limb("neck", self.skin, P(0, 0, 1.39), P(0, 0, 1.49), R(0.046))

    def torso(self):
        b, P, R, s = self.b, self.P, self.R, self.s
        W = self.W
        top, cols = s["top"], s.get("top_cols", [self.skin])
        if top == "gown":    # wide country-cloth gown to the upper thigh, wide sleeves
            pat = stripes(cols, 16)
            b.cone("chest", pat, mat_at(P(0, 0.005, 1.28), scale=(1, 0.72, 1)), R(0.15 * W), R(0.2 * W), R(0.26), segments=12)
            b.cone("spine", pat, mat_at(P(0, 0.005, 1.08), scale=(1, 0.75, 1)), R(0.2 * W), R(0.16 * W), R(0.22), segments=12)
            b.cone("hips", pat, mat_at(P(0, 0.01, 0.83), scale=(1, 0.82, 1)), R(0.26 * W), R(0.2 * W), R(0.28), segments=12)
            for side, sx in (("L", 1), ("R", -1)):
                b.cone(f"upperarm.{side}", pat, mat_at(P(0.2 * sx, 0, 1.24, arm=True)), R(0.1), R(0.07), R(0.24), segments=8)
        elif top in ("shirt", "blouse"):
            pat = bands(cols, 30) if top == "blouse" else cols[0]
            b.cone("chest", pat, mat_at(P(0, 0.005, 1.28), scale=(1, 0.72, 1)), R(0.145 * W), R(0.18 * W), R(0.25), segments=10)
            b.cone("spine", pat, mat_at(P(0, 0.005, 1.08), scale=(1, 0.75, 1)), R(0.16 * W), R(0.15 * W), R(0.22), segments=10)
            for side, sx in (("L", 1), ("R", -1)):
                b.ball(f"upperarm.{side}", pat, mat_at(P(0.19 * sx, 0, 1.33, arm=True), scale=(1, 1, 1.2)), R(0.065 if top == "blouse" else 0.058), segs=(8, 6))
        elif top == "apron":  # bare chest under a scorched leather forge apron
            b.cone("chest", self.skin, mat_at(P(0, 0.005, 1.28), scale=(1, 0.7, 1)), R(0.16 * W), R(0.21 * W), R(0.27), segments=10)
            b.cone("spine", self.skin, mat_at(P(0, 0.005, 1.08), scale=(1, 0.74, 1)), R(0.18 * W), R(0.17 * W), R(0.2), segments=10)
            burn = lambda f: H("#1f150e") if f.calc_center_median().z < self.K * 0.62 else H("#5a3b22")
            b.box("chest", H("#5a3b22"), mat_at(P(0, -0.16, 1.22), rot=(-6, 0, 0)), (R(0.28), R(0.025), R(0.24)))
            b.box("hips", burn, mat_at(P(0, -0.2, 0.8), rot=(4, 0, 0)), (R(0.34), R(0.025), R(0.46)))
            for sx in (1, -1):
                b.limb("chest", LEATHER, P(0.1 * sx, -0.15, 1.34), P(0.05 * sx, -0.02, 1.47), R(0.012), segments=4)
        # waist
        b.cone("hips", LEATHER if top == "apron" else s.get("bottom_cols", [self.skin])[0], mat_at(P(0, 0.005, 0.985), scale=(1, 0.78, 1)), R(0.17 * W), R(0.165 * W), R(0.07), segments=10)

    def legs(self):
        b, P, R, s = self.b, self.P, self.R, self.s
        bottom, cols = s["bottom"], s.get("bottom_cols", [self.skin])
        for side, sx in (("L", 1), ("R", -1)):
            x = 0.1 * sx
            if bottom == "wrapper":   # long wrapper, built round each leg so it sits and walks with her
                pat = bands(cols, 16)
                b.cone("hips", pat, mat_at(P(0, 0.01, 0.9), scale=(1, 0.85, 1)), R(0.21), R(0.17), R(0.17), segments=12)
                if sx == 1:   # the cloth hangs closed between the legs down to the knee
                    b.cone("hips", pat, mat_at(P(0, 0.01, 0.7), scale=(1, 0.85, 1)), R(0.235), R(0.205), R(0.42), segments=14)
                b.cone(f"thigh.{side}", pat, mat_at(P(x, 0, 0.66)), R(0.11), R(0.12), R(0.36), segments=10)
                b.cone(f"shin.{side}", pat, mat_at(P(x, 0, 0.3)), R(0.13), R(0.11), R(0.42), segments=10)
            elif bottom == "shorts":
                b.cone(f"thigh.{side}", cols[0], mat_at(P(x, 0, 0.7)), R(0.085), R(0.1), R(0.36), segments=8)
                b.ball(f"shin.{side}", self.skin, mat_at(P(x, 0, 0.49)), R(0.055), segs=(6, 5))
                b.limb(f"shin.{side}", self.skin, P(x, 0, 0.49), P(x, 0, 0.1), R(0.055), R(0.04))
            else:                     # trousers
                b.cone(f"thigh.{side}", cols[0], mat_at(P(x, 0, 0.66)), R(0.075), R(0.088), R(0.4), segments=8)
                b.cone(f"shin.{side}", cols[0], mat_at(P(x, 0, 0.29)), R(0.068), R(0.075), R(0.42), segments=8)
            if s["feet"] == "sandals":
                b.box(f"foot.{side}", LEATHER, mat_at(P(x, -0.045, 0.015)), (R(0.085), R(0.21), R(0.025)))
                b.box(f"foot.{side}", self.dark, mat_at(P(x, -0.05, 0.05)), (R(0.07), R(0.17), R(0.04)))
                b.limb(f"foot.{side}", LEATHER, P(x - 0.035, -0.07, 0.06), P(x + 0.035, -0.07, 0.06), R(0.01), segments=4)
            else:
                b.box(f"foot.{side}", self.dark, mat_at(P(x, -0.05, 0.03)), (R(0.075), R(0.2), R(0.045)))

    def arms(self):
        b, P, R = self.b, self.P, self.R
        thick = 1.25 if self.s["top"] == "apron" else 1.0
        for side, sx in (("L", 1), ("R", -1)):
            if self.s["top"] in ("apron",):
                b.ball(f"upperarm.{side}", self.skin, mat_at(P(0.19 * sx, 0, 1.355, arm=True)), R(0.065), segs=(8, 6))
            b.limb(f"upperarm.{side}", self.skin, P(0.195 * sx, 0, 1.33, arm=True), P(0.205 * sx, 0, 1.11, arm=True), R(0.045 * thick), R(0.038 * thick))
            b.ball(f"forearm.{side}", self.skin, mat_at(P(0.205 * sx, 0, 1.11, arm=True)), R(0.04 * thick), segs=(6, 5))
            b.limb(f"forearm.{side}", self.skin, P(0.205 * sx, 0, 1.11, arm=True), P(0.215 * sx, 0, 0.9, arm=True), R(0.04 * thick), R(0.032 * thick))
            b.ball(f"hand.{side}", self.skin, mat_at(P(0.215 * sx, -0.005, 0.85, arm=True), scale=(0.8, 1, 1.15)), R(0.045 * thick), segs=(6, 5))

    def extras(self):
        b, P, R, s = self.b, self.P, self.R, self.s
        for e in s.get("extras", []):
            if e == "necklace":
                for j in range(12):
                    a = math.radians(-75 + j * (150 / 11))
                    p = P(math.sin(a) * 0.11, -math.cos(a) * 0.085, 1.38 - math.cos(a) * 0.05)
                    if j % 3 == 0:
                        b.ball("chest", COWRIE, mat_at(p, scale=(0.8, 0.5, 1)), R(0.013), segs=(5, 4))
                    else:
                        b.gem("chest", BEADS[j % 4], mat_at(p), R(0.011))
            elif e == "bangles":
                for side, sx in (("L", 1), ("R", -1)):
                    for k in range(2):
                        b.limb(f"forearm.{side}", BRASS, self.P(0.214 * sx, 0, 0.94 - k * 0.022, arm=True), self.P(0.215 * sx, 0, 0.93 - k * 0.022, arm=True), R(0.036))
            elif e == "armbands":
                for side, sx in (("L", 1), ("R", -1)):
                    b.limb(f"upperarm.{side}", IRON, self.P(0.198 * sx, 0, 1.25, arm=True), self.P(0.2 * sx, 0, 1.22, arm=True), R(0.05))
            elif e == "baby":   # a baby tied on her back in a lappa
                cloth = bands([H("#b8352a"), H("#e0a83a")], 40)
                b.ball("chest", cloth, mat_at(P(0, 0.17, 1.15), scale=(1, 0.8, 1.15)), R(0.13), segs=(9, 6))
                b.ball("chest", SKINS["warm"], mat_at(P(0.02, 0.2, 1.33)), R(0.065), segs=(8, 6))
                b.ball("chest", BLACK_HAIR, mat_at(P(0.02, 0.22, 1.36), scale=(1, 1, 0.7)), R(0.06), segs=(8, 5))
                b.limb("chest", cloth, P(0.15, -0.1, 1.32), P(-0.15, -0.1, 1.05), R(0.025), segments=5)   # the tie across her chest

    def build(self):
        self.head(); self.torso(); self.legs(); self.arms(); self.extras()
        return self.b

    # ---------- props (rigid, riding on a hand) ----------
    def prop(self, kind):
        P, R = self.P, self.R
        b = Body(kind)
        hand_r = Vector(P(-0.215, -0.02, 0.85, arm=True))
        hand_l = Vector(P(0.215, -0.02, 0.85, arm=True))
        if kind == "whisk":       # a fly whisk: carved handle, a long tail of fibre
            b.limb("x", WOOD_DARK, tuple(hand_r + Vector((0, 0, R(0.08)))), tuple(hand_r - Vector((0, 0, R(0.06)))), R(0.016))
            b.cone("x", BRASS, mat_at(tuple(hand_r + Vector((0, 0, R(0.09))))), R(0.02), R(0.012), R(0.03), segments=6)
            for k in range(7):
                a = k / 7 * 2 * math.pi
                top = hand_r - Vector((0, 0, R(0.06)))
                b.limb("x", RAFFIA, tuple(top), tuple(top + Vector((math.cos(a) * R(0.04), math.sin(a) * R(0.04) - R(0.02), -R(0.38)))), R(0.012), R(0.004), segments=3)
        elif kind == "rattle":    # a seed rattle: gourd in a net of beads
            g = hand_l - Vector((0, R(0.02), R(0.12)))
            b.ball("x", GOURD, mat_at(tuple(g), scale=(1, 1, 1.15)), R(0.07), segs=(8, 6))
            for k in range(10):
                a = k / 10 * 2 * math.pi
                b.gem("x", COWRIE if k % 2 else BEADS[k % 4], mat_at(tuple(g + Vector((math.cos(a) * R(0.07), math.sin(a) * R(0.07), 0)))), R(0.012))
            b.limb("x", WOOD, tuple(g + Vector((0, 0, R(0.07)))), tuple(hand_l + Vector((0, 0, R(0.03)))), R(0.012))
        elif kind == "staff":     # the chief's carved staff of office, brass-topped, longer than he is tall
            base = hand_r + Vector((0, -R(0.03), -R(0.83)))
            top = hand_r + Vector((0, -R(0.03), R(0.98)))
            b.limb("x", WOOD_DARK, tuple(base), tuple(top), R(0.022), R(0.026), segments=6)
            for k in range(4):
                z = hand_r.z + R(0.3 + k * 0.12)
                b.limb("x", BRASS, (top.x, top.y, z), (top.x, top.y, z + R(0.02)), R(0.03), segments=6)
            b.ball("x", BRASS, mat_at(tuple(top + Vector((0, 0, R(0.05)))), scale=(1, 1, 1.4)), R(0.045), segs=(8, 6))
        elif kind == "hammer":    # a smith's hammer, handle forward and down
            d = Vector((0, -0.55, -1)).normalized()
            end = hand_r + d * R(0.3)
            b.limb("x", WOOD, tuple(hand_r - d * R(0.05)), tuple(end), R(0.018))
            b.box("x", IRON, Matrix.Translation(end) @ d.to_track_quat("Y", "Z").to_matrix().to_4x4(), (R(0.07), R(0.07), R(0.16)))
        elif kind == "pestle":    # a long wooden pestle, held upright
            b.limb("x", WOOD, tuple(hand_r + Vector((0, -R(0.05), -R(0.6)))), tuple(hand_r + Vector((0, -R(0.05), R(0.75)))), R(0.04), R(0.04), segments=6)
            b.ball("x", WOOD, mat_at(tuple(hand_r + Vector((0, -R(0.05), -R(0.62))))), R(0.05), segs=(6, 4))
        elif kind == "hoe":       # a short-handled West African hoe
            d = Vector((0, -0.7, -0.7)).normalized()
            end = hand_r + d * R(0.45)
            b.limb("x", WOOD, tuple(hand_r - d * R(0.08)), tuple(end), R(0.02))
            b.box("x", IRON, Matrix.Translation(end + Vector((0, R(0.03), -R(0.06)))) @ mat_at(rot=(30, 0, 0)), (R(0.14), R(0.02), R(0.16)))
        elif kind == "stick":     # a walking stick from hand to ground
            b.limb("x", WOOD, tuple(hand_r + Vector((0, -R(0.08), -R(0.85)))), tuple(hand_r + Vector((0, -R(0.02), R(0.06)))), R(0.018), R(0.022), segments=5)
        return b


# ---------- animation ----------
def seat(K):
    return {"hips": {"rot": (0, 0, 0), "loc": (0, -0.4 * K, 0)}, **L("L", thigh=(-88, 0, -5), shin=(88, 0, 0)), **L("R", thigh=(-88, 0, 5), shin=(88, 0, 0))}


def clips(arm, name, spec):
    K = spec["K"]
    stoop = {"spine": (12, 0, 0), "chest": (8, 0, 0), "head": (-12, 0, 0)} if spec.get("stoop") else {}
    A = {}
    rest = lambda k: {**stoop, "chest": (k * 2 + stoop.get("chest", (0, 0, 0))[0], 0, 0), "head": (-k * 3 + stoop.get("head", (0, 0, 0))[0], 0, k * 3),
                      **L("L", upperarm=(0, 0, -4), forearm=(-10, 0, 0)), **L("R", upperarm=(0, 0, 4), forearm=(-10, 0, 0))}
    if name == "elder":   # leaning on the stick
        rest = lambda k, r=rest: {**r(k), **L("R", upperarm=(-25, 0, 6), forearm=(-25, 0, 0))}
    A["Idle"] = add_action(arm, "Idle", [(1, rest(0)), (40, rest(1)), (80, rest(0))])

    def step(lead, trail, bob):
        p = {**stoop, "hips": {"rot": (0, 0, 0), "loc": (0, bob, 0)}, "spine": (4 + stoop.get("spine", (0, 0, 0))[0], 0, 0)}
        p.update(L(lead, thigh=(-24, 0, 0), shin=(8, 0, 0), upperarm=(16, 0, 0), forearm=(-15, 0, 0)))
        p.update(L(trail, thigh=(16, 0, 0), shin=(30, 0, 0), upperarm=(-16, 0, 0), forearm=(-25, 0, 0)))
        if name == "elder":
            p.update(L("R", upperarm=(-25, 0, 6), forearm=(-25, 0, 0)))
        return p
    def passing(up, bob):
        down = "R" if up == "L" else "L"
        return {**stoop, "hips": {"rot": (0, 0, 0), "loc": (0, bob, 0)}, **L(up, thigh=(-12, 0, 0), shin=(45, 0, 0)), **L(down, thigh=(4, 0, 0))}
    A["Walk"] = add_action(arm, "Walk", [(1, step("L", "R", -0.015 * K)), (9, passing("R", 0.012 * K)), (17, step("R", "L", -0.015 * K)), (25, passing("L", 0.012 * K)), (33, step("L", "R", -0.015 * K))])
    talk = lambda s: {**stoop, "head": (-4, 0, 8 * s), "chest": (-2, 6 * s, 0), **L("R", upperarm=(-40, 0, 15), forearm=(-45 + 15 * s, 0, 0)),
                      **L("L", upperarm=(-10 * (1 - s), 0, -10), forearm=(-30, 0, 0))}
    A["Talk"] = add_action(arm, "Talk", [(1, talk(1)), (30, talk(-1)), (60, talk(1))])

    # the audience: seated, clapping, answering
    S = seat(K)
    sit = lambda k: {**S, "chest": (4 + k * 2, 0, 0), "head": (-2, 0, k * 5), **L("L", upperarm=(-30, 0, -6), forearm=(-55, 0, 0)), **L("R", upperarm=(-30, 0, 6), forearm=(-55, 0, 0))}
    A["Sit"] = add_action(arm, "Sit", [(1, sit(0)), (45, sit(1)), (90, sit(0))])
    clap = lambda shut: {**S, "chest": (-4, 0, 0), "head": (-8, 0, 0), **L("L", upperarm=(-55, -10, 22 if shut else 8), forearm=(-60, 0, 0)),
                         **L("R", upperarm=(-55, 10, -22 if shut else -8), forearm=(-60, 0, 0))}
    A["Clap"] = add_action(arm, "Clap", [(1, clap(False)), (5, clap(True)), (9, clap(False)), (13, clap(True)), (17, clap(False))])
    answer = {**S, "chest": (-10, 0, 0), "head": (-22, 0, 0), **L("R", upperarm=(-160, 0, 10), forearm=(-15, 0, 0)), **L("L", upperarm=(-30, 0, -6), forearm=(-55, 0, 0))}
    A["Answer"] = add_action(arm, "Answer", [(1, sit(0)), (6, answer), (18, answer), (28, sit(0))], loop=False)

    sp = spec.get("special", [])
    if "Tell" in sp:   # the storyteller: steps, turns, sweeps the whisk, shakes the rattle
        tell = lambda s: {"chest": (0, 18 * s, 0), "head": (-6, 0, 12 * s), "hips": {"rot": (0, 0, 0), "loc": (0, -0.03, 0)},
                          **L("R", upperarm=(-90 + 40 * s, 30 * s, 25), forearm=(-30, 0, 0)), **L("L", upperarm=(-45, 0, -20 - 15 * s), forearm=(-70 + 20 * s, 0, 0)),
                          **L("L", thigh=(-12 * s, 0, 0), shin=(10, 0, 0)), **L("R", thigh=(12 * s, 0, 0), shin=(10, 0, 0))}
        A["Tell"] = add_action(arm, "Tell", [(1, tell(1)), (20, tell(-0.4)), (40, tell(-1)), (60, tell(0.4)), (80, tell(1))])
        sing = lambda s: {"chest": (-12, 0, 0), "head": (-28, 0, 6 * s), **L("L", upperarm=(-80, 0, -50), forearm=(-25 + 10 * s, 0, 0)),
                          **L("R", upperarm=(-80, 0, 50), forearm=(-25 - 10 * s, 0, 0))}
        A["Sing"] = add_action(arm, "Sing", [(1, sing(1)), (24, sing(-1)), (48, sing(1))])
    if "Worry" in sp:  # the Chief: hands to his head, rocking
        worry = lambda s: {"spine": (10, 0, 0), "head": (20, 0, 10 * s), **L("L", upperarm=(-150, 0, 25), forearm=(-110, 0, 0)),
                           **L("R", upperarm=(-18, 0, 4), forearm=(-20, 0, 0))}   # the other hand keeps his staff
        A["Worry"] = add_action(arm, "Worry", [(1, worry(1)), (25, worry(-1)), (50, worry(1))])
        speak = lambda s: {"chest": (-6, -8, 0), "head": (-8, 0, 6 * s), **L("R", upperarm=(-35, 0, 10), forearm=(-30, 0, 0)),
                           **L("L", upperarm=(-70, 0, -25 + 10 * s), forearm=(-35, 0, 0))}
        A["Speak"] = add_action(arm, "Speak", [(1, speak(1)), (30, speak(-1)), (60, speak(1))])
    if "Hammer" in sp:  # the smith: raise, strike, rebound
        up = {"spine": (6, 0, 0), "chest": (-6, -14, 0), **L("R", upperarm=(-155, 0, 10), forearm=(-60, 0, 0)), **L("L", upperarm=(-45, 0, -10), forearm=(-50, 0, 0)),
              **L("L", thigh=(-15, 0, 0), shin=(15, 0, 0)), **L("R", thigh=(10, 0, 0))}
        hit = {"spine": (20, 0, 0), "chest": (10, -6, 0), **L("R", upperarm=(-55, 0, 6), forearm=(-20, 0, 0)), **L("L", upperarm=(-45, 0, -10), forearm=(-50, 0, 0)),
               **L("L", thigh=(-15, 0, 0), shin=(15, 0, 0)), **L("R", thigh=(10, 0, 0))}
        A["Hammer"] = add_action(arm, "Hammer", [(1, up), (8, hit), (10, {**hit, **L("R", upperarm=(-75, 0, 6))}), (18, up)])
    if "Pound" in sp:   # pounding rice: both hands on the pestle, lift and drop
        up = {"chest": (-8, 0, 0), "head": (-6, 0, 0), **L("R", upperarm=(-150, 0, -18), forearm=(-25, 0, 0)), **L("L", upperarm=(-150, 0, 18), forearm=(-25, 0, 0)),
              "hips": {"rot": (0, 0, 0), "loc": (0, 0.02, 0)}}
        down = {"spine": (14, 0, 0), "head": (10, 0, 0), **L("R", upperarm=(-60, 0, -18), forearm=(-25, 0, 0)), **L("L", upperarm=(-60, 0, 18), forearm=(-25, 0, 0)),
                **L("L", thigh=(-10, 0, 0), shin=(14, 0, 0)), **L("R", thigh=(-10, 0, 0), shin=(14, 0, 0)), "hips": {"rot": (0, 0, 0), "loc": (0, -0.05, 0)}}
        A["Pound"] = add_action(arm, "Pound", [(1, up), (10, down), (12, down), (24, up)])
    if "Hoe" in sp:     # hoeing the upland rice farm, bent to the ground
        bend = {"spine": (30, 0, 0), "chest": (10, 0, 0), "head": (-15, 0, 0), **L("L", thigh=(-30, 0, 0), shin=(30, 0, 0)), **L("R", thigh=(10, 0, 0), shin=(15, 0, 0))}
        lift = {**bend, **L("R", upperarm=(-120, 0, 10), forearm=(-50, 0, 0)), **L("L", upperarm=(-40, 0, -10), forearm=(-60, 0, 0))}
        chop = {**bend, "spine": (38, 0, 0), **L("R", upperarm=(-25, 0, 6), forearm=(-15, 0, 0)), **L("L", upperarm=(-40, 0, -10), forearm=(-60, 0, 0))}
        A["Hoe"] = add_action(arm, "Hoe", [(1, lift), (10, chop), (13, chop), (24, lift)])
    return A


def bones_for(spec):
    K, W = spec["K"], spec["W"]
    out = {}
    for n, (h, t, p) in korto.BONES.items():
        w = W if n.split(".")[0] in ("upperarm", "forearm", "hand") else 1
        out[n] = ((h[0] * K * w, h[1] * K, h[2] * K), (t[0] * K * w, t[1] * K, t[2] * K), p)
    return out


def build_person(name):
    """Build one person into the current scene; returns (armature, body, props, actions)."""
    spec = PEOPLE[name]
    rig = "".join(w.capitalize() for w in name.split("_")) + "Rig"
    arm = build_armature(rig, bones_for(spec))
    person = Person(name, spec)
    mat = vertex_color_material(name)
    body = person.build().to_object(mat)
    body.name = "".join(w.capitalize() for w in name.split("_"))
    skin_to(body, arm)
    props = []
    for pname, kind, bone in spec.get("props", []):
        o = person.prop(kind).to_object(mat)
        o.vertex_groups.clear(); o.name = pname
        attach_to_bone(o, arm, bone, Matrix.Identity(4))
        props.append(o)
    actions = clips(arm, name, spec)
    rest_pose(arm)
    return arm, body, props, actions


def main():
    shots_front, shots_work = [], []
    work = {"storyteller": ("Tell", 1), "chief": ("Worry", 1), "blacksmith": ("Hammer", 1), "villager_woman": ("Pound", 1),
            "villager_man": ("Hoe", 1), "elder": ("Walk", 1), "child": ("Answer", 12)}
    for name in PEOPLE:
        reset_scene()
        arm, body, props, actions = build_person(name)
        export_glb(MODELS_OUT / f"{name}.glb")
        if "--preview" in sys.argv:
            cam = setup_preview(size=(420, 600))
            K = PEOPLE[name]["K"]
            pose_at(arm, actions["Idle"], 1)
            aim_camera(cam, 20, target=(0, 0, 0.95), dist=4.4, height=1.45)
            p = PREVIEWS_OUT / f"_pf_{name}.png"; render_to(p); shots_front.append(p)
            act, fr = work[name]
            pose_at(arm, actions[act], fr)
            aim_camera(cam, 45, target=(0, 0, 0.9), dist=4.4, height=1.6)
            p = PREVIEWS_OUT / f"_pw_{name}.png"; render_to(p); shots_work.append(p)
    if "--preview" in sys.argv:
        labels = ["Storyteller", "Chief", "Blacksmith (father)", "Villager woman", "Rice farmer", "Elder", "Child"]
        contact_sheet(shots_front, PREVIEWS_OUT / "people.png", cols=7, labels=labels)
        contact_sheet(shots_work, PREVIEWS_OUT / "people-at-work.png", cols=7,
                      labels=["Telling the tale", "Chief: the rice is gone", "At the anvil", "Pounding rice", "Hoeing", "Walking", "Answering wese"])


if __name__ == "__main__":
    main()
