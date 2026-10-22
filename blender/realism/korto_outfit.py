"""Korto's clothes, from "Korto — realism brief" (Costume): country-cloth head tie, sleeveless top,
wrapper hitched at the left hip, dark under-shorts, leather belt with an iron buckle, bracer on the
bow arm, sandals, trade beads and her father's iron bangle."""
import math
import random

import bmesh
import bpy
import mathutils

import costume as C
import human_lib as H

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
        # armholes: an oval in the front view, from the strap at the shoulder down past the armpit
        # (two stacked rectangles cut it square before)
        ox, oz = arm_x + 0.01, clav_z - 0.02
        if ((abs(p.x - cx) - ox) / 0.075) ** 2 + ((p.z - oz) / 0.13) ** 2 < 1.0:
            return False
        if abs(p.x - cx) > arm_x + 0.005:              # the arm itself
            return False
        front = p.y < cy
        neck = clav_z - 0.005 - (0.075 * max(0.0, 1 - abs(p.x - cx) / 0.1) if front else 0.0)
        return p.z < neck or abs(p.x - cx) > 0.085
    def top_off(p, n):
        # fitted: close over the stomach (hanging straight down from the bust read as a big belly)
        below = max(0.0, min(1.0, (chest_z - p.z) / 0.16))
        back = 1.0 if p.y > cy else 0.0                 # her lower back showed through it at the dimples
        return 0.004 + 0.003 * below + 0.004 * back * below
    made["top"] = C.shell(B, "KortoTop", top_keep, top_off, 0.0018, mats["top"])
    bridge_dents(made["top"])
    smooth_edges(made["top"])

    # ---------------- under-shorts to mid-thigh
    def shorts_keep(p, n):
        return (B.head("thigh_l").z - 0.2 < p.z < waist_z - 0.02) and abs(p.x - cx) < 0.24
    made["shorts"] = C.shell(B, "KortoShorts", shorts_keep, 0.003, 0.0015, mats["shorts"])
    smooth_edges(made["shorts"])

    # ---------------- wrapper: draped by cloth simulation, wrapped once and a bit, open at the left hip
    top_z = hip_z + 0.045
    bot_z = knee_z - 0.06            # just below the knee: lower, the calf caught the hem when the knee bent
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
    def layer_edge(z, ang):
        """Two turns of cloth cross in a V over the forehead and run back round the sides. Above each
        turn's lower edge the cloth stands out by one layer, a soft step a few millimetres high:
        overlapping layers are what make it read as wrapped cloth rather than a cap."""
        lift = 0.0
        for sign in (1, -1):
            line = eye_z + 0.062 + sign * 0.03 * (ang / math.radians(150)) + 0.012 * (abs(ang) / math.radians(150)) ** 2
            if abs(ang) > math.radians(160):
                continue
            d = z - line                                     # above the edge: on the upper layer
            if d > 0:
                lift += 0.0055 * min(1.0, d / 0.004) * max(0.0, 1.0 - d / 0.05)
        return lift
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
        ridge = 0.004 * (r1 * (0.5 + 0.5 * front) + r2 * front * 0.8)     # small creases between layers
        return n * (ridge + layer_edge(p.z, ang))
    tie = C.shell(B, "KortoHeadTie", tie_keep, tie_off, 0.002, mats["headtie"], smooth=2, extra=wraps)
    edge_z = lambda ang: eye_z + tie_line(ang) + 0.004
    hem_loop = clean_edge(tie, head_c, edge_z)
    folds(tie, 0.003, 60.0)
    made["headtie"] = tie
    made["hem"] = hem(hem_loop, mats["headtie"], "KortoTieHem", 0.0055)
    # the turns of cloth, as real bands laid over the base one on top of another: a low band round
    # the head, then two crossing in a V over the forehead. Each stands a few millimetres off the
    # one below, puffs a little across its width and rolls at its edges, so the layers cast shadows
    # and the tie reads as wrapped cloth rather than a cap. Their ends tuck under the knot.
    span = math.radians(150)
    bands = [
        # (name, centre height above the eyes at angle a, width, layer)
        ("KortoTieBand0", lambda a: 0.052 + 0.006 * (abs(a) / span) - 0.01 * (abs(a) / span) ** 2, 0.042, 1),
        ("KortoTieBand1", lambda a: 0.083 + 0.03 * (a / span) + 0.012 * (abs(a) / span) ** 2, 0.05, 2),
        ("KortoTieBand2", lambda a: 0.083 - 0.03 * (a / span) + 0.012 * (abs(a) / span) ** 2, 0.05, 3),
    ]
    for name, centre, width, layer in bands:
        made[name] = tie_band(tie, head_c, eye_z, name, centre, width, layer, span, mats["headtie"])
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
    # her own shape round the hips and thighs, angle by angle (0 = front): the furthest the body
    # reaches out at that angle anywhere from the waistband to the hem. A round tube sized to her hip
    # width stood far off her stomach and buttocks (she is shallower front to back than side to side).
    step = 5
    prof = [0.0] * (360 // step)
    for p, ok in zip(B.points, B.skin):
        if not ok or not (bot_z - 0.02 < p.z < top_z) or abs(p.x - cx) > 0.2:
            continue
        a_deg = math.degrees(math.atan2(p.x - cx, -(p.y - cy))) % 360
        k = int(a_deg // step)
        prof[k] = max(prof[k], math.hypot(p.x - cx, p.y - cy))
    for _ in range(4):                               # smooth round the body
        prof = [max(prof[k], (prof[k - 1] + prof[k] + prof[(k + 1) % len(prof)]) / 3) for k in range(len(prof))]
    def body_r(a):
        k = (math.degrees(a) % 360) / step
        i = int(k) % len(prof)
        f = k - int(k)
        return prof[i] * (1 - f) + prof[(i + 1) % len(prof)] * f
    turn = 2 * math.pi + 0.95                       # once round and a bit: the end overlaps at the front-left
    start = math.radians(70)                         # the open edge sits at her left hip
    grid = []
    for r in range(rows):
        t = r / (rows - 1)
        z = top_z + (bot_z - top_z) * t
        row = []
        for c in range(cols):
            a = start + turn * c / (cols - 1)
            # her shape plus a little room; the overlapping end lies a little further out
            rad = (body_r(a) + 0.012 + 0.01 * (c / (cols - 1))) * (1.0 + 0.07 * t)  # a little flare for a striding leg
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
    # ease: the drape settles snug against her outer thighs, so any leg movement pushed through.
    # Give the cloth room below the hips, as a wrap skirt has (more toward the hem).
    for v in obj.data.vertices:          # drape() replaced the mesh
        t = max(0.0, min(1.0, (top_z - v.co.z) / (top_z - bot_z)))
        k = max(0.0, min(1.0, (t - 0.08) / 0.3))
        d = V((v.co.x - cx, v.co.y - cy, 0.0))
        if d.length > 1e-6:
            side = abs(d.normalized().x)          # 1 at her sides, 0 at front and back
            # room where the thighs push (her sides); front and back stay close, or the cloth
            # stood off her back and made her look broad behind
            # ...and toward the hem, all round, room for the knees and calves
            v.co += d.normalized() * ((0.016 * k + 0.008 * t) * (0.25 + 0.75 * side) + 0.016 * t * t)
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


def bridge_dents(obj, iterations=10, rate=0.5):
    """Untangle a garment made by offsetting the skin. Inside a hollow (the dimples of her lower
    back) the skin's normals point toward each other, so the offset surface crosses over itself into
    a small inside-out lens, which rendered as oval marks. Plain smoothing of the inside of the
    garment (open edges kept) untangles the folds and lets the cloth span the hollow."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for _ in range(iterations):
        new = {}
        for v in bm.verts:
            if v.is_boundary or not v.link_edges:
                continue
            avg = sum((e.other_vert(v).co for e in v.link_edges), V((0, 0, 0))) / len(v.link_edges)
            new[v] = v.co + (avg - v.co) * rate
        for v, co in new.items():
            v.co = co
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


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
    radius = [sorted(bins[k])[len(bins[k]) // 2] if k in bins else None for k in range(n)]
    known = [k for k in range(n) if radius[k] is not None]
    for k in range(n):                 # fill gaps from the nearest known angles
        if radius[k] is None:
            nearest = min(known, key=lambda j: min(abs(j - k), n - abs(j - k)))
            radius[k] = radius[nearest]
    for _ in range(3):
        radius = [(radius[k - 1] + 2 * radius[k] + radius[(k + 1) % n]) / 4 for k in range(n)]
    # near the edge, nothing stands further out than the edge (+1 cm): cloth taken over the top of
    # an ear and pushed off along the ear's surface made a fin sticking out beside her head
    for v in bm.verts:
        rel = v.co - center
        a_deg = ang_of(v.co)
        if v.co.z > edge_z(abs(a_deg)) + 0.035:
            continue
        k = int(round(a_deg / step_deg)) % n
        r = math.hypot(rel.x, rel.y)
        lim = radius[k] + 0.01
        if r > lim:
            v.co.x = center.x + rel.x * lim / r
            v.co.y = center.y + rel.y * lim / r
    loop = []
    for k in range(n):
        a = math.radians(k * step_deg)
        r = radius[k] + 0.002
        loop.append(V((center.x + r * math.sin(a), center.y - r * math.cos(a), edge_z(abs(math.degrees(math.atan2(math.sin(a), math.cos(a))))))))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return loop


def tie_band(tie, head_c, eye_z, name, centre, width, layer, span, material, cols=72, rows=7):
    """One band of a head tie laid over the tie's surface: from -span to +span round the head
    (0 = front), centred at eye_z + centre(angle), `width` tall, `layer` layers out."""
    bm = bmesh.new()
    uv_rows = []
    grid = []
    for c in range(cols):
        a = -span + 2 * span * c / (cols - 1)
        d = V((math.sin(a), -math.cos(a), 0))
        # taper the ends, where they tuck under the knot
        end = min(1.0, (span - abs(a)) / math.radians(25))
        w = width * (0.45 + 0.55 * end)
        row = []
        for r in range(rows):
            sv = r / (rows - 1)                          # 0 bottom edge .. 1 top edge
            z = eye_z + centre(a) + (sv - 0.5) * w
            origin = V((head_c.x, head_c.y, z)) + d * 0.25
            hit, nrm = H.surface_point(tie, origin, -d, 0.3)
            if hit is None:
                hit, nrm = V((head_c.x, head_c.y, z)) + d * 0.1, d
            puff = 0.0035 * math.sin(math.pi * sv) + 0.0022 * (1 - abs(2 * sv - 1)) ** 8   # body and rolled edges
            lip = 0.002 * (max(0.0, 1 - sv / 0.12) + max(0.0, 1 - (1 - sv) / 0.12))
            row.append(bm.verts.new(hit + nrm * (0.0035 * layer + puff * end + lip)))
        grid.append(row)
    faces = []
    for c in range(cols - 1):
        for r in range(rows - 1):
            faces.append(bm.faces.new((grid[c][r], grid[c + 1][r], grid[c + 1][r + 1], grid[c][r + 1])))
    uv = bm.loops.layers.uv.new("UVMap")
    arc = 0.09 * 2 * span                             # about the band's length in metres
    for f in faces:
        for loop in f.loops:
            for c, row in enumerate(grid):
                if loop.vert in row:
                    r = row.index(loop.vert)
                    loop[uv].uv = (arc * c / (cols - 1), width * r / (rows - 1))
                    break
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = 0.0015
    sol.offset = -1.0
    sub = obj.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    folds(obj, 0.0015, 90.0)
    return obj


def hem(points, material, name, radius, cyclic=True):
    """A rolled hem along a garment edge: a closed tube through `points`."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, pt in zip(sp.points, points):
        p.co = (pt.x, pt.y, pt.z, 1.0)
    sp.use_cyclic_u = cyclic
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
    # one bunched knot, wider than tall, pressed flat against the head (two round lobes read as a bun)
    ret = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.032, matrix=mathutils.Matrix.Translation(at))
    rnd = random.Random(7)
    for v in ret["verts"]:
        q = v.co - at
        v.co = at + V((q.x * 1.35, q.y * 0.6, q.z * 0.85)) * (0.94 + 0.1 * rnd.random())
    # two ends hanging from it, tapering and turned slightly apart
    for side in (-1, 1):
        ret = bmesh.ops.create_grid(bm, x_segments=3, y_segments=6, size=0.5)
        for v in ret["verts"]:
            u, w = v.co.x + 0.5, v.co.y + 0.5            # 0..1 across, 0..1 down
            width = 0.03 * (1 - 0.4 * w)
            x = side * (0.01 + 0.008 * w) + (u - 0.5) * width
            v.co = at + V((x, 0.012 + 0.004 * w * w - 0.02 * w, -0.01 - 0.06 * w))   # lies back against the head
        bmesh.ops.solidify(bm, geom=list({f for v in ret["verts"] for f in v.link_faces}), thickness=0.002)
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
