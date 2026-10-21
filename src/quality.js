// Picks the graphics level: the player's saved choice, or Auto
// (High on computers, Medium on phones and tablets).

import { QUALITY } from './config.js';

const KEY = 'bts-quality';

export function savedChoice() {
  try {
    const v = localStorage.getItem(KEY);
    return v && (v === 'auto' || QUALITY[v]) ? v : 'auto';
  } catch {
    return 'auto';
  }
}

export function saveChoice(choice) {
  try { localStorage.setItem(KEY, choice); } catch { /* private mode */ }
}

export function isPhoneLike() {
  const coarse = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches;
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : '';
  return coarse || /Android|iPhone|iPad|Mobile/i.test(ua);
}

export function resolveQuality(choice = savedChoice()) {
  const key = choice === 'auto' ? (isPhoneLike() ? 'medium' : 'high') : choice;
  return { key, choice, ...QUALITY[key] };
}
