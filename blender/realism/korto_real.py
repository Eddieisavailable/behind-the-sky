"""Realistic Korto, step 1: body and face from MPFB 2 (MakeHuman for Blender, CC0 output).

Run:  blender-venv/bin/python blender/realism/korto_real.py [--preview out_dir]

Follows "Korto — realism brief": a young West African woman of about 19, 1.65 m, lean and athletic,
oval face with high cheekbones, firm jaw to a small chin, large wide-set eyes, broad rounded nose,
full lips. Uses MPFB's "game_engine" rig, which has the Unreal / MetaHuman bone names, so animation
made for her carries over if she becomes a MetaHuman later.
"""
import math
import os
import sys
from pathlib import Path

import bpy  # first: it puts Blender's own modules (addon_utils) on the path
import addon_utils

sys.path.insert(0, str(Path(__file__).resolve().parent))

HERE = Path(__file__).resolve().parent
MH_DATA = Path("/home/claude/tools/mpfb/mh/makehuman/data")
HEIGHT = 1.65

# ---------------------------------------------------------------- the character, in MPFB's terms

PHENOTYPE = {
    "gender": 0.0,          # 0 female, 1 male
    "age": 0.366,           # 0.1875 = 11 years, 0.5 = 25 years: about 19
    "muscle": 0.64,         # athletic: forge work and the bow
    "weight": 0.40,         # lean
    "proportions": 0.75,    # long-legged, idealised a little
    "height": 0.55,         # scaled to exactly 1.65 m afterwards
    "cupsize": 0.42,
    "firmness": 0.6,
    "race": {"african": 1.0, "asian": 0.0, "caucasian": 0.0},
}

# Face and body detail on top of the phenotype: (target, weight). Kept moderate: the African
# phenotype already gives a broad nose and full lips; pushing further turns into caricature.
TARGETS = [
    # head: oval, not round; a little less soft tissue
    ("head-oval", 0.45), ("head-fat-decr", 0.35), ("head-scale-vert-incr", 0.1),
    # cheekbones high and defined, cheeks lean
    ("l-cheek-bones-incr", 0.55), ("r-cheek-bones-incr", 0.55),
    ("l-cheek-volume-decr", 0.3), ("r-cheek-volume-decr", 0.3),
    ("l-cheek-trans-up", 0.2), ("r-cheek-trans-up", 0.2),
    # firm jaw narrowing to a small chin
    ("chin-width-decr", 0.25), ("chin-prominent-incr", 0.15), ("chin-height-decr", 0.1),
    # large, almond, slightly wide-set eyes with a heavy upper lid
    ("l-eye-scale-incr", 0.25), ("r-eye-scale-incr", 0.25),
    ("l-eye-trans-out", 0.15), ("r-eye-trans-out", 0.15),
    ("l-eye-corner1-up", 0.15), ("r-eye-corner1-up", 0.15),
    ("l-eye-eyefold-down", 0.25), ("r-eye-eyefold-down", 0.25),
    # broad nose with a rounded tip and full nostrils, straight bridge
    ("nose-point-width-incr", 0.3), ("nose-flaring-incr", 0.3), ("nose-hump-decr", 0.3),
    # full lips, the lower fuller
    ("mouth-lowerlip-volume-incr", 0.35), ("mouth-upperlip-volume-incr", 0.15),
    ("mouth-cupidsbow-incr", 0.3),
    # straight, strong brows sit slightly low
    ("eyebrows-trans-down", 0.15),
    # body: the African phenotype at full strength gives large, high buttocks and a sway in the lower
    # back. She is lean and athletic: smaller, firmer buttocks, less hip depth, a flat toned stomach
    ("buttocks-volume-decr", 0.75), ("hip-scale-depth-decr", 0.45), ("pelvis-tone-incr", 0.5),
    ("stomach-pregnant-decr", 0.9), ("stomach-tone-incr", 0.7),
]


def mpfb(name):
    return sys.modules["bl_ext.user_default.mpfb." + name]


