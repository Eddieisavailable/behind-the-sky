"""Gbelewala: the hero's village (episode 1's morning, and the storytelling nights).

A kit of pieces like environment.py, each one mesh at the origin on the ground (z = 0):
round and long houses of wattle-and-daub under thatch, the palaver hut where the Chief meets and the
storyteller sings, the seed-rice store (a raised granary, found empty, its door hanging open and its
walls gouged by rattan claws, rice spilled in the dirt), woven fences, a mortar and pestle, a cook
fire, the storyteller's fire, a rice-drying rack, a bench and stools, banana plants, water pots,
a chicken, and a patch of upland rice farm.

    python blender/gbelewala.py            # build + export public/models/gbelewala.glb
    python blender/gbelewala.py --preview  # also render a preview sheet
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, aim_camera, contact_sheet, export_glb, glow_material,
                 hexcol, jitter, mat_at, render_to, reset_scene, setup_preview, static_object, vertex_color_material)

H = hexcol
MUD = H("#9c5a34")
MUD_LIGHT = H("#c58a5a")
MUD_DARK = H("#7a4428")
WHITEWASH = H("#d9cbb0")
THATCH = H("#b89a5a")
THATCH_DARK = H("#8e7442")
WOOD = H("#5e3d22")
WOOD_DARK = H("#3e2716")
WOOD_PALE = H("#8a6a44")
STICK = H("#7a5a38")
LATERITE = H("#8a5a3c")
STONE = H("#6f6a60")
CLAY = H("#8f4a2a")
CLAY_DARK = H("#6e3820")
CHARCOAL = H("#1c1814")
RICE = H("#efe6cf")
RICE_GOLD = H("#d6b46a")
STRAW = H("#c9b070")
GREEN = H("#4f7d2e")
GREEN_DARK = H("#3a5f24")
BANANA = H("#5f9a34")
BANANA_DARK = H("#3f6a24")
GOUGE = H("#2a1a10")
EMBER = H("#ff6a1f")
FEATHER = H("#b85a2a")
FEATHER_DARK = H("#6a2a14")
COMB = H("#c22a20")
LEG = H("#d8a83a")


def thatch_rings(z0):
    return lambda f: THATCH_DARK if int((f.calc_center_median().z - z0) * 4) % 2 else THATCH


def wall(z_split):
    """Mud walls, whitewashed band at the bottom like many Kpelle houses."""
    return lambda f: WHITEWASH if f.calc_center_median().z < z_split else MUD


def house_round():
    """A big round house with a deep thatch overhang resting on porch posts."""
    b = Body("house_round")
    jitter(b.cone("x", LATERITE, mat_at((0, 0, 0.12)), 2.7, 2.6, 0.24, segments=16), 0.02, 1)
    b.cone("x", wall(0.6), mat_at((0, 0, 1.15)), 2.2, 2.15, 2.1, segments=16)
    b.box("x", WOOD_DARK, mat_at((0, -2.15, 0.95)), (0.85, 0.14, 1.6))                 # door
    b.box("x", WOOD, mat_at((0, -2.2, 1.8)), (1.05, 0.12, 0.12))
    for a in (-55, 55):                                                               # small windows
        r = math.radians(a - 90)
        b.box("x", WOOD_DARK, mat_at((math.cos(r) * 2.16, math.sin(r) * 2.16, 1.35), rot=(0, 0, a)), (0.45, 0.12, 0.4))
    for k in range(10):                                                               # porch posts
        a = k / 10 * 2 * math.pi
        b.limb("x", WOOD, (math.cos(a) * 2.75, math.sin(a) * 2.75, 0.2), (math.cos(a) * 2.75, math.sin(a) * 2.75, 2.15), 0.06, segments=5)
    b.cone("x", thatch_rings(2.2), mat_at((0, 0, 3.55)), 3.25, 0.12, 2.9, segments=16)
    b.cone("x", THATCH_DARK, mat_at((0, 0, 2.15)), 3.3, 3.1, 0.14, segments=16)
    b.cone("x", WOOD_DARK, mat_at((0, 0, 5.1)), 0.09, 0.02, 0.5, segments=5)
    return b


def house_long():
    """A rectangular mud house with a hipped thatch roof and a front veranda."""
    b = Body("house_long")
    jitter(b.box("x", LATERITE, mat_at((0, 0, 0.1)), (5.8, 4.4, 0.2)), 0.02, 2)
    b.box("x", wall(0.6), mat_at((0, 0.3, 1.15)), (5.0, 3.0, 2.1))
    b.box("x", WOOD_DARK, mat_at((0, -1.22, 0.95)), (0.9, 0.12, 1.6))
    for x in (-1.6, 1.6):                                                             # shuttered windows
        b.box("x", WOOD_DARK, mat_at((x, -1.22, 1.35)), (0.6, 0.12, 0.5))
        b.box("x", WOOD_PALE, mat_at((x + 0.42, -1.3, 1.35), rot=(0, 0, 20)), (0.3, 0.05, 0.5))
    for x in (-2.4, -0.8, 0.8, 2.4):                                                  # veranda posts
        b.limb("x", WOOD, (x, -1.95, 0.2), (x, -1.95, 2.2), 0.06, segments=5)
    roof = lambda f: THATCH_DARK if int(f.calc_center_median().z * 4) % 2 else THATCH
    b.cone("x", roof, mat_at((0, 0.1, 3.15), rot=(0, 0, 45), scale=(1.35, 1, 1)), 3.7, 0.25, 2.1, segments=4)
    return b


def palaver_hut():
    """The open, round meeting hut: posts, a low wall to lean on, benches inside, a high thatch roof."""
    b = Body("palaver_hut")
    jitter(b.cone("x", LATERITE, mat_at((0, 0, 0.08)), 3.6, 3.5, 0.16, segments=18), 0.02, 3)
    for k in range(10):
        a = k / 10 * 2 * math.pi + 0.31
        x, y = math.cos(a) * 3.2, math.sin(a) * 3.2
        b.limb("x", WOOD, (x, y, 0.15), (x, y, 2.5), 0.09, 0.08, segments=6)
        if k not in (7, 8):                                                          # a gap is the way in
            a2 = (k + 1) / 10 * 2 * math.pi + 0.31
            mid = Vector(((x + math.cos(a2) * 3.2) / 2, (y + math.sin(a2) * 3.2) / 2, 0.42))
            b.box("x", MUD, mat_at(tuple(mid), rot=(0, 0, math.degrees((a + a2) / 2) + 90)), (2.0, 0.22, 0.55))
    for k in range(3):                                                                # benches round the inside
        a = math.radians(-30 + k * 80)
        b.box("x", WOOD_PALE, mat_at((math.cos(a) * 2.5, math.sin(a) * 2.5, 0.42), rot=(0, 0, math.degrees(a) + 90)), (2.2, 0.4, 0.1))
    b.cone("x", thatch_rings(2.5), mat_at((0, 0, 3.9)), 4.3, 0.15, 2.9, segments=18)
    b.cone("x", WOOD_DARK, mat_at((0, 0, 5.45)), 0.1, 0.02, 0.5, segments=5)
    return b


def rice_store():
    """The seed-rice store, found empty: a raised round granary, door hanging open, walls clawed
    by rattan, rice spilled in the dirt and a basket knocked over."""
    b = Body("rice_store")
    rnd = random.Random(7)
    for k in range(6):                                                               # stilts
        a = k / 6 * 2 * math.pi
        b.limb("x", WOOD_DARK, (math.cos(a) * 1.0, math.sin(a) * 1.0, 0), (math.cos(a) * 1.0, math.sin(a) * 1.0, 1.25), 0.1, 0.09, segments=6)
    b.cone("x", WOOD, mat_at((0, 0, 1.3)), 1.4, 1.4, 0.15, segments=12)             # floor
    weave = lambda f: MUD_LIGHT if int(f.calc_center_median().z * 10) % 3 == 0 else MUD
    b.cone("x", weave, mat_at((0, 0, 2.15)), 1.12, 1.2, 1.6, segments=12)          # basket body plastered with mud
    b.box("x", CHARCOAL, mat_at((0, -1.17, 2.0)), (0.6, 0.06, 0.9))                 # the dark doorway
    b.box("x", WOOD_PALE, Matrix.Translation(Vector((0.3, -1.17, 2.0))) @ mat_at(rot=(0, 0, -70)) @ mat_at((0.3, 0, 0)), (0.6, 0.06, 0.88))  # door swung open
    b.cone("x", thatch_rings(2.9), mat_at((0, 0, 3.55)), 1.75, 0.08, 1.5, segments=12)
    # notched log ladder
    b.limb("x", WOOD, (0.2, -2.1, 0), (0.1, -1.25, 1.35), 0.09, segments=6)
    for k in range(4):
        t = (k + 1) / 5
        p = Vector((0.2, -2.1, 0)) + (Vector((0.1, -1.25, 1.35)) - Vector((0.2, -2.1, 0))) * t
        b.box("x", WOOD_DARK, mat_at(tuple(p + Vector((0, -0.06, 0)))), (0.2, 0.05, 0.05))
    # rattan claw gouges: three sets of three, with demon embers in some
    for s, (a, z) in enumerate(((-120, 2.4), (-60, 1.9), (-150, 1.8))):
        r = math.radians(a)
        for k in range(3):
            base = Vector((math.cos(r) * 1.18, math.sin(r) * 1.18, z))
            off = Vector((-math.sin(r), math.cos(r), 0)) * (k * 0.1)
            b.box("x", GOUGE, mat_at(tuple(base + off), rot=(0, 30, math.degrees(r) + 90)), (0.04, 0.05, 0.75))
        b.gem("x", EMBER, mat_at((math.cos(r) * 1.2, math.sin(r) * 1.2, z + 0.25)), 0.03, mat=1)
    # spilled rice in the dirt, a knocked-over basket
    for k in range(40):
        a = rnd.uniform(-2.6, -0.5)
        d = rnd.uniform(0.8, 2.6)
        b.gem("x", RICE if k % 3 else RICE_GOLD, mat_at((math.cos(a) * d, math.sin(a) * d, 0.02)), 0.03)
    b.cone("x", STRAW, mat_at((1.4, -1.7, 0.22), rot=(80, 0, 30)), 0.3, 0.2, 0.4, segments=10)
    for k in range(3):                                                               # rattan scraps left behind
        b.limb("x", STICK, (-1.6 + k * 0.3, -1.4 - k * 0.2, 0.03), (-1.1 + k * 0.35, -1.9 - k * 0.1, 0.03), 0.025, segments=3)
    return b


def fence():
    """A 4 m section of woven stick fence."""
    b = Body("fence")
    for k in range(9):
        x = -2 + k * 0.5
        b.limb("x", WOOD_DARK, (x, 0, 0), (x, 0, 1.15 + (k % 2) * 0.1), 0.045, 0.035, segments=4)
    for z in (0.35, 0.65, 0.95):
        for k in range(8):
            x0 = -2 + k * 0.5
            dy = 0.05 if (k + int(z * 10)) % 2 else -0.05
            b.limb("x", STICK, (x0, dy, z), (x0 + 0.5, -dy, z), 0.025, segments=3)
    return b


def mortar():
    b = Body("mortar")
    b.cone("x", WOOD, mat_at((0, 0, 0.32)), 0.22, 0.28, 0.64, segments=10)
    b.cone("x", WOOD_DARK, mat_at((0, 0, 0.64)), 0.22, 0.22, 0.015, segments=10)
    b.cone("x", RICE_GOLD, mat_at((0, 0, 0.6)), 0.19, 0.19, 0.04, segments=10)
    b.limb("x", WOOD_PALE, (0.32, 0.05, 0.0), (0.12, 0.1, 1.6), 0.04, segments=6)  # a pestle leaning on it
    return b


def cook_fire():
    b = Body("cook_fire")
    for k in range(3):
        a = k / 3 * 2 * math.pi
        jitter(b.gem("x", LATERITE, mat_at((math.cos(a) * 0.32, math.sin(a) * 0.32, 0.14)), 0.17), 0.03, k)
    b.ball("x", CLAY_DARK, mat_at((0, 0, 0.5), scale=(1, 1, 0.8)), 0.3, segs=(10, 6))
    b.cone("x", CHARCOAL, mat_at((0, 0, 0.73)), 0.18, 0.18, 0.05, segments=10)
    for k in range(5):
        b.gem("x", EMBER if k % 2 else CHARCOAL, mat_at((math.cos(k) * 0.12, math.sin(k) * 0.12, 0.08)), 0.06, mat=1 if k % 2 else 0)
    return b


def story_fire():
    """The storyteller's fire: logs leaned together over glowing coals (the game adds the flames)."""
    b = Body("story_fire")
    for k in range(7):
        a = k / 7 * 2 * math.pi
        b.limb("x", WOOD_DARK if k % 2 else WOOD, (math.cos(a) * 0.7, math.sin(a) * 0.7, 0.05), (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.9), 0.07, 0.05, segments=5)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        b.gem("x", EMBER if k % 2 else CHARCOAL, mat_at((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.08)), 0.1, mat=1 if k % 2 else 0)
    for k in range(10):
        a = k / 10 * 2 * math.pi
        jitter(b.gem("x", STONE, mat_at((math.cos(a) * 1.0, math.sin(a) * 1.0, 0.08)), 0.15), 0.03, k)
    return b


