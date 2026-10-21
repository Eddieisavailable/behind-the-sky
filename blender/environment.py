"""Environment assets for the clearing and Gbelewala: forest, village and the places of the slice.

Every asset is one mesh standing at the origin on the ground (z = 0), so the game can
place and instance it. Layout notes for the game: Blender (x, y, z) becomes three.js
(x, z, -y), so "south" in the game (+z) is -y here.

    python blender/environment.py            # build + export public/models/environment.glb
    python blender/environment.py --preview  # also render a preview sheet
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Vector, aim_camera, contact_sheet, export_glb, glow_material,
                 hexcol, jitter, mat_at, render_to, reset_scene, setup_preview, static_object, vertex_color_material)

# ---------- palette ----------
BARK = hexcol("#4a3423")
BARK_DARK = hexcol("#35251a")
BARK_PALE = hexcol("#6b5440")
LEAF = [hexcol("#2f5a2a"), hexcol("#3b6b2f"), hexcol("#28492a"), hexcol("#4a7a34")]
PALM_TRUNK = hexcol("#5a4632")
PALM_RING = hexcol("#3f3124")
FROND = hexcol("#4f7d2e")
FROND_DARK = hexcol("#3c6224")
PALM_FRUIT = hexcol("#c2461f")
LATERITE = hexcol("#8a5a3c")   # Liberia's red laterite stone
LATERITE_DARK = hexcol("#6e4630")
STONE = hexcol("#6f6a60")
MUD = hexcol("#9c5a34")         # wattle-and-daub wall
MUD_LIGHT = hexcol("#c58a5a")
THATCH = hexcol("#b89a5a")
THATCH_DARK = hexcol("#8e7442")
WOOD = hexcol("#5e3d22")
WOOD_DARK = hexcol("#3e2716")
CLAY = hexcol("#8f4a2a")
CHARCOAL = hexcol("#1c1814")
IRON = hexcol("#4a4f55")
IRON_RUST = hexcol("#7a4a2c")
LEATHER = hexcol("#6b4a2a")
RICE = hexcol("#efe6cf")
CLOTH = [hexcol("#2d3a6b"), hexcol("#e9dcc0"), hexcol("#a4532c")]
VINE = hexcol("#4d6a2a")
CANE = hexcol("#b8894f")
THORN = hexcol("#3a2b1a")
EMBER = hexcol("#ff7a1a")


def leafy(rnd):
    return LEAF[rnd.randrange(len(LEAF))]


def tree_giant():
    """A rainforest giant: buttress roots, a tall clean trunk, a flat layered crown."""
    rnd = random.Random(3)
    b = Body("tree_giant")
    jitter(b.limb("x", BARK, (0, 0, 0), (0, 0, 9.0), 0.62, 0.34, segments=7), 0.04, 1)
    for k in range(5):  # buttress fins
        a = k / 5 * 2 * math.pi + 0.4
        b.box("x", BARK_PALE if k % 2 else BARK, mat_at((math.cos(a) * 0.7, math.sin(a) * 0.7, 0.75), rot=(0, 0, math.degrees(a)), scale=(1, 1, 1)) @ mat_at(rot=(0, -28, 0)), (1.25, 0.14, 1.7))
    for k, (a, h) in enumerate(((0.3, 7.2), (2.4, 7.8), (4.3, 7.5), (5.4, 8.3))):  # main branches
        tip = (math.cos(a) * 3.0, math.sin(a) * 3.0, h + 1.8)
        b.limb("x", BARK_DARK, (0, 0, h), tip, 0.24, 0.1, segments=5)
    for k in range(8):  # crown: a wide umbrella of flattened leaf masses in two layers
        a = k / 8 * 2 * math.pi + rnd.uniform(-0.25, 0.25)
        r = 3.4 if k % 2 else 2.4
        z = 9.4 + (0.9 if k % 2 == 0 else 0.2)
        jitter(b.ball("x", leafy(rnd), mat_at((math.cos(a) * r, math.sin(a) * r, z), scale=(1, 1, 0.38)), rnd.uniform(2.3, 3.0), segs=(8, 5)), 0.18, k)
    jitter(b.ball("x", LEAF[1], mat_at((0, 0, 10.7), scale=(1, 1, 0.4)), 3.0, segs=(9, 5)), 0.18, 9)
    return b


def tree_mid():
    """Understory tree: a short crooked trunk and a round crown."""
    rnd = random.Random(5)
    b = Body("tree_mid")
    b.limb("x", BARK, (0, 0, 0), (0.25, 0, 2.4), 0.24, 0.16, segments=6)
    b.limb("x", BARK, (0.25, 0, 2.4), (-0.1, 0.15, 3.6), 0.16, 0.1, segments=6)
    for k in range(4):
        a = k / 4 * 2 * math.pi
        jitter(b.ball("x", leafy(rnd), mat_at((math.cos(a) * 0.8, math.sin(a) * 0.8, 3.5 + (k % 2) * 0.5), scale=(1, 1, 0.75)), rnd.uniform(1.0, 1.35), segs=(7, 5)), 0.08, k)
    jitter(b.ball("x", LEAF[3], mat_at((0, 0, 4.3), scale=(1, 1, 0.7)), 1.2, segs=(7, 5)), 0.08, 7)
    return b


def palm():
    """Oil palm: ringed trunk, arching fronds, a red-orange fruit bunch."""
    b = Body("palm")
    pts = [Vector((0, 0, 0))]
    for i in range(1, 7):
        pts.append(Vector((math.sin(i * 0.5) * 0.12 + i * 0.05, 0, i * 1.0)))
    for i, (a, c) in enumerate(zip(pts, pts[1:])):
        b.limb("x", PALM_TRUNK if i % 2 else PALM_RING, a, c, 0.3 - i * 0.015, 0.28 - i * 0.015, segments=7)
        for k in range(4):  # old frond stubs
            ang = k / 4 * 2 * math.pi + i
            p = a + (c - a) * 0.5
            b.cone("x", PALM_RING, mat_at((p.x + math.cos(ang) * 0.28, p.y + math.sin(ang) * 0.28, p.z), rot=(math.degrees(-math.sin(ang)) * 0.9, math.degrees(math.cos(ang)) * 0.9, 0)), 0.07, 0.02, 0.22, segments=4)
    top = pts[-1]
    for k in range(10):  # fronds: three arching blade sections each
        ang = k / 10 * 2 * math.pi
        d = Vector((math.cos(ang), math.sin(ang), 0))
        prev = top + Vector((0, 0, 0.2))
        for s, (out, drop) in enumerate(((1.0, 0.55), (1.0, 0.05), (0.9, -0.6))):
            nxt = prev + d * out * 1.15 + Vector((0, 0, drop))
            mid = (prev + nxt) / 2
            rot = (nxt - prev).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
            m = mat_at(tuple(mid)) @ rot @ mat_at(rot=(0, 0, math.degrees(ang) + 90), scale=(1, 0.18, 1))
            b.cone("x", FROND if (k + s) % 2 else FROND_DARK, m, 0.32 - s * 0.08, 0.2 - s * 0.07, (nxt - prev).length, segments=4)
            prev = nxt
    for k in range(9):  # fruit bunch tucked under the crown
        ang = k / 9 * 2 * math.pi
        b.ball("x", PALM_FRUIT, mat_at((top.x + math.cos(ang) * 0.3, top.y + math.sin(ang) * 0.3 - 0.05, top.z - 0.3 - (k % 3) * 0.08)), 0.09, segs=(5, 4))
    return b


def bush():
    rnd = random.Random(11)
    b = Body("bush")
    jitter(b.ball("x", LEAF[2], mat_at((0, 0, 0.35), scale=(1, 1, 0.7)), 0.5, segs=(7, 5)), 0.05, 1)
    for k in range(9):
        a = k / 9 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        tilt = rnd.uniform(35, 60)
        b.cone("x", leafy(rnd), mat_at((math.cos(a) * 0.25, math.sin(a) * 0.25, 0.25), rot=(-math.sin(a) * tilt, math.cos(a) * tilt, 0)) @ mat_at((0, 0, 0.45), scale=(1, 0.3, 1)), 0.16, 0.01, 0.95, segments=4)
    return b


def rock(seed, size, color):
    b = Body(f"rock_{seed}")
    jitter(b.gem("x", color, mat_at((0, 0, size * 0.35), scale=(1.2, 1.0, 0.7)), size), size * 0.18, seed)
    return b


def vine_clump():
    """Where crawlers rise: a knot of rattan cane, vine and thorns."""
    rnd = random.Random(21)
    b = Body("vine_clump")
    jitter(b.ball("x", LATERITE_DARK, mat_at((0, 0, 0.0), scale=(1.3, 1.3, 0.35)), 0.6, segs=(8, 4)), 0.06, 1)
    for k in range(7):
        a = k / 7 * 2 * math.pi
        base = Vector((math.cos(a) * 0.35, math.sin(a) * 0.35, 0.05))
        h = rnd.uniform(1.0, 1.9)
        top = base + Vector((math.cos(a + 1.2) * 0.4, math.sin(a + 1.2) * 0.4, h))
        b.limb("x", CANE if k % 2 else VINE, base, top, 0.06, 0.025, segments=5)
        b.cone("x", THORN, mat_at(tuple((base + top) / 2), rot=(0, 70, math.degrees(a))), 0.025, 0.0, 0.14, segments=4)
        b.cone("x", LEAF[3], mat_at(tuple(top), rot=(rnd.uniform(-40, 40), rnd.uniform(-40, 40), 0), scale=(1, 0.3, 1)), 0.08, 0.0, 0.3, segments=4)
    return b


def hut():
    """Kpelle round house: wattle-and-daub walls, a conical thatched roof."""
    b = Body("hut")
    wall = lambda f: MUD_LIGHT if f.calc_center_median().z > 1.15 else MUD
    jitter(b.cone("x", LATERITE_DARK, mat_at((0, 0, 0.1)), 2.1, 2.05, 0.2, segments=14), 0.02, 2)  # raised floor
    b.cone("x", wall, mat_at((0, 0, 1.0)), 1.8, 1.75, 1.8, segments=14)
    b.box("x", WOOD_DARK, mat_at((0, -1.75, 0.85)), (0.75, 0.12, 1.45))  # doorway
    b.box("x", WOOD, mat_at((0, -1.8, 1.62)), (0.95, 0.1, 0.12))          # lintel
    ring = lambda f: THATCH_DARK if int(f.calc_center_median().z * 4) % 2 else THATCH
    b.cone("x", ring, mat_at((0, 0, 2.95)), 2.55, 0.12, 2.5, segments=14)
    b.cone("x", THATCH_DARK, mat_at((0, 0, 1.78)), 2.6, 2.4, 0.12, segments=14)    # roof edge
    b.cone("x", WOOD_DARK, mat_at((0, 0, 4.35)), 0.08, 0.02, 0.5, segments=5)      # roof pin
    for k in range(3):  # water pot and stools by the door
        b.cone("x", CLAY, mat_at((1.0 + k * 0.4, -2.2, 0.22)), 0.16, 0.2, 0.44, segments=7)
    return b


def shrine():
    """Crossroads offering stone with a carved wooden bowl of rice and a ring of stones."""
    b = Body("shrine")
    jitter(b.cone("x", LATERITE, mat_at((0, 0, 0.3)), 1.0, 0.85, 0.6, segments=9), 0.06, 4)
    b.cone("x", WOOD, mat_at((0, 0, 0.66)), 0.24, 0.42, 0.14, segments=12)                 # bowl wall
    b.cone("x", WOOD_DARK, mat_at((0, 0, 0.72)), 0.38, 0.38, 0.02, segments=12)            # bowl rim
    b.ball("x", RICE, mat_at((0, 0, 0.72), scale=(1, 1, 0.35)), 0.33, segs=(10, 4))        # rice offering
    for k in range(10):
        a = k / 10 * 2 * math.pi
        jitter(b.gem("x", STONE if k % 2 else LATERITE_DARK, mat_at((math.cos(a) * 2.2, math.sin(a) * 2.2, 0.1), scale=(1.2, 1, 0.6)), 0.22), 0.04, k)
    return b


def brazier():
    """Three hearth stones, a clay fire-pot and glowing charcoal. The game adds the flame."""
    b = Body("brazier")
    for k in range(3):
        a = k / 3 * 2 * math.pi
        jitter(b.gem("x", LATERITE_DARK, mat_at((math.cos(a) * 0.55, math.sin(a) * 0.55, 0.18), scale=(1, 1, 1.1)), 0.24), 0.04, k)
    b.cone("x", CLAY, mat_at((0, 0, 0.6)), 0.38, 0.62, 0.62, segments=10)
    b.cone("x", hexcol("#6e3820"), mat_at((0, 0, 0.92)), 0.64, 0.64, 0.05, segments=10)
    for k in range(7):
        a = k / 7 * 2 * math.pi
        b.gem("x", CHARCOAL, mat_at((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.95)), 0.12)
        b.gem("x", EMBER, mat_at((math.cos(a + 0.4) * 0.18, math.sin(a + 0.4) * 0.18, 0.98)), 0.08, mat=1)
    return b


def forge():
    """The smithy: a thatched shade on four posts, stone anvil, bag bellows and a charcoal hearth.
    Laid out to match the game: hearth at game (+1.6, -0.4) = Blender (1.6, 0.4)."""
    b = Body("forge")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.limb("x", WOOD, (sx * 1.45, sy * 1.25, 0), (sx * 1.45, sy * 1.25, 2.3), 0.09, 0.07, segments=5)
    b.cone("x", WOOD_DARK, mat_at((0, 0, 2.3), rot=(0, 0, 45)), 2.35, 2.35, 0.1, segments=4)
    ring = lambda f: THATCH_DARK if int(f.calc_center_median().z * 5) % 2 else THATCH
    b.cone("x", ring, mat_at((0, 0, 2.95), rot=(0, 0, 45)), 2.6, 0.1, 1.3, segments=4)
    # stone anvil with an iron face, a hammer resting on it
    jitter(b.box("x", STONE, mat_at((0, 0, 0.28)), (0.75, 0.55, 0.56)), 0.03, 3)
    b.box("x", IRON, mat_at((0, 0, 0.6)), (0.55, 0.32, 0.08))
    b.limb("x", WOOD, (-0.15, -0.05, 0.66), (0.25, -0.2, 0.66), 0.025)
    b.box("x", IRON, mat_at((-0.17, -0.04, 0.68)), (0.08, 0.14, 0.08))
    # charcoal hearth: a low clay ring full of coals
    b.cone("x", CLAY, mat_at((1.6, 0.4, 0.15)), 0.75, 0.65, 0.3, segments=10)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        r = 0.35 if k % 2 else 0.15
        b.gem("x", CHARCOAL, mat_at((1.6 + math.cos(a) * r, 0.4 + math.sin(a) * r, 0.32)), 0.13)
        b.gem("x", EMBER, mat_at((1.6 + math.cos(a + 0.5) * r * 0.8, 0.4 + math.sin(a + 0.5) * r * 0.8, 0.36)), 0.08, mat=1)
    # two bag bellows with pump sticks, piped into the hearth
    for k, y in enumerate((0.95, 1.4)):
        b.cone("x", LEATHER, mat_at((2.55, y, 0.16)), 0.26, 0.2, 0.32, segments=8)
        b.limb("x", WOOD, (2.55, y, 0.3), (2.6, y, 0.95), 0.03)
        b.limb("x", CLAY, (2.35, y, 0.12), (1.95, 0.55, 0.2), 0.05, segments=5)
    # quench pot and a sack of charcoal
    b.cone("x", CLAY, mat_at((-1.0, 0.9, 0.25)), 0.25, 0.3, 0.5, segments=8)
    jitter(b.ball("x", hexcol("#5a4a36"), mat_at((-1.1, -0.95, 0.3), scale=(1, 0.8, 1.1)), 0.3, segs=(7, 5)), 0.03, 5)
    return b


def slit_drum():
    """Sii's slit-drum: a hollowed log on two forked rests. Runs along X."""
    b = Body("slit_drum")
    b.limb("x", WOOD, (-0.9, 0, 0.55), (0.9, 0, 0.55), 0.42, 0.42, segments=10)
    for x in (-0.9, 0.9):
        b.limb("x", WOOD_DARK, (x * 0.98, 0, 0.55), (x * 1.02, 0, 0.55), 0.44, 0.44, segments=10)  # carved rims
    b.box("x", CHARCOAL, mat_at((0, 0, 0.97)), (1.2, 0.07, 0.02))                                    # the slit
    for x in (-0.6, 0.6):
        b.limb("x", WOOD_DARK, (x, 0, 0), (x, 0, 0.3), 0.07)
        b.limb("x", WOOD_DARK, (x, 0, 0.3), (x, -0.18, 0.45), 0.05)
        b.limb("x", WOOD_DARK, (x, 0, 0.3), (x, 0.18, 0.45), 0.05)
    return b


