"""Put CMU motion capture (BVH, free for commercial use) onto an MPFB "game_engine" rig.

For each mapped bone, the source's rotation away from its rest pose (in world space) is applied to
the target bone, after the target has been turned to point the way the source pointed at rest, so
different rest poses (CMU's T-pose, MPFB's A-pose) don't leak into the motion. Clips are turned to
face the rig's front, kept in place (the game moves the character), resampled to 30 fps, and cut at
the best loop point when asked.
"""
import math

import bpy
import mathutils

Q = mathutils.Quaternion
V = mathutils.Vector

# CMU (cgspeed BVH) -> MPFB game_engine
MAP = {
    "Hips": "pelvis", "LowerBack": "spine_01", "Spine": "spine_02", "Spine1": "spine_03",
    "Neck": "neck_01", "Head": "head",
    "LeftShoulder": "clavicle_l", "LeftArm": "upperarm_l", "LeftForeArm": "lowerarm_l", "LeftHand": "hand_l",
    "RightShoulder": "clavicle_r", "RightArm": "upperarm_r", "RightForeArm": "lowerarm_r", "RightHand": "hand_r",
    "LeftUpLeg": "thigh_l", "LeftLeg": "calf_l", "LeftFoot": "foot_l", "LeftToeBase": "ball_l",
    "RightUpLeg": "thigh_r", "RightLeg": "calf_r", "RightFoot": "foot_r", "RightToeBase": "ball_r",
}


# cgspeed CMU BVH joints with no length of their own (the importer invents a direction for them)
ZERO_LENGTH = {"LeftHand", "RightHand", "Spine1"}


def import_bvh(path):
    before = set(bpy.data.objects)
    bpy.ops.import_anim.bvh(filepath=str(path), global_scale=1.0, frame_start=1, use_fps_scale=False,
                            update_scene_fps=False, update_scene_duration=False, rotate_mode="NATIVE",
                            axis_forward="-Z", axis_up="Y")
    src = next(o for o in bpy.data.objects if o not in before)
    return src


def _rest_world(arm, bone):
    return (arm.matrix_world @ arm.data.bones[bone].matrix_local)


def _dir(m):
    return (m.to_3x3() @ V((0, 1, 0))).normalized()


