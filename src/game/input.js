// One input state for touch (joystick + look-drag + buttons), mouse and keyboard.
// `move` is the raw stick (x right, z down the screen); game.js turns it into a
// world direction relative to the camera.

const STICK_MAX = 52;      // px the knob can travel

export function createInput(els) {
  const s = {
    move: { x: 0, z: 0 },
    bowHeld: false,
    // one-shot events, cleared by consume()
    attack: false,
    bowReleased: false,
    dodge: false,
    look: { dx: 0, dy: 0 },   // pixels dragged since last frame
    lookKeys: { x: 0, y: 0 }, // arrow keys held
    power: false,
    toggleArrow: false,
    interact: false,
    pause: false,
    usedTouch: false,
  };

  // ---- Joystick (appears where the left thumb lands) ----
  let stickId = null;
  let origin = { x: 0, y: 0 };
  const zone = els.stickZone;
  zone.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse') { startLook(e, zone); return; }
    if (stickId !== null) return;
    stickId = e.pointerId;
    zone.setPointerCapture(e.pointerId);
    origin = { x: e.clientX, y: e.clientY };
    els.stickBase.style.left = `${e.clientX}px`;
    els.stickBase.style.top = `${e.clientY}px`;
    els.stickBase.classList.remove('hidden');
    setKnob(0, 0);
    s.usedTouch = true;
  });
  zone.addEventListener('pointermove', (e) => {
    if (e.pointerId === lookId) { moveLook(e); return; }
    if (e.pointerId !== stickId) return;
    let dx = e.clientX - origin.x;
    let dy = e.clientY - origin.y;
    const len = Math.hypot(dx, dy);
    if (len > STICK_MAX) { dx *= STICK_MAX / len; dy *= STICK_MAX / len; }
    setKnob(dx, dy);
    const dead = 6;
    const mag = Math.max(0, Math.min(1, (Math.hypot(dx, dy) - dead) / (STICK_MAX - dead)));
    const ang = Math.atan2(dy, dx);
    s.move.x = len > dead ? Math.cos(ang) * mag : 0;
    s.move.z = len > dead ? Math.sin(ang) * mag : 0;
  });
  const endStick = (e) => {
    endLook(e);
    if (e.pointerId !== stickId) return;
    stickId = null;
    s.move.x = 0; s.move.z = 0;
    els.stickBase.classList.add('hidden');
  };
  zone.addEventListener('pointerup', endStick);
  zone.addEventListener('pointercancel', endStick);
  function setKnob(dx, dy) { els.stickKnob.style.transform = `translate(${dx}px, ${dy}px)`; }

  // ---- Drag on the right side (or with a mouse anywhere) = look around ----
  let lookId = null;
  let lookLast = { x: 0, y: 0 };
  const startLook = (e, zoneEl) => {
    if (lookId !== null) return;
    lookId = e.pointerId;
    zoneEl.setPointerCapture(e.pointerId);
    lookLast = { x: e.clientX, y: e.clientY };
  };
  const moveLook = (e) => {
    if (e.pointerId !== lookId) return;
    s.look.dx += e.clientX - lookLast.x;
    s.look.dy += e.clientY - lookLast.y;
    lookLast = { x: e.clientX, y: e.clientY };
  };
  const endLook = (e) => { if (e.pointerId === lookId) lookId = null; };
  const lookZone = els.lookZone;
  lookZone.addEventListener('pointerdown', (e) => { startLook(e, lookZone); if (e.pointerType === 'touch') s.usedTouch = true; });
  lookZone.addEventListener('pointermove', moveLook);
  lookZone.addEventListener('pointerup', endLook);
  lookZone.addEventListener('pointercancel', endLook);

  // ---- Buttons ----
  const hold = (btn, down, up) => {
    btn.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      btn.setPointerCapture(e.pointerId);
      btn.classList.add('pressed');
      s.usedTouch = e.pointerType === 'touch' || s.usedTouch;
      down();
    });
    const release = () => { btn.classList.remove('pressed'); up?.(); };
    btn.addEventListener('pointerup', release);
    btn.addEventListener('pointercancel', release);
  };
  hold(els.btnAttack, () => { s.attack = true; });
  hold(els.btnDodge, () => { s.dodge = true; });
  hold(els.btnBow, () => { s.bowHeld = true; }, () => { if (s.bowHeld) { s.bowHeld = false; s.bowReleased = true; } });
  hold(els.btnPower, () => { s.power = true; });
  hold(els.btnArrow, () => { s.toggleArrow = true; });
  hold(els.btnInteract, () => { s.interact = true; });

  // ---- Keyboard ----
  const keys = new Set();
  const updateKeyMove = () => {
    let x = 0, z = 0;
    if (keys.has('KeyA')) x -= 1;
    if (keys.has('KeyD')) x += 1;
    if (keys.has('KeyW')) z -= 1;
    if (keys.has('KeyS')) z += 1;
    const len = Math.hypot(x, z) || 1;
    if (stickId === null) { s.move.x = x / len; s.move.z = z / len; }
    s.lookKeys.x = (keys.has('ArrowRight') ? 1 : 0) - (keys.has('ArrowLeft') ? 1 : 0);
    s.lookKeys.y = (keys.has('ArrowDown') ? 1 : 0) - (keys.has('ArrowUp') ? 1 : 0);
  };
  window.addEventListener('keydown', (e) => {
    if (e.repeat) return;
    keys.add(e.code);
    switch (e.code) {
      case 'KeyJ': s.attack = true; break;
      case 'KeyK': s.bowHeld = true; break;
      case 'Space': s.dodge = true; e.preventDefault(); break;
      case 'KeyF': s.power = true; break;
      case 'KeyQ': s.toggleArrow = true; break;
      case 'KeyE': s.interact = true; break;
      case 'KeyP': case 'Escape': s.pause = true; break;
      default: break;
    }
    updateKeyMove();
  });
  window.addEventListener('keyup', (e) => {
    keys.delete(e.code);
    if (e.code === 'KeyK' && s.bowHeld) { s.bowHeld = false; s.bowReleased = true; }
    updateKeyMove();
  });
  window.addEventListener('blur', () => {
    keys.clear();
    s.lookKeys.x = 0; s.lookKeys.y = 0;
    s.move.x = 0; s.move.z = 0;
    if (s.bowHeld) { s.bowHeld = false; s.bowReleased = true; }
  });

  s.consume = () => {
    s.attack = false;
    s.bowReleased = false;
    s.dodge = false;
    s.look.dx = 0;
    s.look.dy = 0;
    s.power = false;
    s.toggleArrow = false;
    s.interact = false;
    s.pause = false;
  };
  return s;
}
