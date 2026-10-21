"""The bele tree: the demon-grown tree Meni-maa-fa raised to seal the sky road (episode 3, the boss).

About 44 m tall in game metres. Unlike the kit files, this is one assembly whose parts keep their
places, and each part the game needs to act on is its own named object:

  Trunk        buttress roots, the twisted trunk, ember veins, rattan coiled round it
  Platform1-12 branch platforms spiralling up the trunk (the climb); tops are flat and walkable
  Vine1-11     rattan ropes hanging from each platform to the one below (climbed between platforms)
  CutBranch1-3 the three great branches near the top that the hero cuts and burns while the
               lizard heals them (boss phase 1)
  Canopy       the crown that blocks the sky
  RiceSack1-5  Gbelewala's stolen seed rice, bundled in country cloth, hung under the crown;
               when the tree burns they fall on the village like rain

    python blender/bele_tree.py            # build + export public/models/bele_tree.glb
    python blender/bele_tree.py --preview  # also render a preview sheet
"""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Body, MODELS_OUT, PREVIEWS_OUT, Matrix, Vector, aim_camera, contact_sheet, export_glb, glow_material,
                 hexcol, jitter, mat_at, render_to, reset_scene, setup_preview, static_object, vertex_color_material)

BARK = hexcol("#3b2c2c")
BARK_DARK = hexcol("#271d1e")
BARK_LIGHT = hexcol("#54403c")
CANE = hexcol("#b8894f")
CANE_DARK = hexcol("#8a6234")
THORN = hexcol("#2a1f16")
LEAF = [hexcol("#1f3320"), hexcol("#263d24"), hexcol("#18291a"), hexcol("#2e3f22")]
FRUIT = hexcol("#7a1f1a")
CLOTH = [hexcol("#2d3a6b"), hexcol("#e9dcc0"), hexcol("#a4532c")]
EMBER = hexcol("#ff4a1a")

HEIGHT = 36.0          # top of the trunk
PLATFORMS = 12


def trunk_radius(z):
    return 3.2 - 1.7 * min(1.0, z / HEIGHT)


def trunk_axis(z):
    """The trunk leans and twists a little as it climbs."""
    return Vector((math.sin(z * 0.11) * 0.6, math.cos(z * 0.09) * 0.4 - 0.4, z))


def bark(f):
    c = f.calc_center_median()
    return BARK_LIGHT if (int(c.z * 1.3) + int(math.atan2(c.y, c.x) * 3)) % 5 == 0 else (BARK_DARK if int(c.z * 2) % 3 == 0 else BARK)


def build_trunk():
    b = Body("Trunk")
    rnd = random.Random(3)
    # trunk: stacked, twisted sections
    z = 0.0
    while z < HEIGHT:
        z1 = min(HEIGHT, z + 3.0)
        a, c = trunk_axis(z), trunk_axis(z1)
        jitter(b.limb("x", bark, tuple(a), tuple(c), trunk_radius(z), trunk_radius(z1), segments=12), 0.1, int(z))
        z = z1
    # buttress roots: tall fins and roots snaking over the ground
    for k in range(7):
        a = k / 7 * 2 * math.pi + 0.2
        b.box("x", BARK if k % 2 else BARK_DARK, mat_at((math.cos(a) * 3.6, math.sin(a) * 3.6, 1.6), rot=(0, 0, math.degrees(a))) @ mat_at(rot=(0, -30, 0)), (4.2, 0.55, 4.5))
        root = Vector((math.cos(a) * 4.5, math.sin(a) * 4.5, 0.3))
        for s in range(3):
            nxt = root + Vector((math.cos(a + rnd.uniform(-0.4, 0.4)) * 2.2, math.sin(a + rnd.uniform(-0.4, 0.4)) * 2.2, -0.12))
            b.limb("x", BARK_DARK, tuple(root), tuple(nxt), 0.45 - s * 0.12, 0.35 - s * 0.12, segments=6)
            root = nxt
    # ember veins: demon sap glowing in cracks up the bark
    for v in range(5):
        a0 = v / 5 * 2 * math.pi
        prev = None
        for i in range(24):
            z = 1.0 + i * 1.4
            a = a0 + z * 0.08
            r = trunk_radius(z) * 1.01
            p = trunk_axis(z) + Vector((math.cos(a) * r, math.sin(a) * r, 0))
            if prev is not None:
                b.limb("x", EMBER, tuple(prev), tuple(p), 0.06, segments=3, mat=1)
            prev = p
    # rattan coiled round the trunk, thorned
    for v in range(2):
        prev = None
        for i in range(60):
            t = i / 59
            z = 0.5 + t * (HEIGHT - 2)
            a = v * math.pi + t * 7 * math.pi
            r = trunk_radius(z) + 0.18
            p = trunk_axis(z) + Vector((math.cos(a) * r, math.sin(a) * r, 0))
            if prev is not None:
                b.limb("x", CANE if i % 2 else CANE_DARK, tuple(prev), tuple(p), 0.13, segments=5)
                if i % 3 == 0:
                    b.cone("x", THORN, mat_at(tuple(p), rot=(-math.sin(a) * 80, math.cos(a) * 80, 0)), 0.06, 0.0, 0.35, segments=4)
            prev = p
    return b


