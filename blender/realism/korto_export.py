"""Build realistic Korto and export her for Godot: godot/assets/models/characters/korto_real/korto_real.glb

Run:  blender-venv/bin/python blender/realism/korto_export.py
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [sys.argv[0], "--no-preview"]

import bpy  # noqa: E402
import mathutils  # noqa: E402

import export_game as E  # noqa: E402
import korto_real as K  # noqa: E402

ROOT = HERE.parent.parent
OUT = ROOT / "godot" / "assets" / "models" / "characters" / "korto_real"
TEX = HERE / "textures" / "baked"
OUT.mkdir(parents=True, exist_ok=True)
TEX.mkdir(parents=True, exist_ok=True)

# cloth tiles: (material, metres per repeat across, metres per repeat along)
TILES = {"Wrapper": (0.42, 0.42), "Top": (0.24, 0.24), "HeadTie": (0.18, 0.18)}


def image_material(name, color=None, rough=None, normal=None, alpha_from_color=False, rough_value=0.6, metal=0.0, base=(1, 1, 1)):
    """A plain textured Principled material the glTF exporter understands."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs["Roughness"].default_value = rough_value
    b.inputs["Metallic"].default_value = metal
    b.inputs["Base Color"].default_value = (*base, 1)
    if color:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(str(color), check_existing=True)
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if alpha_from_color:
            nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    if rough:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(str(rough), check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(t.outputs["Color"], b.inputs["Roughness"])
    if normal:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(str(normal), check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return mat


def korto_eyes(src_png, out_png):
    """MakeHuman's brown eye texture holds two eyeballs, irises centred at (0.707, 0.297) and
    (0.289, 0.707) of the image, radius about 0.115. Irises go to 45% (deep brown), whites stay at
    95% with a faint warm tint: darkening the whole texture made the whites grey."""
    import numpy as np
    from PIL import Image
    src = Image.open(src_png).convert("RGBA")
    a = np.asarray(src).astype(np.float32) / 255.0
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    iris = np.zeros((h, w), np.float32)
    for cx, cy in ((0.707, 0.297), (0.289, 0.707)):
        d = np.hypot(xx / w - cx, yy / h - cy)
        iris = np.maximum(iris, np.clip((0.125 - d) / 0.012, 0.0, 1.0))   # soft edge at the limbus
    gain = 0.45 * iris + 0.95 * (1.0 - iris)
    tint = np.stack([np.ones_like(iris), 1.0 - 0.03 * (1 - iris), 1.0 - 0.08 * (1 - iris)], -1)
    a[..., :3] = np.clip(a[..., :3] * gain[..., None] * tint, 0.0, 1.0)
    Image.fromarray((a * 255).astype(np.uint8), "RGBA").save(out_png)


def add_skirt_bones(rig):
    """Two helper bones at the hips that the wrapper follows. Each copies its thigh's swing but not
    its twist (a skirt doesn't turn when the leg rolls inward), keyed per clip by skirt_keys()."""
    import bpy
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.scene.objects:
        o.select_set(o is rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    for side in ("l", "r"):
        t = eb[f"thigh_{side}"]
        b = eb.new(f"skirt_{side}")
        b.head, b.tail, b.roll = t.head.copy(), t.tail.copy(), t.roll
        b.parent = eb["pelvis"]
        b.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    for side in ("l", "r"):
        rig.pose.bones[f"skirt_{side}"].rotation_mode = "QUATERNION"


def skirt_keys(rig, action, follow=1.0):
    """Key the skirt bones for one clip: each points `follow` of the way from rest to where its thigh
    points, with no twist."""
    import bpy
    ad = rig.animation_data
    ad.action = action
    ad.action_slot = action.slots[0]
    a0, a1 = map(int, action.frame_range)
    for f in range(a0, a1 + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        for side in ("l", "r"):
            thigh = rig.pose.bones[f"thigh_{side}"]
            sk = rig.pose.bones[f"skirt_{side}"]
            rest = rig.data.bones[f"skirt_{side}"].matrix_local
            rest_dir = (rest.to_3x3() @ mathutils.Vector((0, 1, 0))).normalized()
            now_dir = (thigh.matrix.to_3x3() @ mathutils.Vector((0, 1, 0))).normalized()
            swing = rest_dir.rotation_difference(now_dir)
            swing = mathutils.Quaternion().slerp(swing, follow)
            m = swing.to_matrix().to_4x4() @ rest.to_3x3().to_4x4()
            m.translation = thigh.matrix.translation
            sk.matrix = m
            bpy.context.view_layer.update()
            sk.keyframe_insert("rotation_quaternion", frame=f)
    ad.action = None


def skirt_weights(obj, rig, reach=1.0, blend=0.07, hug=(0.12, 0.55)):
    """Weights for a wrap skirt, replacing the nearest-body weights bind() gave it.
    - Near the waist the cloth hugs her hips, so it keeps the body's own weights there (hip skin moves
      with the thighs; following only the pelvis let her hips push through it). Thigh and leg weights
      go to the skirt bones instead, so the cloth swings with the legs but never twists with them.
    - Lower down the cloth hangs free: each side follows its own skirt bone (up to `reach` at the hem),
      blended smoothly across the front and back over +-`blend` metres. Nearest-body weights split the
      front hard between the legs, and a striding knee pushed through the seam.
    The change from hugging to hanging runs between `hug` fractions of the way down."""
    bones = rig.data.bones
    pelvis = bones["pelvis"].head_local
    left_x = bones["thigh_l"].head_local.x - pelvis.x
    zs = [v.co.z for v in obj.data.vertices]
    top, bot = max(zs), min(zs)
    to_skirt = {}
    for side in ("l", "r"):
        for b in ("thigh", "calf", "foot", "ball", "thigh_twist_01", "calf_twist_01"):
            to_skirt[f"{b}_{side}"] = f"skirt_{side}"
    names = {g.index: g.name for g in obj.vertex_groups}
    body = []
    for v in obj.data.vertices:
        mix = {}
        for g in v.groups:
            n = to_skirt.get(names[g.group], names[g.group])
            mix[n] = mix.get(n, 0.0) + g.weight
        body.append(mix)
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    groups = {}
    def group(n):
        if n not in groups:
            groups[n] = obj.vertex_groups.new(name=n)
        return groups[n]
    h0, h1 = hug
    for v, mix in zip(obj.data.vertices, body):
        t = max(0.0, min(1.0, (top - v.co.z) / max(1e-4, top - bot)))
        k = max(0.0, min(1.0, (t - h0) / (h1 - h0)))
        k = k * k * (3 - 2 * k)                               # 0: hug the body, 1: hang from the skirt bones
        lt = max(0.0, min(1.0, (t - 0.05) / 0.45))          # by mid-thigh the cloth moves with the leg
        legs = reach * (lt * lt * (3 - 2 * lt))
        side = (v.co.x - pelvis.x) * (1 if left_x > 0 else -1)
        u = max(0.0, min(1.0, 0.5 + side / (2 * blend)))
        u = u * u * (3 - 2 * u)
        hang = {"pelvis": 1.0 - legs, "skirt_l": legs * u, "skirt_r": legs * (1 - u)}
        # the back of the hem rides a little on the calves, so a bent knee lifts it instead of
        # pushing through it (running)
        ang = abs(math.degrees(math.atan2(v.co.x - pelvis.x, -(v.co.y - pelvis.y))))
        back = max(0.0, min(1.0, (ang - 95.0) / 45.0))
        low = max(0.0, min(1.0, (t - 0.65) / 0.35))
        c = 0.7 * back * low * low
        if c > 0:
            for side, share in (("l", u), ("r", 1 - u)):
                take = c * share
                hang[f"skirt_{side}"] -= take * legs
                hang[f"calf_{side}"] = hang.get(f"calf_{side}", 0.0) + take * legs
        final = {}
        total_body = sum(mix.values()) or 1.0
        for n, w in mix.items():
            final[n] = final.get(n, 0.0) + (1 - k) * w / total_body
        for n, w in hang.items():
            final[n] = final.get(n, 0.0) + k * w
        # keep the four strongest (what the game engine skins with), normalised
        top4 = sorted(final.items(), key=lambda x: -x[1])[:4]
        tot = sum(w for _, w in top4) or 1.0
        for n, w in top4:
            if w > 1e-4:
                group(n).add([v.index], w / tot, "REPLACE")


def add_animations(rig, blend):
    """Bring the retargeted clips (korto_anims.py) in and put each on its own NLA track, so the glTF
    exporter writes every clip as an animation."""
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.actions = list(src.actions)
    if rig.animation_data is None:
        rig.animation_data_create()
    # the clips key quaternions; a freshly built rig rotates in Euler, which would ignore them
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    import retarget as RT
    names = []
    for act in dst.actions:
        print(f"  {act.name}: facing {RT.facing_offset(rig, act):+.1f} degrees off front")
        skirt_keys(rig, act)
        track = rig.animation_data.nla_tracks.new()
        track.name = act.name
        strip = track.strips.new(act.name, int(act.frame_range[0]), act)
        if hasattr(strip, "action_slot") and len(getattr(act, "slots", [])):
            strip.action_slot = act.slots[0]
        track.mute = True
        names.append(act.name)
    rig.animation_data.action = None
    return names


def principled_value(mat, socket, default):
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            s = n.inputs[socket]
            return tuple(s.default_value)[:3] if socket == "Base Color" else s.default_value
    return default


def main():
    human, rig, eyes = K.build()
    K.dress(human)          # skin, eyes, brows, lashes, cornrows, and the outfit
    objs = {o.name: o for o in bpy.data.objects}
    print("built:", sorted(objs))

    # ---- freeze geometry
    E.freeze(human)
    E.drop_helpers(human)
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o is not human:
            E.freeze(o)

    # ---- triangle budget (the brief: 100k for the whole character on PC High)
    BUDGET = {"KortoWrapper": 14000, "KortoTop": 9000, "KortoHeadTie": 6000, "KortoTieBand0": 2000, "KortoTieBand1": 2000, "KortoTieBand2": 2000, "KortoKnot": 1500, "KortoShorts": 3000,
              "KortoBelt": 1200, "KortoBracer": 1500, "KortoStraps": 800, "KortoScalp": 3000, "KortoBeads": 5000,
              "KortoBangle": 800}
    for name, target in BUDGET.items():
        o = bpy.data.objects.get(name)
        if o:
            print(f"  {name}: {E.triangles(o)} -> {E.reduce_to(o, target)} triangles")

    # ---- bake the skin on her own UVs
    skin = E.bake_maps(human, TEX, "korto_skin", 2048)
    human.data.materials.clear()
    human.data.materials.append(image_material("KortoSkin", skin["color"], skin["rough"], skin["normal"]))

    # ---- cornrows: UV the scalp, bake, and keep the soft hairline as vertex alpha
    scalp = objs["KortoScalp"]
    E._select_only(scalp)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    fade = scalp.data.attributes.get("hairline")
    if fade is not None:
        col = scalp.data.color_attributes.new("Col", "BYTE_COLOR", "POINT")
        for i, d in enumerate(fade.data):
            col.data[i].color = (1, 1, 1, d.value)
        scalp.data.color_attributes.active_color = col
    rows = E.bake_maps(scalp, TEX, "korto_cornrows", 1024)
    scalp.data.materials.clear()
    scalp.data.materials.append(image_material("KortoCornrows", rows["color"], rows["rough"], rows["normal"]))

    # ---- cloth: tiles, and garment UVs rescaled from metres to tiles
    cloth_objs = {"Wrapper": ["KortoWrapper"], "Top": ["KortoTop"], "HeadTie": ["KortoHeadTie", "KortoKnot", "KortoTieHem", "KortoTieBand0", "KortoTieBand1", "KortoTieBand2"]}
    for mname, (pu, pv) in TILES.items():
        mat = bpy.data.materials[mname]
        tile = E.bake_tile(mat, pu, pv, TEX, f"korto_{mname.lower()}", 1024)
        new = image_material(f"Korto{mname}", tile["color"], tile["rough"], tile["normal"])
        for on in cloth_objs[mname]:
            o = objs[on]
            if not o.data.uv_layers:
                import costume
                costume.cylinder_uv(o)
            for d in o.data.uv_layers.active.data:
                d.uv = (d.uv.x / pu, d.uv.y / pv)
            o.data.materials.clear()
            o.data.materials.append(new)

    # hem dust on the wrapper, as vertex colour (Godot multiplies it into the cloth)
    w = objs["KortoWrapper"]
    col = w.data.color_attributes.new("Col", "BYTE_COLOR", "POINT")
    hem = min(v.co.z for v in w.data.vertices)
    for i, v in enumerate(w.data.vertices):
        z = (w.matrix_world @ v.co).z
        k = max(0.0, min(1.0, 1.0 - (z - hem) / 0.12)) * 0.55
        col.data[i].color = (1.0 - 0.12 * k, 1.0 - 0.45 * k, 1.0 - 0.6 * k, 1.0)
    w.data.color_attributes.active_color = col

    # ---- simple materials: flatten to plain values the exporter keeps
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for i, mat in enumerate(o.data.materials):
            if mat and mat.name.split(".")[0] in ("Shorts", "Leather", "LeatherDark", "Iron") or (mat and mat.name.startswith("Bead")):
                base = principled_value(mat, "Base Color", (0.5, 0.5, 0.5))
                # the procedural version multiplied noise in: take the colour a little darker
                o.data.materials[i] = image_material("Korto" + mat.name.split(".")[0], base=tuple(c * 0.9 for c in base),
                                                     rough_value=principled_value(mat, "Roughness", 0.6),
                                                     metal=principled_value(mat, "Metallic", 0.0))

    # ---- eyes: darken the irises toward a deep brown; keep the whites light and a little warm
    eye_png = TEX / "korto_eyes.png"
    korto_eyes(K.MH_DATA / "eyes/materials/brown_eye.png", eye_png)
    eyes.data.materials.clear()
    eyes.data.materials.append(image_material("KortoEyes", eye_png, alpha_from_color=True, rough_value=0.08))

    # ---- brows and lashes: their strand textures, alpha from the texture
    for o in bpy.data.objects:
        if o.name.startswith(("KortoBrow", "KortoLashes")):
            png = K.HERE / "textures" / ("korto_brow.png" if "Brow" in o.name else "korto_lash.png")
            o.data.materials.clear()
            o.data.materials.append(image_material("KortoBrows" if "Brow" in o.name else "KortoLashes", png, alpha_from_color=True, rough_value=0.8))

    # ---- skin everything to the rig
    for o in list(bpy.data.objects):
        if o.type != "MESH" or o is human:
            continue
        name = o.name
        if name.startswith(("KortoBrow", "KortoLashes", "KortoScalp", "KortoHeadTie", "KortoKnot", "KortoTieHem", "KortoTieBand")) or name == "KortoEyes":
            E.bind(o, human, rig, only="head")
        elif name == "KortoBeads":
            E.bind(o, human, rig, only="spine_03")
        elif name == "KortoBangle":
            E.bind(o, human, rig, only="lowerarm_r")
        elif name == "KortoBuckle":
            E.bind(o, human, rig, only="pelvis")
        else:
            E.bind(o, human, rig)

    add_skirt_bones(rig)
    skirt_weights(bpy.data.objects["KortoWrapper"], rig)

    clips = add_animations(rig, HERE / "korto_anims.blend")
    print("clips:", clips)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name in ("tile",):
            bpy.data.objects.remove(o)
    E.export_glb(OUT / "korto_real.glb", [rig] + meshes)
    import os
    if os.environ.get("KORTO_SAVE_BLEND"):          # keep the built scene for checking
        bpy.ops.wm.save_as_mainfile(filepath=os.environ["KORTO_SAVE_BLEND"])
    tris = sum(E.triangles(o) for o in meshes)
    for o in sorted(meshes, key=E.triangles, reverse=True)[:6]:
        print(f"  {o.name}: {E.triangles(o)}")
    print(f"exported {OUT / 'korto_real.glb'}: {len(meshes)} meshes, {tris} triangles")


if __name__ == "__main__":
    main()
