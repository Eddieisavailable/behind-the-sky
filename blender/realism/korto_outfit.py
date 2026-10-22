"""Korto's clothes, from "Korto — realism brief" (Costume): country-cloth head tie, sleeveless top,
wrapper hitched at the left hip, dark under-shorts, leather belt with an iron buckle, bracer on the
bow arm, sandals, trade beads and her father's iron bangle."""
import math
import random

import bmesh
import bpy
import mathutils

import costume as C

V = mathutils.Vector

# country-cloth colours (linear)
INDIGO = (0.008, 0.012, 0.04)
INDIGO_FADED = (0.022, 0.032, 0.07)
COTTON = (0.4, 0.33, 0.24)
COTTON_DARK = (0.27, 0.21, 0.14)
KOLA = (0.1, 0.035, 0.014)
RUST = (0.3, 0.085, 0.03)
RED_EARTH = (0.22, 0.075, 0.035)
LEATHER = (0.045, 0.021, 0.01)       # dark tanned hide: the lighter tan matched her skin and read as skin
LEATHER_DARK = (0.024, 0.012, 0.007)
IRON = (0.32, 0.31, 0.3)


def materials():
    return {
        "wrapper": C.country_cloth("Wrapper", [
            [(INDIGO, 0.42), (COTTON, 0.06), (INDIGO, 0.42), (COTTON, 0.1)],
            [(COTTON, 0.7), (KOLA, 0.1), (COTTON, 0.2)],
            [(KOLA, 0.35), (INDIGO, 0.3), (KOLA, 0.35)],
            [(COTTON, 0.15), (INDIGO, 0.7), (COTTON, 0.15)],
        ], strip_width=0.105, dirt=(RED_EARTH, 0.5), wear=0.2),
        "top": C.country_cloth("Top", [
            [(COTTON, 0.47), (COTTON_DARK, 0.06), (COTTON, 0.47)],
        ], strip_width=0.12, wear=0.3),
        "headtie": C.country_cloth("HeadTie", [
            [(INDIGO_FADED, 0.8), (COTTON, 0.05), (INDIGO_FADED, 0.15)],
            [(INDIGO, 0.9), (INDIGO_FADED, 0.1)],
        ], strip_width=0.09, wear=0.4),
        "shorts": C.simple_material("Shorts", (0.025, 0.02, 0.018), rough=0.9, bump_scale=900, bump=0.15),
        "leather": C.simple_material("Leather", LEATHER, rough=0.55, bump_scale=300, bump=0.25, coat=0.1),
        "leather_dark": C.simple_material("LeatherDark", LEATHER_DARK, rough=0.6, bump_scale=300, bump=0.25),
        "iron": C.simple_material("Iron", IRON, rough=0.42, metal=1.0, bump_scale=150, bump=0.35),
    }


