import { describe, it, expect } from 'vitest';
import { HORNBILL, CRAWLER, CUTLASS, FORGE } from '../src/config.js';
import * as debt from '../src/rules/debt.js';
import * as combo from '../src/rules/combo.js';
import * as life from '../src/rules/crawlerLife.js';
import * as rhythm from '../src/rules/rhythm.js';
import { waveSize, crawlerSpeed } from '../src/rules/waves.js';

describe('spirit debt', () => {
  it('adds debt per use and turns at the limit', () => {
    const g = debt.createGenie();
    let uses = 0;
    while (debt.canUse(g)) {
      expect(debt.usePower(g)).toBe(true);
      uses += 1;
      debt.tickGenie(g, 100); // run out the power and the cooldown
      debt.tickGenie(g, 100);
    }
    expect(uses).toBe(Math.ceil(HORNBILL.maxDebt / HORNBILL.debtPerUse)); // 7 uses
    expect(debt.isTurned(g)).toBe(true);
    expect(g.timesTurned).toBe(1);
    expect(debt.usePower(g)).toBe(false);
  });

  it('cannot fire again while active or cooling down', () => {
    const g = debt.createGenie();
    debt.usePower(g);
    expect(debt.usePower(g)).toBe(false);
    debt.tickGenie(g, HORNBILL.duration);      // power ends, cooldown starts
    expect(debt.canUse(g)).toBe(false);
    debt.tickGenie(g, HORNBILL.cooldown);
    expect(debt.canUse(g)).toBe(true);
  });

  it('offerings clear 50 debt and cost rice or iron', () => {
    const g = debt.createGenie();
    g.debt = 100;
    const pack = { rice: 3, iron: 1 };
    expect(debt.offeringOptions(pack)).toEqual({ rice: true, iron: false });
    expect(debt.payOffering(g, pack, 'iron').ok).toBe(false);
    const r = debt.payOffering(g, pack, 'rice');
    expect(r).toMatchObject({ ok: true, cleared: 50 });
    expect(g.debt).toBe(50);
    expect(pack.rice).toBe(0);
    expect(debt.isTurned(g)).toBe(false);
  });

  it('raises the bond after clearing to zero three times', () => {
    const g = debt.createGenie();
    const pack = { rice: 100, iron: 0 };
    for (let i = 0; i < 3; i++) {
      g.debt = 30;
      const r = debt.payOffering(g, pack, 'rice');
      expect(r.bondUp).toBe(i === 2);
    }
    expect(g.bond).toBe(1);
    expect(debt.costPerUse(g)).toBe(HORNBILL.debtPerUse - HORNBILL.debtDiscountPerBond);
    expect(debt.powerDuration(g)).toBe(HORNBILL.duration + HORNBILL.durationPerBond);
  });

  it('will not take an offering when nothing is owed', () => {
    const g = debt.createGenie();
    const pack = { rice: 9, iron: 9 };
    expect(debt.payOffering(g, pack, 'rice')).toMatchObject({ ok: false, reason: 'no-debt' });
    expect(pack.rice).toBe(9);
  });
});

describe('cutlass combo', () => {
  const run = (c, seconds) => {
    const hits = [];
    for (let t = 0; t < seconds; t += 0.01) {
      const e = combo.tick(c, 0.01);
      if (e) hits.push(e.step);
    }
    return hits;
  };

  it('chains three blows when tapped during each swing', () => {
    const c = combo.createCombo();
    combo.press(c);
    combo.press(c);  // queued
    const hits = [];
    for (let t = 0; t < 1.2; t += 0.01) {
      const e = combo.tick(c, 0.01);
      if (e) { hits.push(e.step); combo.press(c); }
    }
    expect(hits).toEqual([0, 1, 2]);
  });

  it('continues the chain within the combo window, restarts after it', () => {
    const c = combo.createCombo();
    combo.press(c);
    expect(run(c, CUTLASS.duration[0] + 0.05)).toEqual([0]);
    combo.press(c);  // inside window
    expect(run(c, CUTLASS.duration[1] + 0.05)).toEqual([1]);
    run(c, CUTLASS.comboWindow + 0.2); // let the window lapse
    combo.press(c);
    expect(run(c, 0.5)).toEqual([0]);
  });
});

