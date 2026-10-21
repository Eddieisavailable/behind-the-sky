"""Shared helpers for building the game's models in Blender, from scripts.

Style: stylized low-poly, flat-shaded faces coloured with vertex colours, one
material and one skinned mesh per character (one draw call on a phone). Every
part of a character is weighted 100% to one bone ("rigid skinning"), like a
carved puppet, which keeps the rig simple and the joints clean.

Run any model script with Blender's Python:
    python blender/korto.py            (bpy installed with:  pip install bpy==5.1.2)
or inside the Blender app: Scripting tab > open the file > Run Script.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import bpy  # must come first: it makes bmesh and mathutils importable
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parent.parent
# BTS_MODELS_OUT sends the exports elsewhere (the Godot project takes full-precision copies)
MODELS_OUT = Path(os.environ.get("BTS_MODELS_OUT", ROOT / "public" / "models"))
PREVIEWS_OUT = ROOT / "blender" / "previews"


def hexcol(h: str, a: float = 1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    return scene


def mat_at(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)) -> Matrix:
    """Location (m), rotation (degrees, XYZ) and scale as one matrix."""
    t = Matrix.Translation(Vector(loc))
    r = Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()
    s = Matrix.Diagonal(Vector((*scale, 1.0)))
    return t @ r @ s


class Body:
    """Builds one mesh out of simple parts; each part is coloured and bound to a bone."""

    def __init__(self, name: str):
        self.name = name
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new("Col")
        self.dl = self.bm.verts.layers.deform.verify()
        self.groups: list[str] = []

    def _group(self, bone: str) -> int:
        if bone not in self.groups:
            self.groups.append(bone)
        return self.groups.index(bone)

    def _finish_part(self, verts, bone, color, mat=0):
        gi = self._group(bone)
        for v in verts:
            v[self.dl][gi] = 1.0
        faces = {f for v in verts for f in v.link_faces}
        for i, f in enumerate(sorted(faces, key=lambda f: f.index)):
            f.material_index = mat
            c = color(f) if callable(color) else color
            for loop in f.loops:
                loop[self.col] = c
        return verts

    def cone(self, bone, color, matrix, r1, r2, depth, segments=8, mat=0):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segments,
                                    radius1=r1, radius2=r2, depth=depth, matrix=matrix)
        return self._finish_part(res["verts"], bone, color, mat)

    def limb(self, bone, color, a, b, r1, r2=None, segments=6, mat=0):
        """A tapered cylinder from point a to point b."""
        a, b = Vector(a), Vector(b)
        d = b - a
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        m = Matrix.Translation((a + b) / 2) @ rot
        return self.cone(bone, color, m, r1, r2 if r2 is not None else r1, d.length, segments, mat)

    def box(self, bone, color, matrix, size=(1, 1, 1), mat=0):
        m = matrix @ Matrix.Diagonal(Vector((*size, 1.0)))
        res = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        return self._finish_part(res["verts"], bone, color, mat)

    def ball(self, bone, color, matrix, radius, segs=(8, 6), mat=0):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=segs[0], v_segments=segs[1], radius=radius, matrix=matrix)
        return self._finish_part(res["verts"], bone, color, mat)

    def gem(self, bone, color, matrix, radius, mat=0):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=1, radius=radius, matrix=matrix)
        return self._finish_part(res["verts"], bone, color, mat)

    def panel(self, bone, color, pts, thickness=0.004, mat=0):
        """A thin flat shape through the points (a wing membrane), visible from both sides."""
        pts = [Vector(p) for p in pts]
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0]).normalized() * (thickness / 2)
        top = [self.bm.verts.new(p + n) for p in pts]
        bot = [self.bm.verts.new(p - n) for p in pts]
        self.bm.faces.new(top)
        self.bm.faces.new(list(reversed(bot)))
        return self._finish_part(top + bot, bone, color, mat)

    def to_object(self, material, extra_materials=()) -> bpy.types.Object:
        mesh = bpy.data.meshes.new(self.name)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = False  # flat shading: the low-poly look
        if "Col" in mesh.color_attributes:
            mesh.color_attributes.active_color_name = "Col"
            mesh.color_attributes.default_color_name = "Col"
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        for g in self.groups:
            obj.vertex_groups.new(name=g)
        mesh.materials.append(material)
        for m in extra_materials:
            mesh.materials.append(m)
        return obj


def vertex_color_material(name: str, roughness=0.8, emission_from_alpha=False) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def simple_material(name: str, color, roughness=0.6, metallic=0.0, emission=None, strength=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def build_armature(name: str, bones: dict) -> bpy.types.Object:
    """bones: name -> (head, tail, parent or None). Heads/tails in metres."""
    data = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for bname, (head, tail, parent) in bones.items():
        eb = data.edit_bones.new(bname)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        eb.roll = 0.0
        if parent:
            eb.parent = data.edit_bones[parent]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    return arm


def skin_to(mesh_obj, arm):
    mesh_obj.parent = arm
    mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm


def attach_to_bone(obj, arm, bone: str, world_matrix: Matrix):
    """Parent a separate prop (a weapon) to a bone, keeping its place in the world."""
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    bpy.context.view_layer.update()
    obj.matrix_world = world_matrix


def prop_object(name: str, body: Body, material) -> bpy.types.Object:
    """A rigid prop built with Body (bone names are ignored)."""
    obj = body.to_object(material)
    obj.vertex_groups.clear()
    obj.name = name
    return obj


def add_action(arm, name: str, keys: list, loop=True, reverse=False):
    """keys: list of (frame, {bone: (rx, ry, rz) degrees | {"rot": (...), "loc": (...)}}).
    Every bone is keyed at every key frame (unlisted bones go to rest), so each clip
    fully defines the pose and clips blend cleanly in the game."""
    if reverse:
        last = max(f for f, _ in keys)
        first = min(f for f, _ in keys)
        keys = [(first + last - f, p) for f, p in keys]
    arm.animation_data_create()
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    arm.animation_data.action = action
    for frame, pose in keys:
        for pb in arm.pose.bones:
            spec = pose.get(pb.name, (0, 0, 0))
            rot, loc = (spec.get("rot", (0, 0, 0)), spec.get("loc", (0, 0, 0))) if isinstance(spec, dict) else (spec, (0, 0, 0))
            pb.rotation_euler = Euler([math.radians(a) for a in rot], "XYZ")
            pb.location = Vector(loc)
            pb.keyframe_insert("rotation_euler", frame=frame, group=pb.name)
            pb.keyframe_insert("location", frame=frame, group=pb.name)
    action["loop"] = loop
    arm.animation_data.action = None
    return action


def rest_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_euler = Euler((0, 0, 0))
        pb.location = Vector((0, 0, 0))


def export_glb(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_skins=True,
        export_yup=True,
        export_apply=True,
        export_force_sampling=False,       # keep only our keyframes: much smaller files
        export_optimize_animation_size=True,
    )
    print("exported", path, f"{os.path.getsize(path) / 1024:.1f} KB")


# ---------- preview renders ----------

def setup_preview(target=(0, 0, 0.9), dist=4.2, height=1.4, size=(640, 720), bg="#1d2b1f"):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "VERTEX"
    scene.display.shading.show_cavity = True
    scene.display.shading.show_object_outline = True
    scene.display.shading.object_outline_color = (0.05, 0.05, 0.04)
    scene.display.shading.show_shadows = True
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("preview") if not scene.world else scene.world
    scene.world = world
    world.color = hexcol(bg)[:3]
    scene.display.shading.background_type = "WORLD"
    scene.render.image_settings.file_format = "PNG"

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def aim_camera(cam, angle_deg, target=(0, 0, 0.9), dist=4.2, height=1.4):
    a = math.radians(angle_deg)
    # angle 0 = in front of a character that faces -Y
    cam.location = Vector((math.sin(a) * dist, -math.cos(a) * dist, height))
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_to(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def pose_at(arm, action, frame):
    arm.animation_data_create()
    arm.animation_data.action = action
    bpy.context.scene.frame_set(int(frame))


def contact_sheet(paths: list[Path], out: Path, cols: int, labels: list[str] | None = None):
    """Tile renders into one PNG (needs Pillow in the same Python)."""
    from PIL import Image, ImageDraw
    imgs = [Image.open(p) for p in paths]
    w, h = imgs[0].size
    rows = math.ceil(len(imgs) / cols)
    sheet = Image.new("RGB", (cols * w, rows * h), (18, 26, 20))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(imgs):
        x, y = (i % cols) * w, (i // cols) * h
        sheet.paste(im, (x, y))
        if labels:
            d.rectangle([x + 8, y + 8, x + 8 + 9 * len(labels[i]) + 12, y + 34], fill=(18, 26, 20))
            d.text((x + 16, y + 14), labels[i], fill=(239, 227, 200))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    for p in paths:
        p.unlink()
    print("wrote", out)


# ---------- static props ----------

def glow_material(name: str, color, strength=3.0):
    return simple_material(name, color, roughness=0.9, emission=color, strength=strength)


def static_object(name: str, body: Body, materials) -> bpy.types.Object:
    """A non-animated asset: one mesh, no bones; first material is the vertex-colour one."""
    obj = body.to_object(materials[0], extra_materials=materials[1:])
    obj.vertex_groups.clear()
    obj.name = name
    obj.data.name = name
    return obj


def jitter(verts, amount=0.05, seed=1):
    """Roughen a part (rocks, clay, bark) by nudging its vertices."""
    import random
    rnd = random.Random(seed)
    for v in verts:
        v.co += Vector((rnd.uniform(-amount, amount), rnd.uniform(-amount, amount), rnd.uniform(-amount, amount)))
    return verts


# ---------- posing by direction (creatures whose bones don't line up with the axes) ----------

def aim(arm, bone, d, twist=0.0):
    """Pose rotation (degrees XYZ) that points `bone` along d, given in the armature's rest axes
    (for a child bone this is relative to its parent). twist turns it about its own length first."""
    R = arm.data.bones[bone].matrix_local.to_3x3()
    q = Vector((0, 1, 0)).rotation_difference((R.inverted() @ Vector(d)).normalized())
    if twist:
        q = q @ Quaternion((0, 1, 0), math.radians(twist))
    return tuple(math.degrees(a) for a in q.to_euler("XYZ"))


def turned(arm, bone, yaw=0.0, pitch=0.0, tilt=0.0):
    """The bone's rest direction turned about the world axes: pitch about X (a forward-pointing
    bone tips up), tilt about Y (a bone pointing +X tips down), then yaw about Z."""
    R = arm.data.bones[bone].matrix_local.to_3x3()
    d = R @ Vector((0, 1, 0))
    d = (Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(tilt), 3, "Y")
         @ Matrix.Rotation(math.radians(-pitch), 3, "X") @ d)
    return aim(arm, bone, d)


def static_part(name: str, body: "Body", materials, arm, bone: str):
    """A rigid separate piece riding on a bone (armour plates the game can hide one by one)."""
    obj = body.to_object(materials[0], extra_materials=materials[1:])
    obj.vertex_groups.clear()
    obj.name = name
    obj.data.name = name
    attach_to_bone(obj, arm, bone, Matrix.Identity(4))
    return obj


def aim_edge(arm, bone, d, chord=(0, 1, 0), want=(0, 0, -1)):
    """Like aim(), then turn the bone about its own length so that `chord` (a direction across the
    part at rest, e.g. a wing's trailing edge) ends up facing `want`. For folding wings flat."""
    R = arm.data.bones[bone].matrix_local.to_3x3()
    c = R.inverted() @ Vector(chord)
    base = Vector((0, 1, 0)).rotation_difference((R.inverted() @ Vector(d)).normalized())
    best, score = 0, -9
    for tw in range(-180, 180, 5):
        q = base @ Quaternion((0, 1, 0), math.radians(tw))
        s = (R @ (q @ c)).normalized().dot(Vector(want).normalized())
        if s > score:
            best, score = tw, s
    return aim(arm, bone, d, best)
