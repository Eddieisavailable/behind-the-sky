# Behind the Sky (Godot)

The game, in Godot 4.7. PC (Windows) and Android first, iOS later.
The three.js prototype in the repo root stays as the reference for rules and layouts.

## Play

Open this folder in Godot 4.7 and press **F5** (or the ▶ button). You walk Gbelewala as Korto.

- **WASD / arrows** walk · **mouse** looks (click the game window first) · **wheel** zooms
- **E** talks to whoever is close · **Esc** pauses
- A gamepad works too; on a phone, the left thumb walks and the right side looks.

**Graphics** (Ultra, High, Medium, Low) is in the pause menu. High is the PC default. Ultra and High
turn on bounced light, soft sun shadows, haze and temporal anti-aliasing; Low is what phones will get.

To play as Flomo, select the **Main** node in `scenes/main.tscn` and set **Hero Key** to `flomo`.
To walk with the realistic Korto (in progress), set it to `korto_real`.

## Where things are

| Folder | What's there |
| --- | --- |
| `assets/models/` | The Blender models as `.glb`: characters, and kits of world pieces |
| `scenes/` | `main.tscn` (the game) and one scene per area |
| `scripts/rules/` | The game rules: spirit debt, cutlass combo, crawler life, forge rhythm, waves |
| `scripts/tuning.gd` | Every number worth tuning, in one place |
| `scripts/render/` | The look: lighting per time of day, quality presets, the look-dev stage |
| `scripts/world/` | Areas and the kit helpers they're built with |
| `scripts/hero/` | The hero and the follow camera |
| `scripts/ui/` | HUD, talk box, pause menu, touch controls |
| `tests/` | Headless tests |
| `tools/` | Import fixes for the Blender models, an inspector, a facing check, a screenshot tool |

Areas lay themselves out from code when the scene opens (in the editor too), so open
`scenes/areas/gbelewala.tscn` to look round the village. The layout isn't saved into the scene;
edit `scripts/world/areas/gbelewala.gd` instead and tick **Rebuild Now** in the Inspector.

## Look-dev

`scenes/lookdev.tscn` is where every realistic asset is judged before it goes into the game. Open it
and press **F6**. It has a mid-grey ball, a chrome ball, the standard 24-patch colour chart and height
poles at 1.60 m and 1.80 m. You can light it with the game's six times of day or a neutral studio light.
Set the asset in **Model Path** on the root node.

Keys: **1–7** lighting · **T** turntable · **F** face close-up · **B** full body · **N** next animation ·
**G** graphics quality · drag to orbit · right-drag to move up and down · wheel to zoom.

## Tests

```
godot --headless --path . --script res://tests/run_tests.gd    # the rules (50 checks)
godot --headless --path . --script res://tests/walk_test.gd    # walking the village (16 checks)
```

## Realistic characters

Built in Blender from `blender/realism/` with MPFB (MakeHuman for Blender, free CC0 output) and
motion capture from the CMU library, then judged in the look-dev stage. Their skeleton uses the
Unreal / MetaHuman bone names, so animation carries over if a character later becomes a MetaHuman.
`korto_real` is the first.

## Models

Every `.glb` runs through `tools/post_import.gd` on import: vertex colours on, glowing parts
unshaded, and clips set to loop except the one-shot moves. Re-export from Blender with
`BTS_MODELS_OUT=godot/assets/models/... ` (see `tools/build-models.sh` in the repo root).