def rice_bundle():
    """Pickup: rice tied in a twist of country cloth."""
    b = Body("rice")
    stripes = lambda f: CLOTH[int((math.atan2(f.calc_center_median().y, f.calc_center_median().x) + math.pi) * 3 / math.pi) % 3]
    b.ball("x", stripes, mat_at((0, 0, 0.17), scale=(1, 1, 0.85)), 0.19, segs=(9, 6))
    b.cone("x", CLOTH[2], mat_at((0, 0, 0.36)), 0.03, 0.09, 0.12, segments=6)
    b.ball("x", RICE, mat_at((0, -0.12, 0.3), scale=(1, 0.6, 0.5)), 0.07, segs=(5, 4))
    return b


def iron_scrap():
    """Pickup: lumps of smelted iron bloom."""
    b = Body("iron")
    for k, (x, y, s) in enumerate(((0, 0, 0.13), (0.12, 0.06, 0.09), (-0.1, 0.08, 0.08))):
        jitter(b.gem("x", IRON if k != 1 else IRON_RUST, mat_at((x, y, s * 0.8)), s), s * 0.25, k)
    return b


ASSETS = [tree_giant, tree_mid, palm, bush, lambda: rock(1, 0.7, LATERITE), lambda: rock(2, 0.45, STONE),
          vine_clump, hut, shrine, brazier, forge, slit_drum, rice_bundle, iron_scrap]


