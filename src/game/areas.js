// The slice's places, laid out from the Blender kits. Each area says which models it needs, its mood
// (time of day, fog, light), and builds itself through the explore context (see explore.js).
// Game coordinates: x east, z south (the camera starts south of the hero, looking north).

import * as THREE from 'three';
import bele from '../../public/models/bele_tree.json';

export const MOODS = {
  morning: { sky: 0xb7c7c9, fog: [45, 140], hemi: [0xfff1dc, 0x5a4630, 1.45], sun: [0xffe0b0, 2.0, [-25, 30, 18]] },
  day: { sky: 0xa8c9d8, fog: [50, 150], hemi: [0xf4f8ff, 0x5a4a30, 1.55], sun: [0xfff2d6, 2.2, [-18, 34, 12]] },
  dusk: { sky: 0x7a5f68, fog: [30, 95, 0x6a5058], hemi: [0xffc49a, 0x2e2018, 1.2], sun: [0xff9a55, 1.7, [30, 12, -20]] },
  bush: { sky: 0x1f3324, fog: [10, 52], hemi: [0xa6d0a0, 0x18120c, 1.15], sun: [0xe8f0c0, 0.9, [-10, 40, 6]] },
  afternoon: { sky: 0xb2cbc4, fog: [45, 140], hemi: [0xfff4e4, 0x4a4030, 1.5], sun: [0xffe6c0, 2.0, [20, 26, 14]] },
  night: { sky: 0x16243a, fog: [22, 90], hemi: [0x8aa2d8, 0x1a1610, 1.55], sun: [0xb8ccff, 1.4, [-20, 40, -10]] },
};

const PI = Math.PI;

/** Forest between r0 and r1 (outside the walkable area), instanced. */
function forestRing(c, r0, r1, n, seed, kinds = [['tree_giant', 0.55, 0.85], ['tree_mid', 0.9, 1.3], ['palm', 0.9, 1.2], ['bush', 1.4, 2.2]]) {
  c.reseed(seed);
  const lists = Object.fromEntries(kinds.map(([k]) => [k, []]));
  for (let i = 0; i < n; i++) {
    const a = c.rnd() * PI * 2;
    const r = r0 + c.rnd() * (r1 - r0);
    const [k, s0, s1] = kinds[i % kinds.length];
    lists[k].push([Math.cos(a) * r, Math.sin(a) * r, c.rnd() * 6.28, s0 + c.rnd() * (s1 - s0)]);
  }
  for (const [k, list] of Object.entries(lists)) c.scatter('environment', k, list);
}

function distToPath(x, z, pts) {
  let best = Infinity;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, az] = pts[i];
    const [bx, bz] = pts[i + 1];
    const dx = bx - ax;
    const dz = bz - az;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)));
    best = Math.min(best, Math.hypot(x - ax - dx * t, z - az - dz * t));
  }
  return best;
}