def platform_spot(i):
    """Where branch platform i leaves the trunk, its direction and its height."""
    z = 2.4 + i * 2.6
    a = i * math.radians(52) + 0.3
    return z, a


def build_platform(i):
    z, a = platform_spot(i)
    d = Vector((math.cos(a), math.sin(a), 0))
    side = Vector((-d.y, d.x, 0))
    start = trunk_axis(z) + d * (trunk_radius(z) * 0.7)
    end = start + d * 4.2 + Vector((0, 0, 0.5))
    b = Body(f"Platform{i + 1}")
    b.limb("x", BARK, tuple(start - Vector((0, 0, 0.5))), tuple(end - Vector((0, 0, 0.45))), 0.75, 0.45, segments=8)     # the branch
    # flat walkable top, a little wider than a person
    mid = (start + end) / 2
    rot = Matrix((d, side, Vector((0, 0, 1)))).transposed().to_4x4()
    b.box("x", BARK_LIGHT, Matrix.Translation(mid) @ rot, ((end - start).length, 1.7, 0.3))
    for k in range(3):   # knots and a curl of fresh growth at the tip
        b.gem("x", BARK_DARK, mat_at(tuple(start + d * (1 + k * 1.2) + side * (0.85 if k % 2 else -0.85))), 0.22)
    b.ball("x", LEAF[i % 4], mat_at(tuple(end + d * 0.6 + Vector((0, 0, 0.3))), scale=(1, 1, 0.6)), 0.9, segs=(7, 4))
    return b


def build_vine(i):
    """A rattan rope from platform i+1's tip down to platform i's tip."""
    b = Body(f"Vine{i + 1}")
    z0, a0 = platform_spot(i)
    z1, a1 = platform_spot(i + 1)
    p0 = trunk_axis(z0) + Vector((math.cos(a0), math.sin(a0), 0)) * (trunk_radius(z0) * 0.7 + 3.6) + Vector((0, 0, 0.3))
    p1 = trunk_axis(z1) + Vector((math.cos(a1), math.sin(a1), 0)) * (trunk_radius(z1) * 0.7 + 3.2) + Vector((0, 0, 0.2))
    mid = (p0 + p1) / 2 + Vector((0, 0, -0.6))
    for k, (a, c) in enumerate(((p1, mid), (mid, p0))):
        b.limb("x", CANE if k else CANE_DARK, tuple(a), tuple(c), 0.08, segments=5)
    for k in range(4):   # hand-holds: bindings along the rope
        t = (k + 1) / 5
        p = p1 + (p0 - p1) * t + Vector((0, 0, -0.6 * math.sin(t * math.pi)))
        b.limb("x", THORN, tuple(p + Vector((0, 0, 0.05))), tuple(p - Vector((0, 0, 0.05))), 0.12, segments=5)
    return b


