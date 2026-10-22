"""Shared pieces for realistic people: skin, eyes, brows, lashes, hair caps.

Everything is procedural so it can be tuned per character and baked to textures for Godot.
Colours are linear (what Blender's shader nodes expect). For reference, the colour chart's
"dark skin" patch is sRGB (115, 82, 68) = linear (0.171, 0.084, 0.058).
"""
from pathlib import Path

import bpy
import mathutils

MH_DATA = Path("/home/claude/tools/mpfb/mh/makehuman/data")


def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return nt, nt.nodes, nt.links


def _n(nodes, kind, loc, **inputs):
    node = nodes.new(kind)
    node.location = loc
    for k, v in inputs.items():
        if k in node.inputs:
            node.inputs[k].default_value = v
        else:
            setattr(node, k, v)
    return node


def skin_material(name="Skin", base=(0.075, 0.03, 0.015), red=(0.12, 0.036, 0.018), dark=(0.032, 0.013, 0.007),
                  roughness=0.48, pore_scale=900.0, pore_depth=0.35, sss=0.45, unit=1.0):
    """Deep brown skin with a warm red-gold undertone.

    base: the skin's mid tone · red: blood-flushed areas (variation) · dark: creases and knuckles
    pore_scale: pores per metre · pore_depth: bump strength
    unit: metres per object-space unit (MPFB meshes are in decimetres under a scaled rig)
    """
    mat = bpy.data.materials.new(name)
    nt, nodes, links = _nodes(mat)
    out = _n(nodes, "ShaderNodeOutputMaterial", (900, 0))
    bsdf = _n(nodes, "ShaderNodeBsdfPrincipled", (600, 0))
    links.new(bsdf.outputs[0], out.inputs[0])

    tc = _n(nodes, "ShaderNodeTexCoord", (-1400, 0))
    coords = _n(nodes, "ShaderNodeMapping", (-1200, 0))
    coords.inputs["Scale"].default_value = (unit, unit, unit)   # object units -> metres
    links.new(tc.outputs["Object"], coords.inputs["Vector"])
    # large blotches of warmth (blood under the skin), medium mottling, and crease darkening
    warm = _n(nodes, "ShaderNodeTexNoise", (-900, 300), Scale=6.0, Detail=3.0, Roughness=0.5)
    mottle = _n(nodes, "ShaderNodeTexNoise", (-900, 100), Scale=70.0, Detail=4.0, Roughness=0.6)
    links.new(coords.outputs["Vector"], warm.inputs["Vector"])
    links.new(coords.outputs["Vector"], mottle.inputs["Vector"])
    geo = _n(nodes, "ShaderNodeNewGeometry", (-900, -150))
    cavity = _n(nodes, "ShaderNodeMapRange", (-650, -150), **{"From Min": 0.45, "From Max": 0.55, "To Min": 1.0, "To Max": 0.0})
    links.new(geo.outputs["Pointiness"], cavity.inputs["Value"])

    c1 = _n(nodes, "ShaderNodeMix", (-400, 300), data_type="RGBA", blend_type="MIX")
    c1.inputs["A"].default_value = (*base, 1)
    c1.inputs["B"].default_value = (*red, 1)
    ramp_w = _n(nodes, "ShaderNodeMapRange", (-650, 300), **{"From Min": 0.45, "From Max": 0.7, "To Min": 0.0, "To Max": 0.55})
    links.new(warm.outputs["Fac"], ramp_w.inputs["Value"])
    links.new(ramp_w.outputs["Result"], c1.inputs["Factor"])
    c2 = _n(nodes, "ShaderNodeMix", (-200, 200), data_type="RGBA", blend_type="MULTIPLY")
    mott = _n(nodes, "ShaderNodeMapRange", (-650, 100), **{"From Min": 0.3, "From Max": 0.7, "To Min": 0.0, "To Max": 0.18})
    links.new(mottle.outputs["Fac"], mott.inputs["Value"])
    links.new(mott.outputs["Result"], c2.inputs["Factor"])
    links.new(c1.outputs["Result"], c2.inputs["A"])
    c2.inputs["B"].default_value = (0.8, 0.66, 0.55, 1)
    c3 = _n(nodes, "ShaderNodeMix", (0, 150), data_type="RGBA", blend_type="MIX")
    c3.inputs["B"].default_value = (*dark, 1)
    links.new(c2.outputs["Result"], c3.inputs["A"])
    links.new(cavity.outputs["Result"], c3.inputs["Factor"])
    links.new(c3.outputs["Result"], bsdf.inputs["Base Color"])

    # pores (cells) and fine grain, as bump
    pores = _n(nodes, "ShaderNodeTexVoronoi", (-900, -400), feature="DISTANCE_TO_EDGE", Scale=pore_scale)
    grain = _n(nodes, "ShaderNodeTexNoise", (-900, -600), Scale=pore_scale * 2.2, Detail=2.0)
    links.new(coords.outputs["Vector"], pores.inputs["Vector"])
    links.new(coords.outputs["Vector"], grain.inputs["Vector"])
    pore_shape = _n(nodes, "ShaderNodeMapRange", (-650, -400), **{"From Min": 0.0, "From Max": 0.12, "To Min": 0.0, "To Max": 1.0})
    links.new(pores.outputs["Distance"], pore_shape.inputs["Value"])
    bump1 = _n(nodes, "ShaderNodeBump", (-200, -400), Strength=pore_depth, Distance=0.0004)
    links.new(pore_shape.outputs["Result"], bump1.inputs["Height"])
    bump2 = _n(nodes, "ShaderNodeBump", (100, -500), Strength=pore_depth * 0.4, Distance=0.0002)
    links.new(grain.outputs["Fac"], bump2.inputs["Height"])
    links.new(bump1.outputs["Normal"], bump2.inputs["Normal"])
    links.new(bump2.outputs["Normal"], bsdf.inputs["Normal"])

    # oilier T-zone and nose, drier elsewhere: roughness varies with the warm noise
    rough = _n(nodes, "ShaderNodeMapRange", (-200, -150), **{"From Min": 0.0, "From Max": 1.0, "To Min": roughness - 0.08, "To Max": roughness + 0.1})
    links.new(mottle.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])

    bsdf.inputs["Subsurface Weight"].default_value = sss
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.25)
    bsdf.inputs["Subsurface Scale"].default_value = 0.004
    bsdf.inputs["Specular IOR Level"].default_value = 0.55
    bsdf.inputs["Coat Weight"].default_value = 0.06
    bsdf.inputs["Coat Roughness"].default_value = 0.35
    return mat


