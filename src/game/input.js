// One input state for touch (joystick + look-drag + buttons) and PC (mouse + keyboard).
// `move` is the raw stick (x right, z down the screen); game.js turns it into a
// world direction relative to the camera.
//
// PC controls, like most third-person action games:
//   mouse moves the camera (the pointer is captured after a click; Esc frees it)
//   left click = cutlass · hold right click = draw the bow, release to shoot
//   WASD or arrow keys = move · Space or Shift = roll · F = Hornbill sight
//   Q or mouse wheel = switch arrows · E = burn / pay / forge · P or Esc = pause

import { CAMERA } from '../config.js';

const STICK_MAX = 52;      // px the knob can travel

export function createInput(els) {
  const s = {
    move: { x: 0, z: 0 },
    bowHeld: false,
    // one-shot events, cleared by consume()
    attack: false,
    bowReleased: false,
    dodge: false,
    look: { dx: 0, dy: 0 },   // touch-drag pixels (mouse movement is scaled to match)
    pointerLocked: false,
    lockLost: false,          // one-shot: the player pressed Esc or switched windows mid-fight
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
    if (e.pointerType === 'mouse') return; // the mouse is handled below
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
  lookZone.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse') return;
    startLook(e, lookZone);
    s.usedTouch = true;
  });

  // ---- Mouse: captured pointer for the camera, left click cut, right click bow ----
  const lockTarget = els.lockTarget;
  // only computers with a real mouse capture the pointer; phones and tablets use touch
  const hasMouse = typeof matchMedia === 'function' && matchMedia('(pointer: fine)').matches;
  let lockFailed = !hasMouse || typeof lockTarget.requestPointerLock !== 'function';
  let intentionalUnlock = false;
  let fallbackDrag = false;      // when the pointer can't be captured: hold right click to look
  const isGameArea = (t) => t === els.canvas || t === zone || t === lookZone || t === lockTarget;
  const releaseBow = () => { if (s.bowHeld) { s.bowHeld = false; s.bowReleased = true; } };

  let lockReturnsPromise = true;
  const tryLock = (opts) => {
    try {
      const p = opts ? lockTarget.requestPointerLock(opts) : lockTarget.requestPointerLock();
      if (!p?.then) { lockReturnsPromise = false; return Promise.resolve(); }
      return p;
    } catch (err) {
      return Promise.reject(err);
    }
  };
  s.lockPointer = () => {
    if (lockFailed || s.usedTouch || document.pointerLockElement === lockTarget) return;
    // raw mouse input first (no OS acceleration); some browsers refuse it, so fall back once
    tryLock({ unadjustedMovement: true })
      .catch(() => tryLock())
      .catch(() => { lockFailed = true; });
  };
  s.releasePointer = () => {
    if (document.pointerLockElement) {
      intentionalUnlock = true;
      document.exitPointerLock();
    }
  };
  s.canLock = () => !lockFailed && !s.usedTouch;

  let skipMoves = 0;
  document.addEventListener('pointerlockchange', () => {
    const locked = document.pointerLockElement === lockTarget;
    skipMoves = 2; // browsers often report one bogus jump right as the mouse is captured or freed
    if (!locked && s.pointerLocked) {
      releaseBow();
      if (!intentionalUnlock) s.lockLost = true;
    }
    s.pointerLocked = locked;
    intentionalUnlock = false;
  });
  // older browsers only report failure through this event
  document.addEventListener('pointerlockerror', () => { if (!lockReturnsPromise) lockFailed = true; });

  window.addEventListener('mousedown', (e) => {
    if (s.pointerLocked) {
      if (e.button === 0) s.attack = true;
      if (e.button === 2) s.bowHeld = true;
      e.preventDefault();
      return;
    }
    if (!isGameArea(e.target) || !s.inPlay?.()) return;
    if (!lockFailed) {
      s.lockPointer();
      return;
    }
    // no pointer capture available: left click still cuts, right-drag looks and aims
    if (e.button === 0) s.attack = true;
    if (e.button === 2) { s.bowHeld = true; fallbackDrag = true; }
  });
  window.addEventListener('mouseup', (e) => {
    if (e.button === 2) { releaseBow(); fallbackDrag = false; }
  });
  window.addEventListener('mousemove', (e) => {
    if (s.pointerLocked || fallbackDrag) {
      if (skipMoves > 0) { skipMoves -= 1; return; }
      if (Math.abs(e.movementX) > 300 || Math.abs(e.movementY) > 300) return; // spike, not a hand
      const k = CAMERA.mouseSensitivity / CAMERA.sensitivity;
      s.look.dx += e.movementX * k;
      s.look.dy += e.movementY * k;
    }
  });
  let wheelAt = 0;
  window.addEventListener('wheel', (e) => {
    if (!s.pointerLocked && !isGameArea(e.target)) return;
    const now = performance.now();
    if (Math.abs(e.deltaY) > 4 && now - wheelAt > 180) { s.toggleArrow = true; wheelAt = now; }
  }, { passive: true });
  lockTarget.addEventListener('contextmenu', (e) => e.preventDefault());
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
    // arrow keys move exactly like WASD: up forward, down back, left and right
    if (keys.has('KeyA') || keys.has('ArrowLeft')) x -= 1;
    if (keys.has('KeyD') || keys.has('ArrowRight')) x += 1;
    if (keys.has('KeyW') || keys.has('ArrowUp')) z -= 1;
    if (keys.has('KeyS') || keys.has('ArrowDown')) z += 1;
    const len = Math.hypot(x, z) || 1;
    if (stickId === null) { s.move.x = x / len; s.move.z = z / len; }
  };
  window.addEventListener('keydown', (e) => {
    if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault(); // keep the page from scrolling
    if (e.repeat) return;
    keys.add(e.code);
    switch (e.code) {
      case 'KeyJ': s.attack = true; break;
      case 'KeyK': s.bowHeld = true; break;
      case 'Space': case 'ShiftLeft': case 'ShiftRight': s.dodge = true; break;
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
    fallbackDrag = false;
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
    s.lockLost = false;
  };
  return s;
}
