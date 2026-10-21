// Rattan crawlers: bodies, movement and attacks. Their life cycle (downed,
// regrowing, burning, burned) lives in rules/crawlerLife.js.

import * as THREE from 'three';
import { CRAWLER } from '../config.js';
import { COLORS } from './world.js';
import { blobShadow } from './fx.js';
import { createLife, tickLife, regrowProgress, isActive } from '../rules/crawlerLife.js';
import { instantiate, Animator, setGlow, setShade } from './models.js';

const segGeo = new THREE.CapsuleGeometry(0.28, 0.35, 3, 8);
const headGeo = new THREE.SphereGeometry(0.3, 10, 8);
const eyeGeo = new THREE.SphereGeometry(0.06, 6, 4);
const eyeMat = new THREE.MeshBasicMaterial({ color: 0xffd76a });
const postGeo = new THREE.CylinderGeometry(0.1, 0.16, 2.2, 6);
const thornGeo = new THREE.ConeGeometry(0.07, 0.3, 4);

let nextId = 1;

export function createCrawler(scene, x, z, { disguised = false, speed = CRAWLER.speed, models = null, quality = {} } = {}) {
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const mat = new THREE.MeshLambertMaterial({ color: COLORS.rattan, emissive: 0x000000 });
  const body = new THREE.Group();
  const segs = [];
  for (let i = 0; i < 3; i++) {
    const s = new THREE.Mesh(segGeo, mat);
    s.position.y = 0.4 + i * 0.5;
    s.rotation.z = (i - 1) * 0.25;
    body.add(s);
    segs.push(s);
    for (let k = 0; k < 2; k++) {
      const thorn = new THREE.Mesh(thornGeo, mat);
      const a = (k + i * 0.5) * Math.PI;
      thorn.position.set(Math.cos(a) * 0.3, 0.45 + i * 0.5, Math.sin(a) * 0.3);
      thorn.rotation.z = -Math.cos(a) * 1.3;
      thorn.rotation.x = Math.sin(a) * 1.3;
      body.add(thorn);
    }
  }
  const head = new THREE.Mesh(headGeo, mat);
  head.position.y = 1.85;
  const eyeL = new THREE.Mesh(eyeGeo, eyeMat);
  eyeL.position.set(-0.12, 1.9, -0.25);
  const eyeR = eyeL.clone();
  eyeR.position.x = 0.12;
  body.add(head, eyeL, eyeR);

  // the disguise: a plain vine post, same colour as the clumps
  const post = new THREE.Mesh(postGeo, new THREE.MeshLambertMaterial({ color: COLORS.vine, emissive: 0x000000 }));
  post.position.y = 1.1;
  post.visible = disguised;
  body.visible = !disguised;

  const shadow = blobShadow(0.55);
  group.add(body, post, shadow);
  scene.add(group);

  // the Blender model replaces the gray-box body when it loaded
  let model = null;
  let anim = null;
  if (models?.crawler) {
    model = instantiate(models.crawler, { lambert: quality.key !== 'high' });
    group.add(model.object);
    body.visible = false;
    model.object.visible = !disguised;
    anim = new Animator(model.root, model.clips);
    anim.play('Idle', { fade: 0 });
  }

  return {
    id: nextId++,
    group, body, post, mat, shadow,
    model, anim,
    moving: false,
    strikeAnim: 0,
    pos: group.position,
    vel: new THREE.Vector2(),
    life: createLife(CRAWLER, { disguised }),
    speed,
    radius: CRAWLER.radius,
    windup: 0,          // >0 while winding up an attack
    attackCooldown: 0.6,
    stun: 0,
    knock: new THREE.Vector2(),
    wobble: Math.random() * 10,
    glow: 0,
  };
}

export function removeCrawler(scene, c) {
  scene.remove(c.group);
  c.mat.dispose();
  c.post.material.dispose();
  if (c.model) for (const m of c.model.materials) m.dispose();
}

/**
 * Move and attack. `enemyDt` is already slowed while the Hornbill's sight is on.
 * Returns an event or null: { type: 'strike', damage } | { type: 'rose' } | { type: 'ambush' }.
 */