def drying_rack():
    b = Body("drying_rack")
    for x in (-1.2, 1.2):
        b.limb("x", WOOD, (x, 0, 0), (x, 0, 1.8), 0.06, segments=5)
    b.limb("x", WOOD_PALE, (-1.3, 0, 1.75), (1.3, 0, 1.75), 0.05, segments=5)
    b.limb("x", WOOD_PALE, (-1.3, 0, 1.2), (1.3, 0, 1.2), 0.04, segments=5)
    for k in range(7):                                                               # rice bundles hung head-down
        x = -1.0 + k * 0.33
        for z in (1.75, 1.2):
            b.cone("x", STRAW, mat_at((x, 0, z - 0.25)), 0.03, 0.12, 0.45, segments=6)
            b.cone("x", RICE_GOLD, mat_at((x, 0, z - 0.52)), 0.12, 0.07, 0.15, segments=6)
    return b


def bench():
    b = Body("bench")
    b.limb("x", WOOD_PALE, (-1.0, 0, 0.4), (1.0, 0, 0.4), 0.16, segments=8)
    b.box("x", WOOD, mat_at((0, 0, 0.5)), (2.0, 0.26, 0.04))
    for x in (-0.75, 0.75):
        b.box("x", WOOD_DARK, mat_at((x, 0, 0.18)), (0.14, 0.3, 0.36))
    return b