def evaluated_bounds(obj):
    """World-space min and max corners of an object as it renders (shape keys, modifiers, rig)."""
    import mathutils
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mesh = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
    lo = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def build():
    addon_utils.enable("bl_ext.user_default.mpfb", default_set=True)
    HS = mpfb("services.humanservice").HumanService
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # MPFB's character format, every field present (the loader expects them all)
    info = {"clothes": [], "color_adjustments": {}, "expressions": [], "eyebrows": "", "eyelashes": "",
            "eyes": "", "eyes_material_settings": {}, "eyes_material_type": "MAKESKIN", "hair": "",
            "makeup": [], "phenotype": PHENOTYPE, "proxy": "", "rig": "", "skin_material_settings": {},
            "skin_material_type": "NONE", "skin_mhmat": "", "teeth": "", "tongue": "",
            "targets": [{"target": t, "value": v} for t, v in TARGETS]}
    settings = HS.get_default_deserialization_settings()
    settings["subdiv_levels"] = 0
    settings["load_clothes"] = False
    human = HS.deserialize_from_dict(info, settings)
    human.name = "Korto"

    rig = HS.add_builtin_rig(human, "game_engine")
    rig.name = "KortoRig"

    eyes = HS.add_mhclo_asset(str(MH_DATA / "eyes/high-poly/high-poly.mhclo"), human, asset_type="Eyes",
                              subdiv_levels=0, material_type="PROCEDURAL_EYES")
    if eyes:
        eyes.name = "KortoEyes"

    # exactly 1.65 m: measure the finished body (shape keys and the helper mask applied) and scale the rig
    top = evaluated_bounds(human)[1].z
    rig.scale = (HEIGHT / top,) * 3
    bpy.context.view_layer.update()
    return human, rig, eyes


# ---------------------------------------------------------------- skin, eyes, brows, lashes, hair

def dress(human):
    import human_lib as H
    unit = human.matrix_world.to_scale().x
    human.data.materials.clear()
    human.data.materials.append(H.skin_material("KortoSkin", unit=unit, roughness=0.56, pore_depth=0.25))   # matte working skin, not oily
    eyes = bpy.data.objects.get("KortoEyes")
    eyes.data.materials.clear()
    eyes.data.materials.append(H.eye_material("KortoEyes"))
    rig = bpy.data.objects["KortoRig"]
    tex_dir = HERE / "textures"
    tex_dir.mkdir(exist_ok=True)
    brow_mat = H.card_material("KortoBrows", H.strand_texture(tex_dir / "korto_brow.png", "brow"), rough=0.85, spec=0.15)
    lash_mat = H.card_material("KortoLashes", H.strand_texture(tex_dir / "korto_lash.png", "lash", size=(512, 96)), rough=0.35)

    import math
    dg = bpy.context.evaluated_depsgraph_get()
    ev = eyes.evaluated_get(dg)
    em = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in em.vertices]
    ev.to_mesh_clear()
    for side in (1, -1):              # +x is her left
        e = [p for p in pts if p.x * side > 0]
        cx = sum(p.x for p in e) / len(e)
        cz = sum(p.z for p in e) / len(e)
        front = min(p.y for p in e)
        ew = max(p.x for p in e) - min(p.x for p in e)
        # brow: an arch from just inside the eye's inner corner to past the outer corner
        bp, bn, bw = [], [], []
        for i in range(14):
            t = i / 13
            x = cx + side * ew * (-0.62 + 1.45 * t)
            w = 0.0095 - 0.0058 * t ** 1.3
            z = cz + ew * 0.62 + 0.0055 * math.sin(math.pi * min(1.0, t / 0.68) * 0.5) * (1.0 if t < 0.68 else 1.0 - (t - 0.68) * 1.4) - w * 0.5
            p, n = H.surface_point(human, (x, front - 0.3, z), (0, 1, 0))
            if p is not None:
                bp.append(p); bn.append(n); bw.append(w)
        if side < 0:
            bp, bn, bw = bp[::-1], bn[::-1], bw[::-1]
        H.ribbon(f"KortoBrow_{'L' if side > 0 else 'R'}", bp, bn, bw, 0.0007, brow_mat, parent=rig)
        # upper lashes along the lid margin: scan up from the eye's middle until the skin closes over it
        lp, ln, lw = [], [], []
        for i in range(11):
            t = i / 10
            x = cx + side * ew * (-0.42 + 0.84 * t)
            z = cz
            hit = None
            while z < cz + ew * 0.7:
                p, n = H.surface_point(human, (x, front - 0.3, z), (0, 1, 0))
                if p is not None and p.y < front + 0.004:
                    hit = (p, n)
                    break
                z += 0.0004
            if hit:
                lp.append(hit[0]); ln.append(hit[1]); lw.append(0.006 + 0.0045 * math.sin(math.pi * t))
        if side < 0:
            lp, ln, lw = lp[::-1], ln[::-1], lw[::-1]
        if len(lp) > 3:
            H.ribbon(f"KortoLashes_{'L' if side > 0 else 'R'}", lp, ln, lw, 0.0002, lash_mat, parent=rig,
                     up=(0, -0.55, 0.83), follow_surface=False)

    # cornrows on the scalp: MakeHuman's hair helper is a cap over the scalp, shaped to her head
    eye_z = sum(p.z for p in pts) / len(pts)
    eye_front = min(p.y for p in pts)
    make_scalp_cap(human, rig, H.cornrow_material("KortoCornrows"), eye_z, eye_front)
    if "--no-outfit" not in sys.argv:
        import korto_outfit
        korto_outfit.dress(human, rig, eye_z, eye_front)