def eye_material(name="Eyes", iris_png=MH_DATA / "eyes/materials/brown_eye.png", darken=0.4):
    """Wet eyes: the MakeHuman brown iris texture (CC0), darkened toward a deep brown, under a clear coat."""
    mat = bpy.data.materials.new(name)
    nt, nodes, links = _nodes(mat)
    out = _n(nodes, "ShaderNodeOutputMaterial", (1000, 0))
    bsdf = _n(nodes, "ShaderNodeBsdfPrincipled", (300, 0))
    # each MakeHuman eye is an eyeball plus a clear lens over it; the lens maps to the texture's
    # transparent area, so alpha picks: eyeball where opaque, clear reflective lens where not
    clear = _n(nodes, "ShaderNodeBsdfTransparent", (300, -350))
    gloss = _n(nodes, "ShaderNodeBsdfGlossy", (300, -480), Roughness=0.02)
    fres = _n(nodes, "ShaderNodeFresnel", (300, -600), IOR=1.376)
    lens = _n(nodes, "ShaderNodeMixShader", (550, -400))
    links.new(fres.outputs[0], lens.inputs[0])
    links.new(clear.outputs[0], lens.inputs[1])
    links.new(gloss.outputs[0], lens.inputs[2])
    pick = _n(nodes, "ShaderNodeMixShader", (800, 0))
    links.new(lens.outputs[0], pick.inputs[1])
    links.new(bsdf.outputs[0], pick.inputs[2])
    links.new(pick.outputs[0], out.inputs[0])
    tex = _n(nodes, "ShaderNodeTexImage", (-400, 0))
    tex.image = bpy.data.images.load(str(iris_png), check_existing=True)
    hsv = _n(nodes, "ShaderNodeHueSaturation", (-100, 0), Hue=0.5, Saturation=1.1, Value=darken)
    links.new(tex.outputs["Color"], hsv.inputs["Color"])
    links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], pick.inputs[0])
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.02
    bsdf.inputs["Coat IOR"].default_value = 1.376
    return mat


