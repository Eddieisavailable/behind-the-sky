// The hero (Korto or Flomo): movement, roll, cutlass swings and the bow. Combat results are worked
// out in game.js; this file owns the body and how it moves.

import * as THREE from 'three';
import { HERO, HEROES, BOW } from '../config.js';
import { COLORS } from './world.js';
import { blobShadow } from './fx.js';
import { createCombo } from '../rules/combo.js';
import { instantiate, Animator, setGlow } from './models.js';

export function createHero(scene, models = null, quality = {}, kind = HEROES.korto) {
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

  // the Blender model replaces the gray-box shapes when it loaded
  let model = null;
  let anim = null;
  let bowNode = null;
  const gltf = models?.[kind.key] ?? models?.korto;
  if (gltf) {
    model = instantiate(gltf, { lambert: quality.key !== 'high', scale: kind.scale });
    group.add(model.object);
    for (const part of [body, head, wrap, nose, pivot, bow]) part.visible = false;
    anim = new Animator(model.root, model.clips);
    bowNode = model.root.getObjectByName('Bow');
    if (bowNode) bowNode.visible = false;
    anim.play('Idle');
  }

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
    model, anim, bowNode,
    hurtAnim: 0,
    burnAnim: 0,
    dead: false,
    animStep: -1,
    pos: new THREE.Vector3(0, 0, 4),
    facing: new THREE.Vector2(0, -1),   // unit vector on the ground (x, z)
    kind,
    name: kind.name,
    speed: kind.speed,
    damage: kind.damage,
    health: kind.health,
    maxHealth: kind.health,
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

/** Pick the animation for what the hero is doing right now. */
function animateModel(h, dt, moving, speedFactor) {
  const a = h.anim;
  const c = h.combo;
  h.hurtAnim = Math.max(0, h.hurtAnim - dt);
  h.burnAnim = Math.max(0, h.burnAnim - dt);
  if (h.dead) a.play('Death', { once: true, fade: 0.1 });
  else if (h.dodgeLeft > 0) a.play('Roll', { once: true, fade: 0.05, seconds: 0.3 });
  else if (c.step >= 0) {
    const name = `Slash${c.step + 1}`;
    a.play(name, { once: true, fade: 0.06, seconds: c.cfg.duration[c.step], restart: h.animStep !== c.step });
    h.animStep = c.step;
  } else if (h.burnAnim > 0) a.play('Burn', { once: true, fade: 0.06, seconds: 0.4 });
  else if (h.drawing) a.play('Draw', { once: true, fade: 0.1, seconds: 0.3 });
  else if (h.hurtAnim > 0) a.play('Hurt', { once: true, fade: 0.05, seconds: 0.3 });
  else if (moving) a.play('Run', { timeScale: Math.max(0.6, speedFactor) * 1.1, fade: 0.15 });
  else a.play('Idle', { fade: 0.2 });
  if (c.step < 0) h.animStep = -1;
  if (h.bowNode) h.bowNode.visible = h.drawing;
  a.update(dt);
}

/** Update pose: position, facing, bob, cutlass swing, bow and aim guide. */
export function poseHero(h, dt, { moving, aimDir, aimLength, speedFactor = 1 }) {
  h.group.position.copy(h.pos);
  h.group.rotation.y = Math.atan2(-h.facing.x, -h.facing.y);
  if (h.anim) {
    animateModel(h, dt, moving, speedFactor);
    poseAim(h, aimDir, aimLength);
    if (h.hurtFlash > 0) h.hurtFlash = Math.max(0, h.hurtFlash - dt);
    setGlow(h.model.materials, h.hurtFlash * 2.5, 0, 0);
    h.group.visible = !(h.invulnerable > 0 && h.dodgeLeft <= 0 && !h.dead && Math.floor(h.invulnerable * 20) % 2 === 0);
    return;
  }

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
  poseAim(h, aimDir, aimLength);

  if (h.hurtFlash > 0) {
    h.hurtFlash = Math.max(0, h.hurtFlash - dt);
    h.bodyMat.emissive.setRGB(h.hurtFlash * 2, 0, 0);
  } else {
    h.bodyMat.emissive.setRGB(0, 0, 0);
  }
  // blink while invulnerable after a hit
  h.group.visible = !(h.invulnerable > 0 && h.dodgeLeft <= 0 && Math.floor(h.invulnerable * 20) % 2 === 0);
}

function poseAim(h, aimDir, aimLength) {
  h.aim.visible = h.drawing && !!aimDir;
  if (!h.aim.visible) return;
  const len = aimLength;
  h.aim.scale.set(1, len, 1);
  h.aim.position.set(h.pos.x + aimDir.x * (len / 2 + 0.5), 0.05, h.pos.z + aimDir.y * (len / 2 + 0.5));
  h.aim.rotation.set(-Math.PI / 2, 0, Math.atan2(-aimDir.x, -aimDir.y));
  h.aim.material.color.setHex(h.arrowKind === 'fire' ? 0xe8742a : 0xf2b33d);
}
