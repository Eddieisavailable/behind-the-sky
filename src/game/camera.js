// Third-person camera: sits behind the hero, the player drags to look around,
// and it drifts back behind the hero while running.

import * as THREE from 'three';
import { ARENA, CAMERA } from '../config.js';

export function createCameraRig(camera) {
  const rig = {
    camera,
    yaw: 0,                 // 0 = camera south of the hero, looking north
    pitch: CAMERA.pitch,
    dist: CAMERA.distance,
    sinceLook: 99,          // seconds since the player last dragged the view
    target: new THREE.Vector3(),
    desired: new THREE.Vector3(),
  };
  return rig;
}

/** Ground-plane forward (where the camera looks) and right vectors. */
export function cameraBasis(rig) {
  return {
    fx: -Math.sin(rig.yaw), fz: -Math.cos(rig.yaw),
    rx: Math.cos(rig.yaw), rz: -Math.sin(rig.yaw),
  };
}

/** Turn a stick (x right, z down the screen) into a world direction on the ground. */
export function stickToWorld(rig, sx, sz) {
  const b = cameraBasis(rig);
  return { x: b.rx * sx - b.fx * sz, z: b.rz * sx - b.fz * sz };
}

export function look(rig, dx, dy) {
  if (!dx && !dy) return;
  rig.yaw -= dx * CAMERA.sensitivity;
  rig.pitch = THREE.MathUtils.clamp(rig.pitch + dy * CAMERA.sensitivity, CAMERA.minPitch, CAMERA.maxPitch);
  rig.sinceLook = 0;
}

const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));

/**
 * @param hero    { pos: Vector3, facing: Vector2 }
 * @param opts    { moving, aiming, snap }
 */
export function updateRig(rig, dt, hero, { moving = false, aiming = false, snap = false } = {}) {
  rig.sinceLook += dt;

  // drift behind the hero while running forward or sideways, unless the player is steering the view
  if (moving && !aiming && rig.sinceLook > CAMERA.followDelay) {
    const behind = Math.atan2(-hero.facing.x, -hero.facing.y);
    const diff = wrap(behind - rig.yaw);
    if (Math.abs(diff) < (Math.PI * 3) / 4) rig.yaw += diff * Math.min(1, dt * CAMERA.followRate);
  }

  const wantDist = aiming ? CAMERA.aimDistance : CAMERA.distance;
  rig.dist += (wantDist - rig.dist) * Math.min(1, dt * 8);

  rig.target.set(hero.pos.x, CAMERA.height, hero.pos.z);
  // keep the camera out of the tree wall: pull in when it would leave the clearing
  let d = rig.dist;
  const cp = Math.cos(rig.pitch);
  for (let i = 0; i < 12; i++) {
    const x = hero.pos.x + Math.sin(rig.yaw) * cp * d;
    const z = hero.pos.z + Math.cos(rig.yaw) * cp * d;
    if (Math.hypot(x, z) <= ARENA.radius + CAMERA.edgeAllowance || d <= CAMERA.minDistance) break;
    d -= 0.4;
  }
  rig.desired.set(
    hero.pos.x + Math.sin(rig.yaw) * cp * d,
    CAMERA.height + Math.sin(rig.pitch) * d,
    hero.pos.z + Math.cos(rig.yaw) * cp * d,
  );

  const k = snap ? 1 : 1 - Math.exp(-dt * 14);
  rig.camera.position.lerp(rig.desired, k);
  // look a little over the right shoulder so the hero doesn't block the centre of the screen
  const b = cameraBasis(rig);
  rig.camera.lookAt(rig.target.x + b.rx * CAMERA.shoulder + b.fx * 2, rig.target.y + 0.2, rig.target.z + b.rz * CAMERA.shoulder + b.fz * 2);
}
