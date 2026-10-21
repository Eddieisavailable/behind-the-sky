#!/usr/bin/env sh
# Rebuild every model from its Blender script, then shrink it for phones.
# Needs Blender's Python package (pip install bpy==5.1.2) or set BLENDER_PY to a Python that has it.
set -e
PY="${BLENDER_PY:-python3}"
shrink() { npx --yes @gltf-transform/cli@4 quantize public/models/$1.glb public/models/$1.glb; }

# one script, one model
for m in korto flomo hornbill crawler sii environment meni_lizard meni_true rattan_bull bat \
         genie_iron genie_ant gelengol river_woman kelema swamp bele_tree gbelewala; do
  "$PY" blender/$m.py "$@"
  shrink $m
done

# blender/people.py makes the whole village cast
"$PY" blender/people.py "$@"
for m in storyteller chief blacksmith villager_woman villager_man elder child; do
  shrink $m
done
ls -la public/models
