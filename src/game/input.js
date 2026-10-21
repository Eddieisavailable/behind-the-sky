// One input state for touch (joystick + buttons + swipe) and keyboard.
// The camera looks north (−z), so screen-right is +x and screen-down is +z.

const STICK_MAX = 52;      // px the knob can travel
const SWIPE_MIN = 45;      // px for a swipe to count as a roll
const SWIPE_MAX_MS = 320;

export function createInput(els) {
  const s = {
    move: { x: 0, z: 0 },
    bowHeld: false,
    // one-shot events, cleared by consume()
    attack: false,
    bowReleased: false,
    dodge: null,           // null or { x, z } (zero vector = roll where you face)
    power: false,
    toggleArrow: false,
    interact: false,
    pause: false,
    strike: false,
    usedTouch: false,
  };

  // ---- Joystick (appears where the left thumb lands) ----
  let stickId = null;
  let origin = { x: 0, y: 0 };
  const zone = els.stickZone;
  zone.addEventListener('pointerdown', (e) => {
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
    if (e.pointerId !== stickId) return;
    stickId = null;
    s.move.x = 0; s.move.z = 0;
    els.stickBase.classList.add('hidden');
  };
  zone.addEventListener('pointerup', endStick);
  zone.addEventListener('pointercancel', endStick);
  function setKnob(dx, dy) { els.stickKnob.style.transform = `translate(${dx}px, ${dy}px)`; }

  // ---- Swipe on the right side = roll ----
  const swipes = new Map();
  els.swipeZone.addEventListener('pointerdown', (e) => {
    swipes.set(e.pointerId, { x: e.clientX, y: e.clientY, t: performance.now() });
    s.usedTouch = true;
  });
  els.swipeZone.addEventListener('pointerup', (e) => {
    const start = swipes.get(e.pointerId);
    swipes.delete(e.pointerId);
    if (!start) return;
    const dx = e.clientX - start.x;
    const dy = e.clientY - start.y;
    const len = Math.hypot(dx, dy);
    if (len >= SWIPE_MIN && performance.now() - start.t <= SWIPE_MAX_MS) {
      s.dodge = { x: dx / len, z: dy / len };
    }
  });
  els.swipeZone.addEventListener('pointercancel', (e) => swipes.delete(e.pointerId));

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
  hold(els.btnDodge, () => { s.dodge = { x: 0, z: 0 }; });
  hold(els.btnBow, () => { s.bowHeld = true; }, () => { if (s.bowHeld) { s.bowHeld = false; s.bowReleased = true; } });
  hold(els.btnPower, () => { s.power = true; });
  hold(els.btnArrow, () => { s.toggleArrow = true; });
  hold(els.btnInteract, () => { s.interact = true; });

  // ---- Keyboard ----
  const keys = new Set();
  const updateKeyMove = () => {
    let x = 0, z = 0;
    if (keys.has('KeyA') || keys.has('ArrowLeft')) x -= 1;
    if (keys.has('KeyD') || keys.has('ArrowRight')) x += 1;
    if (keys.has('KeyW') || keys.has('ArrowUp')) z -= 1;
    if (keys.has('KeyS') || keys.has('ArrowDown')) z += 1;
    const len = Math.hypot(x, z) || 1;
    if (stickId === null) { s.move.x = x / len; s.move.z = z / len; }
  };
  window.addEventListener('keydown', (e) => {
    if (e.repeat) return;
    keys.add(e.code);
    switch (e.code) {
      case 'KeyJ': s.attack = true; break;
      case 'KeyK': s.bowHeld = true; break;
      case 'Space': s.dodge = { x: 0, z: 0 }; s.strike = true; e.preventDefault(); break;
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
    s.move.x = 0; s.move.z = 0;
    if (s.bowHeld) { s.bowHeld = false; s.bowReleased = true; }
  });

  s.consume = () => {
    s.attack = false;
    s.bowReleased = false;
    s.dodge = null;
    s.power = false;
    s.toggleArrow = false;
    s.interact = false;
    s.pause = false;
    s.strike = false;
  };
  return s;
}