export const AREAS = {
  // ---------------------------------------------------------------- the village
  gbelewala: {
    name: 'Gbelewala', sub: 'Morning. The seed-rice store stands open.', mood: 'morning', radius: 30,
    arrive: 'Morning in Gbelewala. Something has been at the seed-rice store.',
    models: ['gbelewala', 'environment', 'chief', 'blacksmith', 'villager_woman', 'villager_man', 'elder', 'child', 'storyteller'],
    build(c) {
      c.ground(0x7a5233, 31, 0x3b5a2c);
      c.path([[0, 4], [12, 2], [30, 0]]);
      c.path([[0, 4], [-10, 6]], 2.0);
      // the square: palaver hut and the storyteller's fire
      c.piece('gbelewala', 'palaver_hut', 0, -12, 0);
      c.piece('gbelewala', 'story_fire', 0, -2, 0, 1, { r: 1.1 });
      for (const [a, s] of [[205, 1], [245, 1], [295, 1], [335, 1]]) {
        const t = (a * PI) / 180;
        const x = Math.cos(t) * 3.4;
        const z = -2 - Math.sin(t) * 3.4;
        c.piece('gbelewala', 'bench', x, z, c.faceTo(x, z, 0, -2), s);
      }
      // houses round the square, doors facing in, a gap to the east for the farm road
      for (const [a, r, kind] of [[150, 17, 'house_round'], [115, 18, 'house_long'], [70, 17, 'house_round'], [35, 18, 'house_round'],
        [-40, 17, 'house_long'], [-75, 18, 'house_round'], [200, 17, 'house_round'], [235, 18, 'house_long']]) {
        const t = (a * PI) / 180;
        const x = Math.cos(t) * r;
        const z = -Math.sin(t) * r;
        c.piece('gbelewala', kind, x, z, c.faceTo(x, z, 0, 0), 1, { r: kind === 'house_long' ? 3.0 : 2.9 });
      }
      // the seed-rice store, found empty
      c.piece('gbelewala', 'rice_store', -10, 8, c.faceTo(-10, 8, 0, 3), 1, { r: 1.7 });
      c.label('The seed-rice store', -10, 4.6, 8);
      // the forge where the father works
      c.piece('environment', 'forge', 14, -8, c.faceTo(14, -8, 0, 0), 1, { r: 1.9 });
      c.label('Your father’s forge', 14, 3.6, -8);
      // everyday things
      c.piece('gbelewala', 'mortar', -12, -6, 0, 1, { r: 0.35 });
      c.piece('gbelewala', 'water_pots', -10, -9.5, 1, 1, { r: 0.6 });
      c.piece('gbelewala', 'cook_fire', -14, -3, 0, 1, { r: 0.6 });
      c.piece('gbelewala', 'drying_rack', 6, 10, 0.3, 1, { r: 0.4 });
      c.piece('gbelewala', 'drying_rack', -3, -18, 0, 1);
      c.piece('gbelewala', 'stool', 2.6, 1.0);
      const chickens = [[4, -5], [5.5, -6], [7, 4], [-5, 6]].map(([x, z], i) => c.piece('gbelewala', 'chicken', x, z, i * 1.7));
      c.scatter('gbelewala', 'banana_plant', [0, 1, 2, 3, 4, 5, 6, 7, 8].map((k) => { const t = (k * 40 + 15) * PI / 180; return [Math.cos(t) * 22.5, Math.sin(t) * 22.5, k, 1]; }), { r: 0.5 });
      const fence = [];
      for (let k = 0; k < 16; k++) {
        const t = (k * 22.5 + 11) * PI / 180;
        if (Math.abs(Math.cos(t)) > 0.92 && Math.cos(t) > 0) continue;   // the gap for the farm road
        fence.push([Math.cos(t) * 26, Math.sin(t) * 26, PI / 2 - t, 1]);
      }
      c.scatter('gbelewala', 'fence', fence);
      forestRing(c, 31, 52, 150, 3);
      // people
      c.actor('chief', -7.5, 9.5, c.lookAt(-7.5, 9.5, 0, 5), 'Worry', { scale: 1.0, label: 'The Chief' });
      c.talk('the Chief', -7.5, 9.5, 'The seed rice is gone. If we don’t plant before the rain season, hunger will catch all of us.');
      c.actor('blacksmith', 13.3, -6.2, c.lookAt(13.3, -6.2, 14, -8), 'Hammer', { scale: 1.0, label: 'Your father' });
      c.talk('your father', 13.3, -6.2, 'The forge is hot. If you go after that rice, go with iron in your hand.');
      c.actor('villager_woman', -11.3, -5.2, c.lookAt(-11.3, -5.2, -12, -6), 'Pound', { scale: 1.0 });
      c.actor('elder', -4, 9, c.lookAt(-4, 9, -10, 8), 'Idle', { scale: 1.0, hide: [] });
      c.actor('villager_man', -5.5, 11.5, c.lookAt(-5.5, 11.5, -10, 8), 'Talk', { scale: 1.0, hide: ['Hoe'] });
      c.actor('storyteller', 2.6, 1.6, c.lookAt(2.6, 1.6, 0, -2), 'Sit', { scale: 1.0, hide: ['Whisk', 'Rattle'], label: 'The storyteller' });
      c.talk('the storyteller', 2.6, 1.6, 'Sit with us tonight and I will tell how Woi’s iron was made. Dried millet...');
      const child = c.actor('child', 5, -5, 0, 'Walk', { scale: 1.0 });
      c.every((dt, t) => {   // the child chases the chickens round and round
        const a = t * 0.6;
        child.object.position.set(5.2 + Math.cos(a) * 2.6, 0, -4.5 + Math.sin(a) * 2.6);
        child.object.rotation.y = Math.atan2(Math.sin(a), -Math.cos(a)) + PI;
        chickens[0].position.set(5.2 + Math.cos(a + 0.7) * 2.8, 0, -4.5 + Math.sin(a + 0.7) * 2.8);
        chickens[0].rotation.y = -a;
      });
      c.exit('rice_farm', 28, 0, 'The rice farm');
      return {
        spawns: { start: { x: 0, z: 6, face: 0 }, rice_farm: { x: 25, z: 0, face: PI / 2 } },
      };
    },
  },

  // ---------------------------------------------------------------- the rice farm
  rice_farm: {
    name: 'The rice farm', sub: 'Rattan marks lead from the store to here.', mood: 'day', radius: 31,
    arrive: 'The upland rice farm. Rattan has been dragged through the young rice.',
    models: ['gbelewala', 'environment', 'villager_man', 'villager_woman'],
    build(c) {
      c.ground(0x6a5634, 32, 0x3b5a2c);
      c.path([[-30, 2], [-8, 1], [0, -6], [0, -30]]);
      for (const [x, z, r] of [[-14, -10, 0.1], [12, -12, -0.1], [-14, 9, 0.05], [13, 9, 0.12], [0, 14, 0], [-22, -2, 1.57]]) c.piece('gbelewala', 'rice_farm', x, z, r, 1.6);
      c.piece('gbelewala', 'drying_rack', 6, 0, 1.57, 1, { r: 0.4 });
      c.piece('gbelewala', 'drying_rack', -6, -3, 1.57, 1, { r: 0.4 });
      c.piece('environment', 'hut', -20, -18, c.faceTo(-20, -18, 0, 0), 1, { r: 2.1 });
      c.piece('gbelewala', 'mortar', -16, -14, 0, 1, { r: 0.35 });
      c.piece('gbelewala', 'water_pots', -18, -13, 0, 1, { r: 0.6 });
      // the burning field brazier: where fire arrows are lit
      c.piece('environment', 'brazier', 7, 5, 0, 1, { r: 0.7 });
      c.fire(7, 0.95, 5, 0.9);
      c.label('Field brazier: light fire arrows here', 7, 2.8, 5);
      // rattan sign at the forest edge
      for (const [x, z] of [[21, -15], [23, -9], [19, -20]]) c.piece('environment', 'vine_clump', x, z, x, 1.2, { r: 0.6 });
      c.label('Rattan: something was dragged into the bush', 22, 2.6, -13);
      c.actor('villager_man', -14, -8.5, c.lookAt(-14, -8.5, -14, -12), 'Hoe', { scale: 1.0 });
      c.actor('villager_man', 13, 10.5, c.lookAt(13, 10.5, 13, 8), 'Hoe', { scale: 1.0 });
      c.actor('villager_woman', -15.6, -12.6, c.lookAt(-15.6, -12.6, -16, -14), 'Pound', { scale: 1.0 });
      c.talk('the farmer', -14, -8.5, 'They came in the night, all of them rattan. Dragged the bundles that way, to the crossroads.');
      forestRing(c, 32, 52, 150, 7);
      c.exit('gbelewala', -29, 2, 'Gbelewala');
      c.exit('crossroads', 0, -29, 'The crossroads');
      return {
        spawns: { start: { x: -26, z: 2, face: -PI / 2 }, gbelewala: { x: -26, z: 2, face: -PI / 2 }, crossroads: { x: 0, z: -26, face: PI } },
      };
    },
  },

  // ---------------------------------------------------------------- the crossroads
  crossroads: {
    name: 'The crossroads', sub: 'Where debts to the spirits are paid.', mood: 'dusk', radius: 24,
    arrive: 'The crossroads at dusk. Someone is singing.',
    models: ['environment', 'gelengol', 'hornbill'],
    build(c) {
      c.ground(0x4a5a34, 25, 0x2a3a22);
      c.path([[0, 25], [0, 0]], 2.8);
      c.path([[0, 0], [-12, -3], [-25, -5]], 2.6);
      c.path([[0, 0], [12, -4], [25, -6]], 2.6);
      c.piece('environment', 'shrine', 0, -1.5, 0, 1, { r: 1.0 });
      c.label('Offering stone', 0, 1.6, -1.5);
      c.actor('gelengol', -6, -6, c.lookAt(-6, -6, 0, 0), 'Sing', { scale: 1.05, hide: ['Bowl'], label: 'Gelengol' });
      c.obstacles.push({ x: -6, z: -6, r: 1.2 });
      c.talk('Gelengol', -6, -6, 'Who borrows from the bush, pays the bush.');
      // the Hornbill on its carved post
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.13, 1.55, 7), new THREE.MeshLambertMaterial({ color: 0x3e2716, flatShading: true }));
      post.position.set(4.5, 0.775, -4);
      c.scene.add(post);
      c.obstacles.push({ x: 4.5, z: -4, r: 0.3 });
      c.actor('hornbill', 4.5, -4, c.lookAt(4.5, -4, 0, 6), 'Perch', { scale: 1.35, y: 1.55, label: 'The Hornbill Genie' });
      c.talk('the Hornbill', 4.5, -4, 'Far sight, for a price. Pay me here, at the fork, before the dark comes for you.');
      c.reseed(11);
      const rocks = [];
      for (let i = 0; i < 10; i++) { const a = c.rnd() * 6.28; const r = 8 + c.rnd() * 12; rocks.push([Math.cos(a) * r, Math.sin(a) * r, c.rnd() * 6, 0.6 + c.rnd()]); }
      c.scatter('environment', 'rock_1', rocks.slice(0, 5));
      c.scatter('environment', 'rock_2', rocks.slice(5));
      c.scatter('environment', 'bush', [[-9, 8, 0, 1.8], [10, 9, 1, 2], [-14, -13, 2, 1.6], [14, -15, 3, 1.7], [-17, 12, 1, 2.1], [17, 11, 2, 1.9]]);
      forestRing(c, 25, 46, 160, 13);
      c.exit('rice_farm', 0, 22, 'The rice farm');
      c.exit('deep_bush', -22, -4.6, 'The deep bush');
      c.exit('river_rocks', 22, -5.5, 'The river rocks');
      return {
        spawns: { start: { x: 0, z: 18.5, face: 0 }, rice_farm: { x: 0, z: 18.5, face: 0 }, deep_bush: { x: -18.5, z: -4, face: -PI / 2 }, river_rocks: { x: 18.5, z: -4.8, face: PI / 2 } },
      };
    },
  },

  // ---------------------------------------------------------------- the deep bush
  deep_bush: {
    name: 'The deep bush', sub: 'Home of the bush genii.', mood: 'bush', radius: 34,
    arrive: 'The deep bush. Between villages, where the genii live.',
    models: ['environment', 'genie_iron', 'genie_ant', 'swamp'],
    build(c) {
      c.ground(0x2c3a22, 35, 0x1a2414);
      const trail = [[33, 2], [18, 6], [6, 0], [-4, -8], [-2, -22], [0, -33]];
      c.path(trail, 2.2, 0x5a4a30);
      const glades = [[-15, 9, 7], [15, -17, 7]];
      // the bush crowds right up to the trail
      c.reseed(21);
      const lists = { tree_giant: [], tree_mid: [], palm: [], bush: [] };
      const kinds = [['tree_giant', 0.5, 0.8, 1.0], ['tree_mid', 0.9, 1.3, 0.35], ['palm', 0.9, 1.2, 0.35], ['bush', 1.4, 2.2, 0]];
      for (let i = 0; i < 420 && Object.values(lists).flat().length < 230; i++) {
        const x = (c.rnd() * 2 - 1) * 44;
        const z = (c.rnd() * 2 - 1) * 44;
        if (distToPath(x, z, trail) < 3.2) continue;
        if (glades.some(([gx, gz, gr]) => Math.hypot(x - gx, z - gz) < gr)) continue;
        const [k, s0, s1, block] = kinds[i % kinds.length];
        const s = s0 + c.rnd() * (s1 - s0);
        lists[k].push([x, z, c.rnd() * 6.28, s]);
        if (block && Math.hypot(x, z) < 34) c.obstacles.push({ x, z, r: block * (k === 'tree_giant' ? 0.9 : 0.6) });
      }
      for (const [k, list] of Object.entries(lists)) c.scatter('environment', k, list);
      c.scatter('swamp', 'fallen_log', [[-8, 14, 0.4, 0.9], [20, -4, 2, 0.8]]);
      c.scatter('swamp', 'koong_plant', [[-12, 4, 0, 1.2], [12, -12, 1, 1.2]]);
      c.actor('genie_iron', -16, 10, c.lookAt(-16, 10, 0, 0), 'Idle', { scale: 1.0, hide: ['GiftStone'], label: 'The Iron-Stone Genie' });
      c.obstacles.push({ x: -16, z: 10, r: 1.4 });
      c.talk('the Iron-Stone Genie', -16, 10, 'Stone skin, for a price, child of the smith. Stone is slow to forget what it is owed.');
      c.actor('genie_ant', 16, -18, c.lookAt(16, -18, 4, -4), 'Idle', { scale: 1.0, label: 'The Driver-Ant Genie' });
      c.obstacles.push({ x: 16, z: -18, r: 1.6 });
      c.talk('the Driver-Ant Genie', 16, -18, 'The column eats whatever stands in the road. Borrow it, and feed it after.');
      c.exit('crossroads', 31, 2, 'The crossroads');
      c.exit('swamp', 0, -31, 'The swamp');
      return {
        spawns: { start: { x: 28, z: 2, face: PI / 2 }, crossroads: { x: 28, z: 2, face: PI / 2 }, swamp: { x: 0, z: -28, face: PI } },
      };
    },
  },

  // ---------------------------------------------------------------- the river rocks
  river_rocks: {
    name: 'The river rocks', sub: 'Shout first, or she sets the price.', mood: 'afternoon', radius: 30,
    arrive: 'A woman sits on the rocks, combing her hair. Speak to water spirits before they speak to you.',
    models: ['swamp', 'environment', 'river_woman'],
    build(c) {
      c.ground(0x4f6a2c, 31, 0x2f4a22);
      c.water(0, -26, 140, 40, 0.18, 0x2c4e4a);
      // the muddy bank
      const bank = new THREE.Mesh(new THREE.PlaneGeometry(70, 3), new THREE.MeshLambertMaterial({ color: 0x5a4430 }));
      bank.rotation.x = -Math.PI / 2;
      bank.position.set(0, 0.02, -6.5);
      c.scene.add(bank);
      c.path([[-30, 2], [-10, -2], [10, -2], [30, 0]], 2.4);
      c.piece('swamp', 'river_rocks', 2, -9.5, 0.4, 1.4);
      c.actor('river_woman', 2, -9.6, c.lookAt(2, -9.6, 2, 0), 'Comb', { scale: 1.05, y: 0.55 * 1.4 - 0.44, label: 'The River Woman' });
      c.talk('the River Woman', 2, -7, 'You called before me. So you can set the price.');
      c.scatter('swamp', 'reeds', [[-12, -7.5, 0, 1.2], [-6, -8, 1, 1], [8, -7.6, 2, 1.1], [14, -8, 3, 1.3], [20, -7.4, 0.5, 1], [-20, -7.8, 2, 1.1]]);
      c.scatter('swamp', 'lily_pads', [[-8, -14, 0, 1.3], [10, -16, 1, 1.2], [-2, -20, 2, 1.4], [18, -13, 0, 1]]);
      // the far bank
      c.scatter('swamp', 'stilt_tree', [[-24, -40, 0, 1.2], [-6, -42, 1, 1.1], [14, -40, 2, 1.3], [30, -44, 3, 1.2]]);
      c.scatter('swamp', 'raffia_palm', [[-16, -38, 0, 1.2], [4, -38, 1.5, 1.1], [24, -37, 2.5, 1.2]]);
      c.reseed(31);
      const south = [];
      for (let i = 0; i < 70; i++) { const x = (c.rnd() * 2 - 1) * 40; const z = 18 + c.rnd() * 30; south.push([x, z, c.rnd() * 6, 0.6 + c.rnd() * 0.4]); }
      c.scatter('environment', 'tree_giant', south.slice(0, 25));
      c.scatter('environment', 'palm', south.slice(25, 50));
      c.scatter('environment', 'bush', south.slice(50).map(([x, z, r]) => [x, z, r, 1.8]));
      c.exit('crossroads', -28, 2, 'The crossroads');
      c.exit('swamp', 28, 0, 'Along the river to the swamp');
      return {
        spawns: { start: { x: -25, z: 2, face: -PI / 2 }, crossroads: { x: -25, z: 2, face: -PI / 2 }, swamp: { x: 25, z: 0, face: PI / 2 } },
        blockers(p) { if (p.z < -6.6) p.z = -6.6; },   // the river is deep past the bank
      };
    },
  },

  // ---------------------------------------------------------------- the swamp at night, and the bele tree
  swamp: {
    name: 'The swamp', sub: 'Night. The bele tree blocks the sky.', mood: 'night', radius: 38,
    arrive: 'The swamp at night. The demon’s tree rises out of the water. Climb it: walk the branches, climb the vines.',
    models: ['swamp', 'bele_tree', 'rattan_bull', 'bat', 'meni_lizard', 'environment'],
    build(c) {
      c.ground(0x3a3222, 39, 0x1e241a);
      c.water(0, 0, 120, 120, 0.2, 0x1e3330);
      const T = { x: 0, z: -18 };
      // the tree: every named part
      const names = ['Trunk', 'Canopy'];
      for (let i = 1; i <= 12; i++) names.push(`Platform${i}`);
      for (let i = 1; i <= 11; i++) names.push(`Vine${i}`);
      for (let i = 1; i <= 3; i++) names.push(`CutBranch${i}`);
      for (let i = 1; i <= 5; i++) names.push(`RiceSack${i}`);
      for (const n of names) c.piece('bele_tree', n, T.x, T.z);
      // the swamp round it
      c.scatter('swamp', 'raffia_palm', [[-16, 10, 0.5, 1.2], [14, 16, 2, 1.1], [-24, -8, 1, 1.0], [24, -14, 3, 1.2], [-12, 28, 0.2, 1.1], [26, 22, 1, 1.0]], { r: 0.5 });
      c.scatter('swamp', 'dead_tree', [[-8, 16, 0.3, 1.0], [10, 4, 2, 1.1], [-20, 20, 1, 1.2], [20, -30, 2, 1.1]], { r: 0.45 });
      c.scatter('swamp', 'stilt_tree', [[18, 8, 1, 1.0], [-22, 4, 2, 1.2], [-6, -38, 0.5, 1.1]], { r: 1.2 });
      c.scatter('swamp', 'reeds', [[-4, 22, 0, 1.2], [6, 24, 1, 1.0], [-14, 18, 2, 1.0], [12, 14, 3, 1.1], [4, 8, 4, 1.0], [-6, 4, 1, 1.2]]);
      c.scatter('swamp', 'lily_pads', [[2, 18, 0, 1.3], [-8, 12, 2, 1.0], [10, 2, 1, 1.0], [-14, -4, 0.5, 1.2]]);
      c.scatter('swamp', 'hummock', [[8, 12, 0.4, 1.2], [-12, 8, 1, 1.3], [16, -4, 2, 1.0]], { r: 1.0 });
      c.scatter('swamp', 'fallen_log', [[-10, 24, 0.7, 1.0]], { r: 1.0 });
      c.piece('swamp', 'koong_plant', 9, 9, 0, 1.4);
      c.piece('swamp', 'koong_plant', -12, 5, 1, 1.3);
      c.label('Koong: its smoke calms bats', 9, 1.6, 9, 10);
      c.piece('swamp', 'lair_arch', -18, -8, c.faceTo(-18, -8, 0, 10), 1.4, { r: 2.6 });
      c.label('The lizard’s lair', -18, 4.2, -8);
      const lairLight = new THREE.PointLight(0xff5a1f, 8, 10, 1.6);
      lairLight.position.set(-17, 1, -5.5);
      c.scene.add(lairLight);
      forestRing(c, 39, 56, 120, 41, [['tree_giant', 0.5, 0.8], ['palm', 0.9, 1.2], ['tree_mid', 0.9, 1.2]]);
      // the Rattan Bull guarding the tree's foot
      c.actor('rattan_bull', 9, -8, c.lookAt(9, -8, 0, 30), 'Idle', { scale: 1.3, label: 'The Rattan Bull' });
      c.obstacles.push({ x: 9, z: -8, r: 1.8 });
      // Meni-maa-fa clinging head-up to the trunk, high above, facing out over the swamp
      const h = 24;
      const ax = trunkAt(h);
      const liz = c.actor('meni_lizard', T.x + ax.x, h, 0, 'Idle', { scale: 1.4, label: 'Meni-maa-fa' });
      liz.object.position.set(T.x + ax.x, h, T.z + ax.z + ax.r + 0.05);
      liz.object.rotation.set(PI / 2, 0, 0);
      c.labels[c.labels.length - 1] = { key: 'meni', text: 'Meni-maa-fa', x: T.x + ax.x, y: h + 3, z: T.z + ax.z + ax.r, near: 60 };
      // bats circling the crown
      const bats = [];
      for (let i = 0; i < 8; i++) bats.push({ a: c.actor('bat', 0, 0, 0, 'Fly', { scale: 2.2 }), ph: (i / 8) * PI * 2, r: 8 + (i % 3) * 2.5, y: 28 + (i % 4) * 2, sp: 0.5 + (i % 3) * 0.12 });
      c.every((dt, t) => {
        for (const b of bats) {
          const a = b.ph + t * b.sp;
          b.a.object.position.set(T.x + Math.cos(a) * b.r, b.y + Math.sin(t * 2 + b.ph) * 0.8, T.z + Math.sin(a) * b.r);
          b.a.object.rotation.y = -a;
        }
      });
      // the climb: platform tops are floors, vines join them; a first rope from the ground
      const surfaces = bele.platforms.map((p) => ({
        x: T.x + p.mid[0], z: T.z - p.mid[1], ux: p.dir[0], uz: -p.dir[1], halfLen: p.length / 2 + 0.15, halfWidth: p.width / 2, top: p.top,
      }));
      const tip = (p) => ({ x: T.x + p.tip[0], z: T.z - p.tip[1], y: p.top, fx: T.x, fz: T.z });
      const vines = [];
      const p1 = tip(bele.platforms[0]);
      const g0 = { x: T.x + bele.platforms[0].tip[0] + bele.platforms[0].dir[0] * 0.9, z: T.z - bele.platforms[0].tip[1] - bele.platforms[0].dir[1] * 0.9, y: 0, fx: T.x, fz: T.z };
      vines.push({ a: g0, b: p1 });
      const rope = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, p1.y + 0.4, 5), new THREE.MeshLambertMaterial({ color: 0xb8894f }));
      rope.position.set(g0.x, (p1.y + 0.4) / 2, g0.z);
      rope.rotation.set(0, 0, Math.atan2(g0.x - p1.x, p1.y) * 0.3);
      c.scene.add(rope);
      for (let i = 0; i < bele.platforms.length - 1; i++) vines.push({ a: tip(bele.platforms[i]), b: tip(bele.platforms[i + 1]) });
      c.label('Climb the vine', g0.x, 2.2, g0.z, 8);
      const last = bele.platforms[bele.platforms.length - 1];
      c.label('The crown: the stolen seed rice hangs above', T.x + last.mid[0], last.top + 2, T.z - last.mid[1], 10);
      // the trunk: solid at every height; the buttresses at its foot
      c.obstacles.push({ x: T.x, z: T.z, r: 4.6, top: 2.4 });
      const blockers = (p, r) => {
        const ax2 = trunkAt(p.y);
        const cx = T.x + ax2.x;
        const cz = T.z + ax2.z;
        const dx = p.x - cx;
        const dz = p.z - cz;
        const d = Math.hypot(dx, dz);
        const min = ax2.r + r * 0.7;
        if (d < min && d > 1e-4) { p.x = cx + (dx / d) * min; p.z = cz + (dz / d) * min; }
      };
      const fits = (x, z, y) => {
        const ax2 = trunkAt(Math.max(0, y));
        return Math.hypot(x - (T.x + ax2.x), z - (T.z + ax2.z)) > ax2.r + 0.6 && Math.hypot(x, z) < 52;
      };
      c.exit('river_rocks', 0, 35, 'The river rocks');
      c.exit('deep_bush', -35, 6, 'The deep bush');
      return {
        spawns: { start: { x: 0, z: 32, face: 0 }, river_rocks: { x: 0, z: 32, face: 0 }, deep_bush: { x: -32, z: 6, face: -PI / 2 } },
        surfaces, vines, blockers, fits,
      };
    },
  },
};

/** The trunk's centre offset and radius at height y (game axes, relative to the tree's position). */
function trunkAt(y) {
  const rows = bele.trunk;
  let i = 0;
  while (i < rows.length - 2 && rows[i + 1][0] < y) i++;
  const [z0, x0, y0, r0] = rows[i];
  const [z1, x1, y1, r1] = rows[i + 1];
  const t = Math.max(0, Math.min(1, (y - z0) / (z1 - z0)));
  return { x: x0 + (x1 - x0) * t, z: -(y0 + (y1 - y0) * t), r: r0 + (r1 - r0) * t };
}

export const AREA_ORDER = ['gbelewala', 'rice_farm', 'crossroads', 'deep_bush', 'river_rocks', 'swamp'];
