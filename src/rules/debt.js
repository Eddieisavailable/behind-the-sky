// The spirit-debt rule: every gift is a loan, paid at the crossroads.
// Pure logic, no rendering, so it can be unit-tested.

import { HORNBILL, OFFERING } from '../config.js';

export function createGenie(cfg = HORNBILL) {
  return {
    cfg,
    debt: 0,
    bond: 0,          // 0..maxBond
    clears: 0,        // times the debt was paid down to zero at this bond level
    activeFor: 0,     // seconds of power left
    cooldown: 0,
    timesTurned: 0,
    uses: 0,
  };
}

export const isTurned = (g) => g.debt >= g.cfg.maxDebt;

export const costPerUse = (g) =>
  Math.max(g.cfg.debtPerUseMin, g.cfg.debtPerUse - g.bond * g.cfg.debtDiscountPerBond);

export const powerDuration = (g) => g.cfg.duration + g.bond * g.cfg.durationPerBond;

export function canUse(g) {
  return !isTurned(g) && g.activeFor <= 0 && g.cooldown <= 0;
}

/** Use the gift. Returns true if it fired. Adds debt; may tip the genie into "turned". */
export function usePower(g) {
  if (!canUse(g)) return false;
  const wasTurned = isTurned(g);
  g.debt = Math.min(g.cfg.maxDebt, g.debt + costPerUse(g));
  g.activeFor = powerDuration(g);
  g.uses += 1;
  if (!wasTurned && isTurned(g)) g.timesTurned += 1;
  return true;
}

export function tickGenie(g, dt) {
  if (g.activeFor > 0) {
    g.activeFor = Math.max(0, g.activeFor - dt);
    if (g.activeFor === 0) g.cooldown = g.cfg.cooldown;
  } else if (g.cooldown > 0) {
    g.cooldown = Math.max(0, g.cooldown - dt);
  }
}

/** What an offering can be paid with, given the hero's pack. */
export function offeringOptions(pack, cfg = OFFERING) {
  return {
    rice: pack.rice >= cfg.riceCost,
    iron: pack.iron >= cfg.ironCost,
  };
}

/**
 * Pay one offering at the crossroads with 'rice' or 'iron'.
 * Returns { ok, cleared, bondUp } and mutates genie and pack.
 */
export function payOffering(g, pack, kind, cfg = OFFERING) {
  if (g.debt <= 0) return { ok: false, reason: 'no-debt' };
  const cost = kind === 'rice' ? cfg.riceCost : cfg.ironCost;
  if ((pack[kind] ?? 0) < cost) return { ok: false, reason: 'cannot-afford' };
  pack[kind] -= cost;
  const before = g.debt;
  g.debt = Math.max(0, g.debt - cfg.clears);
  let bondUp = false;
  if (before > 0 && g.debt === 0 && g.bond < g.cfg.maxBond) {
    g.clears += 1;
    if (g.clears >= g.cfg.clearsPerBond) {
      g.bond += 1;
      g.clears = 0;
      bondUp = true;
    }
  }
  return { ok: true, cleared: before - g.debt, bondUp };
}