def dress(human, rig, eye_z, eye_front):
    mats = materials()
    body = C.Body(human, rig)
    B = body
    pelvis = B.head("pelvis")
    cx, cy = pelvis.x, pelvis.y
    hip_z = pelvis.z
    waist_z = B.head("spine_02").z
    chest_z = B.head("spine_03").z + 0.04
    clav_z = B.head("clavicle_l").z
    arm_x = abs(B.head("upperarm_l").x)
    knee_z = B.head("calf_l").z
    ankle_z = B.head("foot_l").z
    made = {}

    def torso_xy(p):
        return math.hypot(p.x - cx, (p.y - cy) * 1.25)

    # ---------------- top: sleeveless, scooped neck, falls straight from the bust to just below the waist
    def top_keep(p, n):
        if p.z < waist_z - 0.06 or p.z > clav_z + 0.03:
            return False
        if abs(p.x - cx) > arm_x - 0.015:              # armholes
            return False
        if p.z > clav_z - 0.11 and abs(p.x - cx) > arm_x - 0.06 and p.z > chest_z:
            return False
        front = p.y < cy
        neck = clav_z - 0.005 - (0.075 * max(0.0, 1 - abs(p.x - cx) / 0.1) if front else 0.0)
        return p.z < neck or abs(p.x - cx) > 0.085
    def top_off(p, n):
        below = max(0.0, min(1.0, (chest_z - p.z) / 0.16))
        return 0.006 + 0.012 * below * (1 if p.y < cy + 0.02 else 0.4)
    made["top"] = C.shell(B, "KortoTop", top_keep, top_off, 0.0018, mats["top"])
    smooth_edges(made["top"])

    # ---------------- under-shorts to mid-thigh
    def shorts_keep(p, n):
        return (B.head("thigh_l").z - 0.2 < p.z < waist_z - 0.02) and abs(p.x - cx) < 0.24
    made["shorts"] = C.shell(B, "KortoShorts", shorts_keep, 0.003, 0.0015, mats["shorts"])
    smooth_edges(made["shorts"])

    # ---------------- wrapper: draped by cloth simulation, wrapped once and a bit, open at the left hip
    top_z = hip_z + 0.045
    bot_z = knee_z - 0.09
    ring = [p for p in B.ring(top_z, 0.012) if abs(p.x - cx) < 0.2]     # not her hands, which hang here
    r_top = max(math.hypot(p.x - cx, p.y - cy) for p in ring) + 0.012
    made["wrapper"] = wrapper(B, mats["wrapper"], (cx, cy), top_z, bot_z, r_top)

    # ---------------- belt over the wrapper's top edge, with an iron buckle at the front
    made["belt"] = C.band(B, "KortoBelt", (cx, cy), top_z + 0.012, 0.045, 0.012, mats["leather"])
    front_y = min(p.y for p in B.ring(top_z + 0.012, 0.01) if abs(p.x - cx) < 0.04) - 0.026
    made["buckle"] = buckle(mats["iron"], V((cx, front_y, top_z + 0.012)))

    # ---------------- head tie: wrapped high, with a knot at the back and the ends tucked
    def tie_line(ang):
        """Height of the tie's lower edge above the eyes, by angle round the head (0 = front):
        high on the forehead, over the tops of the ears, low at the nape. Smooth, so the edge is clean."""
        t = max(0.0, min(1.0, (ang - 45.0) / 85.0))
        t = t * t * (3 - 2 * t)
        return 0.034 + (-0.016 - 0.034) * t
    def tie_keep(p, n):
        if p.z < eye_z - 0.03:
            return False
        ang = abs(math.degrees(math.atan2(p.x, -(p.y - (eye_front + 0.085)))))
        return p.z > eye_z + tie_line(ang)
    def tie_off(p, n):
        # wrapped high: the cloth stands off the crown and builds up toward the back, where the
        # turns gather into the knot
        crown = max(0.0, min(1.0, (p.z - (eye_z + 0.06)) / 0.08))
        back = max(0.0, min(1.0, (p.y - eye_front - 0.06) / 0.1))
        return 0.012 + 0.045 * crown + 0.04 * crown * back + 0.012 * back
    # the cloth goes round the head several times, rising toward the back: each turn leaves a ridge
    head_c = V((0, eye_front + 0.085, eye_z))
    def wraps(p, n):
        rel = p - head_c
        ang = math.atan2(rel.x, -rel.y)
        # two sets of turns climbing toward the back from opposite sides cross at the forehead in a V;
        # each turn leaves a rolled ridge where it overlaps the one below
        k1 = rel.z - 0.03 * math.cos(ang) - 0.05 * math.sin(ang) * math.cos(ang / 2)
        k2 = rel.z - 0.03 * math.cos(ang) + 0.05 * math.sin(ang) * math.cos(ang / 2)
        front = max(0.0, math.cos(ang)) ** 2
        r1 = (0.5 + 0.5 * math.sin(k1 * 2 * math.pi / 0.034)) ** 3
        r2 = (0.5 + 0.5 * math.sin(k2 * 2 * math.pi / 0.034)) ** 3
        ridge = 0.009 * (r1 * (0.5 + 0.5 * front) + r2 * front * 0.8)
        return n * ridge
    tie = C.shell(B, "KortoHeadTie", tie_keep, tie_off, 0.002, mats["headtie"], smooth=2, extra=wraps)
    edge_z = lambda ang: eye_z + tie_line(ang) + 0.004
    hem_loop = clean_edge(tie, head_c, edge_z)
    folds(tie, 0.003, 60.0)
    made["headtie"] = tie
    made["hem"] = hem(hem_loop, mats["headtie"], "KortoTieHem", 0.0055)
    made["knot"] = knot(mats["headtie"], V((0, eye_front + 0.2, eye_z + 0.13)))

    # ---------------- bracer on the left forearm (her bow arm)
    a, b = B.head("lowerarm_l"), B.head("hand_l")
    axis = (b - a)
    def bracer_keep(p, n):
        t = (p - a).dot(axis) / axis.length_squared
        return 0.4 < t < 0.88 and (p - (a + axis * t)).length < 0.06
    made["bracer"] = C.shell(B, "KortoBracer", bracer_keep, 0.004, 0.003, mats["leather_dark"])
    smooth_edges(made["bracer"])

    # ---------------- sandals: a hide sole and an ankle strap
    made["sole_l"] = C.sole(B, "KortoSoleL", 1, mats["leather_dark"], cx)
    made["sole_r"] = C.sole(B, "KortoSoleR", -1, mats["leather_dark"], cx)
    def strap_keep(p, n):
        return abs(p.z - (ankle_z - 0.01)) < 0.011 and abs(p.x - cx) > 0.03
    made["straps"] = C.shell(B, "KortoStraps", strap_keep, 0.003, 0.002, mats["leather"])

    # ---------------- trade beads and the iron bangle
    made["beads"] = beads(human, B, clav_z, cx, cy)
    made["bangle"] = bangle(mats["iron"], B.head("hand_r"), B.head("lowerarm_r"))

    for name in ("top", "shorts", "belt", "headtie", "bracer", "straps"):
        if name == "belt":
            continue
        C.cylinder_uv(made[name], (cx, cy))
    return made


