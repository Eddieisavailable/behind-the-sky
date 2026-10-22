"""Clothes cut from a character's own body, and the country-cloth material.

A garment here is a shell: the body's surface inside a region, lifted off the skin and given
thickness. Regions are chosen with plain tests on world position and the rig's bones, on a
subdivided copy of the body so the edges come out smooth. The wrapper (lappa) is draped with
Blender's cloth simulation so it falls in real folds.
"""
import math

import bmesh
import bpy
import mathutils

V = mathutils.Vector


# ---------------------------------------------------------------- reading the body

class Body:
    """The body as it renders (shape keys, rig), subdivided once, in world space, plus bone positions."""

    def __init__(self, human, rig, subdiv=2):
        tmp = human.copy()
        tmp.data = human.data.copy()
        bpy.context.scene.collection.objects.link(tmp)
        if subdiv:
            m = tmp.modifiers.new("sub", "SUBSURF")
            m.levels = subdiv
        dg = bpy.context.evaluated_depsgraph_get()
        ev = tmp.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        self.points = [mw @ v.co for v in me.vertices]
        rot = mw.to_3x3()
        self.normals = [(rot @ v.normal).normalized() for v in me.vertices]
        # skin only: MakeHuman meshes also carry fitting helpers and joint markers
        g = human.vertex_groups.get("body")
        self.skin = [g is None or any(x.group == g.index and x.weight > 0.5 for x in v.groups) for v in me.vertices]
        self.faces = [tuple(p.vertices) for p in me.polygons if all(self.skin[i] for i in p.vertices)]
        ev.to_mesh_clear()
        bpy.data.objects.remove(tmp)
        self.bones = {b.name: (rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local) for b in rig.data.bones}
        self.human = human
        self.rig = rig

    def head(self, bone):
        return self.bones[bone][0]

    def tail(self, bone):
        return self.bones[bone][1]

    def ring(self, z, band=0.01):
        """Points of the body near height z (for measuring girth)."""
        return [p for p, ok in zip(self.points, self.skin) if ok and abs(p.z - z) < band]


# ---------------------------------------------------------------- shells

def shell(body, name, keep, offset, thickness=0.0015, material=None, smooth=1, parent_bone=None, extra=None):
    """A garment from the body faces whose vertices all pass keep(p, n). offset(p, n) -> metres off the
    skin (a number works too). extra(p, n) -> extra displacement vector, for bulk such as a head tie's folds."""
    ok = [s and keep(p, n) for p, n, s in zip(body.points, body.normals, body.skin)]
    bm = bmesh.new()
    vmap = {}
    for f in body.faces:
        if all(ok[i] for i in f):
            vs = []
            for i in f:
                if i not in vmap:
                    p, n = body.points[i], body.normals[i]
                    off = offset(p, n) if callable(offset) else offset
                    q = p + n * off
                    if extra:
                        q = q + extra(p, n)
                    vmap[i] = bm.verts.new(q)
                vs.append(vmap[i])
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
    # close small holes the region test left (openings like armholes are far larger and stay open)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=20)
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    for poly in me.polygons:
        poly.use_smooth = True
    if smooth:
        s = obj.modifiers.new("Smooth", "SUBSURF")
        s.levels = s.render_levels = smooth
    if thickness:
        sol = obj.modifiers.new("Thickness", "SOLIDIFY")
        sol.thickness = thickness
        sol.offset = 1.0
        sol.use_even_offset = False   # "even" blew sharp creases out into fins (one beside her ear)
    if material:
        me.materials.append(material)
    return obj


