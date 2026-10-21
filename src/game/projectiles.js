// Arrows (iron and fire) and pickups (rice and iron scrap).

import * as THREE from 'three';
import { BOW, DROPS } from '../config.js';

const shaftGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.9, 4);
shaftGeo.rotateX(Math.PI / 2);
const tipGeo = new THREE.ConeGeometry(0.07, 0.2, 4);
tipGeo.rotateX(-Math.PI / 2);
tipGeo.translate(0, 0, -0.5);
const ironMat = new THREE.MeshBasicMaterial({ color: 0xd8dde2 });
const fireMat = new THREE.MeshBasicMaterial({ color: 0xff8a3a });
const woodMat = new THREE.MeshBasicMaterial({ color: 0x7a5530 });

export function createArrows(scene) {
  const list = [];
  const pool = [];

  function take(kind) {
    let a = pool.pop();
    if (!a) {
      const g = new THREE.Group();
      const shaft = new THREE.Mesh(shaftGeo, woodMat);
      const tip = new THREE.Mesh(tipGeo, ironMat);
      g.add(shaft, tip);
      a = { group: g, tip };
      scene.add(g);
    }
    a.group.visible = true;
    a.tip.material = kind === 'fire' ? fireMat : ironMat;
    return a;
  }

  function fire({ x, z, dir, kind, damage }) {
    const a = take(kind);
    a.kind = kind;
    a.damage = damage;
    a.dir = dir.clone().normalize();
    a.pos = new THREE.Vector3(x + a.dir.x * 0.6, 1.1, z + a.dir.y * 0.6);
    a.travelled = 0;
    a.group.position.copy(a.pos);
    a.group.rotation.y = Math.atan2(-a.dir.x, -a.dir.y);
    list.push(a);
  }

  /** Move arrows; call hitTest(arrow) → true when it struck something. */
  function update(dt, hitTest, onTrail) {
    for (let i = list.length - 1; i >= 0; i--) {
      const a = list[i];
      const step = BOW.arrowSpeed * dt;
      // sub-step so fast arrows don't skip through a crawler
      const n = Math.max(1, Math.ceil(step / 0.4));
      let done = false;
      for (let k = 0; k < n && !done; k++) {
        a.pos.x += a.dir.x * (step / n);
        a.pos.z += a.dir.y * (step / n);
        a.travelled += step / n;
        if (hitTest(a)) done = true;
      }
      if (a.kind === 'fire' && onTrail && Math.random() < 0.5) onTrail(a.pos);
      a.group.position.copy(a.pos);
      if (done || a.travelled > BOW.maxRange) {
        a.group.visible = false;
        pool.push(a);
        list.splice(i, 1);
      }
    }
  }

  function clear() {
    for (const a of list) { a.group.visible = false; pool.push(a); }
    list.length = 0;
  }

  return { fire, update, clear, list };
}

const riceGeo = new THREE.SphereGeometry(0.18, 6, 5);
const riceMat = new THREE.MeshLambertMaterial({ color: 0xf4ecd4, emissive: 0x2a2620 });
const ironGeo = new THREE.BoxGeometry(0.3, 0.12, 0.22);
const scrapMat = new THREE.MeshLambertMaterial({ color: 0x8a96a3, emissive: 0x1a1d20 });

export function createPickups(scene, templates = null) {
  const list = [];

  function drop(x, z, kind) {
    const tpl = templates?.[kind];
    const mesh = tpl ? tpl.clone() : new THREE.Mesh(kind === 'rice' ? riceGeo : ironGeo, kind === 'rice' ? riceMat : scrapMat);
    if (tpl) mesh.scale.setScalar(1.4); // a bit larger than life so they're easy to spot
    const a = Math.random() * Math.PI * 2;
    const p = { kind, mesh, tpl, pos: new THREE.Vector3(x, 0.3, z), vel: new THREE.Vector3(Math.cos(a) * 2.5, 4, Math.sin(a) * 2.5), t: 0 };
    mesh.position.copy(p.pos);
    scene.add(mesh);
    list.push(p);
  }

  /** Bounce, drift toward the hero when close, collect. Returns kinds collected this frame. */
  function update(dt, hero) {
    const got = [];
    for (let i = list.length - 1; i >= 0; i--) {
      const p = list[i];
      p.t += dt;
      p.vel.y -= 16 * dt;
      p.pos.addScaledVector(p.vel, dt);
      const floor = p.tpl ? 0.02 : 0.2;
      if (p.pos.y < floor) { p.pos.y = floor; p.vel.y = Math.abs(p.vel.y) * 0.3; p.vel.x *= 0.6; p.vel.z *= 0.6; }
      const dx = hero.pos.x - p.pos.x;
      const dz = hero.pos.z - p.pos.z;
      const d = Math.hypot(dx, dz);
      if (p.t > 0.35 && d < DROPS.magnetRadius) {
        const pull = 10 * (1 - d / DROPS.magnetRadius) + 3;
        p.pos.x += (dx / d) * pull * dt;
        p.pos.z += (dz / d) * pull * dt;
      }
      p.mesh.position.copy(p.pos);
      p.mesh.rotation.y += dt * 3;
      if (p.t > 0.35 && d < DROPS.pickupRadius) {
        scene.remove(p.mesh);
        list.splice(i, 1);
        got.push(p.kind);
      }
    }
    return got;
  }

  function clear() {
    for (const p of list) scene.remove(p.mesh);
    list.length = 0;
  }

  return { drop, update, clear, list };
}
