# Behind the Sky (Godot)

The game, in Godot 4.7. PC (Windows) and Android first, iOS later.
The three.js prototype in the repo root stays as the reference for rules and layouts.

## Play

Open this folder in Godot 4.7 and press **F5** (or the ▶ button). You walk Gbelewala as Korto.

- **WASD / arrows** walk · **mouse** looks (click the game window first) · **wheel** zooms
- **E** talks to whoever is close · **Esc** pauses
- A gamepad works too; on a phone, the left thumb walks and the right side looks.

To play as Flomo, select the **Main** node in `scenes/main.tscn` and set **Hero Key** to `flomo`.

## Where things are

| Folder | What's there |
| --- | --- |
| `assets/models/` | The Blender models as `.glb`: characters, and kits of world pieces |
| `scenes/` | `main.tscn` (the game) and one scene per area |
| `scripts/rules/` | The game rules: spirit debt, cutlass combo, crawler life, forge rhythm, waves |
| `scripts/tuning.gd` | Every number worth tuning, in one place |
| `scripts/world/` | Areas and the kit helpers they're built with |
| `scripts/hero/` | The hero and the follow camera |
| `scripts/ui/` | HUD, talk box, pause menu, touch controls |
| `tests/` | Headless tests |
| `tools/` | Import fixes for the Blender models, and an inspector |

Areas lay themselves out from code when the scene opens (in the editor too), so open
`scenes/areas/gbelewala.tscn` to look round the village. The layout isn't saved into the scene;
edit `scripts/world/areas/gbelewala.gd` instead and tick **Rebuild Now** in the Inspector.

## Tests

```
godot --headless --path . --script res://tests/run_tests.gd    # the rules (50 checks)
godot --headless --path . --script res://tests/walk_test.gd    # walking the village (16 checks)
```

## Models

Every `.glb` runs through `tools/post_import.gd` on import: vertex colours on, glowing parts
unshaded, and clips set to loop except the one-shot moves. Re-export from Blender with
`BTS_MODELS_OUT=godot/assets/models/... ` (see `tools/build-models.sh` in the repo root).
