// Headless play-through of the prototype: loads the built game in a phone-sized
// landscape viewport, drives each system, takes screenshots and checks for errors.
import { chromium } from 'playwright';
import fs from 'node:fs';

const URL = process.argv[2] ?? 'http://localhost:4173/';
const OUT = process.argv[3] ?? './shots';
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
const ctx = await browser.newContext({ viewport: { width: 844, height: 390 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
const page = await ctx.newPage();
const errors = [];
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errors.push(`${m.type()}: ${m.text()}`); });
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));

const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok, detail }); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`); };
const g = (fn, arg) => page.evaluate(fn, arg);
const wait = (ms) => page.waitForTimeout(ms);
const frames = (n) => g((k) => new Promise((r) => { let i = 0; const f = () => (++i >= k ? r() : requestAnimationFrame(f)); requestAnimationFrame(f); }), n);
const shot = (name) => page.screenshot({ path: `${OUT}/${name}.png` });

// Low graphics on the phone pass: software rendering in the test browser is slow, and these checks are about rules
await page.addInitScript(() => { try { localStorage.setItem('bts-quality', 'low'); } catch {} });
await page.goto(URL, { waitUntil: 'networkidle' });
await wait(800);
await shot('01-start');
check('start screen shows', await page.isVisible('#screen-start'));

await page.click('#btn-start');
await wait(3500);
await shot('02-wave1');
const w1 = await g(() => ({ phase: __bts.game.g.phase, wave: __bts.game.g.wave, n: __bts.game.g.crawlers.length }));
check('round starts and wave 1 spawns 3 crawlers', w1.phase === 'play' && w1.wave === 1 && w1.n === 3, JSON.stringify(w1));

// --- the pause button works with a finger (it was blocked by the touch layer) ---
const pauseBox = await page.locator('#btn-pause').boundingBox();
await page.touchscreen.tap(pauseBox.x + pauseBox.width / 2, pauseBox.y + pauseBox.height / 2);
await wait(300);
check('pause button responds to a tap', await page.isVisible('#screen-pause'));
await page.click('#btn-resume');
await wait(300);

// --- third-person look: drag on the right side turns the camera ---
const cdp = await ctx.newCDPSession(page);
const yaw0 = await g(() => __bts.game.rig.yaw);
await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 600, y: 250, id: 7 }] });
for (let i = 1; i <= 10; i++) {
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 600 + i * 15, y: 250, id: 7 }] });
  await wait(16);
}
await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
await wait(200);
const yaw1 = await g(() => __bts.game.rig.yaw);
check('dragging the right side turns the camera', Math.abs(yaw1 - yaw0) > 0.5, `yaw ${yaw0.toFixed(2)} -> ${yaw1.toFixed(2)}`);
await shot('02b-looked-around');

// --- W walks away from the camera, whichever way it faces ---
const walk = await g(async () => {
  const { g, rig } = __bts.game;
  rig.yaw = Math.PI / 2;          // camera to the east, looking west
  g.hero.pos.set(0, 0, 0);
  return true;
});
await page.keyboard.down('KeyW'); await wait(400); await frames(15); await page.keyboard.up('KeyW');
const walked = await g(() => ({ x: __bts.game.g.hero.pos.x, z: __bts.game.g.hero.pos.z }));
check('movement is relative to the camera', walked.x < -1 && Math.abs(walked.z) < 0.8, JSON.stringify(walked));

// --- cutlass: stand next to a crawler and swing until it goes down ---
await g(() => {
  const { g } = __bts.game;
  const c = g.crawlers[0];
  c.life.state = 'alive'; c.life.timer = 0;
  g.hero.pos.set(c.pos.x + 1.2, 0, c.pos.z);
  g.hero.health = 999; // keep the bot alive while it tests
});
for (let i = 0; i < 9; i++) { await page.keyboard.press('KeyJ'); await wait(140); }
const downed = await g(() => __bts.game.g.crawlers.map((c) => c.life.state));
check('cutlass combo puts a crawler down', downed.includes('downed') || downed.includes('regrowing'), downed.join(','));
await shot('03-downed');

// --- fire arrow burns the downed crawler ---
const fireRes = await g(async () => {
  const { g } = __bts.game;
  const c = g.crawlers.find((k) => k.life.state === 'downed' || k.life.state === 'regrowing');
  if (!c) return { ok: false, why: 'none downed' };
  c.life.state = 'downed'; c.life.timer = 0;
  g.hero.pos.set(c.pos.x, 0, c.pos.z + 5);
  g.hero.facing.set(0, -1);
  __bts.game.rig.yaw = 0;          // camera south, looking north at the pile
  g.hero.arrowKind = 'fire';
  return { ok: true, id: c.id, x: c.pos.x, z: c.pos.z };
});
await page.keyboard.down('KeyK'); await wait(450); await page.keyboard.up('KeyK');
await wait(600);
const afterFire = await g((id) => {
  const c = __bts.game.g.crawlers.find((k) => k.id === id);
  return { state: c ? c.life.state : 'removed', fire: __bts.game.g.hero.fireArrows };
}, fireRes.id);
check('fire arrow burns a downed crawler', afterFire.state === 'burned' || afterFire.state === 'removed', JSON.stringify(afterFire));
await g((p) => { __bts.game.g.hero.pos.set(p.x + 0.5, 0, p.z + 0.5); }, fireRes);  // walk over to the loot
await wait(1500);
const pack = await g(() => ({ ...__bts.game.g.pack }));
check('burned crawler drops rice that gets collected', pack.rice >= 1, JSON.stringify(pack));

// --- regrowth: a downed crawler left alone rises again ---
const regrew = await g(async () => {
  const { g } = __bts.game;
  const c = g.crawlers.find((k) => k.life.state === 'alive' || k.life.state === 'regrowing');
  if (!c) return 'none';
  g.hero.pos.set(c.pos.x + 9, 0, c.pos.z + 9);
  c.life.state = 'downed'; c.life.timer = 0;
  const t0 = performance.now();
  while (c.life.state !== 'alive' && performance.now() - t0 < 30000) await new Promise((r) => setTimeout(r, 250));
  return c.life.state;
});
check('a downed crawler grows back after ~4s', regrew === 'alive', regrew);

// --- Burn it button: knock one down, stand next to it, tap ---
const burnSetup = await g(() => {
  const { g } = __bts.game;
  const c = g.crawlers.find((k) => k.life.state !== 'burned' && k.life.state !== 'disguised');
  c.life.state = 'downed'; c.life.timer = 0; c.wasKnocked = true;
  g.hero.pos.set(c.pos.x + 1.5, 0, c.pos.z);
  g.hero.fireArrows = 3;
  return c.id;
});
await wait(400);
const burnLabel = await page.textContent('#btn-interact');
await shot('03b-burn-it');
const burnBox = await page.locator('#btn-interact').boundingBox();
await page.touchscreen.tap(burnBox.x + burnBox.width / 2, burnBox.y + burnBox.height / 2);
await wait(300);
const burned = await g((id) => { const c = __bts.game.g.crawlers.find((k) => k.id === id); return c ? c.life.state : 'removed'; }, burnSetup);
check('Burn it button appears by a downed crawler and burns it', /Burn it/.test(burnLabel) && (burned === 'burned' || burned === 'removed'), `${burnLabel} -> ${burned}`);
const label = await page.$$eval('.world-label.burn', (n) => n.length);

// --- Hornbill sight: debt, slow time, vignette ---
await page.keyboard.press('KeyF');
await wait(300);
const p1 = await g(() => ({ debt: __bts.game.g.genie.debt, active: __bts.game.g.genie.activeFor > 0, vig: getComputedStyle(document.getElementById('vignette')).opacity }));
await shot('04-hornbill-sight');
check('Hornbill sight adds 15 debt and starts', p1.debt === 15 && p1.active, JSON.stringify(p1));

// --- debt full: darkness ---
await g(() => { const gn = __bts.game.g.genie; gn.activeFor = 0; gn.cooldown = 0; gn.debt = 90; });
await page.keyboard.press('KeyF');
await wait(1500);
const dark = await g(() => ({ debt: __bts.game.g.genie.debt, dark: document.getElementById('darkness').style.opacity }));
await shot('05-turned-darkness');
check('debt reaching 100 turns the gift: darkness', dark.debt === 100 && dark.dark === '1', JSON.stringify(dark));

// --- crossroads: pay it back ---
await g(() => {
  const { g } = __bts.game;
  g.pack.rice = 6;
  g.hero.pos.set(g.world.crossroads.x + 2, 0, g.world.crossroads.z + 1.5);
});
await frames(6);
const interactShown = await page.isVisible('#btn-interact');
check('interact button appears at the crossroads', interactShown);
await page.keyboard.press('KeyE');
await frames(6);
check('crossroads menu opens', await page.isVisible('#screen-crossroads'));
await shot('06-crossroads');
await page.click('#btn-pay-rice');
await page.click('#btn-pay-rice');
const paid = await g(() => ({ debt: __bts.game.g.genie.debt, rice: __bts.game.g.pack.rice, clears: __bts.game.g.genie.clears }));
check('two rice offerings clear 100 debt', paid.debt === 0 && paid.rice === 0 && paid.clears === 1, JSON.stringify(paid));
await page.click('#btn-cr-close');
await wait(1500);
const light = await g(() => document.getElementById('darkness').style.opacity);
check('darkness lifts after paying', light === '0', light);

// --- forge: the rhythm mini-game ---
await g(() => {
  const { g } = __bts.game;
  g.pack.iron = 3;
  g.hero.pos.set(g.world.forge.x + 2.4, 0, g.world.forge.z + 1);
});
await wait(300);
await page.keyboard.press('KeyE');
await wait(300);
check('forge menu opens', await page.isVisible('#screen-forge'));
await page.click('#btn-forge-go');
await wait(2600);
await shot('07-forge-rhythm');
// strike on a rough 100 bpm beat; the bot is not a good drummer, that's fine
const strikeBox = await page.locator('#btn-strike').boundingBox();
const t0 = Date.now();
while (Date.now() - t0 < 26000) {
  await page.mouse.click(strikeBox.x + strikeBox.width / 2, strikeBox.y + strikeBox.height / 2);
  await wait(600);
}
await wait(3500);
const forged = await g(() => ({ result: document.getElementById('fg-result').textContent, runs: __bts.stats.session.forgeRuns ?? 0, level: __bts.game.g.forgeLevel, iron: __bts.game.g.pack.iron }));
await shot('08-forge-result');
check('forge run completes and is scored', forged.runs === 1 && forged.iron === 0 && /perfect/.test(forged.result), JSON.stringify(forged));
await page.click('#btn-forge-done');

// --- wave clears and the next one comes, with a disguised crawler ---
await g(async () => {
  const { g } = __bts.game;
  for (const c of g.crawlers) { c.life.state = 'burned'; }
  await new Promise((r) => setTimeout(r, 1200));
  g.breatherLeft = 0.2;
  await new Promise((r) => setTimeout(r, 1200));
});
const w2 = await g(() => ({ wave: __bts.game.g.wave, states: __bts.game.g.crawlers.map((c) => c.life.state) }));
check('wave 2 arrives with one disguised crawler', w2.wave === 2 && w2.states.filter((s) => s === 'disguised').length === 1, JSON.stringify(w2));
await wait(1500);
await shot('09-wave2');

// --- winning: clear wave 5 ---
const won = await g(async () => {
  const { g } = __bts.game;
  g.wave = 5;
  g.waveState = 'fighting';
  for (const c of g.crawlers) c.life.state = 'burned';
  await new Promise((r) => setTimeout(r, 600));
  return g.phase;
});
check('clearing wave 5 wins the round', won === 'won' && await page.isVisible('#screen-win'), won);
await shot('09b-win');
await page.click('#btn-win-again');
await wait(2500);

// --- performance: CPU throttled 4x, measure game logic time per frame ---
const client = await ctx.newCDPSession(page);
await client.send('Emulation.setCPUThrottlingRate', { rate: 4 });
const perf = await g(async () => {
  const game = __bts.game;
  const orig = game.update;
  const times = [];
  game.update = (dt) => { const t = performance.now(); orig(dt); times.push(performance.now() - t); };
  let frames = 0;
  const start = performance.now();
  await new Promise((resolve) => {
    const tick = () => { frames += 1; if (performance.now() - start < 8000) requestAnimationFrame(tick); else resolve(); };
    requestAnimationFrame(tick);
  });
  game.update = orig;
  times.sort((a, b) => a - b);
  return {
    fps: +(frames / 8).toFixed(1),
    updateMsMedian: +times[Math.floor(times.length / 2)].toFixed(2),
    updateMsP95: +times[Math.floor(times.length * 0.95)].toFixed(2),
    drawCalls: null,
  };
});
await client.send('Emulation.setCPUThrottlingRate', { rate: 1 });
const draw = await g(() => {
  // count draw calls for one frame
  const r = document.getElementById('scene');
  return null;
});
console.log('PERF', JSON.stringify(perf));
check('game logic stays under 4 ms per frame on a 4x slower CPU', perf.updateMsP95 < 4, JSON.stringify(perf));

// --- death screen ---
await g(() => { __bts.game.g.hero.health = 1; __bts.game.g.hero.invulnerable = 0; __bts.game.g.hero.dodgeLeft = 0; });
await g(async () => {
  const { g } = __bts.game;
  const c = g.crawlers.find((k) => k.life.state !== 'burned');
  c.life.state = 'alive';
  c.pos.set(g.hero.pos.x + 0.8, 0, g.hero.pos.z);
  c.attackCooldown = 0;
  await new Promise((r) => setTimeout(r, 2500));
});
check('death screen shows when health runs out', await page.isVisible('#screen-dead'));
await shot('10-dead');

// --- pause screen + stats ---
await page.click('#btn-again');
await wait(800);
await page.keyboard.press('KeyP');
await wait(300);
check('pause screen shows playtest stats', await page.isVisible('#screen-pause') && (await page.textContent('#stats')).includes('Average fps'));
await shot('11-pause');

const realErrors = errors.filter((e) => !/GPU stall|swiftshader|WebGL|GL_|Automatic fallback/i.test(e));
check('no console errors', realErrors.length === 0, realErrors.slice(0, 5).join(' | '));

// --- the second hero and the Hornbill ---
const pickedFlomo = await g(() => { const gm = __bts.game; gm.setHero('flomo'); gm.start(); const h = gm.g.hero; return { name: h.name, hp: h.maxHealth, speed: h.speed }; });
check('Flomo can be chosen: slower, tougher', pickedFlomo.name === 'Flomo' && pickedFlomo.hp > 100 && pickedFlomo.speed < 6.5, JSON.stringify(pickedFlomo));
const perched = await g(() => __bts.game.hornbill.state);
await g(() => { const gm = __bts.game; gm.g.waveState = 'breather'; gm.g.breatherLeft = 999; gm.g.genie.activeFor = 20; });
let birdState = perched;
for (let i = 0; i < 40 && birdState !== 'circling'; i++) { await frames(5); birdState = await g(() => __bts.game.hornbill.state); }
check('the Hornbill leaves its perch and circles while its sight is lent', perched === 'perched' && birdState === 'circling', `${perched} -> ${birdState}`);
await g(() => { __bts.game.setHero('korto'); });

// --- desktop: High graphics with real shadows ---
const desk = await browser.newContext({ viewport: { width: 1280, height: 720 } });
const dp = await desk.newPage();
dp.on('pageerror', (e) => errors.push(`pageerror(desktop): ${e.message}`));
await dp.goto(URL, { waitUntil: 'networkidle' });
await dp.click('#btn-start');
await dp.waitForTimeout(4500);
const q = await dp.evaluate(() => ({ key: __bts.quality.key, shadows: __bts.quality.shadows }));
await dp.screenshot({ path: `${OUT}/12-desktop-high.png` });
check('computers get High graphics with shadows by default', q.key === 'high' && q.shadows, JSON.stringify(q));
await dp.close();
const realErrors2 = errors.filter((e) => !/GPU stall|swiftshader|WebGL|GL_|Automatic fallback/i.test(e));
check('no errors on desktop either', realErrors2.length === realErrors.length, realErrors2.slice(realErrors.length).join(' | '));

await browser.close();
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
process.exit(failed.length ? 1 : 0);