def cylinder_uv(obj, center=(0, 0), unit=True):
    """UVs in metres: u around the body (arc length at the vertex's radius), v up. Cloth patterns
    use these directly, so stripes keep their real width whatever the garment's size."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    cx, cy = center
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = obj.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            ang = math.atan2(p.x - cx, -(p.y - cy))          # 0 at the front
            r = math.hypot(p.x - cx, p.y - cy)
            uv[li].uv = (ang * max(r, 0.08), p.z)


# ---------------------------------------------------------------- materials

def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return nt.nodes, nt.links


def country_cloth(name, strips, strip_width=0.11, weave=0.0012, rough=0.85, dirt=None, wear=0.0):
    """Kpelle country cloth: narrow hand-woven strips sewn edge to edge. `strips` is a list of strip
    designs, each a list of (colour, fraction of the strip's width) stripes running along the strip.
    The strips repeat across u (metres); a raised seam joins them; a fine plain weave covers all.
    dirt: (colour, height in metres below which the cloth is dusty), e.g. red earth at a hem.
    wear: 0..1 fading and pilling."""
    mat = bpy.data.materials.new(name)
    nodes, links = _nodes(mat)

    def n(kind, loc, **kw):
        node = nodes.new(kind)
        node.location = loc
        for k, v in kw.items():
            if k in node.inputs:
                node.inputs[k].default_value = v
            else:
                setattr(node, k, v)
        return node

    def m(op, a, b=None, loc=(0, 0)):
        node = n("ShaderNodeMath", loc, operation=op)
        for i, v in enumerate([a, b]):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                node.inputs[i].default_value = v
            else:
                links.new(v, node.inputs[i])
        return node.outputs[0]

    out = n("ShaderNodeOutputMaterial", (1600, 0))
    bsdf = n("ShaderNodeBsdfPrincipled", (1300, 0), Roughness=rough)
    bsdf.inputs["Sheen Weight"].default_value = 0.12        # cotton fuzz catches light at grazing angles
    bsdf.inputs["Sheen Roughness"].default_value = 0.6
    links.new(bsdf.outputs[0], out.inputs[0])
    uvn = n("ShaderNodeUVMap", (-1400, 0))
    sep = n("ShaderNodeSeparateXYZ", (-1200, 0))
    links.new(uvn.outputs[0], sep.inputs[0])
    u, v = sep.outputs["X"], sep.outputs["Y"]

    period = strip_width * len(strips)
    pos = m("FRACT", m("DIVIDE", u, period, (-1000, 200)), None, (-850, 200))          # 0..1 across one repeat
    # colour: walk the strips and their stripes as a ramp across the repeat
    ramp = n("ShaderNodeValToRGB", (-600, 300))
    ramp.color_ramp.interpolation = "CONSTANT"
    stops = []
    for si, design in enumerate(strips):
        x = si / len(strips)
        for colour, frac in design:
            stops.append((x, colour))
            x += frac / len(strips)
    els = ramp.color_ramp.elements
    while len(els) > 1:
        els.remove(els[-1])
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
    for x, c in stops[1:]:
        e = els.new(min(x, 0.999))
        e.color = (*c, 1)
    links.new(pos, ramp.inputs["Fac"])

    # weave: two sine gratings (warp along v, weft along u) multiplied; varies the colour a little and bumps
    warp = m("SINE", m("MULTIPLY", u, 2 * math.pi / weave, (-1000, -200)), None, (-850, -200))
    weft = m("SINE", m("MULTIPLY", v, 2 * math.pi / weave, (-1000, -350)), None, (-850, -350))
    cloth = m("MULTIPLY", m("ABSOLUTE", warp, None, (-700, -200)), m("ABSOLUTE", weft, None, (-700, -350)), (-550, -270))
    # irregular hand-spun thread: low-frequency noise along the warp
    slub = n("ShaderNodeTexNoise", (-850, -550), Scale=40.0, Detail=2.0)
    links.new(uvn.outputs[0], slub.inputs["Vector"])
    # seams between strips: a narrow raised ridge where pos crosses a strip edge
    edge_dist = m("ABSOLUTE", m("SUBTRACT", m("FRACT", m("MULTIPLY", pos, len(strips), (-700, 50)), None, (-550, 50)), 0.5, (-400, 50)), None, (-250, 50))
    seam = n("ShaderNodeMapRange", (-100, 50), **{"From Min": 0.47, "From Max": 0.5, "To Min": 0.0, "To Max": 1.0})
    links.new(edge_dist, seam.inputs["Value"])

    shade = n("ShaderNodeMapRange", (-300, -250), **{"From Min": 0.0, "From Max": 1.0, "To Min": 0.82, "To Max": 1.05})
    links.new(cloth, shade.inputs["Value"])
    col = n("ShaderNodeMix", (100, 250), data_type="RGBA", blend_type="MULTIPLY")
    col.inputs["Factor"].default_value = 1.0
    links.new(ramp.outputs["Color"], col.inputs["A"])
    shade_rgb = n("ShaderNodeCombineColor", (-100, -250))
    for k in ("Red", "Green", "Blue"):
        links.new(shade.outputs["Result"], shade_rgb.inputs[k])
    links.new(shade_rgb.outputs[0], col.inputs["B"])
    colour = col.outputs["Result"]
    if wear:
        faded = n("ShaderNodeHueSaturation", (150, 450), Hue=0.5, Saturation=0.75, Value=1.7)
        links.new(colour, faded.inputs["Color"])
        fade = n("ShaderNodeMix", (300, 250), data_type="RGBA", blend_type="MIX")
        f = n("ShaderNodeMapRange", (100, 650), **{"From Min": 0.3, "From Max": 0.8, "To Min": 0.0, "To Max": wear})
        links.new(slub.outputs["Fac"], f.inputs["Value"])
        links.new(f.outputs["Result"], fade.inputs["Factor"])
        links.new(colour, fade.inputs["A"])
        links.new(faded.outputs["Color"], fade.inputs["B"])
        colour = fade.outputs["Result"]
    if dirt:
        dc, dz = dirt
        geo = n("ShaderNodeNewGeometry", (100, 650))
        gz = n("ShaderNodeSeparateXYZ", (250, 650))
        links.new(geo.outputs["Position"], gz.inputs[0])
        dmask = n("ShaderNodeMapRange", (400, 650), **{"From Min": dz, "From Max": dz - 0.1, "To Min": 0.0, "To Max": 0.6})
        links.new(gz.outputs["Z"], dmask.inputs["Value"])
        noise = n("ShaderNodeTexNoise", (400, 850), Scale=18.0, Detail=4.0)
        dm2 = m("MULTIPLY", dmask.outputs["Result"], noise.outputs["Fac"], (600, 700))
        dmix = n("ShaderNodeMix", (750, 300), data_type="RGBA")
        dmix.inputs["B"].default_value = (*dc, 1)
        links.new(m("MINIMUM", m("MULTIPLY", dm2, 1.6, (700, 750)), 1.0, (850, 750)), dmix.inputs["Factor"])
        links.new(colour, dmix.inputs["A"])
        colour = dmix.outputs["Result"]
    links.new(colour, bsdf.inputs["Base Color"])

    height = m("ADD", m("MULTIPLY", cloth, 0.6, (-100, -450)), m("MULTIPLY", seam.outputs["Result"], 1.4, (-100, -600)), (100, -500))
    height = m("ADD", height, m("MULTIPLY", slub.outputs["Fac"], 0.5, (100, -650)), (250, -550))
    bump = n("ShaderNodeBump", (1000, -300), Strength=0.6, Distance=0.0015)
    links.new(height, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def simple_material(name, colour, rough=0.6, metal=0.0, bump_scale=0.0, bump=0.0, coat=0.0):
    mat = bpy.data.materials.new(name)
    nodes, links = _nodes(mat)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    b = nodes.new("ShaderNodeBsdfPrincipled")
    b.location = (300, 0)
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    links.new(b.outputs[0], out.inputs[0])
    if bump:
        tc = nodes.new("ShaderNodeTexCoord")
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = bump_scale
        tex.inputs["Detail"].default_value = 6.0
        links.new(tc.outputs["Object"], tex.inputs["Vector"])
        bp = nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.001
        links.new(tex.outputs["Fac"], bp.inputs["Height"])
        links.new(bp.outputs["Normal"], b.inputs["Normal"])
        # leather and iron aren't flat in colour either
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["A"].default_value = (*colour, 1)
        mix.inputs["Factor"].default_value = 0.35
        links.new(tex.outputs["Color"], mix.inputs["B"])
        links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return mat


# ---------------------------------------------------------------- cloth simulation

def drape(obj, collider, pin_group, frames=45, quality=8, mass=0.35, stiffness=12.0):
    """Let a garment fall onto the body under gravity, pinned along `pin_group`; then make the
    result its shape."""
    col = collider.modifiers.new("Collision", "COLLISION")
    collider.collision.thickness_outer = 0.004
    collider.collision.cloth_friction = 8.0
    cl = obj.modifiers.new("Cloth", "CLOTH")
    s = cl.settings
    s.quality = quality
    s.mass = mass
    s.tension_stiffness = s.compression_stiffness = stiffness
    s.shear_stiffness = stiffness * 0.5
    s.bending_stiffness = 0.6
    s.vertex_group_mass = pin_group
    s.air_damping = 2.0
    cl.collision_settings.distance_min = 0.003
    cl.collision_settings.use_self_collision = False
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = frames
    cl.point_cache.frame_start = 1
    cl.point_cache.frame_end = frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    # bake the draped shape into the mesh
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    obj.modifiers.clear()
    old = obj.data
    obj.data = me
    bpy.data.meshes.remove(old)
    collider.modifiers.remove(col)
    sc.frame_set(1)
    return obj


def sole(body, name, foot_x_sign, material, cx, thickness=0.01, margin=0.006):
    """A flat hide sole under one foot: the outline of the foot's underside, a little larger."""
    pts = [p for p, ok in zip(body.points, body.skin) if ok and p.z < 0.03 and (p.x - cx) * foot_x_sign > 0.02]
    hull2 = mathutils.geometry.convex_hull_2d([(p.x, p.y) for p in pts])
    ring = [V((pts[i].x, pts[i].y, 0)) for i in hull2]
    c = sum(ring, V()) / len(ring)
    ring = [c + (q - c) * (1 + margin / max(0.02, (q - c).length)) for q in ring]
    bm = bmesh.new()
    bottom = [bm.verts.new((q.x, q.y, 0.0)) for q in ring]
    top = [bm.verts.new((q.x, q.y, thickness)) for q in ring]
    bm.faces.new(bottom[::-1])
    bm.faces.new(top)
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.002, segments=2, affect="EDGES")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    return obj


