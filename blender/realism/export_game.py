"""Turn a built realistic character into a game asset for Godot.

- Bakes procedural materials to textures (Cycles): skin colour, roughness and normal on the body's UVs;
  cloth as small tiling textures (the garments' UVs are in metres, so Godot repeats the tile).
- Freezes the body (MPFB shape keys applied, fitting helpers removed).
- Skins every garment and accessory to the rig, copying weights from the nearest point on the body.
- Exports one .glb plus the textures.
"""
import math
from pathlib import Path

import bmesh
import bpy
import mathutils
from mathutils.bvhtree import BVHTree


def _select_only(obj):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def freeze(obj, keep_armature=True):
    """Apply shape keys and every modifier except the armature; keep vertex groups."""
    arm = [m for m in obj.modifiers if m.type == "ARMATURE"]
    arm_targets = [m.object for m in arm]
    for m in arm:
        m.show_viewport = m.show_render = False
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    old = obj.data
    obj.modifiers.clear()
    obj.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    if obj.data.shape_keys:
        obj.shape_key_clear()
    if keep_armature:
        rigs = [m_rig for m_rig in arm_targets if m_rig]
        for r in rigs:
            mod = obj.modifiers.new("Armature", "ARMATURE")
            mod.object = r
    return obj


def drop_helpers(human):
    """Delete MakeHuman's fitting helpers and joint markers: keep only the 'body' group."""
    g = human.vertex_groups["body"].index
    bm = bmesh.new()
    bm.from_mesh(human.data)
    deform = bm.verts.layers.deform.active
    gone = [v for v in bm.verts if v[deform].get(g, 0.0) < 0.5]
    bmesh.ops.delete(bm, geom=gone, context="VERTS")
    bm.to_mesh(human.data)
    bm.free()
    for vg in list(human.vertex_groups):
        if vg.name.startswith(("helper", "joint", "Helper", "Joint")) or vg.name in ("body", "Left", "Right", "Mid"):
            human.vertex_groups.remove(vg)


def bind(obj, body, rig, only=None):
    """Skin `obj` to `rig` with weights copied from the nearest point on `body` (world space).
    only: a single bone name to give everything to it (rigid things like a bead strand)."""
    mw_obj = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    obj.matrix_world = mw_obj
    # bake the object's own transform into its vertices so its space matches the rig's
    me = obj.data
    me.transform(rig.matrix_world.inverted() @ mw_obj)
    obj.matrix_world = rig.matrix_world.copy()
    bone_names = [b.name for b in rig.data.bones]
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    groups = {n: obj.vertex_groups.new(name=n) for n in bone_names}
    if only:
        groups[only].add(range(len(me.vertices)), 1.0, "REPLACE")
    else:
        # triangulated body in world space, with per-vertex weights
        bm = bmesh.new()
        bm.from_mesh(body.data)
        bm.transform(body.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        tree = BVHTree.FromBMesh(bm)
        deform = bm.verts.layers.deform.active
        idx_to_name = {vg.index: vg.name for vg in body.vertex_groups}
        tris = [[v.index for v in f.verts] for f in bm.faces]
        pts = [v.co.copy() for v in bm.verts]
        wts = [{idx_to_name[k]: w for k, w in v[deform].items() if k in idx_to_name and idx_to_name[k] in groups} for v in bm.verts]
        bm.free()
        world = obj.matrix_world
        acc = {}
        for v in me.vertices:
            p = world @ v.co
            loc, _, fi, _ = tree.find_nearest(p)
            a, b, c = tris[fi]
            bc = mathutils.geometry.intersect_point_tri(loc, pts[a], pts[b], pts[c]) or loc
            # barycentric weights
            w = _barycentric(loc, pts[a], pts[b], pts[c])
            mix = {}
            for vi, f in zip((a, b, c), w):
                for name, x in wts[vi].items():
                    mix[name] = mix.get(name, 0.0) + x * f
            total = sum(mix.values()) or 1.0
            for name, x in mix.items():
                if x / total > 0.01:
                    acc.setdefault(name, []).append((v.index, x / total))
        for name, items in acc.items():
            g = groups[name]
            for i, x in items:
                g.add([i], x, "REPLACE")
    for vg in list(obj.vertex_groups):
        if not any(vg.index in [g.group for g in v.groups] for v in me.vertices[:1]) and False:
            pass
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return obj


def _barycentric(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01 or 1e-12
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return (1 - v - w, v, w)


# ---------------------------------------------------------------- baking

def _bake_setup(samples=1):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.render.bake.margin = 8


def bake_maps(obj, out_dir, prefix, size=2048, maps=("color", "rough", "normal"), uv_name=None):
    """Bake obj's material to images on its active UVs. Returns {map: path}."""
    _bake_setup()
    _select_only(obj)
    if uv_name:
        obj.data.uv_layers.active = obj.data.uv_layers[uv_name]
    paths = {}
    for kind in maps:
        img = bpy.data.images.new(f"{prefix}_{kind}", size, size, alpha=False, float_buffer=False)
        if kind != "color":
            img.colorspace_settings.name = "Non-Color"
        for mat in obj.data.materials:
            nt = mat.node_tree
            node = nt.nodes.new("ShaderNodeTexImage")
            node.image = img
            node.name = "BakeTarget"
            nt.nodes.active = node
        if kind == "color":
            bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
        elif kind == "rough":
            bpy.ops.object.bake(type="ROUGHNESS")
        elif kind == "normal":
            bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
        path = Path(out_dir) / f"{prefix}_{kind}.png"
        img.filepath_raw = str(path)
        img.file_format = "PNG"
        img.save()
        paths[kind] = path
        for mat in obj.data.materials:
            nt = mat.node_tree
            n = nt.nodes.get("BakeTarget")
            if n:
                nt.nodes.remove(n)
    return paths


def bake_tile(material, period_u, period_v, out_dir, prefix, size=1024, z=3.0):
    """Bake a metre-UV material (country cloth) over one repeat into tiling textures.
    The plane sits high (z) so height-based effects such as hem dust stay out of the tile."""
    me = bpy.data.meshes.new("tile")
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z + y)) for x, y in ((0, 0), (period_u, 0), (period_u, period_v), (0, period_v))]
    f = bm.faces.new(vs)
    uv_m = bm.loops.layers.uv.new("UVMap")
    uv_b = bm.loops.layers.uv.new("BakeUV")
    for loop, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv_m].uv = (u * period_u, v * period_v)
        loop[uv_b].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("tile", me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    for n in material.node_tree.nodes:
        if n.type == "UVMAP":
            n.uv_map = "UVMap"
    me.uv_layers.active = me.uv_layers["BakeUV"]
    paths = bake_maps(obj, out_dir, prefix, size)
    bpy.data.objects.remove(obj)
    return paths


def export_glb(path, objects):
    for o in bpy.context.scene.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                              export_apply=False, export_skins=True, export_animations=True,
                              export_animation_mode="NLA_TRACKS",   # one animation per track, named by it
                              export_yup=True, export_image_format="AUTO", export_texcoords=True,
                              export_normals=True, export_tangents=True, export_vertex_color="ACTIVE")


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def reduce_to(obj, target):
    """Collapse-decimate a frozen mesh down to about `target` triangles (UVs and vertex groups kept)."""
    now = triangles(obj)
    if now <= target:
        return now
    d = obj.modifiers.new("Reduce", "DECIMATE")
    d.decimate_type = "COLLAPSE"
    d.ratio = target / now
    d.use_collapse_triangulate = True
    freeze(obj)
    return triangles(obj)