def stool():
    b = Body("stool")
    b.cone("x", WOOD, mat_at((0, 0, 0.36)), 0.2, 0.2, 0.05, segments=10)
    b.cone("x", WOOD_DARK, mat_at((0, 0, 0.2)), 0.07, 0.13, 0.28, segments=8)
    b.cone("x", WOOD, mat_at((0, 0, 0.04)), 0.18, 0.17, 0.08, segments=10)
    return b


def banana_plant():
    b = Body("banana_plant")
    b.cone("x", GREEN_DARK, mat_at((0, 0, 0.9)), 0.16, 0.12, 1.8, segments=7)
    for k in range(7):
        a = k / 7 * 2 * math.pi
        start = Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 1.7 + (k % 3) * 0.15))
        d = Vector((math.cos(a), math.sin(a), 0.9 - (k % 2) * 0.6)).normalized()
        mid = start + d * 0.9
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        b.cone("x", BANANA if k % 2 else BANANA_DARK, Matrix.Translation(mid) @ rot @ mat_at(rot=(0, 0, math.degrees(a) + 90), scale=(1, 0.12, 1)), 0.32, 0.1, 1.8, segments=4)
    b.ball("x", GREEN, mat_at((0.12, -0.1, 1.45), scale=(1, 1, 1.4)), 0.13, segs=(7, 5))   # a bunch
    return b