describe('rattan crawler life', () => {
  it('iron puts it down, and it grows back unless burned', () => {
    const l = life.createLife();
    expect(life.hitIron(l, CRAWLER.health)).toBe('downed');
    life.tickLife(l, CRAWLER.regrowAfter);
    expect(l.state).toBe('regrowing');
    expect(life.tickLife(l, CRAWLER.regrowDuration)).toBe('rose');
    expect(l.state).toBe('alive');
    expect(l.health).toBe(CRAWLER.health);
  });

  it('a fire arrow on a downed crawler burns it for good', () => {
    const l = life.createLife();
    life.hitIron(l, 999);
    expect(life.hitFire(l, 1)).toBe('burned');
    expect(life.isGone(l)).toBe(true);
  });

  it('a burning crawler cut down is burned, not downed', () => {
    const l = life.createLife();
    life.hitFire(l, 5);
    expect(l.burnLeft).toBeGreaterThan(0);
    expect(life.hitIron(l, 999)).toBe('burned');
  });

  it('burning alone can finish a weakened crawler', () => {
    const l = life.createLife();
    life.hitIron(l, CRAWLER.health - 4);
    life.hitFire(l, 1);
    for (let i = 0; i < 100 && l.state === 'alive'; i++) life.tickLife(l, 0.05);
    expect(l.state).toBe('burned');
  });

  it('a disguised crawler is unmasked by iron and still takes the blow', () => {
    const l = life.createLife(CRAWLER, { disguised: true });
    expect(life.isActive(l)).toBe(false);
    life.hitIron(l, 10);
    expect(l.state).toBe('alive');
    expect(l.health).toBe(CRAWLER.health - 10);
  });
});

describe('rhythm forge', () => {
  it('builds the same 30-second pattern every time', () => {
    const a = rhythm.buildPattern();
    const b = rhythm.buildPattern();
    expect(a).toEqual(b);
    expect(a.length).toBeGreaterThan(35);
    expect(a.at(-1).t).toBeLessThanOrEqual(FORGE.seconds);
    for (let i = 1; i < a.length; i++) expect(a[i].t).toBeGreaterThan(a[i - 1].t);
  });

  it('judges strikes by timing and counts missed notes', () => {
    const notes = [{ t: 1 }, { t: 2 }, { t: 3 }, { t: 4 }];
    const j = rhythm.createJudge(notes);
    expect(rhythm.strike(j, 1.03)).toBe('perfect');
    expect(rhythm.strike(j, 2.1)).toBe('good');
    expect(rhythm.strike(j, 2.6)).toBe(null);   // stray strike between notes
    rhythm.sweep(j, 3.5);                        // note 3 slid past
    expect(j.miss).toBe(1);
    expect(rhythm.strike(j, 4)).toBe('perfect');
    expect(rhythm.isDone(j)).toBe(true);
    expect(rhythm.score(j)).toBeCloseTo((2 + 0.5) / 4);
  });

  it('turns a score into forge levels', () => {
    expect(rhythm.levelsEarned(0.3)).toBe(0);
    expect(rhythm.levelsEarned(0.6)).toBe(1);
    expect(rhythm.levelsEarned(0.9)).toBe(2);
  });
});

describe('waves', () => {
  it('grows from 3 to 5 regular crawlers and adds a disguised one from wave 2', () => {
    expect(waveSize(1)).toEqual({ regular: 3, disguised: 0, total: 3 });
    expect(waveSize(2)).toEqual({ regular: 4, disguised: 1, total: 5 });
    expect(waveSize(5)).toEqual({ regular: 5, disguised: 1, total: 6 });
  });

  it('caps crawler speed', () => {
    expect(crawlerSpeed(1)).toBe(CRAWLER.speed);
    expect(crawlerSpeed(50)).toBe(CRAWLER.maxSpeed);
  });
});
