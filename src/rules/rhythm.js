// The rhythm forge: Sii beats the slit-drum, the player strikes on the beat.
// Pure timing logic so it can be tested without audio.

import { FORGE } from '../config.js';

/** Small deterministic random generator so a pattern is the same every run. */
export function seeded(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Build the note times (seconds from start). The first bars are plain quarter
 * notes; later bars add off-beat pairs and the odd rest so it stays alive.
 * Each note has a drum: 'low' or 'high' (the two tongues of a slit-drum).
 */
export function buildPattern({ bpm = FORGE.bpm, seconds = FORGE.seconds, seed = 7, leadIn = 2 } = {}) {
  const rand = seeded(seed);
  const beat = 60 / bpm;
  const notes = [];
  const beats = Math.floor((seconds - leadIn) / beat);
  for (let i = 0; i < beats; i++) {
    const t = leadIn + i * beat;
    const bar = Math.floor(i / 4);
    const inBar = i % 4;
    if (bar >= 2 && inBar === 3 && rand() < 0.35) continue; // a rest
    notes.push({ t, drum: inBar === 0 ? 'low' : 'high' });
    if (bar >= 3 && inBar % 2 === 1 && rand() < 0.45) {
      notes.push({ t: t + beat / 2, drum: 'high' }); // off-beat pair
    }
  }
  return notes.sort((a, b) => a.t - b.t);
}

export function createJudge(notes, cfg = FORGE) {
  return {
    cfg,
    notes: notes.map((n) => ({ ...n, result: null })),
    next: 0,          // first note not yet judged
    perfect: 0,
    good: 0,
    miss: 0,
    streak: 0,
    best: 0,
  };
}

function record(j, note, result) {
  note.result = result;
  j[result] += 1;
  j.streak = result === 'miss' ? 0 : j.streak + 1;
  j.best = Math.max(j.best, j.streak);
}

/** Mark notes that slid past the window as missed. Call every frame with song time. */
export function sweep(j, now) {
  const late = j.cfg.goodMs / 1000;
  const missed = [];
  while (j.next < j.notes.length && now - j.notes[j.next].t > late) {
    const n = j.notes[j.next];
    if (!n.result) { record(j, n, 'miss'); missed.push(n); }
    j.next += 1;
  }
  return missed;
}

/** A strike at song time `now`. Returns 'perfect' | 'good' | null (a stray strike). */
export function strike(j, now) {
  sweep(j, now);
  const n = j.notes[j.next];
  if (!n) return null;
  const off = Math.abs(now - n.t) * 1000;
  if (off > j.cfg.goodMs) return null;
  const result = off <= j.cfg.perfectMs ? 'perfect' : 'good';
  record(j, n, result);
  j.next += 1;
  return result;
}

export const isDone = (j) => j.next >= j.notes.length;

/** 0..1: perfect counts fully, good counts half. */
export function score(j) {
  const total = j.notes.length || 1;
  return (j.perfect + j.good * 0.5) / total;
}

/** How many forge levels this score earns: 0, 1 or 2. */
export function levelsEarned(s, cfg = FORGE) {
  if (s >= cfg.greatAt) return 2;
  if (s >= cfg.upgradeAt) return 1;
  return 0;
}
