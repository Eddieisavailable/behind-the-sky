import './style.css';
import { createRenderer } from './game/world.js';
import { createInput } from './game/input.js';
import { createGame } from './game/game.js';
import { createUi } from './ui.js';
import { createStats } from './stats.js';
import { unlockAudio } from './audio.js';
import { PERF } from './config.js';
import { resolveQuality } from './quality.js';
import { loadModels, loadModel } from './game/models.js';
import { createExplore } from './game/explore.js';

const $ = (id) => document.getElementById(id);

const quality = resolveQuality();
const stats = createStats();
const ui = createUi({ stats, quality });
const input = createInput({
  stickZone: $('stick-zone'), stickBase: $('stick-base'), stickKnob: $('stick-knob'), lookZone: $('look-zone'),
  btnAttack: $('btn-attack'), btnDodge: $('btn-dodge'), btnBow: $('btn-bow'), btnPower: $('btn-power'),
  btnArrow: $('btn-arrow'), btnInteract: $('btn-interact'),
  canvas: $('scene'), lockTarget: $('app'),
});
const canvas = $('scene');
const renderer = createRenderer(canvas, quality);
const models = await loadModels();
const game = createGame({ input, ui, stats, quality, models });
const explore = createExplore({ input, ui, quality, models });
let active = game;   // the clearing fight, or walking the world

// ---- sizing and adaptive resolution ----
const basePixelRatio = Math.min(window.devicePixelRatio, quality.maxPixelRatio);
let scale = 1;
function resize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  renderer.setPixelRatio(basePixelRatio * scale);
  renderer.setSize(w, h, false);
  game.setAspect(w, h);
  explore.setAspect(w, h);
  ui.checkOrientation();
}
window.addEventListener('resize', resize);
window.addEventListener('orientationchange', () => setTimeout(resize, 200));
resize();

// ---- start ----
function goFullscreen() {
  const root = document.documentElement;
  if (matchMedia('(pointer: coarse)').matches && root.requestFullscreen) {
    root.requestFullscreen({ navigationUI: 'hide' })
      .then(() => screen.orientation?.lock?.('landscape').catch(() => {}))
      .catch(() => {});
  }
}
async function startExplore() {
  unlockAudio();
  goFullscreen();
  active = explore;
  ui.setActive(explore);
  document.body.classList.add('explore');
  ui.enterPlay();
  explore.setHero(game.heroKey);
  input.lockPointer();
  await explore.start('gbelewala');
}
function start() {
  unlockAudio();
  const root = document.documentElement;
  if (matchMedia('(pointer: coarse)').matches && root.requestFullscreen) {
    root.requestFullscreen({ navigationUI: 'hide' })
      .then(() => screen.orientation?.lock?.('landscape').catch(() => {}))
      .catch(() => {});
  }
  ui.enterPlay();
  game.start();
  input.lockPointer(); // PC: capture the mouse for the camera (needs this click)
}
const startBtn = $('btn-start');
startBtn.disabled = false;
startBtn.textContent = 'Fight in the clearing';
const exploreBtn = $('btn-explore');
exploreBtn.disabled = false;
exploreBtn.addEventListener('click', startExplore);
ui.bind(game, {
  onStart: start,
  onPause: () => input.releasePointer(),
  onResume: () => input.lockPointer(),
});

// pause when the phone locks or the tab is hidden
document.addEventListener('visibilitychange', () => {
  if (document.hidden && active.g.phase === 'play') ui.pause();
  if (document.hidden) stats.save();
});

const lockHint = $('lock-hint');

// ---- loop ----
let last = performance.now();
let windowTime = 0;
let windowFrames = 0;
let goodWindows = 0;
function frame(now) {
  const rawDt = (now - last) / 1000;
  last = now;
  const dt = Math.min(rawDt, 0.05);

  active.update(dt);
  if (active.scene) renderer.render(active.scene, active.camera);
  ui.labels(active.labelAnchors(), active.camera, window.innerWidth, window.innerHeight);
  lockHint.classList.toggle('hidden', !(active.g.phase === 'play' && input.canLock() && !input.pointerLocked));

  // frame-rate meter and adaptive resolution (measured over 2-second windows)
  windowTime += rawDt;
  windowFrames += 1;
  if (windowTime >= 2) {
    const fps = windowFrames / windowTime;
    if (active.g.phase === 'play') stats.sampleFps(fps, windowTime);
    if (fps < PERF.lowFps && scale > quality.minScale) {
      scale = Math.max(quality.minScale, scale - (fps < PERF.veryLowFps ? 0.25 : 0.15));
      resize();
      goodWindows = 0;
    } else if (fps > 56 && scale < 1) {
      goodWindows += 1;
      if (goodWindows >= 3) { scale = Math.min(1, scale + 0.1); resize(); goodWindows = 0; }
    }
    ui.setFps(fps, renderer.getPixelRatio());
    windowTime = 0;
    windowFrames = 0;
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// ---- offline support (a failure here must never stop the game) ----
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  import('virtual:pwa-register')
    .then(({ registerSW }) => registerSW({ immediate: true }))
    .catch(() => {});
}

// handle for automated tests and for poking at tuning in the console
window.__bts = { game, explore, stats, input, quality, models, renderer, loadModel, get active() { return active; } };
