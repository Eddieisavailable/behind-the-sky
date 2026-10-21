// Loads the Blender-made characters (public/models/*.glb) and plays their animations.
// If loading fails, the game keeps its gray-box shapes.

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/examples/jsm/utils/SkeletonUtils.js';

const loader = new GLTFLoader();

/** Load one model by name (public/models/<name>.glb). */
export async function loadModel(name) {
  const url = new URL(`models/${name}.glb`, document.baseURI).href;
  try {
    return await loader.loadAsync(url);
  } catch (err) {
    // hosts that don't serve .glb files get the same bytes as a script module (base64)
    const mod = await import(/* @vite-ignore */ `${url}.js`);
    const bytes = Uint8Array.from(atob(mod.default), (ch) => ch.charCodeAt(0));
    return loader.parseAsync(bytes.buffer, '');
  }
}

/** What the clearing needs at start. Later areas' creatures load when the player reaches them. */
export const STARTUP_MODELS = ['korto', 'flomo', 'hornbill', 'crawler', 'sii', 'environment'];
/** Built and ready for areas not made yet: the boss, mini-boss, bats, the other genii, Gelengol, the River Woman, Kelema-ninga, the swamp, the bele tree, and Gbelewala with its people. */
export const LATER_MODELS = ['meni_lizard', 'meni_true', 'rattan_bull', 'bat', 'genie_iron', 'genie_ant', 'gelengol', 'river_woman', 'kelema', 'swamp', 'bele_tree',
  'gbelewala', 'storyteller', 'chief', 'blacksmith', 'villager_woman', 'villager_man', 'elder', 'child'];

export async function loadModels(names = STARTUP_MODELS) {
  try {
    const list = await Promise.all(names.map(loadModel));
    return Object.fromEntries(names.map((n, i) => [n, list[i]]));
  } catch (err) {
    console.warn('Models did not load; using the gray-box shapes.', err);
    return null;
  }
}

export function convert(m, lambert) {
  // glowing parts (eyes, embers, spirit marks): drawn in their own colour, unlit. A strong emissive
  // on a lit material washes out to white.
  if (m.name === 'Glow') return new THREE.MeshBasicMaterial({ name: m.name, color: m.emissive.clone() });
  if (!lambert) return m.clone();
  // Lambert is cheaper per pixel: used on Medium and Low graphics
  return new THREE.MeshLambertMaterial({
    name: m.name,
    color: m.color.clone(),
    vertexColors: m.vertexColors,
    emissive: m.emissive.clone(),
    emissiveIntensity: m.emissiveIntensity,
    flatShading: true,
  });
}

/**
 * A fresh copy of a model with its own materials (so one crawler can glow
 * without the others). Blender's front faces +Z in three.js; the game's
 * characters face −Z, so the copy is turned around inside a wrapper.
 */
export function instantiate(gltf, { lambert = false, scale = 1.12 } = {}) {
  const root = cloneSkinned(gltf.scene);
  const materials = [];
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.frustumCulled = false; // animated poses can leave the bind-pose bounds
    o.material = Array.isArray(o.material) ? o.material.map((m) => convert(m, lambert)) : convert(o.material, lambert);
    for (const m of [o.material].flat()) materials.push(m);
  });
  root.rotation.y = Math.PI;
  const object = new THREE.Group();
  object.add(root);
  object.scale.setScalar(scale); // a touch larger than life so they read on a phone screen
  return { object, root, materials, clips: gltf.animations };
}

/** Plays one clip at a time, cross-fading between them. */
export class Animator {
  constructor(root, clips) {
    this.mixer = new THREE.AnimationMixer(root);
    this.actions = {};
    this.durations = {};
    for (const clip of clips) {
      this.actions[clip.name] = this.mixer.clipAction(clip);
      this.durations[clip.name] = clip.duration || 0.0001;
    }
    this.current = null;
    this.name = null;
  }

  has(name) { return !!this.actions[name]; }

  /**
   * @param once      play a single time and hold the last pose
   * @param seconds   stretch or squeeze the clip to last this long
   * @param restart   start again even if it's already playing
   */
  play(name, { once = false, fade = 0.12, timeScale = 1, seconds = 0, restart = false } = {}) {
    const a = this.actions[name];
    if (!a) return;
    a.timeScale = seconds > 0 ? this.durations[name] / seconds : timeScale;
    if (this.current === a && !restart) return;
    const prev = this.current;
    a.reset();
    a.setLoop(once ? THREE.LoopOnce : THREE.LoopRepeat, Infinity);
    a.clampWhenFinished = once;
    a.enabled = true;
    a.setEffectiveWeight(1);
    a.play();
    if (prev && prev !== a && fade > 0) a.crossFadeFrom(prev, fade, false);
    else if (prev && prev !== a) prev.stop();
    this.current = a;
    this.name = name;
  }

  update(dt) { this.mixer.update(dt); }
}

/** Set an emissive glow on materials (the eyes keep their own). */
export function setGlow(materials, r, g, b) {
  for (const m of materials) {
    if (m.name === 'Eyes' || m.name === 'Glow') continue;
    m.emissive.setRGB(r, g, b);
  }
}

export function setShade(materials, k) {
  for (const m of materials) {
    if (m.name === 'Eyes' || m.name === 'Glow') continue;
    m.color.setScalar(k);
  }
}