def surface_point(obj, origin, direction, max_dist=0.5):
    """First point where a ray from `origin` along `direction` hits `obj` as it renders (world space)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    inv = ev.matrix_world.inverted()
    o = inv @ mathutils.Vector(origin)
    d = (inv.to_3x3() @ mathutils.Vector(direction)).normalized()
    ok, loc, normal, _ = ev.ray_cast(o, d, distance=max_dist / ev.matrix_world.to_scale().x)
    if not ok:
        return None, None
    return ev.matrix_world @ loc, (ev.matrix_world.to_3x3() @ normal).normalized()


# ---------------------------------------------------------------- hair textures (cards)

def strand_texture(path, kind="brow", size=(512, 128), seed=3, color=(18, 11, 8)):
    """Draw an alpha texture of hairs for a card. kind: 'brow' (short hairs slanting along the card,
    rising at the inner end) or 'lash' (curved hairs from the bottom edge)."""
    import math
    import random
    from PIL import Image, ImageDraw
    rnd = random.Random(seed)
    w, h = size
    img = Image.new("RGBA", (w * 2, h * 2), (*color, 0))   # draw at 2x, scale down for soft edges
    d = ImageDraw.Draw(img)
    W, Hh = w * 2, h * 2
    if kind == "brow":
        for _ in range(1500):
            u = rnd.random() ** 1.15              # 0 inner end .. 1 tail (denser at the head of the brow)
            thick = 1.0 - 0.75 * u                # the brow thins toward the tail
            v = 0.5 + (rnd.random() - 0.5) * thick * 0.9
            ang = math.radians(70 - 60 * min(1, u * 2.2))   # inner hairs point up, the rest lie along
            ln = (0.18 + 0.12 * rnd.random()) * Hh
            x0, y0 = u * W * 0.97, v * Hh
            x1, y1 = x0 + math.cos(ang) * ln, y0 - math.sin(ang) * ln
            a = int(120 + 110 * rnd.random())
            d.line([(x0, y0), (x1, y1)], fill=(*color, a), width=2)
    else:
        for _ in range(220):
            u = 0.04 + rnd.random() * 0.92
            ln = (0.55 + 0.4 * math.sin(math.pi * u)) * Hh * (0.8 + 0.2 * rnd.random())
            x0, y0 = u * W, Hh - 2
            bend = (u - 0.5) * 0.5 * Hh
            pts = [(x0 + bend * (t ** 2), y0 - ln * t) for t in [i / 8 for i in range(9)]]
            d.line(pts, fill=(*color, 245), width=3)
    img = img.resize((w, h), Image.LANCZOS)
    img.save(path)
    return path


def card_material(name, png, rough=0.45, spec=0.5):
    mat = bpy.data.materials.new(name)
    nt, nodes, links = _nodes(mat)
    out = _n(nodes, "ShaderNodeOutputMaterial", (600, 0))
    bsdf = _n(nodes, "ShaderNodeBsdfPrincipled", (300, 0), Roughness=rough)
    bsdf.inputs["Specular IOR Level"].default_value = spec
    tex = _n(nodes, "ShaderNodeTexImage", (-100, 0))
    tex.image = bpy.data.images.load(str(png), check_existing=True)
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs[0], out.inputs[0])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    return mat


def ribbon(name, points, normals, widths, lift, material, parent=None, up=(0, 0, 1), tilt=0.0, follow_surface=True):
    """A strip of quads along `points`: each cross-section runs from the point along `up` for
    `widths[i]` (laid along the skin when follow_surface, then tipped toward the normal by `tilt`),
    raised `lift` off the surface. UV u runs along the strip, v across it."""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    up = mathutils.Vector(up)
    rows = []
    n = len(points)
    for i, (p, nrm) in enumerate(zip(points, normals)):
        base = p + nrm * lift
        side = (up - nrm * up.dot(nrm)) if follow_surface else up.copy()
        side = side.normalized().lerp(nrm, tilt).normalized()
        rows.append((bm.verts.new(base), bm.verts.new(base + side * widths[i])))
    for i in range(n - 1):
        a0, a1 = rows[i]
        b0, b1 = rows[i + 1]
        f = bm.faces.new((a0, b0, b1, a1))
        for loop, (u, v) in zip(f.loops, [(i / (n - 1), 0), ((i + 1) / (n - 1), 0), ((i + 1) / (n - 1), 1), (i / (n - 1), 1)]):
            loop[uv].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    if parent is not None:
        attach_to_bone(obj, parent, "head")
    return obj


def attach_to_bone(obj, rig, bone):
    """Parent a world-placed object to a bone, keeping where it is."""
    mw = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    bpy.context.view_layer.update()
    obj.matrix_world = mw


def cornrow_material(name="Cornrows", scalp=(0.05, 0.02, 0.01), hair=(0.006, 0.0042, 0.0032), row=0.009, plait=0.0048):
    """Close cornrows running front to back: dark plaited rows with a line of scalp between them.
    row: distance between rows (m) · plait: length of one plait twist (m). Object space in metres."""
    mat = bpy.data.materials.new(name)
    nt, nodes, links = _nodes(mat)
    out = _n(nodes, "ShaderNodeOutputMaterial", (1100, 0))
    bsdf = _n(nodes, "ShaderNodeBsdfPrincipled", (800, 0), Roughness=0.7)
    bsdf.inputs["Coat Weight"].default_value = 0.05     # a little oil sheen
    bsdf.inputs["Coat Roughness"].default_value = 0.45
    links.new(bsdf.outputs[0], out.inputs[0])
    tc = _n(nodes, "ShaderNodeTexCoord", (-1200, 0))
    sep = _n(nodes, "ShaderNodeSeparateXYZ", (-1000, 0))
    links.new(tc.outputs["Object"], sep.inputs[0])

    def math(op, a, b=None, loc=(0, 0)):
        m = _n(nodes, "ShaderNodeMath", loc, operation=op)
        for i, v in enumerate([a, b]):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                links.new(v, m.inputs[i])
        return m.outputs[0]

    across = math("FRACT", math("DIVIDE", sep.outputs["X"], row, (-800, 100)), None, (-600, 100))
    lane = math("FLOOR", math("DIVIDE", sep.outputs["X"], row, (-800, 250)), None, (-600, 250))
    # each plait: a bulge across the row, and twists along it (offset per row so they don't line up)
    bulge = math("SINE", math("MULTIPLY", across, 3.14159, (-400, 100)), None, (-200, 100))
    along = math("FRACT", math("ADD", math("DIVIDE", sep.outputs["Y"], plait, (-800, -100)), math("MULTIPLY", lane, 0.37, (-600, -250)), (-500, -100)), None, (-350, -100))
    twist = math("ABSOLUTE", math("SINE", math("MULTIPLY", along, 3.14159, (-200, -100))), None, (0, -100))
    height = math("MULTIPLY", bulge, math("ADD", math("MULTIPLY", twist, 0.45, (150, -100)), 0.55, (300, -100)), (450, 0))
    bump = _n(nodes, "ShaderNodeBump", (600, -200), Strength=0.9, Distance=0.002)
    links.new(height, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # scalp shows in the parting between rows
    part = _n(nodes, "ShaderNodeMapRange", (450, 250), **{"From Min": 0.12, "From Max": 0.3, "To Min": 0.0, "To Max": 1.0})
    links.new(bulge, part.inputs["Value"])
    mix = _n(nodes, "ShaderNodeMix", (650, 200), data_type="RGBA")
    mix.inputs["A"].default_value = (*scalp, 1)
    mix.inputs["B"].default_value = (*hair, 1)
    links.new(part.outputs["Result"], mix.inputs["Factor"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    # soft hairline: the cap fades out over its last few millimetres (attribute set by the cap builder)
    edge = _n(nodes, "ShaderNodeAttribute", (450, 450), attribute_name="hairline")
    links.new(edge.outputs["Fac"], bsdf.inputs["Alpha"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    return mat