export function updateCrawler(c, enemyDt, hero, others, { reveal }) {
  const lifeEvent = tickLife(c.life, enemyDt);
  const st = c.life.state;
  let event = lifeEvent === 'rose' ? { type: 'rose' } : null;

  if (st === 'disguised') {
    const d = Math.hypot(hero.pos.x - c.pos.x, hero.pos.z - c.pos.z);
    if (d < CRAWLER.ambushRange) {
      c.life.state = 'alive';
      c.life.timer = 0;
      event = { type: 'ambush' };
    }
  }

  c.moving = false;
  if (isActive(c.life)) {
    c.attackCooldown = Math.max(0, c.attackCooldown - enemyDt);
    if (c.stun > 0) {
      c.stun = Math.max(0, c.stun - enemyDt);
    } else {
      const dx = hero.pos.x - c.pos.x;
      const dz = hero.pos.z - c.pos.z;
      const dist = Math.hypot(dx, dz);
      if (c.windup > 0) {
        c.windup -= enemyDt;
        if (c.windup <= 0) {
          c.windup = 0;
          c.attackCooldown = CRAWLER.attackCooldown;
          c.strikeAnim = 0.4;
          if (dist < CRAWLER.attackRange + 0.35) event = { type: 'strike', damage: CRAWLER.damage };
        }
      } else if (dist < CRAWLER.attackRange && c.attackCooldown <= 0) {
        c.windup = CRAWLER.windup;
      } else if (dist > CRAWLER.attackRange * 0.8) {
        // walk toward the hero, keeping a little apart from the pack
        let mx = dx / dist;
        let mz = dz / dist;
        for (const o of others) {
          if (o === c || !isActive(o.life)) continue;
          const ox = c.pos.x - o.pos.x;
          const oz = c.pos.z - o.pos.z;
          const od = Math.hypot(ox, oz);
          if (od < 1.3 && od > 1e-3) { mx += (ox / od) * 0.8; mz += (oz / od) * 0.8; }
        }
        const ml = Math.hypot(mx, mz) || 1;
        c.moving = true;
        c.pos.x += (mx / ml) * c.speed * enemyDt;
        c.pos.z += (mz / ml) * c.speed * enemyDt;
      }
      c.group.rotation.y = Math.atan2(-dx, -dz);
    }
  }
  // knockback slides out regardless of state
  if (c.knock.lengthSq() > 0.01) {
    c.pos.x += c.knock.x * enemyDt;
    c.pos.z += c.knock.y * enemyDt;
    c.knock.multiplyScalar(Math.max(0, 1 - 8 * enemyDt));
  }

  poseCrawler(c, enemyDt, reveal);
  return event;
}

function animateModel(c, dt, reveal) {
  const st = c.life.state;
  const a = c.anim;
  const disguised = st === 'disguised';
  c.model.object.visible = !disguised || reveal;
  c.post.visible = disguised && !reveal;
  c.strikeAnim = Math.max(0, c.strikeAnim - dt);

  if (st === 'burned') {
    // sink into ash; the game removes it a moment later
    c.model.object.scale.y = Math.max(0.05, c.model.object.scale.y - dt * 3);
    setShade(c.model.materials, 0.25);
    setGlow(c.model.materials, 0.6, 0.2, 0.02);
    a.update(dt);
    return;
  }
  if (st === 'downed') a.play('Down', { once: true, fade: 0.08, seconds: 0.45 });
  else if (st === 'regrowing') a.play('Rise', { once: true, fade: 0.05, seconds: c.life.cfg.regrowDuration });
  else if (disguised) a.play('Idle');
  else if (c.windup > 0) a.play('Windup', { once: true, fade: 0.08, seconds: CRAWLER.windup });
  else if (c.strikeAnim > 0) a.play('Strike', { once: true, fade: 0.04, seconds: 0.4 });
  else if (c.moving) a.play('Walk', { timeScale: c.speed / CRAWLER.speed, fade: 0.15 });
  else a.play('Idle', { fade: 0.2 });
  a.update(dt);

  const burning = c.life.burnLeft > 0 && st === 'alive';
  setShade(c.model.materials, st === 'downed' || st === 'regrowing' ? 0.6 : 1);
  if (burning) setGlow(c.model.materials, 0.8 + Math.sin(c.wobble * 3) * 0.2, 0.3, 0.05);
  else if (reveal) setGlow(c.model.materials, 0.5, 0.38, 0.05);
  else if (c.windup > 0) setGlow(c.model.materials, 0.35, 0.05, 0.02);
  else setGlow(c.model.materials, 0, 0, 0);
  c.post.material.emissive.setRGB(reveal ? 0.55 : 0, reveal ? 0.42 : 0, reveal ? 0.05 : 0);
}

function poseCrawler(c, dt, reveal) {
  if (c.anim) {
    c.wobble += dt * 6;
    animateModel(c, dt, reveal);
    return;
  }
  const st = c.life.state;
  c.wobble += dt * (c.windup > 0 ? 30 : 6);
  const disguised = st === 'disguised';
  c.body.visible = !disguised || reveal;
  c.post.visible = disguised && !reveal;

  // burned crawlers sink and fade out (removed by the game once gone)
  if (st === 'burned') {
    c.body.scale.y = Math.max(0.05, c.body.scale.y - dt * 3);
    c.mat.color.setHex(0x2a2420);
    c.mat.emissive.setHex(0x000000);
    return;
  }

  const grow = st === 'downed' || st === 'regrowing' ? 0.18 + regrowProgress(c.life) * 0.82 : 1;
  c.body.scale.set(1 + (1 - grow) * 0.6, grow, 1 + (1 - grow) * 0.6);
  c.body.rotation.z = st === 'alive' ? Math.sin(c.wobble) * (c.windup > 0 ? 0.25 : 0.07) : 0;
  c.body.rotation.x = c.windup > 0 ? -0.35 : 0;

  // colour tells the story: dark when downed, orange when burning, gold glow under the Hornbill's sight
  const burning = c.life.burnLeft > 0 && st === 'alive';
  if (st === 'downed' || st === 'regrowing') c.mat.color.setHex(0x6e5233);
  else c.mat.color.setHex(COLORS.rattan);
  if (burning) c.mat.emissive.setRGB(0.8 + Math.sin(c.wobble * 3) * 0.2, 0.3, 0.05);
  else if (reveal) c.mat.emissive.setRGB(0.55, 0.42, 0.05);
  else if (c.windup > 0) c.mat.emissive.setRGB(0.35, 0.05, 0.02);
  else c.mat.emissive.setRGB(0, 0, 0);
  c.post.material.emissive.setRGB(reveal ? 0.55 : 0, reveal ? 0.42 : 0, reveal ? 0.05 : 0);
}
