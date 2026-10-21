// Cutlass three-hit combo as a small state machine.
// press() is called on each attack tap; tick() advances time and reports
// the moment each blow should land.

import { CUTLASS } from '../config.js';

export function createCombo(cfg = CUTLASS) {
  return { cfg, step: -1, t: 0, landed: false, queued: false, sinceEnd: Infinity };
}

export const isSwinging = (c) => c.step >= 0;

export function press(c) {
  if (c.step < 0) {
    // Start a new chain, or continue one that just ended.
    const next = c.sinceEnd <= c.cfg.comboWindow && c.lastStep != null && c.lastStep < 2 ? c.lastStep + 1 : 0;
    beginStep(c, next);
    return true;
  }
  // Mid-swing: queue the next blow if there is one.
  if (c.step < 2) c.queued = true;
  return false;
}

function beginStep(c, step) {
  c.step = step;
  c.t = 0;
  c.landed = false;
  c.queued = false;
}

/** Returns an event or null: { type: 'hit', step } when a blow lands. */
export function tick(c, dt) {
  if (c.step < 0) {
    c.sinceEnd += dt;
    return null;
  }
  c.t += dt;
  let event = null;
  if (!c.landed && c.t >= c.cfg.hitTime[c.step]) {
    c.landed = true;
    event = { type: 'hit', step: c.step };
  }
  if (c.t >= c.cfg.duration[c.step]) {
    const finished = c.step;
    if (c.queued && finished < 2) {
      beginStep(c, finished + 1);
    } else {
      c.lastStep = finished;
      c.step = -1;
      c.sinceEnd = 0;
    }
  }
  return event;
}

export function cancel(c) {
  c.step = -1;
  c.queued = false;
  c.lastStep = null;
  c.sinceEnd = Infinity;
}
