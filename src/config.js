// All tuning numbers in one place. They are first guesses from the design doc
// ("Behind the Sky — Core Loop and Slice"); the prototype exists to tune them.

export const ARENA = {
  radius: 25,          // walkable radius of the clearing (metres)
  crossroads: { x: 0, z: -19 },
  forge: { x: -15, z: 11 },
  brazier: { x: 13, z: 9 },
};

export const HERO = {
  name: 'Korto',
  health: 100,
  speed: 6.5,
  aimSpeedFactor: 0.4,     // move speed while drawing the bow
  radius: 0.45,
  dodge: { speed: 13, duration: 0.28, invulnerable: 0.32, cooldown: 0.45 },
  hurtInvulnerable: 0.5,   // grace time after being hit
};

export const CUTLASS = {
  damage: [10, 10, 18],    // three-hit combo; third hit staggers
  hitTime: [0.1, 0.1, 0.14],   // when in the swing the blow lands
  duration: [0.26, 0.26, 0.38],
  comboWindow: 0.45,       // time after a swing ends to continue the combo
  range: 2.4,
  arcDegrees: 120,
  knockback: 7,
  stagger: 0.55,
  assistRange: 3.6,        // auto-turn toward the nearest enemy within this range
};

export const BOW = {
  fullDraw: 0.35,          // seconds to a full-strength shot
  arrowSpeed: 32,
  maxRange: 22,
  ironDamage: 14,
  fireDamage: 8,
  weakFactor: 0.5,         // a quick, undrawn shot
  assistDegrees: 30,
  assistRange: 20,
  fireArrowsMax: 6,
};

export const CRAWLER = {
  health: 30,
  radius: 0.5,
  speed: 3.1,
  speedPerWave: 0.15,
  maxSpeed: 4.4,
  attackRange: 1.45,
  windup: 0.5,
  damage: 8,
  attackCooldown: 1.2,
  regrowAfter: 4,          // seconds a downed crawler lies before it rises again
  regrowDuration: 1.2,     // the rise itself
  burnDuration: 3,         // fire arrow sets it burning
  burnDps: 6,
  ambushRange: 2.2,        // a disguised crawler springs when the hero comes this close
};

export const DROPS = {
  rice: 1,
  extraRiceChance: 0.4,
  ironChance: 0.5,
  pickupRadius: 1.4,
  magnetRadius: 4,
};

export const HORNBILL = {
  debtPerUse: 15,
  debtPerUseMin: 6,
  debtDiscountPerBond: 3,
  duration: 4,
  durationPerBond: 1,
  cooldown: 1.5,
  slowFactor: 0.35,        // enemies and arrows move at this fraction of speed
  maxDebt: 100,
  warnAt: 70,
  maxBond: 3,
  clearsPerBond: 3,        // clearing the debt to zero this many times raises the bond
};

export const OFFERING = {
  clears: 50,
  riceCost: 3,
  ironCost: 2,
};

export const FORGE = {
  ironCost: 3,
  bpm: 100,
  seconds: 30,
  perfectMs: 60,
  goodMs: 130,
  upgradeAt: 0.5,          // score needed for +1 forge level
  greatAt: 0.85,           // score needed for +2
  maxLevel: 5,
  damagePerLevel: 0.12,    // +12% cutlass and iron-arrow damage per level
};

export const WAVES = {
  baseCount: 3,
  extraUpTo: 2,            // wave 1: 3, wave 2: 4, wave 3+: 5 regular crawlers
  disguisedFrom: 2,        // one disguised crawler per wave from wave 2
  breather: 10,
};

export const CAMERA = {
  distance: 7,             // metres behind the hero
  aimDistance: 5,          // pulls in while drawing the bow
  minDistance: 3,
  height: 1.6,             // the point the camera orbits (the hero's shoulders)
  pitch: 0.38,             // radians above the horizon
  minPitch: 0.08,
  maxPitch: 1.05,
  shoulder: 0.6,           // look a little right of the hero
  sensitivity: 0.006,      // radians per pixel dragged
  followDelay: 1.2,        // seconds after a drag before the camera drifts back behind the hero
  followRate: 2.2,
  edgeAllowance: 2.5,      // how far past the clearing's edge the camera may sit
  fov: 60,
  portraitFov: 75,
};

export const WAVES_PER_ROUND = 5;

export const PERF = {
  lowFps: 40,              // drop resolution if the average stays below this
  veryLowFps: 28,
};

// Graphics levels. "Auto" picks High on computers and Medium on phones.
export const QUALITY = {
  high: { label: 'High', antialias: true, maxPixelRatio: 2, minScale: 0.75, shadows: true, shadowMapSize: 2048, trees: 260, grass: 1600, fogNear: 30, fogFar: 90 },
  medium: { label: 'Medium', antialias: false, maxPixelRatio: 1.5, minScale: 0.6, shadows: false, shadowMapSize: 0, trees: 160, grass: 600, fogNear: 24, fogFar: 66 },
  low: { label: 'Low', antialias: false, maxPixelRatio: 1, minScale: 0.6, shadows: false, shadowMapSize: 0, trees: 90, grass: 0, fogNear: 18, fogFar: 52 },
};