def band(body, name, center, z, height, offset, material, segments=96, keep_x=0.22):
    """A clean band round the body (a belt, a strap): at each angle, the body's radius at that height
    plus `offset`."""
    cx, cy = center
    pts = [p for p, ok in zip(body.points, body.skin) if ok and abs(p.z - z) < height and abs(p.x - cx) < keep_x]
    radius = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        d = V((math.sin(a), -math.cos(a), 0))
        best = 0.0
        for p in pts:
            q = V((p.x - cx, p.y - cy, 0))
            if q.length < 1e-6:
                continue
            if q.normalized().dot(d) > 0.985:
                best = max(best, q.length)
        radius.append(best)
    # fill angles that found nothing from their neighbours, then smooth
    for _ in range(3):
        radius = [r if r > 0 else max(radius[i - 1], radius[(i + 1) % segments]) for i, r in enumerate(radius)]
    radius = [(radius[i - 1] + 2 * radius[i] + radius[(i + 1) % segments]) / 4 for i in range(segments)]
    bm = bmesh.new()
    rows = []
    for zz in (z - height / 2, z + height / 2):
        rows.append([bm.verts.new((cx + math.sin(2 * math.pi * i / segments) * (radius[i] + offset),
                                   cy - math.cos(2 * math.pi * i / segments) * (radius[i] + offset), zz)) for i in range(segments)])
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((rows[0][i], rows[0][j], rows[1][j], rows[1][i]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    for poly in me.polygons:
        poly.use_smooth = True
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = 0.004
    sol.offset = 1.0
    bev = obj.modifiers.new("Edges", "BEVEL")
    bev.width = 0.0012
    bev.segments = 2
    me.materials.append(material)
    return obj
