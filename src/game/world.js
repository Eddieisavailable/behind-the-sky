// The clearing: ground, tree wall, crossroads, brazier, forge and vine clumps.
// Gray-box on purpose: plain shapes and flat colours, cheap to draw on a low-end phone.

import * as THREE from 'three';
import { ARENA } from '../config.js';

export const COLORS = {
  sky: 0x1d2b1f,
  ground: 0x3b5a2c,
  groundEdge: 0x24361d,
  path: 0x8b6a43,
  trunk: 0x3a2a1c,
  canopy: 0x22402a,
  canopyDark: 0x183020,
  stone: 0x6f6a60,
  bowl: 0xa0703f,
  iron: 0x8a96a3,
  fire: 0xe8742a,
  vine: 0x5b6a2e,
  rattan: 0xb08454,
  hero: 0xd9822b,
};

export function createRenderer(canvas, quality) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: quality.antialias,
    powerPreference: 'high-performance',
    stencil: false,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, quality.maxPixelRatio));
  renderer.setClearColor(COLORS.sky);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  if (quality.shadows) {
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  }
  return renderer;
}

/** Mark every mesh in an object as casting (and optionally receiving) real shadows. */
export function castShadows(obj, receive = false) {
  obj.traverse((o) => {
    if (o.isMesh && !o.userData.noShadow) {
      o.castShadow = true;
      if (receive) o.receiveShadow = true;
    }
  });
}

export function createWorld(quality) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(COLORS.sky);
  scene.fog = new THREE.Fog(COLORS.sky, quality.fogNear, quality.fogFar);

  scene.add(new THREE.HemisphereLight(0xcfe3c0, 0x2a2118, quality.shadows ? 1.3 : 1.6));
  const sun = new THREE.DirectionalLight(0xfff0d6, quality.shadows ? 2.1 : 1.5);
  sun.position.set(-12, 25, 10);
  scene.add(sun, sun.target);
  if (quality.shadows) {
    sun.castShadow = true;
    sun.shadow.mapSize.set(quality.shadowMapSize, quality.shadowMapSize);
    const c = sun.shadow.camera;
    c.left = -22; c.right = 22; c.top = 22; c.bottom = -22; c.near = 1; c.far = 70;
    sun.shadow.bias = -0.0006;
    sun.shadow.normalBias = 0.04;
  }

  const obstacles = []; // { x, z, r } circles the hero and crawlers can't walk through

  // Ground: the clearing and the darker forest floor around it
  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(ARENA.radius + 3, 48),
    new THREE.MeshLambertMaterial({ color: COLORS.ground }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = quality.shadows;
  scene.add(ground);
  const floor = new THREE.Mesh(
    new THREE.RingGeometry(ARENA.radius + 2.9, 80, 48, 1),
    new THREE.MeshLambertMaterial({ color: COLORS.groundEdge }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.01;
  scene.add(floor);

  addTrees(scene, quality);
  const crossroads = addCrossroads(scene, obstacles);
  const brazier = addBrazier(scene, obstacles);
  const forge = addForge(scene, obstacles);
  const vines = addVineClumps(scene, obstacles);
  if (quality.grass) addGrass(scene, quality.grass, obstacles);
  if (quality.shadows) for (const g of [crossroads.group, brazier.group, forge.group]) castShadows(g, true);

  /** Keep the sun's shadow box centred on the hero. */
  function followSun(x, z) {
    if (!quality.shadows) return;
    sun.position.set(x - 12, 25, z + 10);
    sun.target.position.set(x, 0, z);
  }

  return { scene, obstacles, crossroads, brazier, forge, vines, sun, followSun };
}

function addGrass(scene, count, obstacles) {
  // short blades: thin three-sided cones, tinted per instance
  const geo = new THREE.ConeGeometry(0.06, 0.45, 3);
  geo.translate(0, 0.22, 0);
  const mesh = new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ color: 0xffffff }), count);
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const e = new THREE.Euler();
  const s = new THREE.Vector3();
  const p = new THREE.Vector3();
  const c = new THREE.Color();
  const a1 = new THREE.Color(0x4f7a34);
  const a2 = new THREE.Color(0x2f4d22);
  let seed = 29;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  let i = 0;
  while (i < count) {
    const a = rnd() * Math.PI * 2;
    const d = Math.sqrt(rnd()) * (ARENA.radius + 2);
    const x = Math.cos(a) * d;
    const z = Math.sin(a) * d;
    if (obstacles.some((o) => Math.hypot(o.x - x, o.z - z) < o.r + 0.3)) continue;
    // keep the crossroads paths bare
    const cx = x - ARENA.crossroads.x;
    const cz = z - ARENA.crossroads.z;
    if ((Math.abs(cx) < 1.7 && cz < 2) || (Math.abs(cz) < 1.7 && Math.abs(cx) < 11)) continue;
    p.set(x, 0, z);
    q.setFromEuler(e.set((rnd() - 0.5) * 0.5, rnd() * Math.PI, (rnd() - 0.5) * 0.5));
    const k = 0.6 + rnd() * 0.9;
    s.set(k, k * (0.7 + rnd() * 0.8), k);
    m.compose(p, q, s);
    mesh.setMatrixAt(i, m);
    mesh.setColorAt(i, c.copy(a2).lerp(a1, rnd()));
    i += 1;
  }
  mesh.userData.noShadow = true;
  scene.add(mesh);
}

