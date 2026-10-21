"""The swamp: low flooded ground where the lizard demon hides (episode 2, at night).

A kit of pieces, each one mesh standing at the origin on the ground or water line (z = 0),
for the game to place and instance, like environment.py:
raffia palms (the swamp palm with the biggest leaves in the world), stilt-root trees, dead trees
for the bats, reeds, lily pads, the koong plant (its leaves make the smoke that calms bats),
the River Woman's rocks, mud hummocks, a fallen log, and the root arch over the lizard's lair.
The water itself is drawn by the game.

    python blender/swamp.py            # build + export public/models/swamp.glb
    python blender/swamp.py --preview  # also render a preview sheet
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, aim_camera, contact_sheet, export_glb, glow_material,
                 hexcol, jitter, mat_at, render_to, reset_scene, setup_preview, static_object, vertex_color_material)

BARK = hexcol("#4a3a2c")
BARK_DARK = hexcol("#30261c")
BARK_GREY = hexcol("#6e6a62")
BARK_PALE = hexcol("#8a8478")
FROND = hexcol("#3f6a2c")
FROND_DARK = hexcol("#2c4f22")
FROND_DRY = hexcol("#8a7a44")
LEAF = [hexcol("#2c4a26"), hexcol("#365a2a"), hexcol("#24401f")]
REED = hexcol("#6a7a3a")
REED_DARK = hexcol("#4a5a2a")
CATTAIL = hexcol("#5a3a22")
PAD = hexcol("#3a6a34")
PAD_DARK = hexcol("#2a4e28")
LILY = hexcol("#f0ece2")
LILY_HEART = hexcol("#f2c84a")
KOONG = hexcol("#9fb8a0")
KOONG_VEIN = hexcol("#a8342a")
ROCK = hexcol("#4e5054")
ROCK_WET = hexcol("#3a3c40")
ROCK_MOSS = hexcol("#4a6a34")
MUD = hexcol("#4a3a2a")
MUD_DARK = hexcol("#33281e")
GRASS = hexcol("#4e6a2c")
MOSS = hexcol("#5a7a34")
EMBER = hexcol("#ff5a1f")


def raffia_palm():
    """Short trunk shaggy with old leaf bases, enormous arching fronds."""
    b = Body("raffia_palm")
    rnd = random.Random(2)
    for i in range(4):
        z0, z1 = i * 0.8, (i + 1) * 0.8
        b.cone("x", BARK_DARK if i % 2 else BARK, mat_at((0, 0, (z0 + z1) / 2)), 0.42 - i * 0.03, 0.39 - i * 0.03, 0.8, segments=8)
        for k in range(6):  # shaggy old leaf bases
            a = k / 6 * 2 * math.pi + i
            b.cone("x", FROND_DRY, mat_at((math.cos(a) * 0.38, math.sin(a) * 0.38, z0 + 0.5), rot=(math.degrees(-math.sin(a)) * 1.3, math.degrees(math.cos(a)) * 1.3, 0), scale=(1, 0.3, 1)), 0.1, 0.0, 0.5, segments=4)
    top = Vector((0, 0, 3.3))
    for k in range(9):
        a = k / 9 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        prev = top
        for s, (out, rise) in enumerate(((1.4, 1.5), (1.8, 0.6), (1.8, -0.5), (1.5, -1.3))):
            nxt = prev + d * out + Vector((0, 0, rise))
            mid = (prev + nxt) / 2
            rot = (nxt - prev).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
            m = Matrix.Translation(mid) @ rot @ mat_at(rot=(0, 0, math.degrees(a) + 90), scale=(1, 0.15, 1))
            b.cone("x", FROND if (k + s) % 2 else FROND_DARK, m, 0.5 - s * 0.08, 0.42 - s * 0.1, (nxt - prev).length, segments=4)
            b.limb("x", FROND_DRY, tuple(prev), tuple(nxt), 0.035, 0.025, segments=3)       # midrib
            prev = nxt
    return b


def stilt_tree():
    """A swamp tree raised on arching prop roots, dark crown."""
    b = Body("stilt_tree")
    rnd = random.Random(5)
    base = Vector((0, 0, 1.6))
    for k in range(7):
        a = k / 7 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        foot = Vector((math.cos(a) * 1.6, math.sin(a) * 1.6, -0.2))
        knee = Vector((math.cos(a) * 1.0, math.sin(a) * 1.0, 1.2))
        b.limb("x", BARK_GREY, tuple(base + Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.2))), tuple(knee), 0.12, 0.1, segments=6)
        b.limb("x", BARK_GREY, tuple(knee), tuple(foot), 0.1, 0.07, segments=6)
    jitter(b.limb("x", BARK_GREY, (0, 0, 1.4), (0.2, 0.1, 6.5), 0.35, 0.22, segments=7), 0.03, 1)
    for k in range(5):
        a = k / 5 * 2 * math.pi
        jitter(b.ball("x", LEAF[k % 3], mat_at((math.cos(a) * 1.6 + 0.2, math.sin(a) * 1.6, 7.0 + (k % 2) * 0.5), scale=(1, 1, 0.55)), rnd.uniform(1.4, 1.8), segs=(8, 5)), 0.12, k)
    jitter(b.ball("x", LEAF[1], mat_at((0.2, 0, 7.8), scale=(1, 1, 0.55)), 1.8, segs=(8, 5)), 0.12, 9)
    return b


def dead_tree():
    """A grey snag with bare, crooked branches: where the bats hang."""
    b = Body("dead_tree")
    rnd = random.Random(8)
    pts = [Vector((0, 0, 0)), Vector((0.1, 0.05, 2.5)), Vector((-0.1, 0.1, 5.0)), Vector((0.05, -0.05, 7.2))]
    for i, (a, c) in enumerate(zip(pts, pts[1:])):
        jitter(b.limb("x", BARK_PALE if i % 2 else BARK_GREY, tuple(a), tuple(c), 0.4 - i * 0.1, 0.32 - i * 0.1, segments=7), 0.03, i)
    for k in range(7):
        z = 2.5 + k * 0.7
        a = k * 2.3
        start = Vector((0, 0, z))
        mid = start + Vector((math.cos(a) * 1.2, math.sin(a) * 1.2, 0.5))
        tip = mid + Vector((math.cos(a + 0.6) * 1.0, math.sin(a + 0.6) * 1.0, rnd.uniform(-0.4, 0.8)))
        b.limb("x", BARK_GREY, tuple(start), tuple(mid), 0.12 - k * 0.01, 0.08, segments=5)
        b.limb("x", BARK_PALE, tuple(mid), tuple(tip), 0.08, 0.02, segments=4)
    for k in range(4):  # roots into the mud
        a = k / 4 * 2 * math.pi + 0.4
        b.limb("x", BARK_GREY, (0, 0, 0.4), (math.cos(a) * 1.1, math.sin(a) * 1.1, -0.15), 0.18, 0.06, segments=5)
    return b


def reeds():
    b = Body("reeds")
    rnd = random.Random(11)
    for k in range(16):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0, 0.5)
        base = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        h = rnd.uniform(1.2, 2.2)
        lean = Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), 0))
        b.limb("x", REED if k % 3 else REED_DARK, tuple(base), tuple(base + lean + Vector((0, 0, h))), 0.025, 0.006, segments=3)
        if k % 4 == 0:
            b.limb("x", CATTAIL, tuple(base + lean * 0.85 + Vector((0, 0, h * 0.82))), tuple(base + lean * 0.95 + Vector((0, 0, h * 0.95))), 0.04, segments=5)
    return b


def lily_pads():
    b = Body("lily_pads")
    rnd = random.Random(13)
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.2, 1.2)
        x, y = math.cos(a) * r, math.sin(a) * r
        size = rnd.uniform(0.18, 0.32)
        b.cone("x", PAD if k % 2 else PAD_DARK, mat_at((x, y, 0.01), rot=(0, 0, rnd.uniform(0, 360))), size, size, 0.02, segments=9)
        if k % 3 == 0:
            for p in range(6):
                pa = p / 6 * 2 * math.pi
                b.cone("x", LILY, mat_at((x + math.cos(pa) * 0.05, y + math.sin(pa) * 0.05, 0.06), rot=(math.degrees(-math.sin(pa)) * 0.7, math.degrees(math.cos(pa)) * 0.7, 0), scale=(1, 0.4, 1)), 0.04, 0.0, 0.12, segments=4)
            b.gem("x", LILY_HEART, mat_at((x, y, 0.07)), 0.025)
    return b


def koong_plant():
    """The koong plant: broad silver-green leaves with red veins. Burned, the leaves make the smoke
    that calms bats. (Invented for the game.)"""
    b = Body("koong_plant")
    for k in range(8):
        a = k / 8 * 2 * math.pi
        tilt = 45 + (k % 2) * 15
        leaf = mat_at((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.15), rot=(-math.sin(a) * tilt, math.cos(a) * tilt, 0)) @ mat_at((0, 0, 0.35), scale=(1, 0.18, 1))
        b.ball("x", KOONG, leaf @ mat_at(scale=(1, 0.35, 2.4)), 0.12, segs=(8, 4))
        b.box("x", KOONG_VEIN, leaf @ mat_at((0, 0.05, 0)), (0.015, 0.03, 0.52))
    b.cone("x", KOONG_VEIN, mat_at((0, 0, 0.15)), 0.06, 0.04, 0.3, segments=6)
    return b


def river_rocks():
    """Smooth wet boulders: the big flat one is where the River Woman sits (its top is at 0.55)."""
    b = Body("river_rocks")
    wet = lambda f: ROCK_MOSS if f.calc_center_median().z > 0.5 and f.calc_center_median().x > 0.2 else (ROCK if f.calc_center_median().z > 0.3 else ROCK_WET)
    jitter(b.ball("x", wet, mat_at((0, 0, 0.18), scale=(1.4, 1.1, 0.42)), 0.9, segs=(10, 7)), 0.04, 1)
    jitter(b.ball("x", wet, mat_at((1.3, 0.6, 0.15), scale=(1.0, 0.9, 0.7)), 0.6, segs=(8, 6)), 0.05, 2)
    jitter(b.ball("x", wet, mat_at((-1.2, 0.7, 0.05), scale=(1.1, 1.0, 0.5)), 0.5, segs=(8, 6)), 0.05, 3)
    jitter(b.ball("x", ROCK_WET, mat_at((0.6, -1.0, 0.0), scale=(1.0, 0.8, 0.4)), 0.35, segs=(7, 5)), 0.04, 4)
    return b


def hummock():
    b = Body("hummock")
    rnd = random.Random(17)
    jitter(b.ball("x", lambda f: GRASS if f.calc_center_median().z > 0.25 else MUD, mat_at((0, 0, -0.1), scale=(1.6, 1.3, 0.45)), 1.0, segs=(10, 6)), 0.08, 1)
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0, 0.9)
        base = Vector((math.cos(a) * r * 1.4, math.sin(a) * r, 0.3 - r * 0.25))
        b.cone("x", GRASS, mat_at(tuple(base), rot=(rnd.uniform(-20, 20), rnd.uniform(-20, 20), 0), scale=(1, 0.3, 1)), 0.06, 0.0, 0.5, segments=3)
    return b


def fallen_log():
    b = Body("fallen_log")
    jitter(b.limb("x", BARK, (-2.2, 0, 0.25), (2.2, 0.2, 0.3), 0.38, 0.32, segments=8), 0.03, 1)
    b.cone("x", MUD_DARK, mat_at((2.22, 0.2, 0.3), rot=(0, 90, 0)), 0.3, 0.3, 0.02, segments=8)   # the broken end
    for k in range(5):
        b.ball("x", MOSS, mat_at((-1.8 + k * 0.85, 0.08, 0.6), scale=(1.4, 1, 0.35)), 0.25, segs=(7, 4))
    b.limb("x", BARK_DARK, (-1.0, 0.0, 0.4), (-1.3, 0.8, 1.3), 0.08, 0.03, segments=4)            # a broken branch
    return b


def lair_arch():
    """Twisted roots arching over a hollow in the bank: Meni-maa-fa's lair. Embers inside."""
    b = Body("lair_arch")
    jitter(b.ball("x", MUD, mat_at((0, 0.6, 0.4), scale=(2.2, 1.4, 1.0)), 1.4, segs=(10, 7)), 0.08, 1)
    b.ball("x", MUD_DARK, mat_at((0, -1.25, 0.55), scale=(1.0, 0.45, 0.8)), 0.95, segs=(9, 6))           # the dark mouth
    b.ball("x", hexcol("#120c08"), mat_at((0, -1.55, 0.5), scale=(0.75, 0.3, 0.6)), 0.95, segs=(9, 6))
    for k in range(6):
        a = math.radians(-160 + k * 28)
        p0 = Vector((math.cos(a) * 1.5, -1.6, 0))
        p1 = Vector((math.cos(a) * 1.1, -1.75, 1.5 + math.sin(-a) * 0.3))
        p2 = Vector((0, -1.5, 2.2))
        b.limb("x", BARK_DARK if k % 2 else BARK, tuple(p0), tuple(p1), 0.16, 0.12, segments=6)
        b.limb("x", BARK_DARK if k % 2 else BARK, tuple(p1), tuple(p2), 0.12, 0.08, segments=6)
    for k in range(4):  # embers glowing in the dark
        b.gem("x", EMBER, mat_at((-0.4 + k * 0.27, -1.75, 0.35 + (k % 2) * 0.25)), 0.05, mat=1)
    return b


