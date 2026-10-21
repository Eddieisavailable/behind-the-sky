// The Hornbill Genie in the clearing. It waits on a carved post by the crossroads shrine.
// When Korto (or Flomo) borrows its sight, it takes off and circles above the hero
// until the sight runs out, then flies home. It calls when an offering is paid.
// Without the Blender model (models failed to load) none of this exists.

import * as THREE from 'three';
import { HORNBILL_BIRD as B } from '../config.js';
import { instantiate, Animator } from './models.js';

export function createHornbill(world, models, quality) {
  if (!models?.hornbill) return { update() {}, call() {}, pos: null };
  const { scene, crossroads } = world;
  const lambert = quality.key !== 'high';

  // the carved perch post: a dark hardwood pole with a crossbar, pegged into the ground
  const post = new THREE.Group();
  const wood = new THREE.MeshLambertMaterial({ color: 0x3e2716, flatShading: true });
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.13, B.perch.height, 7), wood);
  pole.position.y = B.perch.height / 2;
  const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.7, 6), wood);
  bar.rotation.z = Math.PI / 2;
  bar.position.y = B.perch.height - 0.03;
  const band = new THREE.Mesh(new THREE.CylinderGeometry(0.105, 0.105, 0.08, 7), new THREE.MeshLambertMaterial({ color: 0xc58a2c, flatShading: true }));
  band.position.y = B.perch.height * 0.62;
  post.add(pole, bar, band);
  const home = new THREE.Vector3(crossroads.x + B.perch.dx, B.perch.height, crossroads.z + B.perch.dz);
  post.position.set(home.x, 0, home.z);
  if (quality.shadows) post.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  scene.add(post);
  world.obstacles.push({ x: home.x, z: home.z, r: 0.25 });

  const model = instantiate(models.hornbill, { lambert, scale: B.scale });
  model.object.position.copy(home);
  if (quality.shadows) model.object.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  scene.add(model.object);
  const anim = new Animator(model.root, model.clips);
  anim.play('Perch', { fade: 0 });

  // face the clearing while it waits
  const restYaw = Math.atan2(-(0 - home.x), -(0 - home.z));
  model.object.rotation.y = restYaw;

  const pos = model.object.position;
  const vel = new THREE.Vector3();
  const target = new THREE.Vector3();
  let state = 'perched';       // perched | out | circling | home
  let angle = 0;
  let callLeft = 0;
  let glideClock = 0;

  function call() {
    if (state !== 'perched') return;
    anim.play('Call', { once: true, fade: 0.1, restart: true });
    callLeft = 0.9;
  }

  /**
   * sight: is the Hornbill's sight lent right now; hero: who it watches over;
   * camera: the player's view (it circles a little ahead of the hero so it stays on screen).
   */
  const ahead = new THREE.Vector3();
  function update(dt, { sight, hero, camera }) {
    if (sight && (state === 'perched' || state === 'home')) {
      state = 'out';
      angle = hero ? Math.atan2(pos.z - hero.pos.z, pos.x - hero.pos.x) : 0;
    }
    if (!sight && (state === 'out' || state === 'circling')) state = 'home';

    if (state === 'perched') {
      if (callLeft > 0 && (callLeft -= dt) <= 0) anim.play('Perch', { fade: 0.3 });
      // settle the yaw back toward the clearing
      model.object.rotation.y += angleDiff(restYaw, model.object.rotation.y) * Math.min(1, dt * 3);
      anim.update(dt);
      return;
    }

    if (state === 'out' || state === 'circling') {
      angle += B.circleSpeed * dt;
      ahead.set(0, 0, 0);
      if (camera) { camera.getWorldDirection(ahead); ahead.y = 0; ahead.normalize().multiplyScalar(B.circleAhead); }
      const cx = (hero ? hero.pos.x : 0) + ahead.x;
      const cz = (hero ? hero.pos.z : 0) + ahead.z;
      target.set(cx + Math.cos(angle) * B.circleRadius, B.flyHeight, cz + Math.sin(angle) * B.circleRadius);
    } else {
      target.copy(home);
    }

    const to = target.clone().sub(pos);
    const dist = to.length();
    if (state === 'out' && dist < 1.5) state = 'circling';
    if (state === 'home' && dist < 0.08) {
      pos.copy(home);
      vel.set(0, 0, 0);
      state = 'perched';
      anim.play('Perch', { fade: 0.35 });
      anim.update(dt);
      return;
    }

    // steer: approach fast, ease in when arriving home
    const speed = state === 'home' ? Math.min(B.speed, 0.6 + dist * 2.2) : B.speed;
    const want = to.multiplyScalar(speed / Math.max(dist, 1e-4));
    vel.lerp(want, Math.min(1, dt * 3.5));
    pos.addScaledVector(vel, dt);

    // face where it's going; beat the wings when climbing or travelling, glide on the circle
    if (Math.hypot(vel.x, vel.z) > 0.3) {
      const yaw = Math.atan2(-vel.x, -vel.z);
      model.object.rotation.y += angleDiff(yaw, model.object.rotation.y) * Math.min(1, dt * 6);
    }
    glideClock += dt;
    const climbing = vel.y > 0.6 || (state !== 'circling' && dist > 2);
    const flap = climbing || glideClock % 4 < 1.2;   // a few beats, then a long glide
    anim.play(flap ? 'Fly' : 'Glide', { fade: 0.4 });
    anim.update(dt);
  }

  return { update, call, pos, get state() { return state; } };
}

function angleDiff(a, b) {
  let d = a - b;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return d;
}