function addTrees(scene, quality) {
  const count = quality.trees;
  const trunkGeo = new THREE.CylinderGeometry(0.35, 0.55, 5, 6);
  trunkGeo.translate(0, 2.5, 0);
  const canopyGeo = new THREE.ConeGeometry(2.6, 7, 7);
  canopyGeo.translate(0, 7.5, 0);
  const trunks = new THREE.InstancedMesh(trunkGeo, new THREE.MeshLambertMaterial({ color: COLORS.trunk }), count);
  const canopies = new THREE.InstancedMesh(canopyGeo, new THREE.MeshLambertMaterial({ color: COLORS.canopy }), count);
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  const p = new THREE.Vector3();
  const dark = new THREE.Color(COLORS.canopyDark);
  const light = new THREE.Color(COLORS.canopy);
  const c = new THREE.Color();
  let i = 0;
  // Deterministic scatter so every phone sees the same forest
  let seed = 11;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  while (i < count) {
    const a = rnd() * Math.PI * 2;
    const d = ARENA.radius + 3.5 + Math.pow(rnd(), 0.7) * 26;
    // leave a gap in the tree wall behind the crossroads so the paths lead somewhere
    const gapAngle = Math.atan2(ARENA.crossroads.z, ARENA.crossroads.x);
    const da = Math.abs(Math.atan2(Math.sin(a - gapAngle), Math.cos(a - gapAngle)));
    if (da < 0.12 && d < ARENA.radius + 14) continue;
    const scale = 0.75 + rnd() * 0.7;
    p.set(Math.cos(a) * d, 0, Math.sin(a) * d);
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), rnd() * Math.PI);
    s.set(scale, scale * (0.85 + rnd() * 0.4), scale);
    m.compose(p, q, s);
    trunks.setMatrixAt(i, m);
    canopies.setMatrixAt(i, m);
    canopies.setColorAt(i, c.copy(dark).lerp(light, rnd()));
    i += 1;
  }
  if (quality.shadows) {
    trunks.castShadow = true;
    canopies.castShadow = true;
  }
  scene.add(trunks, canopies);
}

function addCrossroads(scene, obstacles) {
  const { x, z } = ARENA.crossroads;
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const pathMat = new THREE.MeshLambertMaterial({ color: COLORS.path });
  const a = new THREE.Mesh(new THREE.PlaneGeometry(3, 26), pathMat);
  a.rotation.x = -Math.PI / 2;
  a.position.set(0, 0.02, -6);
  const b = new THREE.Mesh(new THREE.PlaneGeometry(22, 3), pathMat);
  b.rotation.x = -Math.PI / 2;
  b.position.set(0, 0.02, 0);
  group.add(a, b);
  // offering stone with a bowl on it
  const stone = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 1.1, 0.8, 8), new THREE.MeshLambertMaterial({ color: COLORS.stone }));
  stone.position.y = 0.4;
  const bowl = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 10, 6, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2),
    new THREE.MeshLambertMaterial({ color: COLORS.bowl, side: THREE.DoubleSide }),
  );
  bowl.position.y = 1.35;
  group.add(stone, bowl);
  // a glow ring that lights up when you owe and stand close
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(2.4, 2.8, 32),
    new THREE.MeshBasicMaterial({ color: 0xf2b33d, transparent: true, opacity: 0, depthWrite: false }),
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.04;
  group.add(ring);
  scene.add(group);
  obstacles.push({ x, z, r: 1.1 });
  return { x, z, group, ring, interactRange: 3.6 };
}

