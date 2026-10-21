// Everything on the DOM side: HUD, toasts, the crossroads and forge menus,
// the rhythm mini-game, pause and death screens, and world labels.

import * as THREE from 'three';
import { FORGE, OFFERING } from './config.js';
import { buildPattern, createJudge, strike, sweep, isDone, score, levelsEarned } from './rules/rhythm.js';
import { unlockAudio, audioNow, audioLatency, sfx } from './audio.js';
import { saveChoice } from './quality.js';

const $ = (id) => document.getElementById(id);
const RING = 2 * Math.PI * 44;

export function createUi({ stats, quality }) {
  const el = {
    hud: $('hud'), controls: $('controls'),
    healthFill: $('health-fill'), healthText: $('health-text'),
    rice: $('rice'), iron: $('iron'), forgeLevel: $('forge-level'), bond: $('bond'),
    waveTitle: $('wave-title'), waveSub: $('wave-sub'),
    debtRing: $('debt-ring'), debtText: $('debt-text'), btnPower: $('btn-power'),
    btnArrow: $('btn-arrow'), arrowKind: $('arrow-kind'), arrowCount: $('arrow-count'),
    btnInteract: $('btn-interact'),
    toast: $('toast'), fps: $('fps'),
    vignette: $('vignette'), darkness: $('darkness'), hurt: $('hurt'),
    labels: $('labels'),
    start: $('screen-start'), pause: $('screen-pause'), dead: $('screen-dead'), win: $('screen-win'),
    crossroads: $('screen-crossroads'), forge: $('screen-forge'), rotate: $('screen-rotate'),
  };
  el.debtRing.style.strokeDasharray = `${RING}`;
  el.debtRing.style.strokeDashoffset = `${RING}`;

  let game = null;
  let toastTimer = 0;
  let last = {};
  let showFps = true;
  let renderScale = 1;

  // ---------- HUD ----------
  function hud(s) {
    const set = (k, v, fn) => { if (last[k] !== v) { last[k] = v; fn(v); } };
    set('health', Math.ceil(s.health), (v) => {
      el.healthFill.style.width = `${(v / s.maxHealth) * 100}%`;
      el.healthText.textContent = `${v}`;
    });
    set('rice', s.rice, (v) => { el.rice.textContent = v; });
    set('iron', s.iron, (v) => { el.iron.textContent = v; });
    set('forgeLevel', s.forgeLevel, (v) => { el.forgeLevel.textContent = v; });
    set('bond', s.bond, (v) => { el.bond.textContent = v; });
    set('debt', s.debt, (v) => {
      el.debtRing.style.strokeDashoffset = `${RING * (1 - v / s.maxDebt)}`;
      el.debtRing.style.stroke = v >= s.maxDebt ? 'var(--danger)' : v >= 70 ? '#f08a3d' : 'var(--debt)';
      el.debtText.textContent = `${v} owed`;
    });
    set('power', `${s.powerActive}|${s.powerReady}|${s.turned}`, () => {
      el.btnPower.classList.toggle('active', s.powerActive);
      el.btnPower.classList.toggle('disabled', !s.powerReady && !s.powerActive);
    });
    set('arrow', `${s.arrowKind}|${s.fireArrows}`, () => {
      el.arrowKind.textContent = s.arrowKind === 'fire' ? 'Fire' : 'Iron';
      el.arrowCount.textContent = s.arrowKind === 'fire' ? `${s.fireArrows} left` : '∞';
      el.btnArrow.classList.toggle('fire', s.arrowKind === 'fire');
    });
    const waveLine = s.waveState === 'breather'
      ? (s.wave === 0 ? 'Get ready' : `Next wave in ${Math.ceil(Math.max(0, s.breatherLeft))}`)
      : `${s.remaining} crawler${s.remaining === 1 ? '' : 's'} left${s.downed ? ` · ${s.downed} down: burn ${s.downed === 1 ? 'it' : 'them'}` : ''}`;
    set('waveTitle', s.wave === 0 ? 'The clearing' : `Wave ${s.wave} of ${s.totalWaves}`, (v) => { el.waveTitle.textContent = v; });
    set('waveSub', waveLine, (v) => { el.waveSub.textContent = v; });
    const interact = s.nearby === 'burn' ? (s.fireLeft > 0 ? `Burn it (${s.fireLeft} fire)` : 'No fire: go to the brazier') : s.nearby === 'crossroads' ? (s.owes ? `Pay the Hornbill (${s.debt})` : 'Crossroads') : s.nearby === 'forge' ? 'Use the forge' : null;
    set('interact', interact, (v) => {
      el.btnInteract.classList.toggle('hidden', !v);
      if (v) el.btnInteract.textContent = v;
    });
  }

  function toast(text, ms = 2000) {
    el.toast.textContent = text;
    el.toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.toast.classList.remove('show'), ms);
  }

  const setVignette = (on) => { el.vignette.style.opacity = on ? '1' : '0'; };
  const setDarkness = (v) => {
    if (last.dark === v) return;
    last.dark = v;
    el.darkness.style.opacity = `${v}`;
  };
  function hurt() {
    el.hurt.style.opacity = '1';
    setTimeout(() => { el.hurt.style.opacity = '0'; }, 120);
    if (navigator.vibrate) navigator.vibrate(40);
  }

  function setFps(fps, scale) {
    renderScale = scale;
    if (!showFps) return;
    el.fps.textContent = `${Math.round(fps)} fps · ${scale.toFixed(2)}x`;
  }

  // ---------- screens ----------
  const show = (screen) => screen.classList.remove('hidden');
  const hide = (screen) => screen.classList.add('hidden');

  function pause() {
    game.pauseGame();
    fillStats();
    show(el.pause);
  }

  function fillStats() {
    const s = stats.session;
    const f = stats.fpsSummary();
    const rows = [
      ['Minutes played', ((s.playSeconds ?? 0) / 60).toFixed(1)],
      ['Rounds', s.rounds ?? 0],
      ['Best wave', s.bestWave ?? 0],
      ['Crawlers burned', s.burned ?? 0],
      ['Sight used', s.powerUses ?? 0],
      ['Offerings paid', s.offerings ?? 0],
      ['Times turned', s.turned ?? 0],
      ['Forge best', `${s.forgeBestScore ?? 0}%`],
      ['Average fps', f.avg],
      ['Seconds under 30 fps', f.lowSeconds],
    ];
    $('stats').innerHTML = rows.map(([k, v]) => `<div><span>${k}</span><b>${v}</b></div>`).join('');
  }

  const clock = (sec) => `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, '0')}`;
  function win({ seconds, burned, debt, forge }) {
    $('win-summary').textContent = `You burned ${burned} crawlers in ${clock(seconds)}`
      + `${debt > 0 ? `, but you still owe the Hornbill ${debt}` : ' and owe the Hornbill nothing'}. Forge level ${forge}.`;
    setVignette(false);
    show(el.win);
  }

  function dead({ wave, seconds, burned }) {
    $('dead-summary').textContent = `You reached wave ${wave} and burned ${burned} crawler${burned === 1 ? '' : 's'} in ${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}.`;
    setVignette(false);
    show(el.dead);
  }

  // ---------- crossroads ----------
  function openCrossroads() {
    fillCrossroads();
    $('cr-note').textContent = '';
    show(el.crossroads);
  }
  function fillCrossroads() {
    const { genie, pack } = game.g;
    $('cr-debt').textContent = genie.debt;
    $('btn-pay-rice').textContent = `Offer ${OFFERING.riceCost} rice (have ${pack.rice})`;
    $('btn-pay-iron').textContent = `Offer ${OFFERING.ironCost} iron (have ${pack.iron})`;
    $('btn-pay-rice').disabled = genie.debt <= 0 || pack.rice < OFFERING.riceCost;
    $('btn-pay-iron').disabled = genie.debt <= 0 || pack.iron < OFFERING.ironCost;
    if (genie.debt <= 0) $('cr-note').textContent = 'You owe the Hornbill nothing. Walk on.';
  }
  function pay(kind) {
    const r = game.payOffering(kind);
    if (r.ok) {
      $('cr-note').textContent = r.bondUp
        ? `Paid ${r.cleared}. The Hornbill's bond deepens.`
        : `Paid ${r.cleared}. ${game.g.genie.debt > 0 ? `Still owed: ${game.g.genie.debt}.` : 'The debt is clear.'}`;
    }
    fillCrossroads();
  }
  function closeMenu(screen) {
    hide(screen);
    game.resume();
  }

  // ---------- forge ----------
  let forgeRun = null;

  function openForge() {
    const { forgeLevel, pack } = game.g;
    $('fg-level').textContent = forgeLevel;
    $('forge-title').textContent = 'Forge better iron';
    show($('forge-intro'));
    hide($('forge-play'));
    hide($('forge-result'));
    const go = $('btn-forge-go');
    go.disabled = pack.iron < FORGE.ironCost || forgeLevel >= FORGE.maxLevel;
    $('fg-note').textContent = forgeLevel >= FORGE.maxLevel
      ? 'Your iron is already the best Kpayang-Miling can make.'
      : pack.iron < FORGE.ironCost ? `You need ${FORGE.ironCost} iron scrap (you have ${pack.iron}). Burned crawlers drop it.` : '';
    show(el.forge);
  }

  function startForgeRun() {
    const paid = game.spendForgeIron();
    if (!paid.ok) return;
    unlockAudio();
    hide($('forge-intro'));
    show($('forge-play'));
    $('forge-title').textContent = 'Strike on the beat';
    const notes = buildPattern({ seed: 7 + game.g.forgeLevel });
    const judge = createJudge(notes);
    const notesEl = $('notes');
    notesEl.innerHTML = '';
    const dots = judge.notes.map((n) => {
      const d = document.createElement('div');
      d.className = `note-dot ${n.drum}`;
      notesEl.appendChild(d);
      return d;
    });
    const t0 = audioNow() + 0.15;
    for (const n of notes) sfx.drum(n.drum, t0 + n.t);
    forgeRun = { judge, dots, t0, notes, raf: 0 };
    const lane = $('lane');
    const hitX = 38;
    const judgeEl = $('fg-judge');
    const streakEl = $('fg-streak');
    const timeEl = $('fg-time');
    const end = notes.at(-1).t + 0.6;

    const songTime = () => audioNow() - t0 - audioLatency();
    const frame = () => {
      if (!forgeRun) return;
      const now = songTime();
      const pxPerSec = (lane.clientWidth - hitX) / 2;
      for (const n of sweep(judge, now)) {
        dots[judge.notes.indexOf(n)].classList.add('miss');
        judgeEl.textContent = 'Miss';
        judgeEl.className = 'miss';
      }
      judge.notes.forEach((n, i) => {
        const x = hitX + (n.t - now) * pxPerSec;
        const d = dots[i];
        if (x < -40 || x > lane.clientWidth + 40) { d.style.display = 'none'; return; }
        d.style.display = '';
        d.style.left = `${x}px`;
      });
      streakEl.textContent = judge.streak > 2 ? `${judge.streak} in a row` : '';
      timeEl.textContent = `${Math.max(0, Math.ceil(end - now))}s`;
      if (isDone(judge) && now > end) finishForge();
      else forgeRun.raf = requestAnimationFrame(frame);
    };
    forgeRun.strike = () => {
      const now = songTime();
      const r = strike(judge, now);
      if (r) {
        const i = judge.next - 1;
        dots[i].classList.add(r);
        judgeEl.textContent = r === 'perfect' ? 'Perfect' : 'Good';
        judgeEl.className = r;
        sfx.strike(r);
      }
    };
    forgeRun.raf = requestAnimationFrame(frame);
  }

  function finishForge() {
    if (!forgeRun) return;
    cancelAnimationFrame(forgeRun.raf);
    const s = score(forgeRun.judge);
    const levels = levelsEarned(s);
    const gained = game.applyForge(levels, s);
    const j = forgeRun.judge;
    forgeRun = null;
    hide($('forge-play'));
    show($('forge-result'));
    $('forge-title').textContent = gained ? 'Good iron' : 'Brittle iron';
    $('fg-result').textContent = `${j.perfect} perfect, ${j.good} good, ${j.miss} missed: ${Math.round(s * 100)}%. `
      + (gained ? `Forge level ${game.g.forgeLevel}: your cutlass and iron arrows hit ${Math.round(game.g.forgeLevel * FORGE.damagePerLevel * 100)}% harder.`
        : `Below ${Math.round(FORGE.upgradeAt * 100)}%, the iron cracks. Sii laughs and asks for food.`);
  }

  const strikeBtn = $('btn-strike');
  strikeBtn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    strikeBtn.classList.add('pressed');
    forgeRun?.strike();
  });
  const unpress = () => strikeBtn.classList.remove('pressed');
  strikeBtn.addEventListener('pointerup', unpress);
  strikeBtn.addEventListener('pointercancel', unpress);
  window.addEventListener('keydown', (e) => {
    if (forgeRun && !e.repeat && (e.code === 'Space' || e.code === 'KeyJ' || e.code === 'Enter')) {
      e.preventDefault();
      forgeRun.strike();
    }
  });

  // ---------- labels over places ----------
  const labelEls = new Map();
  const v = new THREE.Vector3();
  function labels(anchors, camera, w, h) {
    const seen = new Set();
    for (const a of anchors) {
      seen.add(a.key);
      let node = labelEls.get(a.key);
      if (!node) {
        node = document.createElement('div');
        node.className = `world-label${a.cls ? ` ${a.cls}` : ''}`;
        el.labels.appendChild(node);
        labelEls.set(a.key, node);
      }
      if (node.textContent !== a.text) node.textContent = a.text;
      v.set(a.x, a.y, a.z).project(camera);
      const onScreen = v.z < 1 && Math.abs(v.x) < 1.1 && Math.abs(v.y) < 1.1;
      node.style.display = onScreen ? '' : 'none';
      if (onScreen) node.style.transform = `translate(${(v.x * 0.5 + 0.5) * w}px, ${(-v.y * 0.5 + 0.5) * h}px) translate(-50%, -100%)`;
    }
    for (const [key, node] of labelEls) {
      if (!seen.has(key)) { node.remove(); labelEls.delete(key); }
    }
  }

  // ---------- wiring ----------
  function bind(g, { onStart }) {
    game = g;
    $('btn-start').addEventListener('click', onStart);
    $('btn-resume').addEventListener('click', () => { hide(el.pause); game.resume(); });
    $('btn-pause').addEventListener('click', () => pause());
    $('btn-again').addEventListener('click', () => { hide(el.dead); onStart(); });
    $('btn-win-again').addEventListener('click', () => { hide(el.win); onStart(); });
    const q = $('opt-quality');
    q.value = quality.choice;
    $('quality-note').textContent = quality.choice === 'auto' ? `now ${quality.label}` : '';
    q.addEventListener('change', () => {
      saveChoice(q.value);
      $('quality-note').textContent = 'Restarting with the new setting…';
      setTimeout(() => location.reload(), 400);
    });
    $('btn-pay-rice').addEventListener('click', () => pay('rice'));
    $('btn-pay-iron').addEventListener('click', () => pay('iron'));
    $('btn-cr-close').addEventListener('click', () => closeMenu(el.crossroads));
    $('btn-forge-go').addEventListener('click', startForgeRun);
    $('btn-forge-close').addEventListener('click', () => closeMenu(el.forge));
    $('btn-forge-done').addEventListener('click', () => closeMenu(el.forge));
    $('opt-fps').addEventListener('change', (e) => {
      showFps = e.target.checked;
      el.fps.classList.toggle('hidden', !showFps);
    });
    $('btn-copy').addEventListener('click', async () => {
      const text = stats.report({ renderScale: renderScale.toFixed(2), quality: quality.key });
      try {
        await navigator.clipboard.writeText(text);
        toast('Stats copied. Paste them into WhatsApp or an email.', 2600);
      } catch {
        // clipboard refused (some in-app browsers): show the text so it can be selected by hand
        const box = document.createElement('textarea');
        box.readOnly = true;
        box.value = text;
        box.style.cssText = 'width:100%;height:9em;grid-column:1/-1;background:#0c120e;color:inherit;border:1px solid var(--line);border-radius:8px;padding:8px;font:12px ui-monospace,monospace';
        $('stats').appendChild(box);
        box.focus();
        box.select();
        toast('Select the text and copy it.', 2600);
      }
    });
  }

  function enterPlay() {
    hide(el.start);
    show(el.hud);
    show(el.controls);
  }

  function checkOrientation() {
    const touch = matchMedia('(pointer: coarse)').matches;
    el.rotate.classList.toggle('hidden', !(touch && innerHeight > innerWidth));
  }

  return { hud, toast, setVignette, setDarkness, hurt, setFps, pause, dead, win, openCrossroads, openForge, labels, bind, enterPlay, checkOrientation };
}
