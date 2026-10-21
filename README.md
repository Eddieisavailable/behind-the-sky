# Behind the Sky — gray-box prototype

An action game rooted in Kpelle folklore and the Woi epic. This repo is **phase 3**: a gray-box prototype that answers one question:

> Is *fight, spend spirit power, pay it back at the crossroads* fun on a cheap phone?

Third-person camera, plain shapes, no story, one arena. Characters, the world and every design will be made in Blender in phase 4 and loaded as glTF. Design docs: the story bible and the *Core Loop and Slice* doc.

## What's in it

| System | Where |
| --- | --- |
| Arena: clearing, crossroads, brazier, forge, vine clumps | `src/game/world.js` |
| Third-person camera: drag to look, drifts back behind the hero, stays out of the trees | `src/game/camera.js` |
| Hero: camera-relative joystick, cutlass three-hit combo, bow aimed where you look, roll | `src/game/hero.js`, `src/game/game.js` |
| Rattan crawlers that grow back after 4 s unless burned (countdown over each pile, **Burn it** button up close); one hides as a vine post from wave 2; 5 waves win the round | `src/game/crawlers.js`, `src/rules/crawlerLife.js` |
| Hornbill sight: slows time, shows hidden crawlers, adds 15 debt; at 100 the dark closes in | `src/rules/debt.js` |
| Paying at the crossroads with rice or iron; bond levels | `src/rules/debt.js`, `src/ui.js` |
| Rhythm forge: 30 seconds to Sii's slit-drum, better iron | `src/rules/rhythm.js`, `src/ui.js` |
| Graphics levels: Auto, High (computers: shadows, anti-aliasing, dense grass), Medium (phones), Low | `src/quality.js`, `src/config.js` |
| Frame-rate counter and automatic resolution drop | `src/main.js` |
| Playtest stats kept on the phone, copyable from the pause screen | `src/stats.js` |

Every tuning number is in `src/config.js`.

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
