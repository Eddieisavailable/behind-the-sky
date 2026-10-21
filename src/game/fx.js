// Cheap pooled particles: red blood for people, green sap for rattan, sparks for iron and fire.

import * as THREE from 'three';

const MAX = 400;

export const PALETTE = {
  blood: [0.75, 0.08, 0.06],
  sap: [0.45, 0.72, 0.2],
  spark: [1.0, 0.75, 0.35],
  fire: [0.95, 0.45, 0.12],
  ash: [0.35, 0.33, 0.3],
  rice: [0.95, 0.92, 0.82],
};

export function createFx(scene) {
  const positions = new Float32Array(MAX * 3);
  const colors = new Float32Array(MAX * 3);
  const vel = new Float32Array(MAX * 3);
  const life = new Float32Array(MAX);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const mat = new THREE.PointsMaterial({ size: 0.22, vertexColors: true, sizeAttenuation: true, depthWrite: false });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  scene.add(points);
  let cursor = 0;

  for (let i = 0; i < MAX; i++) positions[i * 3 + 1] = -100; // parked below the ground

  function burst(x, y, z, kind, n = 12, speed = 4) {
    const c = PALETTE[kind] ?? PALETTE.spark;
    for (let k = 0; k < n; k++) {
      const i = cursor;
      cursor = (cursor + 1) % MAX;
      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;
      const a = Math.random() * Math.PI * 2;
      const up = 0.4 + Math.random();
      const sp = speed * (0.4 + Math.random() * 0.8);
      vel[i * 3] = Math.cos(a) * sp;
      vel[i * 3 + 1] = up * speed * 0.8;
      vel[i * 3 + 2] = Math.sin(a) * sp;
      colors[i * 3] = c[0];
      colors[i * 3 + 1] = c[1];
      colors[i * 3 + 2] = c[2];
      life[i] = 0.5 + Math.random() * 0.4;
    }
  }

  function update(dt) {
    for (let i = 0; i < MAX; i++) {
      if (life[i] <= 0) continue;
      life[i] -= dt;
      vel[i * 3 + 1] -= 14 * dt;
      positions[i * 3] += vel[i * 3] * dt;
      positions[i * 3 + 1] += vel[i * 3 + 1] * dt;
      positions[i * 3 + 2] += vel[i * 3 + 2] * dt;
      if (positions[i * 3 + 1] < 0.03) {
        // land and stain the ground briefly
        positions[i * 3 + 1] = 0.03;
        vel[i * 3] *= 0.2; vel[i * 3 + 1] = 0; vel[i * 3 + 2] *= 0.2;
      }
      if (life[i] <= 0) positions[i * 3 + 1] = -100;
    }
    geo.attributes.position.needsUpdate = true;
    geo.attributes.color.needsUpdate = true;
  }

  return { burst, update };
}

const shadowGeo = new THREE.CircleGeometry(1, 16);
const shadowMat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.32, depthWrite: false });

/** A soft dark disc under a character, instead of real shadows. */
export function blobShadow(radius) {
  const m = new THREE.Mesh(shadowGeo, shadowMat);
  m.rotation.x = -Math.PI / 2;
  m.position.y = 0.02;
  m.scale.setScalar(radius);
  m.userData.noShadow = true;
  m.userData.blob = true;
  return m;
}
