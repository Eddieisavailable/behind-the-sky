// Playtest numbers kept on the phone (no server yet; phase 5 adds real analytics).
// Testers can copy them from the pause screen and send them over.

const KEY = 'bts-playtest-v1';

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) ?? {};
  } catch {
    return {};
  }
}

export function createStats() {
  const lifetime = { sessions: 0, ...load() };
  lifetime.sessions = (lifetime.sessions ?? 0) + 1;
  lifetime.firstSeen ??= new Date().toISOString();
  const session = { startedAt: new Date().toISOString() };
  const fps = { sum: 0, n: 0, lowSeconds: 0 };
  let lastSave = 0;

  function save(force = false) {
    const now = performance.now();
    if (!force && now - lastSave < 5000) return;
    lastSave = now;
    try { localStorage.setItem(KEY, JSON.stringify(lifetime)); } catch { /* private mode: fine */ }
  }

  return {
    session,
    lifetime,
    add(key, n) {
      session[key] = (session[key] ?? 0) + n;
      lifetime[key] = (lifetime[key] ?? 0) + n;
      save();
    },
    max(key, v) {
      session[key] = Math.max(session[key] ?? 0, v);
      lifetime[key] = Math.max(lifetime[key] ?? 0, v);
      save();
    },
    sampleFps(value, dt) {
      fps.sum += value;
      fps.n += 1;
      if (value < 30) fps.lowSeconds += dt;
    },
    fpsSummary() {
      return { avg: fps.n ? Math.round(fps.sum / fps.n) : 0, lowSeconds: Math.round(fps.lowSeconds) };
    },
    save: () => save(true),
    /** Plain-text report for WhatsApp or email. */
    report(extra = {}) {
      const s = session;
      const f = this.fpsSummary();
      const mins = ((s.playSeconds ?? 0) / 60).toFixed(1);
      const lines = [
        'Behind the Sky prototype - playtest',
        `Device: ${navigator.userAgent}`,
        `Screen: ${window.innerWidth}x${window.innerHeight} @${window.devicePixelRatio}x, render scale ${extra.renderScale ?? '?'}`,
        `Session: ${mins} min played, ${s.rounds ?? 0} rounds, best wave ${s.bestWave ?? 0}, ${s.deaths ?? 0} deaths`,
        `Crawlers burned: ${s.burned ?? 0}, waves cleared: ${s.wavesCleared ?? 0}`,
        `Hornbill: ${s.powerUses ?? 0} uses, ${s.offerings ?? 0} offerings, turned ${s.turned ?? 0} times`,
        `Forge: ${s.forgeRuns ?? 0} runs, best score ${s.forgeBestScore ?? 0}%`,
        `Frame rate: avg ${f.avg} fps, ${f.lowSeconds}s below 30`,
        `All time: ${lifetime.sessions} sessions, ${(((lifetime.playSeconds ?? 0)) / 60).toFixed(1)} min, best wave ${lifetime.bestWave ?? 0}`,
      ];
      return lines.join('\n');
    },
  };
}
