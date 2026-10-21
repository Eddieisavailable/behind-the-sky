# Behind the Sky — gray-box prototype

An action game rooted in Kpelle folklore and the Woi epic. This repo is **phase 3**: a gray-box prototype that answers one question:

> Is *fight, spend spirit power, pay it back at the crossroads* fun on a cheap phone?

Plain shapes, no story, one arena. Design docs: the story bible and the *Core Loop and Slice* doc.

## What's in it

| System | Where |
| --- | --- |
| Arena: clearing, crossroads, brazier, forge, vine clumps | `src/game/world.js` |
| Hero: joystick, cutlass three-hit combo, bow (hold and release), roll | `src/game/hero.js`, `src/game/game.js` |
| Rattan crawlers that grow back unless burned; one hides as a vine post from wave 2 | `src/game/crawlers.js`, `src/rules/crawlerLife.js` |
| Hornbill sight: slows time, shows hidden crawlers, adds 15 debt; at 100 the dark closes in | `src/rules/debt.js` |
| Paying at the crossroads with rice or iron; bond levels | `src/rules/debt.js`, `src/ui.js` |
| Rhythm forge: 30 seconds to Sii's slit-drum, better iron | `src/rules/rhythm.js`, `src/ui.js` |
| Frame-rate counter and automatic resolution drop | `src/main.js` |
| Playtest stats kept on the phone, copyable from the pause screen | `src/stats.js` |

Every tuning number is in `src/config.js`.

## Controls

**Phone (landscape):** left thumb anywhere = joystick · **Cut** · **Bow** (hold to aim, release) · **Roll** (or swipe on the right side) · **Sight** (the ring is your debt) · **Iron/Fire** switches arrows · **Pay / Use the forge** appears when you are close.

**Keyboard:** WASD move · J cut · K hold bow · Space roll · F sight · Q switch arrow · E pay/forge · P pause.

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
