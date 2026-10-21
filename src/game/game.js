// The game loop: hero, crawlers, arrows, the Hornbill's debt, waves.
// The DOM side (HUD, menus, the forge mini-game) lives in ui.js and talks to
// this file through the `ui` object passed in.

import * as THREE from 'three';
import { ARENA, HERO, HEROES, CUTLASS, BOW, DROPS, HORNBILL, FORGE, WAVES, WAVES_PER_ROUND, CAMERA } from '../config.js';
import { createWorld, resolveCollisions, castShadows } from './world.js';
import { dressWorld } from './environment.js';
import { createHornbill } from './hornbill.js';
import { createCameraRig, updateRig, look, stickToWorld, cameraBasis } from './camera.js';
import { createHero, poseHero, faceToward } from './hero.js';
import { createCrawler, updateCrawler, removeCrawler } from './crawlers.js';
import { createArrows, createPickups } from './projectiles.js';
import { createFx } from './fx.js';
import * as debt from '../rules/debt.js';
import * as combo from '../rules/combo.js';
import { hitIron, hitFire, isGone } from '../rules/crawlerLife.js';
import { waveSize, crawlerSpeed } from '../rules/waves.js';
import { sfx } from '../audio.js';

const BURN_RANGE = 2.6;

export function createGame({ input, ui, stats, quality, models = null }) {
  const world = createWorld(quality);
  const { scene } = world;
  const camera = new THREE.PerspectiveCamera(CAMERA.fov, 1, 0.2, 150);
  const rig = createCameraRig(camera);
  const fx = createFx(scene);
  const arrows = createArrows(scene);
  const decor = dressWorld(world, models, quality);
  const pickups = createPickups(scene, decor.pickupTemplates);
  const hornbill = createHornbill(world, models, quality);
  let heroKey = 'korto';

  const g = {
    scene, camera, world, fx,
    phase: 'title',            // title | play | menu | paused | dead | won
    hero: null,
    crawlers: [],
    pack: { rice: 0, iron: 0 },
    forgeLevel: 0,
    genie: debt.createGenie(),
    wave: 0,
    waveState: 'fighting',     // fighting | breather
    breatherLeft: 0,
    roundTime: 0,
    hints: new Set(),
    nearby: null,              // 'burn' | 'crossroads' | 'forge' | null
    burnTarget: null,
  };

  function reset() {
    if (g.hero) scene.remove(g.hero.group, g.hero.aim);
    for (const c of g.crawlers) removeCrawler(scene, c);
    arrows.clear();
    pickups.clear();
    g.hero = createHero(scene, models, quality, HEROES[heroKey] ?? HEROES.korto);
    useRealShadows(g.hero.group);
    g.crawlers = [];
    g.pack = { rice: 0, iron: 0 };
    g.forgeLevel = 0;
    g.genie = debt.createGenie();
    g.wave = 0;
    g.roundTime = 0;
    g.roundBurned = 0;
    g.waveState = 'breather';
    g.breatherLeft = 2;        // a moment to look around before wave 1
    combo.cancel(g.hero.combo);
    rig.yaw = 0;
    rig.pitch = CAMERA.pitch;
    updateRig(rig, 0, g.hero, { snap: true });
    ui.setDarkness(0);
    ui.setVignette(false);
    pushHud();
  }

  // ---------- helpers ----------
  function useRealShadows(group) {
    if (!quality.shadows) return;
    castShadows(group);
    group.traverse((o) => { if (o.userData.blob) o.visible = false; });
  }

  const mult = () => 1 + g.forgeLevel * FORGE.damagePerLevel;
  const dist2d = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);

  function hint(key, text) {
    if (g.hints.has(key)) return;
    g.hints.add(key);
    ui.toast(text, 3200);
  }

  function nearestCrawler(maxRange, filter) {
    let best = null;
    let bd = maxRange;
    for (const c of g.crawlers) {
      if (!filter(c)) continue;
      const d = dist2d(c.pos, g.hero.pos);
      if (d < bd) { bd = d; best = c; }
    }
    return best;
  }

  function dropLoot(c) {
    pickups.drop(c.pos.x, c.pos.z, 'rice');
    if (Math.random() < DROPS.extraRiceChance) pickups.drop(c.pos.x, c.pos.z, 'rice');
    if (Math.random() < DROPS.ironChance) pickups.drop(c.pos.x, c.pos.z, 'iron');
  }

  function onBurned(c) {
    fx.burst(c.pos.x, 1, c.pos.z, 'fire', 18, 5);
    fx.burst(c.pos.x, 0.6, c.pos.z, 'ash', 10, 2);
    sfx.burn();
    dropLoot(c);
    stats.add('burned', 1);
    g.roundBurned += 1;
  }

  function afterHit(c, state, before) {
    if (state === 'burned' && before !== 'burned') onBurned(c);
    else if (state === 'downed' && before !== 'downed') {
      c.wasKnocked = true;
      hint('downed', 'Down, but it will grow back in 4 seconds. Stand by it and tap Burn it.');
    }
  }

  // ---------- waves ----------
  function startWave() {
    g.wave += 1;
    g.waveState = 'fighting';
    const size = waveSize(g.wave);
    const speed = crawlerSpeed(g.wave);
    const spots = [...world.vines].sort(() => Math.random() - 0.5);
    const far = spots.filter((s) => Math.hypot(s.x - g.hero.pos.x, s.z - g.hero.pos.z) > 9);
    const use = far.length ? far : spots;
    for (let i = 0; i < size.regular; i++) {
      const s = use[i % use.length];
      const c = createCrawler(scene, s.x + (Math.random() - 0.5) * 2, s.z + (Math.random() - 0.5) * 2, { speed, models, quality });
      c.life.state = 'regrowing';   // rises out of the vines
      c.life.timer = 0;
      useRealShadows(c.group);
      g.crawlers.push(c);
    }
    for (let i = 0; i < size.disguised; i++) {
      // a vine post standing somewhere in the clearing
      for (let tries = 0; tries < 30; tries++) {
        const a = Math.random() * Math.PI * 2;
        const d = 8 + Math.random() * 12;
        const x = Math.cos(a) * d;
        const z = Math.sin(a) * d;
        const clear = [ARENA.crossroads, ARENA.forge, ARENA.brazier].every((p) => Math.hypot(p.x - x, p.z - z) > 5)
          && Math.hypot(g.hero.pos.x - x, g.hero.pos.z - z) > 7;
        if (!clear) continue;
        const c = createCrawler(scene, x, z, { disguised: true, speed, models, quality });
        useRealShadows(c.group);
        g.crawlers.push(c);
        break;
      }
    }
    sfx.wave();
    ui.toast(size.disguised ? `Wave ${g.wave} of ${WAVES_PER_ROUND}: one of them hides as a vine post` : `Wave ${g.wave} of ${WAVES_PER_ROUND}`, 2200);
    stats.max('bestWave', g.wave);
    pushHud();
  }

  function remainingCrawlers() {
    return g.crawlers.filter((c) => !isGone(c.life)).length;
  }
  const isPile = (c) => c.life.state === 'downed' || c.life.state === 'regrowing';
  function downedCrawlers() {
    // spawning crawlers also "regrow" out of the vines; only count real knock-downs
    return g.crawlers.filter((c) => isPile(c) && c.wasKnocked).length;
  }

  /** Burn the pile next to the hero with one fire arrow (the Burn it button). */
  function burnNearby() {
    const h = g.hero;
    const c = g.burnTarget;
    if (!c || !isPile(c)) return;
    if (h.fireArrows <= 0) {
      ui.toast('No fire left. Light more at the brazier.', 2000);
      return;
    }
    h.fireArrows -= 1;
    h.burnAnim = 0.4;
    faceToward(h, c.pos.x - h.pos.x, c.pos.z - h.pos.z);
    const before = c.life.state;
    const after = hitFire(c.life, 0);
    afterHit(c, after, before);
    stats.add('burnButton', 1);
  }

  // ---------- combat ----------
  function cutlassBlow(step) {
    const h = g.hero;
    const arc = (CUTLASS.arcDegrees / 2) * (Math.PI / 180);
    let landed = false;
    for (const c of g.crawlers) {
      const st = c.life.state;
      if (st === 'burned') continue;
      const dx = c.pos.x - h.pos.x;
      const dz = c.pos.z - h.pos.z;
      const d = Math.hypot(dx, dz);
      if (d > CUTLASS.range + c.radius) continue;
      const ang = Math.acos(Math.max(-1, Math.min(1, (dx * h.facing.x + dz * h.facing.y) / (d || 1))));
      if (ang > arc && d > 0.9) continue;
      if (st === 'downed' || st === 'regrowing') {
        fx.burst(c.pos.x, 0.4, c.pos.z, 'spark', 4, 2);
        hint('downed-cut', 'Iron cannot finish what grows back. Tap Burn it.');
        continue;
      }
      const before = st;
      const after = hitIron(c.life, CUTLASS.damage[step] * mult() * h.damage);
      landed = true;
      fx.burst(c.pos.x, 1.2, c.pos.z, 'sap', 10, 4);
      if (before === 'disguised') ui.toast('A crawler was hiding as a vine post!', 1800);
      const push = step === 2 ? CUTLASS.knockback : CUTLASS.knockback * 0.35;
      c.knock.set((dx / (d || 1)) * push, (dz / (d || 1)) * push);
      if (step === 2) { c.stun = CUTLASS.stagger; c.windup = 0; }
      afterHit(c, after, before);
    }
    if (landed) sfx.hit();
  }

  function arrowHits(a) {
    for (const c of g.crawlers) {
      const st = c.life.state;
      if (st === 'burned') continue;
      if ((st === 'downed' || st === 'regrowing') && a.kind === 'iron') continue; // flies over the pile
      if (Math.hypot(c.pos.x - a.pos.x, c.pos.z - a.pos.z) > c.radius + 0.35) continue;
      const before = st;
      const after = a.kind === 'fire' ? hitFire(c.life, a.damage) : hitIron(c.life, a.damage);
      fx.burst(a.pos.x, 1.1, a.pos.z, a.kind === 'fire' ? 'fire' : 'sap', 8, 3);
      if (before === 'disguised') ui.toast('A crawler was hiding as a vine post!', 1800);
      c.knock.set(a.dir.x * 2.5, a.dir.y * 2.5);
      afterHit(c, after, before);
      sfx.hit();
      return true;
    }
    return false;
  }

  function hurtHero(damage) {
    const h = g.hero;
    if (h.dodgeLeft > 0 || h.invulnerable > 0) return;
    h.health = Math.max(0, h.health - damage);
    h.invulnerable = HERO.hurtInvulnerable;
    h.hurtFlash = 0.25;
    h.hurtAnim = 0.3;
    fx.burst(h.pos.x, 1.2, h.pos.z, 'blood', 12, 4);
    sfx.hurt();
    ui.hurt();
    stats.add('damageTaken', damage);
    if (h.health <= 0) die();
  }

  function die() {
    g.phase = 'dead';
    g.hero.dead = true;
    input.releasePointer?.();
    h_stopDraw();
    stats.add('deaths', 1);
    ui.dead({ wave: g.wave, seconds: g.roundTime, burned: g.roundBurned });
  }

  function win() {
    g.phase = 'won';
    input.releasePointer?.();
    h_stopDraw();
    stats.add('roundsWon', 1);
    ui.win({ seconds: g.roundTime, burned: g.roundBurned, debt: g.genie.debt, forge: g.forgeLevel });
  }

  function h_stopDraw() {
    if (!g.hero) return;
    g.hero.drawing = false;
    g.hero.drawTime = 0;
  }

  // ---------- the Hornbill ----------
  function tryPower() {
    const gn = g.genie;
    if (debt.isTurned(gn)) {
      ui.toast('The Hornbill will lend nothing more until you pay at the crossroads.', 2400);
      return;
    }
    if (!debt.canUse(gn)) return;
    const before = gn.debt;
    debt.usePower(gn);
    stats.add('powerUses', 1);
    sfx.power();
    ui.setVignette(true);
    hint('power', 'Time slows and hidden crawlers glow. The Hornbill will want this back.');
    if (debt.isTurned(gn)) {
      sfx.turned();
      stats.add('turned', 1);
      ui.toast('The gift turns: darkness closes in until you pay at the crossroads.', 3500);
    } else if (before < HORNBILL.warnAt && gn.debt >= HORNBILL.warnAt) {
      ui.toast('The Hornbill grows impatient. Pay soon.', 2400);
    }
    pushHud();
  }

  /** Called by the crossroads menu. */
  function payOffering(kind) {
    const res = debt.payOffering(g.genie, g.pack, kind);
    if (res.ok) {
      sfx.pay();
      stats.add('offerings', 1);
      hornbill.call();
      if (res.bondUp) ui.toast(`Your bond with the Hornbill deepens (level ${g.genie.bond}). Its sight lasts longer and costs less.`, 3500);
      ui.setDarkness(debt.isTurned(g.genie) ? 1 : 0);
    }
    pushHud();
    return res;
  }

  /** Called by the forge menu before the rhythm game. */
  function spendForgeIron() {
    if (g.forgeLevel >= FORGE.maxLevel) return { ok: false, reason: 'max' };
    if (g.pack.iron < FORGE.ironCost) return { ok: false, reason: 'iron' };
    g.pack.iron -= FORGE.ironCost;
    pushHud();
    return { ok: true };
  }

  function applyForge(levels, score) {
    const before = g.forgeLevel;
    g.forgeLevel = Math.min(FORGE.maxLevel, g.forgeLevel + levels);
    stats.add('forgeRuns', 1);
    stats.max('forgeBestScore', Math.round(score * 100));
    pushHud();
    return g.forgeLevel - before;
  }

  // ---------- per-frame ----------
  function update(dt) {
    fx.update(dt);
    decor.update(dt);
    if (g.phase !== 'paused') hornbill.update(dt, { sight: g.phase === 'play' && g.genie.activeFor > 0, hero: g.hero, camera });
    world.brazier.flame.scale.y = 1 + Math.sin(performance.now() / 90) * 0.12;
    world.brazier.light.intensity = 13 + Math.sin(performance.now() / 70) * 2;

    if (g.phase !== 'play') {
      input.consume();
      if (g.hero) {
        updateRig(rig, dt, g.hero);
        // let the death fall (and idle breathing behind menus) keep playing
        if (g.hero.anim && g.phase !== 'paused') poseHero(g.hero, dt, { moving: false });
      }
      return;
    }
    g.roundTime += dt;
    stats.add('playSeconds', dt);
    const h = g.hero;
    const inp = input;

    if (inp.pause || inp.lockLost) { input.consume(); ui.pause(); return; }

    // the Hornbill
    const wasActive = g.genie.activeFor > 0;
    debt.tickGenie(g.genie, dt);
    if (wasActive && g.genie.activeFor <= 0) ui.setVignette(false);
    if (inp.power) tryPower();
    const enemyDt = g.genie.activeFor > 0 ? dt * HORNBILL.slowFactor : dt;
    const reveal = g.genie.activeFor > 0;
    ui.setDarkness(debt.isTurned(g.genie) ? 1 : 0);

    // look around (drag, mouse, or arrow keys)
    look(rig, inp.look.dx, inp.look.dy);

    // timers
    h.invulnerable = Math.max(0, h.invulnerable - dt);
    h.dodgeCooldown = Math.max(0, h.dodgeCooldown - dt);

    // arrow kind
    if (inp.toggleArrow) {
      h.arrowKind = h.arrowKind === 'iron' ? 'fire' : 'iron';
      if (h.arrowKind === 'fire' && h.fireArrows <= 0) hint('no-fire', 'No fire arrows. Light them at the brazier.');
    }

    // the stick is relative to the camera
    const moveLen = Math.min(1, Math.hypot(inp.move.x, inp.move.z));
    const mv = stickToWorld(rig, inp.move.x, inp.move.z);

    // roll
    if (inp.dodge && h.dodgeLeft <= 0 && h.dodgeCooldown <= 0) {
      if (moveLen > 0.1) h.dodgeDir.set(mv.x, mv.z).normalize();
      else h.dodgeDir.copy(h.facing);
      h.dodgeLeft = HERO.dodge.duration;
      h.invulnerable = Math.max(h.invulnerable, HERO.dodge.invulnerable);
      h.dodgeCooldown = HERO.dodge.duration + HERO.dodge.cooldown;
      combo.cancel(h.combo);
      h_stopDraw();
      faceToward(h, h.dodgeDir.x, h.dodgeDir.y);
      stats.add('rolls', 1);
    }

    // cutlass
    if (inp.attack && h.dodgeLeft <= 0) {
      if (h.drawing) h_stopDraw();
      const target = nearestCrawler(CUTLASS.assistRange, (c) => c.life.state === 'alive');
      if (target && !combo.isSwinging(h.combo)) faceToward(h, target.pos.x - h.pos.x, target.pos.z - h.pos.z);
      const prevStep = h.combo.step;
      if (combo.press(h.combo) || prevStep !== h.combo.step) sfx.swing();
    }
    const prevStep = h.combo.step;
    const ev = combo.tick(h.combo, dt);
    if (h.combo.step !== prevStep && h.combo.step >= 0) sfx.swing();
    if (ev?.type === 'hit') cutlassBlow(ev.step);

    // bow
    if (inp.bowHeld && !h.drawing && h.dodgeLeft <= 0) {
      h.drawing = true;
      h.drawTime = 0;
      combo.cancel(h.combo);
    }
    let aimDir = null;
    let aimLength = 6;
    if (h.drawing) {
      h.drawTime += dt;
      // aim where the camera looks; the stick strafes
      const b = cameraBasis(rig);
      faceToward(h, b.fx, b.fz);
      aimDir = h.facing.clone();
      const assist = (BOW.assistDegrees * Math.PI) / 180;
      let best = null;
      let bestScore = Infinity;
      for (const c of g.crawlers) {
        const st = c.life.state;
        if (st === 'burned' || (st === 'disguised' && !reveal)) continue;
        if ((st === 'downed' || st === 'regrowing') && h.arrowKind !== 'fire') continue;
        const dx = c.pos.x - h.pos.x;
        const dz = c.pos.z - h.pos.z;
        const d = Math.hypot(dx, dz);
        if (d > BOW.assistRange) continue;
        const ang = Math.acos(Math.max(-1, Math.min(1, (dx * aimDir.x + dz * aimDir.y) / (d || 1))));
        if (ang > assist) continue;
        const score = ang * 6 + d * 0.1;
        if (score < bestScore) { bestScore = score; best = c; }
      }
      if (best) {
        aimDir.set(best.pos.x - h.pos.x, best.pos.z - h.pos.z).normalize();
        aimLength = Math.min(BOW.maxRange, dist2d(best.pos, h.pos));
        faceToward(h, aimDir.x, aimDir.y);
      }
    }
    if (inp.bowReleased && h.drawing) {
      let kind = h.arrowKind;
      if (kind === 'fire' && h.fireArrows <= 0) {
        kind = 'iron';
        hint('no-fire-shot', 'Out of fire arrows: that was iron. Light more at the brazier.');
      }
      const full = h.drawTime >= BOW.fullDraw;
      const base = kind === 'fire' ? BOW.fireDamage : BOW.ironDamage * mult();
      arrows.fire({ x: h.pos.x, z: h.pos.z, dir: h.facing.clone(), kind, damage: base * (full ? 1 : BOW.weakFactor) });
      if (kind === 'fire') h.fireArrows -= 1;
      sfx.shoot();
      stats.add(kind === 'fire' ? 'fireArrowsShot' : 'ironArrowsShot', 1);
      h_stopDraw();
    }

    // movement
    if (h.dodgeLeft > 0) {
      h.dodgeLeft = Math.max(0, h.dodgeLeft - dt);
      h.pos.x += h.dodgeDir.x * HERO.dodge.speed * dt;
      h.pos.z += h.dodgeDir.y * HERO.dodge.speed * dt;
    } else if (moveLen > 0.05) {
      let speed = h.speed;
      if (h.drawing) speed *= HERO.aimSpeedFactor;
      if (combo.isSwinging(h.combo)) speed *= 0.35;
      h.pos.x += mv.x * speed * dt;
      h.pos.z += mv.z * speed * dt;
      if (!h.drawing && !combo.isSwinging(h.combo)) faceToward(h, mv.x, mv.z);
    }
    resolveCollisions(h.pos, h.radius, world.obstacles);

    // crawlers
    for (const c of g.crawlers) {
      const e = updateCrawler(c, enemyDt, h, g.crawlers, { reveal });
      if (e?.type === 'strike') hurtHero(e.damage);
      if (e?.type === 'ambush') { ui.toast('The vine post was a crawler!', 1600); sfx.hurt(); }
      if (e?.type === 'rose' && c.wasKnocked) {
        c.wasKnocked = false;
        hint('rose', 'It grew back. Fire finishes what iron cannot.');
      }
      if (c.life.state !== 'burned') resolveCollisions(c.pos, c.radius, world.obstacles);
      if (c.life.state === 'burned') c.goneFor = (c.goneFor ?? 0) + dt;
    }
    for (let i = g.crawlers.length - 1; i >= 0; i--) {
      if ((g.crawlers[i].goneFor ?? 0) > 0.9) {
        removeCrawler(scene, g.crawlers[i]);
        g.crawlers.splice(i, 1);
      }
    }

    // arrows and pickups
    arrows.update(dt, arrowHits, (p) => fx.burst(p.x, 1.1, p.z, 'fire', 1, 0.5));
    for (const kind of pickups.update(dt, h)) {
      g.pack[kind] += 1;
      sfx.pickup();
      stats.add(kind === 'rice' ? 'riceCollected' : 'ironCollected', 1);
      if (kind === 'iron') hint('iron', 'Iron scrap. Take 3 to the forge to make better iron.');
      if (kind === 'rice' && g.genie.debt > 0) hint('rice', 'Rice. Offer it at the crossroads to pay the Hornbill.');
    }

    // places
    const { crossroads, forge, brazier } = world;
    g.nearby = null;
    g.burnTarget = nearestCrawler(BURN_RANGE, isPile);
    if (g.burnTarget) g.nearby = 'burn';
    else if (dist2d(crossroads, h.pos) < crossroads.interactRange) g.nearby = 'crossroads';
    else if (dist2d(forge, h.pos) < forge.interactRange) g.nearby = 'forge';
    crossroads.ring.material.opacity = g.genie.debt > 0 ? 0.35 + Math.sin(performance.now() / 300) * 0.2 : 0;
    if (dist2d(brazier, h.pos) < brazier.refillRange && h.fireArrows < BOW.fireArrowsMax) {
      h.fireArrows = BOW.fireArrowsMax;
      h.arrowKind = 'fire';
      sfx.burn();
      ui.toast(`Fire arrows lit (${BOW.fireArrowsMax})`, 1400);
    }
    if (inp.interact && g.nearby === 'burn') burnNearby();
    else if (inp.interact && g.nearby) openPlace(g.nearby);

    // waves
    if (g.waveState === 'fighting' && remainingCrawlers() === 0) {
      g.waveState = 'breather';
      g.breatherLeft = WAVES.breather;
      stats.add('wavesCleared', 1);
      sfx.wave();
      if (g.wave >= WAVES_PER_ROUND) { win(); return; }
      ui.toast(g.genie.debt > 0 ? `Wave ${g.wave} cleared. Pay your debt at the crossroads.` : `Wave ${g.wave} cleared.`, 2600);
    } else if (g.waveState === 'breather') {
      g.breatherLeft -= dt;
      if (g.breatherLeft <= 0) startWave();
    }

    poseHero(h, dt, { moving: moveLen > 0.05 || h.dodgeLeft > 0, aimDir, aimLength, speedFactor: moveLen * (h.drawing ? HERO.aimSpeedFactor : 1) });
    updateRig(rig, dt, h, { moving: moveLen > 0.3, aiming: h.drawing });
    world.followSun(h.pos.x, h.pos.z);
    input.consume();
    pushHud();
  }

  function openPlace(place) {
    input.releasePointer?.(); // free the mouse to click the menu
    if (place === 'crossroads') {
      g.phase = 'menu';
      h_stopDraw();
      ui.openCrossroads();
    } else if (place === 'forge') {
      g.phase = 'menu';
      h_stopDraw();
      ui.openForge();
    }
  }

  function pushHud() {
    const h = g.hero;
    if (!h) return;
    const gn = g.genie;
    ui.hud({
      health: h.health,
      maxHealth: h.maxHealth,
      rice: g.pack.rice,
      iron: g.pack.iron,
      forgeLevel: g.forgeLevel,
      bond: gn.bond,
      debt: gn.debt,
      maxDebt: gn.cfg.maxDebt,
      turned: debt.isTurned(gn),
      powerActive: gn.activeFor > 0,
      powerReady: debt.canUse(gn),
      arrowKind: h.arrowKind,
      fireArrows: h.fireArrows,
      wave: g.wave,
      waveState: g.waveState,
      breatherLeft: g.breatherLeft,
      remaining: remainingCrawlers(),
      downed: downedCrawlers(),
      totalWaves: WAVES_PER_ROUND,
      fireLeft: h.fireArrows,
      nearby: g.nearby,
      owes: gn.debt > 0,
    });
  }

  function setAspect(w, h) {
    camera.aspect = w / h;
    // in portrait, widen the view so the sides of the fight stay visible
    camera.fov = w < h ? CAMERA.portraitFov : CAMERA.fov;
    camera.updateProjectionMatrix();
  }

  input.inPlay = () => g.phase === 'play';
  reset();

  return {
    g, scene, camera,
    update, reset, setAspect,
    start() { reset(); g.phase = 'play'; stats.add('rounds', 1); stats.session.hero = heroKey; },
    setHero(key) { if (HEROES[key]) heroKey = key; },
    get heroKey() { return heroKey; },
    hornbill,
    resume() { if (g.phase === 'paused' || g.phase === 'menu') g.phase = 'play'; },
    rig,
    pauseGame() { if (g.phase === 'play') g.phase = 'paused'; },
    payOffering, spendForgeIron, applyForge,
    labelAnchors: () => {
      const list = [
        { key: 'crossroads', text: 'Crossroads', x: world.crossroads.x, y: 2.4, z: world.crossroads.z },
        { key: 'forge', text: 'Forge', x: world.forge.x, y: 2.4, z: world.forge.z },
        { key: 'brazier', text: 'Brazier · fire', x: world.brazier.x, y: 2.8, z: world.brazier.z },
      ];
      // a countdown over every knocked-down crawler, so it's clear it will rise again
      for (const c of g.crawlers) {
        if (!isPile(c) || !c.wasKnocked) continue;
        const left = c.life.state === 'downed' ? Math.max(0, c.life.cfg.regrowAfter - c.life.timer) : 0;
        list.push({ key: `burn-${c.id}`, text: left > 0 ? `Burn it · ${Math.ceil(left)}` : 'Rising!', cls: 'burn', x: c.pos.x, y: 1.2, z: c.pos.z });
      }
      return list;
    },
  };
}
