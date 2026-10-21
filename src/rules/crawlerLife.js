// Life of a rattan crawler. The rule from the story bible:
// "What demons grow, grows back unless burned."
//
//   disguised --(revealed)--> alive --(health 0)--> downed --(4 s)--> regrowing --> alive
//                                 \                     \
//                                  (burning & health 0)  (fire arrow)
//                                   \                     \
//                                    `------------------> burned  (gone for good, drops loot)

import { CRAWLER } from '../config.js';

export function createLife(cfg = CRAWLER, { disguised = false } = {}) {
  return {
    cfg,
    state: disguised ? 'disguised' : 'alive',
    health: cfg.health,
    timer: 0,      // time spent in the current state
    burnLeft: 0,   // seconds of burning left while alive
  };
}

export const isActive = (l) => l.state === 'alive';
export const isGone = (l) => l.state === 'burned';
export const isDowned = (l) => l.state === 'downed' || l.state === 'regrowing';

function enter(l, state) {
  l.state = state;
  l.timer = 0;
}

export function reveal(l) {
  if (l.state === 'disguised') enter(l, 'alive');
}

/** Iron (cutlass or iron arrow). Returns the new state. */
export function hitIron(l, damage) {
  if (l.state === 'disguised') {
    reveal(l);
    // the blow that unmasks it still lands
  }
  if (l.state !== 'alive') return l.state;
  l.health -= damage;
  if (l.health <= 0) {
    l.health = 0;
    enter(l, l.burnLeft > 0 ? 'burned' : 'downed');
  }
  return l.state;
}

/** Fire arrow. Burns a downed crawler away; sets a standing one alight. */
export function hitFire(l, damage) {
  if (l.state === 'downed' || l.state === 'regrowing') {
    enter(l, 'burned');
    return l.state;
  }
  if (l.state === 'disguised') reveal(l);
  if (l.state !== 'alive') return l.state;
  l.burnLeft = l.cfg.burnDuration;
  l.health -= damage;
  if (l.health <= 0) {
    l.health = 0;
    enter(l, 'burned');
  }
  return l.state;
}

/** Advance time. Returns 'rose' when a crawler finishes growing back, else null. */
export function tickLife(l, dt) {
  l.timer += dt;
  if (l.state === 'alive' && l.burnLeft > 0) {
    l.burnLeft = Math.max(0, l.burnLeft - dt);
    l.health -= l.cfg.burnDps * dt;
    if (l.health <= 0) {
      l.health = 0;
      enter(l, 'burned');
    }
  } else if (l.state === 'downed' && l.timer >= l.cfg.regrowAfter) {
    enter(l, 'regrowing');
  } else if (l.state === 'regrowing' && l.timer >= l.cfg.regrowDuration) {
    l.health = l.cfg.health;
    enter(l, 'alive');
    return 'rose';
  }
  return null;
}

/** 0..1 how far a downed crawler has grown back (for drawing). */
export function regrowProgress(l) {
  if (l.state === 'regrowing') return Math.min(1, l.timer / l.cfg.regrowDuration);
  if (l.state === 'downed') return 0;
  return 1;
}
