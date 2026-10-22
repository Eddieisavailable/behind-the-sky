"""Retarget Korto's motion-capture clips onto her rig and save them to textures/../korto_anims.blend.

Clips (CMU motion capture, free for commercial use, mocap.cs.cmu.edu):
  Idle  82_08  standing still (frames 60-1000)   Run   09_02  run
  Walk  93_07  casual walk                   Climb 13_34  climbing a ladder (vines on the bele tree)
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:]]

import bpy  # noqa: E402

import korto_real as K  # noqa: E402
import retarget as RT  # noqa: E402

CMU = Path("/home/claude/tools/mocap/cmu/data")
CLIPS = {
    # name: (file, part of the clip to use (first, last frame) or None, loop length (min s, max s), loop)
    "Run": ("009/09_02.bvh", None, (0.6, 1.2), True),
    "Walk": ("093/93_07.bvh", None, (1.0, 2.0), True),
    "Idle": ("082/82_08.bvh", (90, 980), (4.0, 7.0), True),      # stands still, facing one way
    "Climb": ("013/13_34.bvh", (200, 520), (0.9, 2.2), True),   # the hips rise steadily: on the ladder
}
OUT = HERE / "korto_anims.blend"


def main(only=None):
    human, rig, eyes = K.build()
    for o in (human, eyes):
        for m in o.modifiers:
            if m.type == "ARMATURE":
                m.show_viewport = False
    for name, (f, part, window, loop) in CLIPS.items():
        if only and name not in only:
            continue
        src = RT.import_bvh(CMU / f)
        a0, a1 = map(int, src.animation_data.action.frame_range)
        lo, hi = part if part else (a0 + 30, a1 - 30)
        fps = 120
        a, b = RT.best_loop(src, lo, hi, int(window[0] * fps), int(window[1] * fps))
        # retarget, measure which way she ends up facing, and turn the whole capture to correct it:
        # turning only the hips afterwards would leave legs and torso twisted against them
        fix = 0.0
        for attempt in range(3):
            act = RT.retarget(src, rig, name, a, b, step=4, in_place=True, loop=loop, vertical=(name != "Climb"), yaw_fix=math.radians(fix))
            off = RT.facing_offset(rig, act)
            print(f"{name}: attempt {attempt + 1}, facing {off:+.1f} degrees off front")
            if abs(off) < 3.0 or attempt == 2:
                break
            fix += off
            rig.animation_data.action = None
            bpy.data.actions.remove(act)
        RT.relax_hands(rig, act)
        print(f"{name}: frames {a}-{b} of {a0}-{a1} -> {int(act.frame_range[1])} frames at 30 fps")
        bpy.data.objects.remove(src)
    rig.animation_data.action = None
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))


if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    main(only or None)
