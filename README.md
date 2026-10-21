# Behind the Sky — gray-box prototype

An action game rooted in Kpelle folklore and the Woi epic.

> **Direction (October 2026):** the game ships as a **Godot 4** game for **PC (Windows) and Android first, iOS later**; the PWA is dropped
> (Godot can still export to the web later if that's ever wanted). Blender is used for the realism pass on characters and worlds,
> the cinematic scenes and the trailers; Godot for the gameplay build. Models move from Blender to Godot as glTF (`.glb`), the same
> format this prototype already uses. This repo stays as the playable prototype and reference: its rules (`src/rules/`),
> tuning (`src/config.js`), area layouts (`src/game/areas.js`) and Blender scripts are what the Godot build is ported from.

This repo is **phase 3**: a gray-box prototype that answers one question:

> Is *fight, spend spirit power, pay it back at the crossroads* fun on a cheap phone?

Third-person camera, no story yet, one clearing. Phase 4 is under way: both heroes (Korto and Flomo), the rattan crawler, Sii, the Hornbill Genie and the clearing's forest, village and story places are Blender models. Design docs: the story bible and the *Core Loop and Slice* doc.

## What's in it

| System | Where |
| --- | --- |
| Arena: clearing, crossroads, brazier, forge, vine clumps | `src/game/world.js` |
| Third-person camera: drag to look, drifts back behind the hero, stays out of the trees | `src/game/camera.js` |
| Hero: camera-relative joystick, cutlass three-hit combo, bow aimed where you look, roll | `src/game/hero.js`, `src/game/game.js` |
| Rattan crawlers that grow back after 4 s unless burned (countdown over each pile, **Burn it** button up close); one hides as a vine post from wave 2; 5 waves win the round | `src/game/crawlers.js`, `src/rules/crawlerLife.js` |
| Hornbill sight: slows time, shows hidden crawlers, adds 15 debt; at 100 the dark closes in. The Hornbill leaves its post at the crossroads and circles overhead while its sight is lent | `src/rules/debt.js`, `src/game/hornbill.js` |
| Choose Korto (quick) or Flomo (slower, 130 health, hits 30% harder) on the start screen | `src/config.js` (`HEROES`) |
| Paying at the crossroads with rice or iron; bond levels | `src/rules/debt.js`, `src/ui.js` |
| Rhythm forge: 30 seconds to Sii's slit-drum, better iron | `src/rules/rhythm.js`, `src/ui.js` |
| Graphics levels: Auto, High (computers: shadows, anti-aliasing, dense grass), Medium (phones), Low | `src/quality.js`, `src/config.js` |
| Frame-rate counter and automatic resolution drop | `src/main.js` |
| Playtest stats kept on the phone, copyable from the pause screen | `src/stats.js` |

Every tuning number is in `src/config.js`.

## Walk the world

From the start screen, **Walk the world** opens the slice's places as walkable areas, built from the Blender kits (`src/game/areas.js`, engine in `src/game/explore.js`):

| Area | Mood | What's there | Paths to |
| --- | --- | --- | --- |
| Gbelewala | morning | houses, palaver hut, the emptied seed-rice store, the father's forge, the Chief, villagers | the rice farm |
| The rice farm | day | upland rice, drying racks, farmers, the burning field brazier, rattan sign | Gbelewala, the crossroads |
| The crossroads | dusk | the offering stone, Gelengol singing, the Hornbill on its post | the rice farm, the deep bush, the river rocks |
| The deep bush | dim green | dense forest, the Iron-Stone and Driver-Ant genii in their glades | the crossroads, the swamp |
| The river rocks | afternoon | the river, the River Woman combing her hair | the crossroads, the swamp |
| The swamp | night | water, bats round the crown, the Rattan Bull, the lizard's lair, koong plants, and the bele tree | the river rocks, the deep bush |

The bele tree can be climbed: its 12 branch platforms are floors (`public/models/bele_tree.json`, written by `blender/bele_tree.py`), and each vine is climbed with **E** / the Climb button. Walk off a branch and you fall to what's below. People with something to say have a **Talk** button. No fighting in these areas yet.

## Models (Blender)

Every model is built by a Python script in `blender/`, so it can be rebuilt, tweaked and reviewed like code:

| Model | Script | Animations |
| --- | --- | --- |
| Korto | `blender/korto.py` | Idle, Run, Slash1-3, Roll, Draw, Burn, Hurt, Death |
| Flomo (Korto's older brother) | `blender/flomo.py` | Korto's ten, on a broader build |
| Rattan crawler | `blender/crawler.py` | Idle, Walk, Windup, Strike, Down, Rise |
| Sii the spider | `blender/sii.py` | Idle, Drum |
| Hornbill Genie | `blender/hornbill.py` | Perch, Call, Fly, Glide |
| Clearing and village (14 pieces) | `blender/environment.py` | static |
| Meni-maa-fa, lizard form (boss; six breakable back plates `Plate1`-`Plate6`) | `blender/meni_lizard.py` | Idle (agama push-ups), Crawl, Bite, Heal, Call, Hurt, Fall |
| Meni-maa-fa, true form | `blender/meni_true.py` | Idle, Run, Slash1-3, Block, Offer, Taunt, Hurt, Death, Flee |
| Rattan Bull (mini-boss) | `blender/rattan_bull.py` | Idle, Walk, Windup, Charge, Stunned, Collapse, Rebuild |
| Night bat | `blender/bat.py` | Fly, Dive, Fall |
| Iron-Stone Genie (`GiftStone` part) | `blender/genie_iron.py` | Idle, Walk, Smash, Grant |
| Driver-Ant Genie | `blender/genie_ant.py` | Idle, Walk, Grant, Swarm |
| Gelengol, with her stool and bowls (`Bowl` part) | `blender/gelengol.py` | Sit, Sing, Offer |
| The River Woman (`Comb` part) | `blender/river_woman.py` | Comb, Startled, Speak, Dive |
| Kelema-ninga, the firebird | `blender/kelema.py` | Idle, Fly, Land, Speak |
| The swamp (10 pieces, incl. the River Woman's rocks and the lizard's lair) | `blender/swamp.py` | static |
| The bele tree: `Trunk`, `Platform1-12`, `Vine1-11`, `CutBranch1-3`, `Canopy`, `RiceSack1-5` | `blender/bele_tree.py` | static |
| Gbelewala (15 pieces, incl. the emptied seed-rice store, the palaver hut and the storyteller's fire) | `blender/gbelewala.py` | static |
| The village cast: storyteller (`Whisk`, `Rattle`), Chief (`Staff`), blacksmith father (`Hammer`), woman with baby (`Pestle`), rice farmer (`Hoe`), elder (`Stick`), child | `blender/people.py` (one script, seven models) | everyone: Idle, Walk, Talk, Sit, Clap, Answer; plus Tell, Sing / Worry, Speak / Hammer / Pound / Hoe |

Everything from Meni-maa-fa down is built but not in play yet: the areas they belong to (Gbelewala, the crossroads, the river rocks, the deep bush, the swamp and the bele tree) come next. The game loads them with `loadModel(name)` when an area needs them; glowing parts use a material named `Glow`.

Style: stylized low-poly, flat-shaded vertex colours, one skinned mesh per character (one draw call on a phone), every part bound to one bone like a carved puppet. Preview renders are in `blender/previews/`.

```bash
pip install bpy==5.1.2 pillow             # Blender as a Python package (or use the Blender app's Scripting tab)
./tools/build-models.sh --preview          # rebuild all models, render previews, shrink the .glb files
```

To edit a model by hand, open the exported `public/models/*.glb` in Blender (File > Import > glTF), or run the script inside Blender and save the .blend.

## Controls

**Phone (landscape):** left thumb anywhere = joystick · drag the right side to look around · **Cut** · **Bow** (hold to aim where the camera looks, release) · **Roll** · **Sight** (the ring is your debt) · **Iron/Fire** switches arrows · **Burn it / Pay / Use the forge** appears when you are close.

**Computer (standard PC controls):** click the game once to capture the mouse, then move the mouse to look (Esc frees it and pauses) · **left click** cut · **hold right click** to aim the bow, release to shoot · **WASD or arrow keys** move (Up forward, Down back, Left, Right) · **Space or Shift** roll · **F** Hornbill sight · **Q or mouse wheel** switch arrows · **E** burn / pay / forge · **P** pause. If a browser refuses to capture the mouse, hold right click and drag to look.

## Run it

```bash
npm install
npm run dev        # http://localhost:5173, also on your Wi-Fi so a phone can open it
npm test           # rule tests (debt, combo, regrowth, rhythm, waves)
npm run build      # production build in dist/ (about 610 KB, works offline once loaded)
npm run preview
```

Deploy: import the repo in Vercel (framework preset: Vite). The build is static.

## Playtest checklist (phase 3 pass/fail)

1. Hand a first-time player the phone with no explanation beyond the start screen.
2. After 10 minutes, ask: *want another round?*
3. Pause → **Copy playtest stats** → send them over. Average fps should be 30 or more.

## Known gaps (on purpose)

- One genie (Hornbill), Korto only, no story. Flomo, Iron-Stone and Driver-Ant come in phase 4.
- No real models: Blender assets come in phase 4.
- Performance was measured in a headless browser with software rendering, so real-phone numbers are still needed.
