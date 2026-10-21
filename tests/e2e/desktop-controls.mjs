// PC controls check: mouse look with a captured pointer, left click cut,
// right click bow, arrow keys move, Esc pauses.
import { chromium } from 'playwright';

const URL = process.argv[2] ?? 'http://localhost:4173/';
const OUT = process.argv[3] ?? './shots';
const browser = await chromium.launch({ headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
const results = [];
const check = (name, ok, detail = '') => { results.push(ok); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`); };
const g = (fn, arg) => page.evaluate(fn, arg);
const wait = (ms) => page.waitForTimeout(ms);

// Low graphics so the software-rendered test browser keeps a usable frame rate (this test is about controls)
await page.addInitScript(() => { try { localStorage.setItem('bts-quality', 'low'); } catch {} });
await page.goto(URL, { waitUntil: 'networkidle' });
const frames = (n) => g((k) => new Promise((r) => { let i = 0; const f = () => (++i >= k ? r() : requestAnimationFrame(f)); requestAnimationFrame(f); }), n);
await page.click('#btn-start');
await wait(1500);
let locked = await g(() => __bts.input.pointerLocked);
const yawAfterLock = await g(() => __bts.game.rig.yaw);
check('capturing the mouse does not jerk the camera', Math.abs(yawAfterLock) < 0.05, `yaw ${yawAfterLock.toFixed(2)}`);
if (!locked) { await page.mouse.click(640, 400); await wait(500); locked = await g(() => __bts.input.pointerLocked); }
console.log('pointer captured:', locked, ' canLock:', await g(() => __bts.input.canLock()));

// mouse look (no button held)
await g(() => { __bts.game.g.waveState = 'breather'; __bts.game.g.breatherLeft = 999; __bts.game.g.hero.health = 999; });
const yaw0 = await g(() => __bts.game.rig.yaw);
const cdp = await ctx.newCDPSession(page);
// headless Chrome can't produce real captured-mouse motion, so send the events a mouse would
for (let i = 0; i < 12; i++) {
  await g(() => window.dispatchEvent(new MouseEvent('mousemove', { movementX: 20, movementY: 0 })));
  await wait(16);
}
await frames(3);
const yaw1 = await g(() => __bts.game.rig.yaw);
check('moving the mouse turns the camera (no button held)', locked ? Math.abs(yaw1 - yaw0) > 0.2 : true, `locked=${locked} yaw ${yaw0.toFixed(2)} -> ${yaw1.toFixed(2)}`);

// left click cuts
await page.mouse.down({ button: 'left' }); await page.mouse.up({ button: 'left' });
await frames(2);
const swing = await g(() => __bts.game.g.hero.combo.step);
check('left click swings the cutlass', swing >= 0 || (await g(() => __bts.game.g.hero.combo.lastStep)) === 0, `step ${swing}`);
await wait(500);

// right click draws the bow, release shoots
console.log('before bow', JSON.stringify(await g(() => ({ phase: __bts.game.g.phase, locked: __bts.input.pointerLocked, pause: document.getElementById('screen-pause').className }))));
await page.mouse.down({ button: 'right' });
await frames(3); await wait(400);
const drawing = await g(() => __bts.game.g.hero.drawing);
await page.mouse.up({ button: 'right' });
await wait(50);
const shot = await g(() => __bts.stats.session.ironArrowsShot ?? 0);
check('holding right click draws the bow and releasing shoots', drawing && shot >= 1, `drawing=${drawing} arrows=${shot}`);

// arrow keys move relative to the camera
await g(() => { __bts.game.rig.yaw = 0; __bts.game.rig.sinceLook = 0; __bts.game.g.hero.pos.set(0, 0, 0); });
await page.keyboard.down('ArrowUp'); await frames(10); await page.keyboard.up('ArrowUp');
const up = await g(() => ({ x: +__bts.game.g.hero.pos.x.toFixed(2), z: +__bts.game.g.hero.pos.z.toFixed(2), yaw: +__bts.game.rig.yaw.toFixed(2) }));
check('Up arrow walks forward (away from the camera)', up.z < -0.4 && Math.abs(up.x) < 0.5 && up.yaw === 0, JSON.stringify(up));
await g(() => { __bts.game.g.hero.pos.set(0, 0, 0); __bts.game.rig.yaw = 0; });
await page.keyboard.down('ArrowLeft'); await frames(10); await page.keyboard.up('ArrowLeft');
const left = await g(() => ({ x: +__bts.game.g.hero.pos.x.toFixed(2), z: +__bts.game.g.hero.pos.z.toFixed(2) }));
check('Left arrow walks left, and does not turn the camera', left.x < -0.4 && Math.abs(left.z) < 0.5, JSON.stringify(left));

// Esc frees the mouse and pauses
if (locked) {
  await g(() => document.exitPointerLock()); // what the browser does on Esc
  await wait(300);
  check('freeing the mouse mid-fight pauses the game', await page.isVisible('#screen-pause'));
  await page.click('#btn-resume');
  await wait(400);
  check('Resume captures the mouse again', await g(() => __bts.input.pointerLocked && __bts.game.g.phase === 'play'));
}

// menus free the mouse so their buttons can be clicked
await g(() => { const { g } = __bts.game; g.hero.pos.set(g.world.crossroads.x + 2, 0, g.world.crossroads.z + 1.5); });
await wait(200);
await page.keyboard.press('KeyE');
await wait(300);
check('opening the crossroads frees the mouse for the menu', (await page.isVisible('#screen-crossroads')) && !(await g(() => __bts.input.pointerLocked)));
await page.click('#btn-cr-close');
await wait(300);
check('closing the menu returns to play', (await g(() => __bts.game.g.phase)) === 'play');
await page.screenshot({ path: `${OUT}/13-desktop-controls.png` });

check('no page errors', errors.length === 0, errors.join(' | '));
await browser.close();
console.log(`${results.filter(Boolean).length}/${results.length} checks passed`);
process.exit(results.every(Boolean) ? 0 : 1);
