// "Walk the world": the slice's places as walkable areas, built from the Blender kits.
// Gbelewala, the rice farm, the crossroads, the deep bush, the river rocks and the swamp at night
// with the bele tree, which can be climbed. Paths at the edge of each area lead to the next.
// No fights here yet: this is the world the story and the fights will be put into.

import * as THREE from 'three';
import { CAMERA, HEROES } from '../config.js';
import { createCameraRig, updateRig, look, stickToWorld } from './camera.js';
import { createHero, poseHero, faceToward } from './hero.js';
import { loadModel, instantiate, Animator } from './models.js';
import { partsOf } from './environment.js';
import { AREAS, MOODS } from './areas.js';

const GRAVITY = 22;
const STEP_UP = 0.45;      // the hero walks up onto anything this much higher
const CLIMB_SPEED = 1.7;   // metres per second along a vine
const TALK_RANGE = 2.6;

export function createExplore({ input, ui, quality, models: startup }) {
  const camera = new THREE.PerspectiveCamera(CAMERA.fov, 1, 0.2, 320);
  const rig = createCameraRig(camera);
  const cache = { ...(startup || {}) };
  const lambert = quality.key !== 'high';
  const g = { phase: 'title', loading: false, areaKey: null, visited: new Set() };
  let heroKey = 'korto';
  let area = null;
  let time = 0;
  const fade = document.getElementById('fade');

  async function need(names) {
    for (const n of names) if (!cache[n]) cache[n] = await loadModel(n);
  }

  // ---------- building an area ----------
  function makeCtx(scene) {
    const parts = {};
    const actors = [];
    const labels = [];
    const talks = [];
    const exits = [];
    const obstacles = [];
    const fires = [];
    const updaters = [];
    const shadows = (o, receive = false) => {
      if (!quality.shadows) return o;
      o.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = receive; } });
      return o;
    };
    const partList = (model, name) => (parts[`${model}/${name}`] ??= partsOf(cache[model], name, lambert));
    let seed = 1;
    const ctx = {
      scene, obstacles, actors, labels, talks, exits,
      rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; },
      reseed(s) { seed = s; },
      /** Turn a kit piece (front +Z) toward a point. */
      faceTo: (x, z, tx, tz) => Math.atan2(tx - x, tz - z),
      /** Turn a character (front -Z) toward a point. */
      lookAt: (x, z, tx, tz) => Math.atan2(-(tx - x), -(tz - z)),
      /** One static kit piece. r: also block the hero within this radius. */
      piece(model, name, x, z, ry = 0, s = 1, { r = 0, y = 0 } = {}) {
        const grp = new THREE.Group();
        for (const p of partList(model, name)) grp.add(new THREE.Mesh(p.geometry, p.material));
        grp.position.set(x, y, z);
        grp.rotation.y = ry;
        grp.scale.setScalar(s);
        scene.add(shadows(grp, true));
        if (r) obstacles.push({ x, z, r: r * s });
        return grp;
      },
      /** Many copies of a kit piece in one draw call per part: [[x, z, ry, s], ...]. r: block radius per unit scale. */
      scatter(model, name, list, { r = 0 } = {}) {
        if (!list.length) return;
        const m = new THREE.Matrix4();
        const q = new THREE.Quaternion();
        const up = new THREE.Vector3(0, 1, 0);
        for (const p of partList(model, name)) {
          const inst = new THREE.InstancedMesh(p.geometry, p.material, list.length);
          list.forEach(([x, z, ry, s], i) => inst.setMatrixAt(i, m.compose(new THREE.Vector3(x, 0, z), q.setFromAxisAngle(up, ry), new THREE.Vector3(s, s, s))));
          inst.castShadow = quality.shadows;
          scene.add(inst);
        }
        if (r) for (const [x, z, , s] of list) obstacles.push({ x, z, r: r * s });
      },
      /** An animated character. face: yaw (front -Z). hide: part names to hide (props). */
      actor(model, x, z, face, clip, { scale = 1.12, hide = [], y = 0, label = null, at = Math.random() } = {}) {
        const a = instantiate(cache[model], { lambert, scale });
        a.object.position.set(x, y, z);
        a.object.rotation.y = face;
        for (const n of hide) { const o = a.root.getObjectByName(n); if (o) o.visible = false; }
        scene.add(shadows(a.object));
        a.anim = new Animator(a.root, a.clips);
        a.anim.play(clip, { fade: 0 });
        a.anim.update(at * 2);
        actors.push(a);
        if (label) labels.push({ key: `a-${labels.length}`, text: label, x, y: y + 2.5 * (scale / 1.12), z, near: 14 });
        return a;
      },
      label(text, x, y, z, near = 18) { labels.push({ key: `l-${labels.length}`, text, x, y, z, near }); },
      talk(name, x, z, line) { talks.push({ name, x, z, line }); },
      exit(to, x, z, text, r = 2.6) {
        exits.push({ to, x, z, r });
        const ring = new THREE.Mesh(new THREE.RingGeometry(r * 0.55, r * 0.75, 32), new THREE.MeshBasicMaterial({ color: 0xf2b33d, transparent: true, opacity: 0.35, depthWrite: false }));
        ring.rotation.x = -Math.PI / 2;
        ring.position.set(x, 0.04, z);
        scene.add(ring);
        updaters.push((dt, t) => { ring.material.opacity = 0.25 + Math.sin(t * 3) * 0.12; });
        labels.push({ key: `x-${to}`, text: `→ ${text}`, x, y: 1.4, z, near: 30, cls: 'exit' });
      },
      ground(color, radius, edge = 0x24361d) {
        const ground = new THREE.Mesh(new THREE.CircleGeometry(radius, 56), new THREE.MeshLambertMaterial({ color }));
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = quality.shadows;
        const floor = new THREE.Mesh(new THREE.RingGeometry(radius - 0.1, 160, 56, 1), new THREE.MeshLambertMaterial({ color: edge }));
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = -0.01;
        scene.add(ground, floor);
      },
      /** A flat earth path through points [[x, z], ...]. */
      path(points, width = 2.4, color = 0x8b6a43) {
        const mat = new THREE.MeshLambertMaterial({ color });
        for (let i = 0; i < points.length - 1; i++) {
          const [x0, z0] = points[i];
          const [x1, z1] = points[i + 1];
          const len = Math.hypot(x1 - x0, z1 - z0);
          const seg = new THREE.Mesh(new THREE.PlaneGeometry(width, len + width * 0.6), mat);
          seg.rotation.set(-Math.PI / 2, 0, Math.atan2(x1 - x0, z1 - z0));
          seg.position.set((x0 + x1) / 2, 0.012 + i * 0.0005, (z0 + z1) / 2);
          seg.receiveShadow = quality.shadows;
          scene.add(seg);
        }
      },
      water(x, z, w, d, y = 0.22, color = 0x1d2e2a) {
        const water = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshLambertMaterial({ color, transparent: true, opacity: 0.86 }));
        water.rotation.x = -Math.PI / 2;
        water.position.set(x, y, z);
        scene.add(water);
        return water;
      },
      /** Flames over a fire or brazier, with a flickering light. */
      fire(x, y, z, s = 1) {
        const flame = new THREE.Mesh(new THREE.ConeGeometry(0.35 * s, 1.1 * s, 7), new THREE.MeshBasicMaterial({ color: 0xff9a3a }));
        const core = new THREE.Mesh(new THREE.ConeGeometry(0.18 * s, 0.7 * s, 6), new THREE.MeshBasicMaterial({ color: 0xffe08a }));
        flame.position.set(x, y + 0.55 * s, z);
        core.position.set(x, y + 0.4 * s, z);
        const light = new THREE.PointLight(0xff8a3a, 14 * s, 14 * s, 1.6);
        light.position.set(x, y + 1.2 * s, z);
        scene.add(flame, core, light);
        fires.push({ flame, light, s });
      },
      every(fn) { updaters.push(fn); },
    };
    ctx._internal = { actors, fires, updaters };
    return ctx;
  }

  function setMood(scene, moodKey) {
    const m = MOODS[moodKey];
    scene.background = new THREE.Color(m.sky);
    scene.fog = new THREE.Fog(m.fog[2] ?? m.sky, m.fog[0], m.fog[1]);
    scene.add(new THREE.HemisphereLight(m.hemi[0], m.hemi[1], m.hemi[2] * (quality.shadows ? 0.85 : 1)));
    const sun = new THREE.DirectionalLight(m.sun[0], m.sun[1] * (quality.shadows ? 1.2 : 1));
    sun.position.set(...m.sun[2]);
    scene.add(sun, sun.target);
    if (quality.shadows) {
      sun.castShadow = true;
      sun.shadow.mapSize.set(quality.shadowMapSize, quality.shadowMapSize);
      const c = sun.shadow.camera;
      c.left = -28; c.right = 28; c.top = 28; c.bottom = -28; c.near = 1; c.far = 120;
      sun.shadow.bias = -0.0006;
      sun.shadow.normalBias = 0.04;
    }
    return sun;
  }

  async function enter(key, from = null) {
    g.loading = true;
    const def = AREAS[key];
    ui.title(def.name, 'Loading…');
    await need(def.models);
    const scene = new THREE.Scene();
    const sun = setMood(scene, def.mood);
    const ctx = makeCtx(scene);
    const built = def.build(ctx) || {};
    const hero = createHero(scene, cache, quality, HEROES[heroKey]);
    hero.group.traverse((o) => { if (o.isMesh && quality.shadows) o.castShadow = true; });
    const spawn = (from && built.spawns?.[from]) || built.spawns?.start || { x: 0, z: 0, face: 0 };
    hero.pos.set(spawn.x, 0, spawn.z);
    hero.facing.set(-Math.sin(spawn.face), -Math.cos(spawn.face));
    hero.vy = 0;
    area = {
      key, def, scene, sun, hero, ctx, radius: def.radius ?? 34,
      surfaces: built.surfaces || [], vines: built.vines || [], blockers: built.blockers || null, fits: built.fits || null,
      ...ctx._internal, labels: ctx.labels, talks: ctx.talks, exits: ctx.exits, obstacles: ctx.obstacles,
    };
    hero.pos.y = floorAt(hero.pos.x, hero.pos.z, 0.01);
    rig.yaw = spawn.face;
    rig.pitch = CAMERA.pitch;
    updateRig(rig, 0, hero, { snap: true, fits: area.fits });
    g.areaKey = key;
    g.visited.add(key);
    ui.title(def.name, def.sub);
    if (def.arrive) ui.toast(def.arrive, 4200);
    g.loading = false;
  }

  function go(key, from) {
    if (g.loading) return;
    g.loading = true;
    fade?.classList.add('on');
    setTimeout(async () => {
      try { await enter(key, from); } finally {
        g.loading = false;
        setTimeout(() => fade?.classList.remove('on'), 60);
      }
    }, 380);
  }

  // ---------- the ground under the hero: earth, platforms ----------
  function floorAt(x, z, y) {
    let best = 0;
    for (const s of area.surfaces) {
      if (s.top > y + STEP_UP) continue;
      const dx = x - s.x;
      const dz = z - s.z;
      const u = dx * s.ux + dz * s.uz;
      const v = -dx * s.uz + dz * s.ux;
      if (Math.abs(u) <= s.halfLen && Math.abs(v) <= s.halfWidth && s.top > best) best = s.top;
    }
    return best;
  }

  function collide(h) {
    const p = h.pos;
    for (const o of area.obstacles) {
      if (o.top !== undefined && p.y > o.top) continue;
      const dx = p.x - o.x;
      const dz = p.z - o.z;
      const d = Math.hypot(dx, dz);
      const min = o.r + h.radius;
      if (d < min && d > 1e-4) { p.x = o.x + (dx / d) * min; p.z = o.z + (dz / d) * min; }
    }
    area.blockers?.(p, h.radius);
    const d = Math.hypot(p.x, p.z);
    const lim = area.radius - 0.6;
    if (d > lim) { p.x *= lim / d; p.z *= lim / d; }
  }

  // what the interact button would do right now
  function nearbyAction(h) {
    const p = h.pos;
    let down = null;
    for (const v of area.vines) {
      for (const [end, other] of [[v.a, v.b], [v.b, v.a]]) {
        if (Math.hypot(p.x - end.x, p.z - end.z) < 1.4 && Math.abs(p.y - end.y) < 0.7) {
          if (other.y > end.y) return { kind: 'climb', from: end, to: other, label: 'Climb up' };   // up wins over down
          down = { kind: 'climb', from: end, to: other, label: 'Climb down' };
        }
      }
    }
    if (down) return down;
    for (const t of area.talks) {
      if (Math.hypot(p.x - t.x, p.z - t.z) < TALK_RANGE && p.y < 1) return { kind: 'talk', talk: t, label: `Talk to ${t.name}` };
    }
    return null;
  }

  // ---------- per frame ----------
  function update(dt) {
    time += dt;
    if (!area) return;
    for (const a of area.actors) a.anim.update(dt);
    for (const fn of area.updaters) fn(dt, time);
    for (const f of area.fires) {
      f.flame.scale.y = 1 + Math.sin(time * 11 + f.s) * 0.12;
      f.light.intensity = 14 * f.s + Math.sin(time * 17) * 2;
    }
    const h = area.hero;
    const inp = input;
    if (g.phase !== 'play' || g.loading) {
      inp.consume();
      updateRig(rig, dt, h, { fits: area.fits });
      if (h.anim && g.phase !== 'paused') poseHero(h, dt, { moving: false });
      return;
    }
    if (inp.pause || inp.lockLost) { inp.consume(); ui.pause(); return; }
    look(rig, inp.look.dx, inp.look.dy);

    let moving = false;
    let speedFactor = 0;
    if (h.climbing) {
      const c = h.climbing;
      c.t = Math.min(1, c.t + (dt * CLIMB_SPEED) / c.len);
      h.pos.lerpVectors(c.from, c.to, c.t);
      faceToward(h, c.faceX - h.pos.x, c.faceZ - h.pos.z);
      if (c.t >= 1) {
        h.climbing = null;
        h.pos.copy(c.to);
        h.vy = 0;
      }
    } else {
      const mx = inp.move.x;
      const mz = inp.move.z;
      const len = Math.min(1, Math.hypot(mx, mz));
      if (len > 0.05) {
        const d = stickToWorld(rig, mx / len, mz / len);
        const sp = h.speed * len;
        h.pos.x += d.x * sp * dt;
        h.pos.z += d.z * sp * dt;
        faceToward(h, d.x, d.z);
        moving = true;
        speedFactor = len;
      }
      collide(h);
      // stand on platforms, fall off their edges
      const floor = floorAt(h.pos.x, h.pos.z, h.pos.y);
      if (h.pos.y > floor + 0.02) {
        h.vy = (h.vy || 0) - GRAVITY * dt;
        h.pos.y = Math.max(floor, h.pos.y + h.vy * dt);
        if (h.pos.y === floor) h.vy = 0;
      } else {
        h.pos.y = floor;
        h.vy = 0;
      }
    }

    const act = h.climbing ? null : nearbyAction(h);
    ui.setInteract(act ? act.label : null);
    if (act && inp.interact) {
      if (act.kind === 'climb') {
        const from = new THREE.Vector3(act.from.x, act.from.y, act.from.z);
        const to = new THREE.Vector3(act.to.x, act.to.y, act.to.z);
        h.climbing = { from, to, t: 0, len: Math.max(0.5, from.distanceTo(to)), faceX: act.from.fx, faceZ: act.from.fz };
        h.pos.copy(from);
      } else if (act.kind === 'talk') {
        ui.toast(`${act.talk.name}: “${act.talk.line}”`, 5200);
      }
    }

    if (!h.climbing && h.pos.y < 0.5) {
      for (const e of area.exits) {
        if (Math.hypot(h.pos.x - e.x, h.pos.z - e.z) < e.r) { ui.setInteract(null); go(e.to, area.key); break; }
      }
    }

    poseHero(h, dt, { moving, speedFactor });
    updateRig(rig, dt, h, { moving, fits: area.fits });
    if (area.sun.castShadow) {
      area.sun.target.position.set(h.pos.x, h.pos.y, h.pos.z);
      area.sun.position.set(h.pos.x + MOODS[area.def.mood].sun[2][0], h.pos.y + MOODS[area.def.mood].sun[2][1], h.pos.z + MOODS[area.def.mood].sun[2][2]);
    }
    inp.consume();
  }

  function labelAnchors() {
    if (!area || g.loading) return [];
    const p = area.hero.pos;
    return area.labels.filter((l) => Math.hypot(l.x - p.x, l.z - p.z) < (l.near ?? 18) && Math.abs(l.y - p.y) < 14);
  }

  return {
    g, camera, rig,
    get scene() { return area?.scene ?? null; },
    get area() { return area; },
    update, labelAnchors,
    setAspect(w, h) {
      camera.aspect = w / h;
      camera.fov = w / h < 1.2 ? CAMERA.portraitFov ?? CAMERA.fov : CAMERA.fov;
      camera.updateProjectionMatrix();
    },
    setHero(key) { if (HEROES[key]) heroKey = key; },
    async start(key = 'gbelewala') { g.phase = 'play'; await enter(key); },
    goTo: (key, from = null) => enter(key, from),
    pauseGame() { if (g.phase === 'play') g.phase = 'paused'; },
    resume() { if (g.phase === 'paused' || g.phase === 'menu') g.phase = 'play'; },
  };
}
