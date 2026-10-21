// Korto: movement, roll, cutlass swings and the bow. Combat results are worked
// out in game.js; this file owns the body and how it moves.

import * as THREE from 'three';
import { HERO, BOW } from '../config.js';
import { COLORS } from './world.js';
import { blobShadow } from './fx.js';
import { createCombo } from '../rules/combo.js';

export function createHero(scene) {
  const group = new THREE.Group();
  const bodyMat = new THREE.MeshLambertMaterial({ color: COLORS.hero, emissive: 0x000000 });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.42, 0.9, 4, 10), bodyMat);
  body.position.y = 0.88;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.3, 12, 10), new THREE.MeshLambertMaterial({ color: 0x5a3a22 }));
  head.position.set(0, 1.78, 0);
  // headwrap knot so you can tell which way she faces
  const wrap = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.3, 6), new THREE.MeshLambertMaterial({ color: 0xc8382d }));
  wrap.rotation.x = -Math.PI / 2;
  wrap.position.set(0, 1.82, 0.32);
  const nose = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.16, 0.2), new THREE.MeshLambertMaterial({ color: 0x5a3a22 }));
  nose.position.set(0, 1.74, -0.3);

  // cutlass on a pivot at the right hand
  const pivot = new THREE.Group();
  pivot.position.set(0.45, 1.05, 0);
  const blade = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.06, 1.25), new THREE.MeshLambertMaterial({ color: 0xc9d1d8, emissive: 0x000000 }));
  blade.position.z = -0.75;
  const hilt = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.25), new THREE.MeshLambertMaterial({ color: 0x3a2a1c }));
  hilt.position.z = -0.05;
  pivot.add(blade, hilt);
  pivot.rotation.y = 0.6;

  // bow on the left side, shown while drawing
  const bow = new THREE.Mesh(
    new THREE.TorusGeometry(0.55, 0.035, 4, 14, Math.PI),
    new THREE.MeshLambertMaterial({ color: 0x6b4a2a }),
  );
  bow.rotation.set(0, 0, Math.PI / 2);
  bow.position.set(-0.1, 1.15, -0.45);
  bow.visible = false;

  group.add(body, head, wrap, nose, pivot, bow, blobShadow(0.6));
  scene.add(group);

  // aim guide: a thin strip on the ground
  const aim = new THREE.Mesh(
    new THREE.PlaneGeometry(0.12, 1),
    new THREE.MeshBasicMaterial({ color: 0xf2b33d, transparent: true, opacity: 0.55, depthWrite: false }),
  );
  aim.rotation.x = -Math.PI / 2;
  aim.visible = false;
  scene.add(aim);

  return {
    group, body, bodyMat, pivot, blade, bow, aim,
    pos: new THREE.Vector3(0, 0, 4),
    facing: new THREE.Vector2(0, -1),   // unit vector on the ground (x, z)
    health: HERO.health,
    maxHealth: HERO.health,
    radius: HERO.radius,
    dodgeLeft: 0,
    dodgeDir: new THREE.Vector2(),
    dodgeCooldown: 0,
    invulnerable: 0,
    hurtFlash: 0,
    combo: createCombo(),
    drawing: false,
    drawTime: 0,
    arrowKind: 'iron',
    fireArrows: BOW.fireArrowsMax,
    walkPhase: 0,
  };
}

export function faceToward(h, dx, dz) {
  const len = Math.hypot(dx, dz);
  if (len > 1e-4) h.facing.set(dx / len, dz / len);
}

/** Update pose: position, facing, bob, cutlass swing, bow and aim guide. */
export function poseHero(h, dt, { moving, aimDir, aimLength }) {
  h.group.position.copy(h.pos);
  h.group.rotation.y = Math.atan2(-h.facing.x, -h.facing.y);

  if (moving && h.dodgeLeft <= 0) h.walkPhase += dt * 11;
  const bob = moving ? Math.abs(Math.sin(h.walkPhase)) * 0.08 : 0;
  h.body.position.y = 0.88 + bob;
  h.body.rotation.x = h.dodgeLeft > 0 ? -1.0 : 0;
  h.body.scale.y = h.dodgeLeft > 0 ? 0.7 : 1;

  // cutlass: sweep across depending on which blow of the combo
  const c = h.combo;
  if (c.step >= 0) {
    const t = Math.min(1, c.t / c.cfg.duration[c.step]);
    const e = 1 - Math.pow(1 - t, 3);
    if (c.step === 0) h.pivot.rotation.set(0, THREE.MathUtils.lerp(1.3, -1.3, e), 0);
    else if (c.step === 1) h.pivot.rotation.set(0, THREE.MathUtils.lerp(-1.3, 1.3, e), 0);
    else h.pivot.rotation.set(THREE.MathUtils.lerp(-1.4, 0.3, e), 0, 0); // overhead chop
    h.blade.material.emissive.setHex(0x333333);
  } else {
    h.pivot.rotation.set(0, 0.6, 0);
    h.blade.material.emissive.setHex(0x000000);
  }

  h.bow.visible = h.drawing;
  h.aim.visible = h.drawing;
  if (h.drawing && aimDir) {
    const len = aimLength;
    h.aim.scale.set(1, len, 1);
    h.aim.position.set(h.pos.x + aimDir.x * (len / 2 + 0.5), 0.05, h.pos.z + aimDir.y * (len / 2 + 0.5));
    h.aim.rotation.set(-Math.PI / 2, 0, Math.atan2(-aimDir.x, -aimDir.y));
    h.aim.material.color.setHex(h.arrowKind === 'fire' ? 0xe8742a : 0xf2b33d);
  }

  if (h.hurtFlash > 0) {
    h.hurtFlash = Math.max(0, h.hurtFlash - dt);
    h.bodyMat.emissive.setRGB(h.hurtFlash * 2, 0, 0);
  } else {
    h.bodyMat.emissive.setRGB(0, 0, 0);
  }
  // blink while invulnerable after a hit
  h.group.visible = !(h.invulnerable > 0 && h.dodgeLeft <= 0 && Math.floor(h.invulnerable * 20) % 2 === 0);
}