function addBrazier(scene, obstacles) {
  const { x, z } = ARENA.brazier;
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.45, 1, 8), new THREE.MeshLambertMaterial({ color: COLORS.iron }));
  pot.position.y = 0.5;
  const flame = new THREE.Mesh(new THREE.ConeGeometry(0.5, 1.2, 7), new THREE.MeshBasicMaterial({ color: COLORS.fire }));
  flame.position.y = 1.6;
  const light = new THREE.PointLight(0xff9a4a, 14, 12, 1.6);
  light.position.y = 2.2;
  group.add(pot, flame, light);
  scene.add(group);
  obstacles.push({ x, z, r: 0.8 });
  return { x, z, group, flame, light, refillRange: 2.6 };
}

function addForge(scene, obstacles) {
  const { x, z } = ARENA.forge;
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const ironMat = new THREE.MeshLambertMaterial({ color: 0x4a4f55 });
  const anvilBase = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 0.6), ironMat);
  anvilBase.position.y = 0.4;
  const anvilTop = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.35, 0.7), ironMat);
  anvilTop.position.y = 0.95;
  // Sii's slit-drum: a hollow log on its side, and Sii (a round dark body)
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 1.8, 10), new THREE.MeshLambertMaterial({ color: 0x6b4a2a }));
  drum.rotation.z = Math.PI / 2;
  drum.position.set(-1.8, 0.45, 0.6);
  const sii = new THREE.Mesh(new THREE.SphereGeometry(0.35, 10, 8), new THREE.MeshLambertMaterial({ color: 0x1c1410 }));
  sii.position.set(-1.8, 1.05, 0.6);
  const fireBed = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.9, 0.4, 8), new THREE.MeshBasicMaterial({ color: 0x9c3e16 }));
  fireBed.position.set(1.6, 0.2, -0.4);
  group.add(anvilBase, anvilTop, drum, sii, fireBed);
  scene.add(group);
  obstacles.push({ x, z, r: 1.2 }, { x: x - 1.8, z: z + 0.6, r: 0.8 }, { x: x + 1.6, z: z - 0.4, r: 0.9 });
  return { x, z, group, sii, interactRange: 3.4 };
}

function addVineClumps(scene, obstacles) {
  const spots = [];
  const n = 8;
  const mat = new THREE.MeshLambertMaterial({ color: COLORS.vine });
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + 0.3;
    const d = ARENA.radius - 3.5;
    const x = Math.cos(a) * d;
    const z = Math.sin(a) * d;
    // keep clumps off the crossroads, forge and brazier
    if (Math.hypot(x - ARENA.crossroads.x, z - ARENA.crossroads.z) < 7) continue;
    if (Math.hypot(x - ARENA.forge.x, z - ARENA.forge.z) < 5) continue;
    if (Math.hypot(x - ARENA.brazier.x, z - ARENA.brazier.z) < 5) continue;
    const clump = new THREE.Group();
    clump.position.set(x, 0, z);
    for (let k = 0; k < 5; k++) {
      const h = 1.2 + ((k * 37) % 10) / 10;
      const stalk = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.12, h, 5), mat);
      const ka = (k / 5) * Math.PI * 2;
      stalk.position.set(Math.cos(ka) * 0.45, h / 2, Math.sin(ka) * 0.45);
      stalk.rotation.z = Math.cos(ka) * 0.35;
      stalk.rotation.x = Math.sin(ka) * 0.35;
      clump.add(stalk);
    }
    scene.add(clump);
    obstacles.push({ x, z, r: 0.6 });
    spots.push({ x, z });
  }
  return spots;
}

/** Push a circle (x, z, r) out of obstacles and keep it inside the clearing. */
export function resolveCollisions(pos, r, obstacles) {
  for (const o of obstacles) {
    const dx = pos.x - o.x;
    const dz = pos.z - o.z;
    const d = Math.hypot(dx, dz);
    const min = o.r + r;
    if (d < min && d > 1e-4) {
      pos.x = o.x + (dx / d) * min;
      pos.z = o.z + (dz / d) * min;
    }
  }
  const d = Math.hypot(pos.x, pos.z);
  const lim = ARENA.radius - r;
  if (d > lim) {
    pos.x *= lim / d;
    pos.z *= lim / d;
  }
}