# ---------------------------------------------------------------- pieces

def wrapper(B, material, center, top_z, bot_z, r_top, cols=96, rows=30):
    cx, cy = center
    me = bpy.data.meshes.new("KortoWrapper")
    bm = bmesh.new()
    turn = 2 * math.pi + 0.95                       # once round and a bit: the end overlaps at the front-left
    start = math.radians(70)                         # the open edge sits at her left hip
    grid = []
    for r in range(rows):
        t = r / (rows - 1)
        z = top_z + (bot_z - top_z) * t
        row = []
        for c in range(cols):
            a = start + turn * c / (cols - 1)
            rad = (r_top + 0.012 * (c / (cols - 1))) * (1.0 + 0.1 * t)   # hangs nearly straight; the legs push it out
            # gathered at the waist into soft pleats that open toward the hem, pulling toward the knot
            pleat = 0.012 * (0.4 + t) * math.sin(13 * a + 2.5 * t + 0.8 * math.sin(3 * a))
            rad += pleat
            zz = z + 0.07 * t * max(0.0, math.sin(a)) ** 2          # hitched up on her left side
            row.append(bm.verts.new((cx + math.sin(a) * rad, cy - math.cos(a) * rad, zz)))
        grid.append(row)
    grid_index = {v: r * cols + c for r, row in enumerate(grid) for c, v in enumerate(row)}
    for r in range(rows - 1):
        for c in range(cols - 1):
            bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
    uv = bm.loops.layers.uv.new("UVMap")
    width = turn * r_top
    for f in bm.faces:
        for loop in f.loops:
            i = grid_index[loop.vert]
            r, c = divmod(i, cols)
            loop[uv].uv = (width * c / (cols - 1), -(bot_z - top_z) * r / (rows - 1) + top_z)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("KortoWrapper", me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    pin = obj.vertex_groups.new(name="pin")
    pin.add([i for i in range(cols * 2)], 1.0, "REPLACE")
    C.drape(obj, B.human, "pin", frames=50)
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = 0.002
    sol.offset = 1.0
    sub = obj.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    return obj


def folds(obj, depth, scale):
    """Small soft folds in wrapped cloth."""
    tex = bpy.data.textures.new(obj.name + "Folds", "CLOUDS")
    tex.noise_scale = 1.0 / scale
    d = obj.modifiers.new("Folds", "DISPLACE")
    d.texture = tex
    d.strength = depth
    d.texture_coords = "GLOBAL"
    d.mid_level = 0.5


def smooth_edges(obj, iterations=10):
    """Smooth a shell garment's open edges (armholes, neckline, hems): the region test leaves them
    saw-toothed along the body's triangles. Each edge vertex moves toward the middle of its two edge
    neighbours, in all three directions, so the line runs clean."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    edge = {v for e in bm.edges if e.is_boundary for v in e.verts}
    for _ in range(iterations):
        new = {}
        for v in edge:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2:
                new[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
        for v, co in new.items():
            v.co = co
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def clean_edge(obj, center, edge_z, iterations=6, step_deg=4):
    """Tidy a shell garment's open edge: the region test leaves it stepped along the body's triangles.
    Cloth below the intended line (edge_z(angle), angle in degrees round `center`, 0 = front) is lifted
    onto it, the edge is smoothed, and an even ring of points along the edge is returned for a hem."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    def ang_of(co):
        rel = co - center
        return math.degrees(math.atan2(rel.x, -rel.y))
    for v in bm.verts:
        z = edge_z(abs(ang_of(v.co)))
        if v.co.z < z:
            v.co.z = z
    edge = {v for e in bm.edges if e.is_boundary for v in e.verts}
    for _ in range(iterations):        # smooth the edge sideways, keeping its height
        new = {}
        for v in edge:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2:
                avg = (nb[0].co + nb[1].co) / 2
                new[v] = V((v.co.x * 0.5 + avg.x * 0.5, v.co.y * 0.5 + avg.y * 0.5, v.co.z))
        for v, co in new.items():
            v.co = co
    # the edge's distance from the head's axis, by angle, smoothed round the head
    bins = {}
    for v in edge:
        rel = v.co - center
        k = int(round(ang_of(v.co) / step_deg)) % (360 // step_deg)
        bins.setdefault(k, []).append(math.hypot(rel.x, rel.y))
    n = 360 // step_deg
    radius = [sum(bins[k]) / len(bins[k]) if k in bins else None for k in range(n)]
    known = [k for k in range(n) if radius[k] is not None]
    for k in range(n):                 # fill gaps from the nearest known angles
        if radius[k] is None:
            nearest = min(known, key=lambda j: min(abs(j - k), n - abs(j - k)))
            radius[k] = radius[nearest]
    for _ in range(3):
        radius = [(radius[k - 1] + 2 * radius[k] + radius[(k + 1) % n]) / 4 for k in range(n)]
    loop = []
    for k in range(n):
        a = math.radians(k * step_deg)
        r = radius[k] + 0.002
        loop.append(V((center.x + r * math.sin(a), center.y - r * math.cos(a), edge_z(abs(math.degrees(math.atan2(math.sin(a), math.cos(a))))))))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return loop


def hem(points, material, name, radius):
    """A rolled hem along a garment edge: a closed tube through `points`."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, pt in zip(sp.points, points):
        p.co = (pt.x, pt.y, pt.z, 1.0)
    sp.use_cyclic_u = True
    obj = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(obj)
    cu.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.scene.objects:
        o.select_set(o is obj)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.view_layer.objects.active
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj   # no UVs: the export wraps cloth UVs round it like the other pieces


def knot(material, at):
    """The head tie's knot: two bunched lobes and two short tucked ends."""
    me = bpy.data.meshes.new("KortoKnot")
    bm = bmesh.new()
    for dx, s in ((-0.022, 1.0), (0.024, 0.85)):
        ret = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.034 * s,
                                         matrix=mathutils.Matrix.Translation(at + V((dx, 0.005, 0.0))))
        rnd = random.Random(int(dx * 1000))
        for v in ret["verts"]:
            v.co = at + V((dx, 0.005, 0)) + (v.co - at - V((dx, 0.005, 0))) * V((1.0, 0.75, 0.8)) * (0.92 + 0.12 * rnd.random())
    for side in (-1, 1):                         # ends tucked down the back of the tie
        ret = bmesh.ops.create_cube(bm, size=1.0)
        for v in ret["verts"]:
            v.co = at + V((side * 0.012, 0.02, -0.05)) + V((v.co.x * 0.035, v.co.y * 0.006, v.co.z * 0.06))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("KortoKnot", me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    s = obj.modifiers.new("Smooth", "SUBSURF")
    s.levels = s.render_levels = 1
    folds(obj, 0.004, 80.0)
    return obj


def buckle(material, at):
    me = bpy.data.meshes.new("KortoBuckle")
    bm = bmesh.new()
    ret = bmesh.ops.create_cube(bm, size=1.0)
    for v in ret["verts"]:
        v.co = at + V((v.co.x * 0.05, v.co.y * 0.008, v.co.z * 0.045))
    bmesh.ops.bevel(bm, geom=ret["verts"] + bm.edges[:], offset=0.003, segments=2, affect="EDGES")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("KortoBuckle", me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    return obj


def beads(human, B, clav_z, cx, cy):
    """One strand of old glass trade beads, lying on the skin round the base of the neck, lower at the front."""
    import human_lib as H
    colours = [(0.02, 0.07, 0.25), (0.6, 0.58, 0.52), (0.28, 0.06, 0.025)]
    mats = [C.simple_material(f"Bead{i}", c, rough=0.15, coat=0.5) for i, c in enumerate(colours)]
    me = bpy.data.meshes.new("KortoBeads")
    bm = bmesh.new()
    ids = []
    neck = B.head("neck_01")
    count = 64
    for i in range(count):
        a = 2 * math.pi * i / count
        drop = 0.05 * (0.5 + 0.5 * math.cos(a)) ** 2        # hangs lower at the front (a = 0)
        z = clav_z + 0.035 - drop
        d = V((math.sin(a), -math.cos(a), 0))
        # aim from just outside the neck (rays from far out hit the shoulders first at the sides)
        reach = 0.11 + 0.05 * (0.5 + 0.5 * math.cos(a))
        p, n = H.surface_point(human, (cx + d.x * reach, neck.y + d.y * reach, z), (-d.x, -d.y, -0.25), 0.3)
        if p is None:
            continue
        ret = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.0048,
                                        matrix=mathutils.Matrix.Translation(p + n * 0.0055))
        ids.append((ret["verts"], i % 3))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("KortoBeads", me)
    bpy.context.scene.collection.objects.link(obj)
    for m in mats:
        me.materials.append(m)
    # colour each bead: faces in order of creation, 10*6 per sphere
    per = len(me.polygons) // max(1, len(ids))
    for bi, (_, ci) in enumerate(ids):
        for f in me.polygons[bi * per:(bi + 1) * per]:
            f.material_index = ci
            f.use_smooth = True
    return obj


def bangle(material, wrist, elbow):
    axis = (wrist - elbow).normalized()
    at = wrist - axis * 0.045
    me = bpy.data.meshes.new("KortoBangle")
    bm = bmesh.new()
    rot = axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
    # a torus: a small circle swept round the wrist, a little taller than wide (a forged band)
    major, minor, seg, ring = 0.034, 0.0045, 40, 10
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(ring):
            b = 2 * math.pi * j / ring
            r = major + minor * math.cos(b)
            co = V((r * math.cos(a), r * math.sin(a), minor * 1.4 * math.sin(b)))
            verts.append(bm.verts.new(at + rot @ co))
    for i in range(seg):
        for j in range(ring):
            a = verts[i * ring + j]
            b2 = verts[((i + 1) % seg) * ring + j]
            c = verts[((i + 1) % seg) * ring + (j + 1) % ring]
            d = verts[i * ring + (j + 1) % ring]
            bm.faces.new((a, b2, c, d))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("KortoBangle", me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    return obj
