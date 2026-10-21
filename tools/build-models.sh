#!/usr/bin/env sh
# Rebuild every model from its Blender script, then shrink it for phones.
# Needs Blender's Python package (pip install bpy==5.1.2) or set BLENDER_PY to a Python that has it.
set -e
PY="${BLENDER_PY:-python3}"
for m in korto flomo hornbill crawler sii environment; do
  "$PY" blender/$m.py "$@"
  npx --yes @gltf-transform/cli@4 quantize public/models/$m.glb public/models/$m.glb
done
ls -la public/models
