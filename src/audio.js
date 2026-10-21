// Tiny synthesised sounds, so the prototype ships with no audio files.
// The slit-drum has two tongues: a low and a high note.

let ctx = null;
let master = null;

export function unlockAudio() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = 0.6;
    master.connect(ctx.destination);
  }
  if (ctx.state === 'suspended') ctx.resume();
  return ctx;
}

export const audioNow = () => (ctx ? ctx.currentTime : performance.now() / 1000);
export const audioLatency = () => (ctx ? (ctx.outputLatency || ctx.baseLatency || 0) : 0);

function tone({ at, freq, endFreq = freq, dur = 0.15, type = 'sine', gain = 0.5 }) {
  if (!ctx) return;
  const t = at ?? ctx.currentTime;
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = type;
  o.frequency.setValueAtTime(freq, t);
  o.frequency.exponentialRampToValueAtTime(Math.max(20, endFreq), t + dur);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(gain, t + 0.005);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g).connect(master);
  o.start(t);
  o.stop(t + dur + 0.02);
}

function noise({ at, dur = 0.08, gain = 0.3, freq = 1800, q = 1.2 }) {
  if (!ctx) return;
  const t = at ?? ctx.currentTime;
  const len = Math.ceil(ctx.sampleRate * dur);
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
  const src = ctx.createBufferSource();
  src.buffer = buf;
  const f = ctx.createBiquadFilter();
  f.type = 'bandpass';
  f.frequency.value = freq;
  f.Q.value = q;
  const g = ctx.createGain();
  g.gain.value = gain;
  src.connect(f).connect(g).connect(master);
  src.start(t);
}

export const sfx = {
  drum(kind, at) {
    if (kind === 'low') tone({ at, freq: 150, endFreq: 72, dur: 0.22, gain: 0.8 });
    else tone({ at, freq: 260, endFreq: 150, dur: 0.14, gain: 0.6 });
    noise({ at, dur: 0.03, gain: 0.15, freq: 900 });
  },
  strike(quality) {
    tone({ freq: quality === 'perfect' ? 1400 : 900, endFreq: 600, dur: 0.12, type: 'triangle', gain: 0.35 });
    noise({ dur: 0.05, gain: 0.25, freq: 3200, q: 3 });
  },
  swing() { noise({ dur: 0.09, gain: 0.18, freq: 2400, q: 0.8 }); },
  hit() { tone({ freq: 180, endFreq: 90, dur: 0.08, type: 'square', gain: 0.12 }); noise({ dur: 0.05, gain: 0.2, freq: 1200 }); },
  shoot() { tone({ freq: 520, endFreq: 260, dur: 0.1, type: 'triangle', gain: 0.18 }); },
  burn() { noise({ dur: 0.35, gain: 0.25, freq: 600, q: 0.6 }); },
  hurt() { tone({ freq: 140, endFreq: 70, dur: 0.18, type: 'sawtooth', gain: 0.18 }); },
  pickup() { tone({ freq: 880, endFreq: 1320, dur: 0.08, type: 'triangle', gain: 0.15 }); },
  power() { tone({ freq: 330, endFreq: 990, dur: 0.5, type: 'sine', gain: 0.25 }); },
  turned() { tone({ freq: 220, endFreq: 55, dur: 0.9, type: 'sawtooth', gain: 0.2 }); },
  pay() { tone({ freq: 523, dur: 0.14, gain: 0.25 }); tone({ at: (ctx?.currentTime ?? 0) + 0.12, freq: 784, dur: 0.22, gain: 0.25 }); },
  wave() { tone({ freq: 196, endFreq: 196, dur: 0.4, type: 'triangle', gain: 0.25 }); },
};