def build_cut_branch(i):
    """A great branch near the top: what the hero cuts and burns while the lizard heals it."""
    z = HEIGHT - 4.5 + i * 1.6
    a = i * math.radians(120) + 1.1
    d = Vector((math.cos(a), math.sin(a), 0.35)).normalized()
    start = trunk_axis(z) + Vector((math.cos(a), math.sin(a), 0)) * (trunk_radius(z) * 0.6)
    elbow = start + d * 4.5
    tip = elbow + Vector((math.cos(a + 0.3), math.sin(a + 0.3), 0.15)) * 4.0
    b = Body(f"CutBranch{i + 1}")
    jitter(b.limb("x", bark, tuple(start), tuple(elbow), 0.9, 0.6, segments=9), 0.06, i)
    b.limb("x", BARK, tuple(elbow), tuple(tip), 0.6, 0.25, segments=8)
    b.cone("x", EMBER, Matrix.Translation(start + d * 1.2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4(), 0.94, 0.94, 0.12, segments=9, mat=1)  # the glowing joint where he heals it
    for k in range(4):
        p = elbow + (tip - elbow) * (0.3 + k * 0.23) + Vector((0, 0, 0.6))
        jitter(b.ball("x", LEAF[k % 4], mat_at(tuple(p), scale=(1, 1, 0.55)), 1.5 + k * 0.2, segs=(8, 5)), 0.12, k)
    return b


def build_canopy():
    b = Body("Canopy")
    rnd = random.Random(9)
    top = trunk_axis(HEIGHT)
    for k in range(9):   # limbs spreading into the crown
        a = k / 9 * 2 * math.pi
        p = top + Vector((math.cos(a) * 7, math.sin(a) * 7, 3.5))
        b.limb("x", BARK, tuple(top - Vector((0, 0, 1))), tuple(p), 0.8, 0.35, segments=7)
    for ring, (r, n, zoff, size) in enumerate(((0, 1, 6.5, 6.5), (6, 7, 4.8, 4.6), (11, 11, 3.6, 3.8))):
        for k in range(n):
            a = k / max(1, n) * 2 * math.pi + ring * 0.3
            p = top + Vector((math.cos(a) * r, math.sin(a) * r, zoff + rnd.uniform(-0.6, 0.6)))
            jitter(b.ball("x", LEAF[(k + ring) % 4], mat_at(tuple(p), scale=(1, 1, 0.42)), size * rnd.uniform(0.9, 1.1), segs=(10, 6)), 0.35, k + ring * 20)
    for k in range(14):  # dark red demon fruit hanging under the crown
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(3, 11)
        p = top + Vector((math.cos(a) * r, math.sin(a) * r, 2.0))
        b.gem("x", FRUIT, mat_at(tuple(p), scale=(1, 1, 1.3)), 0.35)
    return b


def build_sack(i):
    top = trunk_axis(HEIGHT)
    a = i / 5 * 2 * math.pi + 0.5
    r = 4.5 + (i % 2) * 2.5
    hang = top + Vector((math.cos(a) * r, math.sin(a) * r, 2.6))
    sack = hang - Vector((0, 0, 3.0 + (i % 3) * 0.8))
    b = Body(f"RiceSack{i + 1}")
    b.limb("x", CANE_DARK, tuple(hang), tuple(sack + Vector((0, 0, 0.6))), 0.05, segments=4)
    stripes = lambda f, s=sack: CLOTH[int((math.atan2(f.calc_center_median().y - s.y, f.calc_center_median().x - s.x) + math.pi) * 3 / math.pi) % 3]
    b.ball("x", stripes, mat_at(tuple(sack), scale=(1, 1, 1.15)), 0.6, segs=(9, 6))
    b.cone("x", CLOTH[2], mat_at(tuple(sack + Vector((0, 0, 0.65)))), 0.12, 0.25, 0.3, segments=6)
    return b


def build_all():
    bark_mat = vertex_color_material("BeleTree", roughness=0.85)
    glow = glow_material("Glow", EMBER, 6.0)
    mats = [bark_mat, glow]
    parts = [static_object("Trunk", build_trunk(), mats)]
    parts += [static_object(f"Platform{i + 1}", build_platform(i), mats) for i in range(PLATFORMS)]
    parts += [static_object(f"Vine{i + 1}", build_vine(i), mats) for i in range(PLATFORMS - 1)]
    parts += [static_object(f"CutBranch{i + 1}", build_cut_branch(i), mats) for i in range(3)]
    parts.append(static_object("Canopy", build_canopy(), mats))
    parts += [static_object(f"RiceSack{i + 1}", build_sack(i), mats) for i in range(5)]
    return parts


def climb_data():
    """Where the walkable platform tops and the climbable vines are, for the game (Blender metres, z up)."""
    plats = []
    for i in range(PLATFORMS):
        z, a = platform_spot(i)
        d = Vector((math.cos(a), math.sin(a), 0))
        start = trunk_axis(z) + d * (trunk_radius(z) * 0.7)
        end = start + d * 4.2 + Vector((0, 0, 0.5))
        mid = (start + end) / 2
        plats.append({"mid": [round(mid.x, 3), round(mid.y, 3)], "dir": [round(d.x, 4), round(d.y, 4)],
                      "length": round((end - start).length, 3), "width": 1.7, "top": round(mid.z + 0.15, 3),
                      "tip": [round(end.x - d.x * 0.5, 3), round(end.y - d.y * 0.5, 3)]})
    trunk = []
    for k in range(0, 41, 2):
        ax = trunk_axis(float(k))
        trunk.append([float(k), round(ax.x, 3), round(ax.y, 3), round(trunk_radius(float(k)), 3)])
    return {"platforms": plats, "trunk": trunk, "height": HEIGHT,
            "crown": [round(trunk_axis(HEIGHT).x, 3), round(trunk_axis(HEIGHT).y, 3), HEIGHT + 4]}


def main():
    reset_scene()
    parts = build_all()
    export_glb(MODELS_OUT / "bele_tree.glb")
    (MODELS_OUT / "bele_tree.json").write_text(json.dumps(climb_data(), indent=1))
    if "--preview" in sys.argv:
        cam = setup_preview(size=(600, 760))
        views = [(20, 20, 70, 14), (200, 22, 70, 14), (35, 10, 26, 8), (60, 33, 26, 38)]
        shots = []
        for i, (ang, tz, dist, h) in enumerate(views):
            aim_camera(cam, ang, target=(0, 0, tz), dist=dist, height=h)
            cam.data.clip_end = 400
            p = PREVIEWS_OUT / f"_bele{i}.png"
            render_to(p)
            shots.append(p)
        contact_sheet(shots, PREVIEWS_OUT / "bele-tree.png", cols=4,
                      labels=["The bele tree", "Other side", "The climb: platforms and vines", "Top: cut branches, rice sacks"])


if __name__ == "__main__":
    main()