def make_scalp_cap(human, rig, material, eye_z, eye_front):
    """Cornrow cap: her own scalp skin above a hairline, lifted 1.5 mm. The hairline is set by the
    angle around the head: high at the forehead, above the ears, down to the nape."""
    import bmesh
    import math
    # (angle from the front in degrees, height of the hairline above the eye centre in metres)
    line = [(0, 0.040), (35, 0.036), (65, 0.030), (90, 0.028), (120, 0.0), (155, -0.045), (180, -0.062)]

    def hairline(deg):
        for (a0, z0), (a1, z1) in zip(line, line[1:]):
            if deg <= a1:
                return z0 + (z1 - z0) * (deg - a0) / (a1 - a0)
        return line[-1][1]

    cy = eye_front + 0.085            # roughly the middle of the head, front to back
    dg = bpy.context.evaluated_depsgraph_get()
    ev = human.evaluated_get(dg)
    me = ev.to_mesh()
    keep = {}
    for v in me.vertices:
        p = ev.matrix_world @ v.co
        if p.z < eye_z - 0.09:
            continue
        deg = abs(math.degrees(math.atan2(p.x, -(p.y - cy))))
        above = p.z - (eye_z + hairline(deg))
        if above > -0.010:
            keep[v.index] = (p, (ev.matrix_world.to_3x3() @ v.normal).normalized(), above)
    bm = bmesh.new()
    fade = bm.verts.layers.float.new("hairline")
    vmap = {}
    for f in me.polygons:
        if all(i in keep for i in f.vertices):
            vs = []
            for i in f.vertices:
                if i not in vmap:
                    p, n, above = keep[i]
                    vmap[i] = bm.verts.new(p + n * 0.0015)
                    vmap[i][fade] = max(0.0, min(1.0, (above + 0.006) / 0.014))   # 0 at the edge .. 1 inside
                vs.append(vmap[i])
            bm.faces.new(vs)
    ev.to_mesh_clear()
    cap_me = bpy.data.meshes.new("KortoScalp")
    bm.normal_update()
    bm.to_mesh(cap_me)
    bm.free()
    cap = bpy.data.objects.new("KortoScalp", cap_me)
    bpy.context.scene.collection.objects.link(cap)
    cap_me.materials.append(material)
    for p in cap_me.polygons:
        p.use_smooth = True
    sub = cap.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 2
    __import__("human_lib").attach_to_bone(cap, rig, "head")
    print("scalp cap:", len(cap_me.vertices), "verts")
    return cap


# ---------------------------------------------------------------- preview renders (Cycles, CPU)

def preview(human, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 900, 1200
    sc.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
    sc.world = world

    dress(human)

    def light(name, loc, energy, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.size, d.color = energy, size, color
        o = bpy.data.objects.new(name, d)
        sc.collection.objects.link(o)
        o.location = loc
        direction = -o.location + bpy.data.objects["Korto"].matrix_world.translation + __import__("mathutils").Vector((0, 0, 1.3))
        o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    light("Key", (1.6, -2.2, 2.2), 260, 1.2, (1, 0.95, 0.88))
    light("Fill", (-2.4, -1.6, 1.4), 70, 2.0, (0.85, 0.9, 1))
    light("Rim", (-0.6, 2.4, 2.4), 200, 1.0)

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    import mathutils

    def shoot(name, loc, target, lens):
        cam.location = loc
        cam.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        sc.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)

    if "--face-only" not in sys.argv:
        shoot("korto_body_front", (0, -3.4, 0.95), (0, 0, 0.86), 50)
        shoot("korto_body_three_quarter", (2.3, -2.5, 1.05), (0, 0, 0.86), 50)
        shoot("korto_body_back", (-1.2, 3.2, 1.1), (0, 0, 0.9), 50)
    if "--body-only" in sys.argv:
        return
    lo, hi = evaluated_bounds(bpy.data.objects["KortoEyes"])
    ez, ey = (lo.z + hi.z) / 2, lo.y
    shoot("korto_face_front", (0, ey - 0.62, ez + 0.01), (0, ey + 0.08, ez - 0.03), 85)
    shoot("korto_face_three_quarter", (0.42, ey - 0.45, ez + 0.02), (0, ey + 0.08, ez - 0.03), 85)


if __name__ == "__main__":
    human, rig, eyes = build()
    print("Korto built:", len(human.data.vertices), "verts; rig bones", len(rig.data.bones), "; scale", tuple(round(s, 3) for s in rig.scale))
    if "--preview" in sys.argv:
        preview(human, sys.argv[sys.argv.index("--preview") + 1])
    if "--save" in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--save") + 1])
