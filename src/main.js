import './style.css';
import { createRenderer } from './game/world.js';
import { createInput } from './game/input.js';
import { createGame } from './game/game.js';
import { createUi } from './ui.js';
import { createStats } from './stats.js';
import { unlockAudio } from './audio.js';
import { PERF } from './config.js';

const $ = (id) => document.getElementById(id);

const stats = createStats();
const ui = createUi({ stats });
const input = createInput({
  stickZone: $('stick-zone'), stickBase: $('stick-base'), stickKnob: $('stick-knob'), swipeZone: $('swipe-zone'),
  btnAttack: $('btn-attack'), btnDodge: $('btn-dodge'), btnBow: $('btn-bow'), btnPower: $('btn-power'),
  btnArrow: $('btn-arrow'), btnInteract: $('btn-interact'),
});
const canvas = $('scene');
const renderer = createRenderer(canvas);
const game = createGame({ input, ui, stats });

// ---- sizing and adaptive resolution ----
const basePixelRatio = Math.min(window.devicePixelRatio, PERF.maxPixelRatio);
let scale = 1;
function resize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  renderer.setPixelRatio(basePixelRatio * scale);
  renderer.setSize(w, h, false);
  game.setAspect(w, h);
  ui.checkOrientation();
}
window.addEventListener('resize', resize);
window.addEventListener('orientationchange', () => setTimeout(resize, 200));
resize();

// ---- start ----
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
}
ui.bind(game, { onStart: start });

// pause when the phone locks or the tab is hidden
document.addEventListener('visibilitychange', () => {
  if (document.hidden && game.g.phase === 'play') ui.pause();
  if (document.hidden) stats.save();
});

// ---- loop ----
let last = performance.now();
let windowTime = 0;
let windowFrames = 0;
let goodWindows = 0;
function frame(now) {
  const rawDt = (now - last) / 1000;
  last = now;
  const dt = Math.min(rawDt, 0.05);

  game.update(dt);
  renderer.render(game.scene, game.camera);
  ui.labels(game.labelAnchors(), game.camera, window.innerWidth, window.innerHeight);

  // frame-rate meter and adaptive resolution (measured over 2-second windows)
  windowTime += rawDt;
  windowFrames += 1;
  if (windowTime >= 2) {
    const fps = windowFrames / windowTime;
    if (game.g.phase === 'play') stats.sampleFps(fps, windowTime);
    if (fps < PERF.lowFps && scale > 0.6) {
      scale = Math.max(0.6, scale - (fps < PERF.veryLowFps ? 0.25 : 0.15));
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
window.__bts = { game, stats, input };