def build_all():
    env = vertex_color_material("Env")
    glow = glow_material("Glow", EMBER, 4.0)
    objs = []
    for f in ASSETS:
        body = f()
        objs.append(static_object(body.name, body, [env, glow]))
    return objs


def main():
    reset_scene()
    objs = build_all()
    export_glb(MODELS_OUT / "environment.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(560, 560))
        frames = {"tree_giant": (14, 7, 18), "tree_mid": (4, 2.4, 8), "palm": (7, 4, 11), "bush": (0.8, 0.5, 2.6), "rock_1": (0.5, 0.4, 2.2), "rock_2": (0.35, 0.3, 1.6),
                  "vine_clump": (1.0, 0.9, 3.0), "hut": (4.6, 2.2, 8.5), "shrine": (0.8, 0.6, 5.2), "brazier": (1.0, 0.7, 2.4), "forge": (2.8, 1.3, 7.0), "slit_drum": (1.4, 0.6, 3.0),
                  "rice": (0.6, 0.2, 0.9), "iron": (0.4, 0.15, 0.7)}
        shots = []
        for o in objs:
            for other in objs:
                other.hide_render = other is not o
            h, tz, d = frames.get(o.name, (2, 1, 5))
            aim_camera(cam, 30, target=(0, 0, tz), dist=d, height=h)
            p = PREVIEWS_OUT / f"_e{o.name}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "environment.png", cols=7, labels=[o.name for o in objs])


if __name__ == "__main__":
    main()
