// Dresses the clearing with the Blender-made environment (public/models/environment.glb):
// forest, huts, shrine, brazier, forge with Sii drumming, vine clumps and rocks.
// world.js builds the gray-box version first; this swaps in models when they loaded.

import * as THREE from 'three';
import { ARENA } from '../config.js';
import { convert, instantiate, Animator } from './models.js';

/**
 * Quantized models store positions as normalized integers in [-1, 1] and put the real size in the node
 * transform. Baking that transform into the geometry needs float attributes, or it clamps to a 2 m cube.
 */
function floatGeometry(src) {
  const geo = new THREE.BufferGeometry();
  const get = ['getX', 'getY', 'getZ', 'getW'];
  for (const [name, attr] of Object.entries(src.attributes)) {
    const n = attr.count;
    const s = attr.itemSize;
    const arr = new Float32Array(n * s);
    for (let i = 0; i < n; i++) for (let k = 0; k < s; k++) arr[i * s + k] = attr[get[k]](i);
    geo.setAttribute(name, new THREE.BufferAttribute(arr, s));
  }
  if (src.index) geo.setIndex(src.index.clone());
  for (const g of src.groups) geo.addGroup(g.start, g.count, g.materialIndex);
  return geo;
}

/** The meshes that make up one named asset, with geometry in the asset's own space. */
function partsOf(gltf, name, lambert) {
  const node = gltf.scene.getObjectByName(name);
  if (!node) return [];
  gltf.scene.updateMatrixWorld(true);
  const parts = [];
  node.traverse((o) => {
    if (!o.isMesh) return;
    const geometry = floatGeometry(o.geometry).applyMatrix4(o.matrixWorld);
    geometry.computeBoundingSphere();
    const src = o.material;
    // embers glow without lighting: a plain bright colour is cheapest
    const material = src.name === 'Glow' ? new THREE.MeshBasicMaterial({ color: src.emissive.clone().multiplyScalar(1.2) }) : convert(src, lambert);
    parts.push({ geometry, material });
  });
  return parts;
}

export function dressWorld(world, models, quality) {
  const env = models?.environment;
  if (!env) return { update() {} };
  const lambert = quality.key !== 'high';
  const cache = {};
  const parts = (name) => (cache[name] ??= partsOf(env, name, lambert));
  const shadows = (obj, receive = false) => {
    if (!quality.shadows) return obj;
    obj.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = receive; } });
    return obj;
  };
  const single = (name) => {
    const g = new THREE.Group();
    for (const p of parts(name)) g.add(new THREE.Mesh(p.geometry, p.material));
    return shadows(g, true);
  };
  const { scene, obstacles } = world;

  // ---- forest: reuse the gray-box tree spots, but as giants, understory trees, oil palms and bushes ----
  const { trunks, canopies } = world.trees;
  trunks.visible = false;
  canopies.visible = false;
  const kinds = { tree_giant: [], tree_mid: [], palm: [], bush: [] };
  const m = new THREE.Matrix4();
  const p = new THREE.Vector3();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  for (let i = 0; i < trunks.count; i++) {
    trunks.getMatrixAt(i, m);
    m.decompose(p, q, s);
    const pick = i % 10;
    const kind = pick < 3 ? 'tree_giant' : pick < 6 ? 'tree_mid' : pick < 9 ? 'palm' : 'bush';
    const k = { tree_giant: 0.7, tree_mid: 1.1, palm: 1.05, bush: 1.8 }[kind] * s.x;
    kinds[kind].push(new THREE.Matrix4().compose(p.clone(), q.clone(), new THREE.Vector3(k, k * (s.y / s.x), k)));
  }
  // a fringe of bushes where the clearing meets the forest
  let seed = 41;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const fringe = Math.round(trunks.count * 0.35);
  for (let i = 0; i < fringe; i++) {
    const a = rnd() * Math.PI * 2;
    const d = ARENA.radius + 1.2 + rnd() * 3;
    const k = 1.3 + rnd() * 1.1;
    kinds.bush.push(new THREE.Matrix4().compose(new THREE.Vector3(Math.cos(a) * d, 0, Math.sin(a) * d),
      new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), rnd() * 6.28), new THREE.Vector3(k, k, k)));
  }
  for (const [name, mats] of Object.entries(kinds)) {
    if (!mats.length) continue;
    for (const part of parts(name)) {
      const inst = new THREE.InstancedMesh(part.geometry, part.material, mats.length);
      mats.forEach((mm, i) => inst.setMatrixAt(i, mm));
      inst.castShadow = quality.shadows;
      scene.add(inst);
    }
  }

  // ---- rocks along the edge of the clearing (too small to block anyone) ----
  for (let i = 0; i < 12; i++) {
    const a = rnd() * Math.PI * 2;
    const d = ARENA.radius - 1 + rnd() * 2.5;
    const rock = single(i % 3 ? 'rock_2' : 'rock_1');
    rock.position.set(Math.cos(a) * d, 0, Math.sin(a) * d);
    rock.rotation.y = rnd() * 6.28;
    rock.scale.setScalar(0.6 + rnd() * 0.7);
    scene.add(rock);
  }

  // ---- two round houses at the village side of the clearing, doors facing in ----
  for (const a of [0.69, 1.48]) {
    const r = ARENA.radius - 2.5;
    const x = Math.cos(a) * r;
    const z = Math.sin(a) * r;
    const hut = single('hut');
    hut.position.set(x, 0, z);
    hut.rotation.y = Math.atan2(-x, -z);
    scene.add(hut);
    obstacles.push({ x, z, r: 2.1 });
  }

  // ---- the crossroads shrine ----
  const { crossroads, brazier, forge } = world;
  for (const g of crossroads.gray) g.visible = false;
  crossroads.group.add(single('shrine'));

  // ---- the brazier: clay fire-pot on hearth stones; the flame sits in the pot ----
  for (const g of brazier.gray) g.visible = false;
  brazier.group.add(single('brazier'));
  brazier.flame.position.y = 1.4;
  brazier.flame.scale.setScalar(0.8);

  // ---- the forge, Sii's slit-drum, and Sii on top of it, drumming ----
  for (const g of forge.gray) g.visible = false;
  forge.group.add(single('forge'));
  const drum = single('slit_drum');
  drum.position.set(-1.8, 0, 0.6);
  forge.group.add(drum);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) obstacles.push({ x: forge.x + sx * 1.45, z: forge.z + sz * 1.25, r: 0.15 });
  let sii = null;
  if (models.sii) {
    sii = instantiate(models.sii, { lambert, scale: 1 });
    sii.object.position.set(-1.8, 0.97, 0.6);
    sii.object.rotation.y = Math.PI; // face the clearing
    forge.group.add(shadows(sii.object));
    sii.anim = new Animator(sii.root, sii.clips);
    sii.anim.play('Drum', { fade: 0 });
  }

  // ---- vine clumps where crawlers rise ----
  for (const spot of world.vines) {
    for (const c of spot.group.children) c.visible = false;
    const v = single('vine_clump');
    v.rotation.y = rnd() * 6.28;
    spot.group.add(v);
  }

  /** Pickup looks for projectiles.js. */
  const pickupTemplates = { rice: single('rice'), iron: single('iron') };

  return {
    pickupTemplates,
    update(dt) { sii?.anim.update(dt); },
  };
}