def retarget(src, tgt, name, start=None, end=None, step=4, in_place=True, loop=False, yaw_fix=0.0, vertical=True):
    """vertical=False also removes steady rise or fall (climbing in place: the game moves her up)."""
    """Bake src's animation (BVH frames start..end) onto tgt as an action called `name`."""
    sc = bpy.context.scene
    act = src.animation_data.action
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    start = f0 if start is None else start
    end = f1 if end is None else end

    # size: hip height ratio
    sc.frame_set(start)
    src_hip = (src.matrix_world @ src.pose.bones["Hips"].head).z
    tgt_hip = _rest_world(tgt, "pelvis").translation.z
    scale = tgt_hip / max(src_hip, 1e-4)

    # facing: turn the clip so the source's hips face the way the target's do, on average
    def lateral(fr):
        sc.frame_set(fr)
        l = src.matrix_world @ src.pose.bones["LeftUpLeg"].head
        r = src.matrix_world @ src.pose.bones["RightUpLeg"].head
        d = l - r
        return V((d.x, d.y, 0)).normalized()
    acc = V((0, 0, 0))
    for fr in range(start, end + 1, max(1, (end - start) // 20)):
        acc += lateral(fr)
    src_lat = acc.normalized()
    t_lat = (_rest_world(tgt, "thigh_l").translation - _rest_world(tgt, "thigh_r").translation)
    t_lat = V((t_lat.x, t_lat.y, 0)).normalized()
    yaw = math.atan2(t_lat.y, t_lat.x) - math.atan2(src_lat.y, src_lat.x) + yaw_fix
    R = Q((0, 0, 1), yaw)

    # rest alignment: target bones turned to point where the (turned) source bones point at rest
    sc.frame_set(start)
    # rest alignment uses the source's own rest; the facing turn R is applied to each bone's motion
    # afterwards. (Applying R to the rest too made the motion R·M·R⁻¹, which for turns about the
    # vertical cancels out: clips kept whatever way the mocap actor faced.)
    src_rest = {s: _rest_world(src, s) for s in MAP}
    def src_rest_dir(s):
        """A source bone's rest direction. The BVH wrists (and Spine1) are zero-length bones whose
        direction the importer makes up; for those, use the parent's, so the hand continues the
        forearm. Using the made-up direction bent her wrists about 90 degrees."""
        bone = src.data.bones[s]
        # the importer warns "zero length node found" for these and gives them a made-up tail
        while (bone.length < 1e-4 or bone.name in ZERO_LENGTH) and bone.parent:
            bone = bone.parent
        return _dir(_rest_world(src, bone.name))
    ref = {}
    for s, t in MAP.items():
        trw = _rest_world(tgt, t)
        a = _dir(trw).rotation_difference(src_rest_dir(s))
        ref[t] = (a @ trw.to_quaternion())

    order = [b.name for b in tgt.data.bones]          # parents come before children
    inv_tgt = tgt.matrix_world.to_quaternion().inverted()
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    tgt.animation_data_create()
    tgt.animation_data.action = action
    for pb in tgt.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)

    hips0 = None
    frames = list(range(start, end + 1, step))
    trail = []
    for i, fr in enumerate(frames):
        sc.frame_set(fr)
        world = {s: src.matrix_world @ src.pose.bones[s].matrix for s in MAP}
        hip = R @ (world["Hips"].translation * 1.0)
        trail.append(hip)
    # remove travel: a straight-line fit of horizontal motion (keeps sway, drops progress)
    n = len(trail)
    if in_place and n > 1:
        a, b = trail[0], trail[-1]
        drift = [(a + (b - a) * (k / (n - 1))) for k in range(n)]
    else:
        drift = [trail[0]] * n

    for i, fr in enumerate(frames):
        sc.frame_set(fr)
        for s, t in MAP.items():
            pass
        world = {s: src.matrix_world @ src.pose.bones[s].matrix for s in MAP}
        for bname in order:
            s = next((k for k, v in MAP.items() if v == bname), None)
            if s is None:
                continue
            pb = tgt.pose.bones[bname]
            D = R @ (world[s].to_quaternion() @ src_rest[s].to_quaternion().inverted())
            W = D @ ref[bname]
            rot_arm = inv_tgt @ W
            m = rot_arm.to_matrix().to_4x4()
            if bname == "pelvis":
                hip = trail[i] - V((drift[i].x, drift[i].y, 0)) + V((0, 0, 0))
                z = trail[i].z if vertical else trail[i].z - (drift[i].z - drift[0].z)
                hip = V((hip.x * scale, hip.y * scale, z * scale))
                m.translation = tgt.matrix_world.inverted() @ (hip + V((0, 0, 0)))
            else:
                m.translation = pb.matrix.translation
            pb.matrix = m
            bpy.context.view_layer.update()
        for bname in order:
            if any(v == bname for v in MAP.values()):
                pb = tgt.pose.bones[bname]
                pb.keyframe_insert("rotation_quaternion", frame=i + 1)
                if bname == "pelvis":
                    pb.keyframe_insert("location", frame=i + 1)
    action.frame_range = (1, len(frames))
    if loop:
        _close_loop(action, len(frames))
    return action


def _close_loop(action, last, blend=6):
    """Ease the last few frames toward the first so the clip loops without a pop."""
    for fc in _fcurves(action):
        kps = fc.keyframe_points
        if len(kps) < blend + 2:
            continue
        first = kps[0].co.y
        for k in range(blend):
            i = len(kps) - blend + k
            t = (k + 1) / blend
            kps[i].co.y = kps[i].co.y * (1 - t) + first * t
        fc.update()


def _fcurves(action):
    """All f-curves of an action (Blender 4.4+ keeps them in layers/strips/channelbags)."""
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                out.extend(bag.fcurves)
    return out


def best_loop(src, start, end, min_len, max_len, step=4):
    """Find the window [a, b] in src's frames where the pose at b best matches the pose at a."""
    sc = bpy.context.scene
    names = ["LeftUpLeg", "LeftLeg", "RightUpLeg", "RightLeg", "LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "Spine1"]

    def pose(fr):
        sc.frame_set(fr)
        return [src.pose.bones[n].matrix.to_quaternion() for n in names]

    cache = {}

    def get(fr):
        if fr not in cache:
            cache[fr] = pose(fr)
        return cache[fr]

    best = (1e9, start, start + min_len)
    for a in range(start, max(start + 1, end - min_len), step * 2):
        pa = get(a)
        for b in range(a + min_len, min(end, a + max_len) + 1, step):
            pb = get(b)
            d = sum(1 - abs(qa.dot(qb)) for qa, qb in zip(pa, pb))
            if d < best[0]:
                best = (d, a, b)
    return best[1], best[2]


def _hips_angle(rig):
    """Direction the hips face, as the angle of the left-to-right hip line in the ground plane."""
    bpy.context.view_layer.update()
    lat = (rig.matrix_world @ rig.pose.bones["thigh_l"].head) - (rig.matrix_world @ rig.pose.bones["thigh_r"].head)
    return math.atan2(lat.y, lat.x)


def _pelvis_curves(action, slot):
    bag = None
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(slot)
    rot = sorted([fc for fc in bag.fcurves if fc.data_path == 'pose.bones["pelvis"].rotation_quaternion'], key=lambda f: f.array_index)
    loc = sorted([fc for fc in bag.fcurves if fc.data_path == 'pose.bones["pelvis"].location'], key=lambda f: f.array_index)
    return rot, loc


def face_front(rig, action):
    """Turn a clip so that, on average, her hips face the way they do at rest (the rig's front).
    Mocap clips face wherever the actor faced; this squares them up. Returns the turn in degrees."""
    ad = rig.animation_data or rig.animation_data_create()
    keep_action, keep_slot = ad.action, getattr(ad, "action_slot", None)
    ad.action = None
    for pb in rig.pose.bones:            # unassigning an action leaves its last pose: clear it
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    rest = _hips_angle(rig)
    ad.action = action
    slot = action.slots[0]
    ad.action_slot = slot
    a0, a1 = map(int, action.frame_range)
    sx = sy = 0.0
    for f in range(a0, a1 + 1):
        bpy.context.scene.frame_set(f)
        a = _hips_angle(rig)
        sx += math.cos(a)
        sy += math.sin(a)
    turn = rest - math.atan2(sy, sx)
    # the turn about world up, carried into the pelvis bone's own space
    w = rig.matrix_world.to_quaternion()
    turn_arm = w.inverted() @ Q((0, 0, 1), turn) @ w
    b = rig.data.bones["pelvis"].matrix_local.to_quaternion()
    conv = b.inverted() @ turn_arm @ b
    rot, loc = _pelvis_curves(action, slot)
    if len(rot) == 4:
        for i in range(len(rot[0].keyframe_points)):
            q = Q([rot[k].keyframe_points[i].co[1] for k in range(4)])
            q2 = conv @ q
            for k in range(4):
                rot[k].keyframe_points[i].co[1] = q2[k]
        for fc in rot:
            fc.update()
    if len(loc) == 3:
        for i in range(len(loc[0].keyframe_points)):
            v = V([loc[k].keyframe_points[i].co[1] for k in range(3)])
            v2 = conv @ v
            for k in range(3):
                loc[k].keyframe_points[i].co[1] = v2[k]
        for fc in loc:
            fc.update()
    # check: the clip's average facing now matches rest
    sx = sy = 0.0
    for f in range(a0, a1 + 1):
        bpy.context.scene.frame_set(f)
        a = _hips_angle(rig)
        sx += math.cos(a)
        sy += math.sin(a)
    off = math.degrees(math.atan2(math.sin(rest - math.atan2(sy, sx)), math.cos(rest - math.atan2(sy, sx))))
    ad.action = keep_action
    if keep_slot is not None:
        ad.action_slot = keep_slot
    return math.degrees(turn), off


def facing_offset(rig, action):
    """How far (degrees) a clip's average hip direction is from the rig's rest facing. Measures only."""
    ad = rig.animation_data or rig.animation_data_create()
    ad.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    rest = _hips_angle(rig)
    ad.action = action
    ad.action_slot = action.slots[0]
    a0, a1 = map(int, action.frame_range)
    sx = sy = 0.0
    for f in range(a0, a1 + 1):
        bpy.context.scene.frame_set(f)
        a = _hips_angle(rig)
        sx += math.cos(a)
        sy += math.sin(a)
    d = rest - math.atan2(sy, sx)
    return math.degrees(math.atan2(math.sin(d), math.cos(d)))


# relaxed hand: curl per joint (degrees) for each finger; the clips don't animate fingers
CURL = {"thumb": (0, 12, 15), "index": (14, 20, 14), "middle": (18, 26, 18), "ring": (22, 30, 20), "pinky": (26, 34, 22)}


def relax_hands(rig, action):
    """Key a relaxed, slightly curled hand into a clip (first and last frame). Each finger joint bends
    toward the palm: the palm side is read from the rest pose, where the middle finger already curves
    a little that way. Without this, fingers stay splayed flat as at rest."""
    slot = action.slots[0]
    ad = rig.animation_data
    ad.action = action
    ad.action_slot = slot
    a0, a1 = map(int, action.frame_range)
    for side in ("l", "r"):
        bones = rig.data.bones
        d1 = _dir(bones[f"middle_01_{side}"].matrix_local)
        d3 = _dir(bones[f"middle_03_{side}"].matrix_local)
        palm = (d3 - d1 * d3.dot(d1)).normalized()      # toward the palm, in armature space
        for finger, angles in CURL.items():
            for j, deg in enumerate(angles, start=1):
                name = f"{finger}_0{j}_{side}"
                if name not in bones or deg == 0:
                    continue
                m = bones[name].matrix_local.to_3x3()
                d = (m @ V((0, 1, 0))).normalized()
                axis_arm = d.cross(palm)
                if axis_arm.length < 1e-6:
                    continue
                axis_local = (m.inverted() @ axis_arm).normalized()
                q = Q(axis_local, math.radians(deg))
                pb = rig.pose.bones[name]
                pb.rotation_mode = "QUATERNION"
                pb.rotation_quaternion = q
                for f in (a0, a1):
                    pb.keyframe_insert("rotation_quaternion", frame=f)
    ad.action = None
