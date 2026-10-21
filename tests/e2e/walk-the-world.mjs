// Walk the world: every area loads, the paths join them, people talk, and the bele tree can be climbed.
import { chromium } from 'playwright';
import fs from 'node:fs';
const URL = process.argv[2] ?? 'http://localhost:4173/';
const OUT = process.argv[3] ?? './shots';
fs.mkdirSync(OUT, { recursive: true });
const quality = process.env.Q ?? 'low';
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const ctx = await b.newContext({ viewport: { width: 1280, height: 720 } });
const p = await ctx.newPage();
const errors = [];
p.on('pageerror', (e) => errors.push(e.message));
p.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
const results = [];
const check = (name, ok, detail = '') => { results.push(ok); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`); };
const g = (fn, arg) => p.evaluate(fn, arg);
const frames = (n) => g((k) => new Promise((r) => { let i = 0; const f = () => (++i >= k ? r() : requestAnimationFrame(f)); requestAnimationFrame(f); }), n);
const shot = async (name) => {
  const url = await g(() => { const e = __bts.explore; __bts.renderer.render(e.scene, e.camera); return __bts.renderer.domElement.toDataURL('image/png'); });
  fs.writeFileSync(`${OUT}/${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
};
const waitArea = async (key) => {
  for (let i = 0; i < 120; i++) {
    const s = await g(() => ({ key: __bts.explore.g.areaKey, loading: __bts.explore.g.loading }));
    if (s.key === key && !s.loading) return true;
    await p.waitForTimeout(250);
  }
  return false;
};

await p.addInitScript((q) => { try { localStorage.setItem('bts-quality', q); } catch {} }, quality);
await p.goto(URL, { waitUntil: 'networkidle' });
await p.waitForFunction(() => !document.querySelector('#btn-explore').disabled);
await p.click('#btn-explore');
check('Walk the world starts in Gbelewala', await waitArea('gbelewala'));
check('the area title shows', (await p.textContent('#wave-title')) === 'Gbelewala');
await frames(10);
await shot('w-gbelewala');

// walk forward with the keyboard
const z0 = await g(() => __bts.explore.area.hero.pos.z);
await p.keyboard.down('KeyW'); await p.waitForTimeout(300); await frames(12); await p.keyboard.up('KeyW');
const z1 = await g(() => __bts.explore.area.hero.pos.z);
check('the hero walks', z1 < z0 - 0.3, `z ${z0.toFixed(2)} -> ${z1.toFixed(2)}`);

// talk to the Chief
await g(() => { const h = __bts.explore.area.hero; h.pos.set(-7.5, 0, 11.4); });
await frames(4);
const talkBtn = await p.textContent('#btn-interact');
await p.keyboard.press('KeyE'); await frames(4);
const toast = await p.textContent('#toast');
check('talking to the Chief', /Talk to the Chief/.test(talkBtn) && /seed rice is gone/.test(toast), `${talkBtn} | ${toast.slice(0, 50)}`);

// the path east leads to the rice farm
await g(() => { const h = __bts.explore.area.hero; h.pos.set(27.5, 0, 0); });
check('the farm road leads to the rice farm', await waitArea('rice_farm'));
await frames(10); await shot('w-rice-farm');

// every other area loads
for (const key of ['crossroads', 'deep_bush', 'river_rocks', 'swamp']) {
  await g((k) => __bts.explore.goTo(k), key);
  const ok = await waitArea(key);
  await frames(8);
  check(`${key.replace('_', ' ')} loads`, ok);
  await shot(`w-${key}`);
}

// climb the bele tree, vine by vine
const climb = await g(async () => {
  const e = __bts.explore;
  const a = e.area;
  const vines = a.vines;
  const press = () => window.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyE' }));
  const release = () => window.dispatchEvent(new KeyboardEvent('keyup', { code: 'KeyE' }));
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  a.hero.pos.set(vines[0].a.x, 0, vines[0].a.z);
  let steps = 0;
  for (let i = 0; i < vines.length; i++) {
    await wait(120);
    const label = document.getElementById('btn-interact').textContent;
    if (!/Climb up/.test(label)) return { steps, y: a.hero.pos.y, label };
    press(); await wait(60); release();
    for (let k = 0; k < 400 && !a.hero.climbing; k++) await wait(10);
    for (let k = 0; k < 2000 && a.hero.climbing; k++) await wait(20);
    steps++;
  }
  return { steps, y: a.hero.pos.y, top: Math.max(...a.surfaces.map((s) => s.top)) };
});
check('the bele tree can be climbed to the top platform', climb.steps === 12 && Math.abs(climb.y - climb.top) < 0.05, JSON.stringify(climb));
await frames(6); await shot('w-tree-top');
// step off the edge: fall to a lower branch or the water, not through the world
const fell = await g(async () => {
  const a = __bts.explore.area;
  const h = a.hero;
  const y0 = h.pos.y;
  h.pos.x += 7; h.pos.z += 7;
  await new Promise((r) => setTimeout(r, 2500));
  return { y0, y1: h.pos.y };
});
check('stepping off a branch falls to what is below', fell.y1 < fell.y0 && fell.y1 >= 0, JSON.stringify(fell));

// pause works in this mode
await p.keyboard.press('Escape'); await frames(3);
check('pause works while walking', await p.isVisible('#screen-pause'));
await p.click('#btn-resume'); await frames(3);

const real = errors.filter((e) => !/GPU stall|swiftshader|WebGL|GL_|Automatic fallback|pointer lock|Pointer Lock/i.test(e));
check('no errors', real.length === 0, real.join(' | '));
console.log(`${results.filter(Boolean).length}/${results.length} checks passed`);
await b.close();
process.exit(results.every(Boolean) ? 0 : 1);