def water_pots():
    b = Body("water_pots")
    for k, (x, y, s) in enumerate(((0, 0, 1.0), (0.55, 0.2, 0.75), (-0.45, 0.3, 0.6))):
        b.ball("x", CLAY if k % 2 == 0 else CLAY_DARK, mat_at((x, y, 0.32 * s), scale=(1, 1, 0.95)), 0.33 * s, segs=(10, 7))
        b.cone("x", CLAY_DARK, mat_at((x, y, 0.62 * s)), 0.13 * s, 0.17 * s, 0.1 * s, segments=10)
    b.cone("x", WOOD_PALE, mat_at((0, 0, 0.7)), 0.17, 0.2, 0.03, segments=10)            # a lid
    return b


def chicken():
    b = Body("chicken")
    b.ball("x", FEATHER, mat_at((0, 0.02, 0.25), scale=(0.75, 1.1, 0.85)), 0.13, segs=(8, 6))
    b.ball("x", FEATHER, mat_at((0, -0.1, 0.38)), 0.065, segs=(7, 5))
    b.cone("x", LEG, mat_at((0, -0.17, 0.37), rot=(-90, 0, 0)), 0.02, 0.0, 0.05, segments=4)
    b.box("x", COMB, mat_at((0, -0.1, 0.45)), (0.015, 0.06, 0.05))
    for k in range(4):
        b.cone("x", FEATHER_DARK, mat_at((0, 0.14, 0.33 + k * 0.03), rot=(-50 + k * 15, 0, 0), scale=(0.3, 1, 1)), 0.04, 0.0, 0.16, segments=4)
    for sx in (1, -1):
        b.limb("x", LEG, (0.04 * sx, 0.02, 0.15), (0.04 * sx, 0.0, 0.0), 0.012, segments=3)
    return b


