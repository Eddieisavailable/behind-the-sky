import { WAVES, CRAWLER } from '../config.js';

/** How many crawlers a wave holds, and how many of them hide as vine posts. */
export function waveSize(n, cfg = WAVES) {
  const regular = cfg.baseCount + Math.min(n - 1, cfg.extraUpTo);
  const disguised = n >= cfg.disguisedFrom ? 1 : 0;
  return { regular, disguised, total: regular + disguised };
}

export function crawlerSpeed(n, cfg = CRAWLER) {
  return Math.min(cfg.maxSpeed, cfg.speed + (n - 1) * cfg.speedPerWave);
}