ASSETS = [raffia_palm, stilt_tree, dead_tree, reeds, lily_pads, koong_plant, river_rocks, hummock, fallen_log, lair_arch]


def build_all():
    env = vertex_color_material("Swamp")
    glow = glow_material("Glow", EMBER, 5.0)
    return [static_object(body.name, body, [env, glow]) for body in (f() for f in ASSETS)]


def main():
    reset_scene()
    objs = build_all()
    export_glb(MODELS_OUT / "swamp.glb")
    if "--preview" in sys.argv:
        cam = setup_preview(size=(520, 520))
        frames = {"raffia_palm": (5, 3, 14), "stilt_tree": (6, 4, 16), "dead_tree": (5, 4, 14), "reeds": (1.5, 1, 4.2), "lily_pads": (2.2, 0, 4.2),
                  "koong_plant": (0.9, 0.4, 2.0), "river_rocks": (2.2, 0.3, 5.5), "hummock": (1.8, 0.2, 5.0), "fallen_log": (2.2, 0.4, 6.5), "lair_arch": (2.4, 1.2, 7.5)}
        shots = []
        for o in objs:
            for other in objs:
                other.hide_render = other is not o
            h, tz, d = frames[o.name]
            aim_camera(cam, 30, target=(0, 0, tz), dist=d, height=h)
            p = PREVIEWS_OUT / f"_sw{o.name}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "swamp.png", cols=5, labels=[o.name.replace("_", " ") for o in objs])


if __name__ == "__main__":
    main()