def rice_farm():
    """A patch of upland rice on burned and cleared ground, with old stumps."""
    b = Body("rice_farm")
    rnd = random.Random(21)
    jitter(b.box("x", MUD_DARK, mat_at((0, 0, 0.0)), (7.0, 5.0, 0.1)), 0.03, 1)
    for i in range(10):
        for j in range(7):
            x = -3.1 + i * 0.68 + rnd.uniform(-0.1, 0.1)
            y = -2.2 + j * 0.68 + rnd.uniform(-0.1, 0.1)
            for k in range(3):
                a = k * 2.1
                b.cone("x", GREEN if (i + j + k) % 2 else GREEN_DARK, mat_at((x, y, 0.25), rot=(math.cos(a) * 15, math.sin(a) * 15, 0), scale=(1, 0.4, 1)), 0.04, 0.0, 0.5, segments=3)
    for (x, y) in ((-2.6, 1.8), (2.4, -1.5), (0.6, 2.1)):
        jitter(b.cone("x", WOOD_DARK, mat_at((x, y, 0.2)), 0.22, 0.18, 0.4, segments=7), 0.03, int(x * 10))
    return b


ASSETS = [house_round, house_long, palaver_hut, rice_store, fence, mortar, cook_fire, story_fire, drying_rack, bench, stool,
          banana_plant, water_pots, chicken, rice_farm]


def build_all():
    env = vertex_color_material("Gbelewala")
    glow = glow_material("Glow", EMBER, 5.0)
    return [static_object(body.name, body, [env, glow]) for body in (f() for f in ASSETS)]


def main():
    reset_scene()
    objs = build_all()
    export_glb(MODELS_OUT / "gbelewala.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(480, 440))
        frames = {"house_round": (5, 2, 14), "house_long": (5, 1.8, 14), "palaver_hut": (6, 2, 15), "rice_store": (3.2, 1.8, 8.5), "fence": (1.6, 0.6, 6),
                  "mortar": (1.2, 0.6, 3.2), "cook_fire": (1, 0.3, 2.4), "story_fire": (1.6, 0.4, 4), "drying_rack": (1.8, 1.2, 5.5), "bench": (1, 0.3, 3.2),
                  "stool": (0.6, 0.2, 1.4), "banana_plant": (2.2, 1.6, 6.5), "water_pots": (1, 0.3, 2.6), "chicken": (0.45, 0.25, 1.3), "rice_farm": (5, 0, 11)}
        shots = []
        for o in objs:
            for other in objs:
                other.hide_render = other is not o
            h, tz, d = frames[o.name]
            aim_camera(cam, 25, target=(0, 0, tz), dist=d, height=h)
            p = PREVIEWS_OUT / f"_gb{o.name}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "gbelewala.png", cols=5, labels=[o.name.replace("_", " ") for o in objs])


if __name__ == "__main__":
    main()
