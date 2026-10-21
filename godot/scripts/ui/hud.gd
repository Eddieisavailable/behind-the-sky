class_name Hud
extends CanvasLayer
## On-screen text and touch controls for walking the world:
## the area's title card, the "talk" prompt, what people say, short notices, the pause menu,
## and on touch screens a move stick (left thumb), drag-to-look (right side) and an action button.

signal interact_pressed
signal resume_pressed
signal quit_pressed

var stick := Vector2.ZERO          # touch move, x right, y down, length ≤ 1
var look_drag := Vector2.ZERO      # touch look, pixels since last frame; read and cleared by Main
var touch_mode := false

var _title: Label
var _sub: Label
var _title_box: VBoxContainer
var _prompt: Label
var _action: Button
var _say_box: PanelContainer
var _say_who: Label
var _say_line: Label
var _toast: Label
var _pause: Control
var _fps: Label
var _stick_base: Panel
var _stick_knob: Panel
var _stick_finger := -1
var _stick_origin := Vector2.ZERO
var _look_finger := -1
var _say_left := 0.0
var _toast_left := 0.0
var _title_left := 0.0

const STICK_RADIUS := 70.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	touch_mode = DisplayServer.is_touchscreen_available() and OS.has_feature("mobile")
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	_title_box = VBoxContainer.new()
	_pin(_title_box, Control.PRESET_TOP_WIDE, 0, 60, 0, 160)
	_title_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_title_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_title_box)
	_title = _text(52, Color(1, 0.95, 0.85))
	_sub = _text(22, Color(0.95, 0.88, 0.72))
	_title_box.add_child(_title)
	_title_box.add_child(_sub)

	_prompt = _text(24, Color(1, 0.93, 0.75))
	_pin(_prompt, Control.PRESET_BOTTOM_WIDE, 0, -200, 0, -160)
	root.add_child(_prompt)

	_say_box = PanelContainer.new()
	_pin(_say_box, Control.PRESET_CENTER_BOTTOM, -360, -150, 360, -40)
	_say_box.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_say_box.add_theme_stylebox_override("panel", _box(Color(0.08, 0.06, 0.04, 0.78)))
	_say_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var say := VBoxContainer.new()
	_say_who = _text(20, Color(0.95, 0.72, 0.35))
	_say_who.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	_say_line = _text(24, Color(1, 0.97, 0.9))
	_say_line.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	_say_line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	say.add_child(_say_who)
	say.add_child(_say_line)
	_say_box.add_child(say)
	_say_box.visible = false
	root.add_child(_say_box)

	_toast = _text(22, Color(1, 0.93, 0.8))
	_pin(_toast, Control.PRESET_TOP_WIDE, 0, 200, 0, 240)
	root.add_child(_toast)

	_fps = _text(14, Color(1, 1, 1, 0.6))
	_fps.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_pin(_fps, Control.PRESET_TOP_RIGHT, -160, 10, -14, 30)
	root.add_child(_fps)

	_action = Button.new()
	_pin(_action, Control.PRESET_BOTTOM_RIGHT, -200, -160, -40, -60)
	_action.add_theme_font_size_override("font_size", 24)
	_action.visible = false
	_action.pressed.connect(func(): interact_pressed.emit())
	root.add_child(_action)

	_stick_base = _circle(STICK_RADIUS, Color(1, 1, 1, 0.12))
	_stick_knob = _circle(32, Color(1, 1, 1, 0.35))
	_stick_base.visible = false
	_stick_knob.visible = false
	root.add_child(_stick_base)
	root.add_child(_stick_knob)

	_build_pause(root)

func _process(dt: float) -> void:
	_fps.text = "%d fps" % Engine.get_frames_per_second()
	_title_left -= dt
	_title_box.modulate.a = clampf(_title_left, 0.0, 1.0)
	_say_left -= dt
	if _say_left <= 0.0:
		_say_box.visible = false
	_toast_left -= dt
	_toast.modulate.a = clampf(_toast_left, 0.0, 1.0)

func show_title(title: String, sub: String) -> void:
	_title.text = title
	_sub.text = sub
	_title_left = 4.5

## The action you can take here, or "" for none.
func set_prompt(text: String) -> void:
	if touch_mode:
		_action.visible = text != ""
		_action.text = text
		_prompt.text = ""
	else:
		_prompt.text = ("E   " + text) if text != "" else ""

func say(who: String, line: String) -> void:
	_say_who.text = who.substr(0, 1).to_upper() + who.substr(1)
	_say_line.text = line
	_say_box.visible = true
	_say_left = 3.0 + line.length() * 0.05

func toast(text: String, seconds := 3.0) -> void:
	_toast.text = text
	_toast_left = seconds

func show_pause(on: bool) -> void:
	_pause.visible = on

func is_paused_menu() -> bool:
	return _pause.visible

# ---------------------------------------------------------------- touch

func _input(e: InputEvent) -> void:
	if not (e is InputEventScreenTouch or e is InputEventScreenDrag):
		return
	touch_mode = true
	var half := get_viewport().get_visible_rect().size.x * 0.5
	if e is InputEventScreenTouch:
		if e.pressed:
			if e.position.x < half and _stick_finger == -1:
				_stick_finger = e.index
				_stick_origin = e.position
				_stick_base.visible = true
				_stick_knob.visible = true
				_place(_stick_base, e.position, STICK_RADIUS)
				_place(_stick_knob, e.position, 32)
			elif e.position.x >= half and _look_finger == -1 and not _action.get_global_rect().has_point(e.position):
				_look_finger = e.index
		else:
			if e.index == _stick_finger:
				_stick_finger = -1
				stick = Vector2.ZERO
				_stick_base.visible = false
				_stick_knob.visible = false
			elif e.index == _look_finger:
				_look_finger = -1
	elif e is InputEventScreenDrag:
		if e.index == _stick_finger:
			var d: Vector2 = (e.position - _stick_origin).limit_length(STICK_RADIUS)
			stick = d / STICK_RADIUS
			_place(_stick_knob, _stick_origin + d, 32)
		elif e.index == _look_finger:
			look_drag += e.relative

# ---------------------------------------------------------------- building blocks

func _build_pause(root: Control) -> void:
	_pause = ColorRect.new()
	_pause.color = Color(0.03, 0.04, 0.03, 0.7)
	_pause.set_anchors_preset(Control.PRESET_FULL_RECT)
	_pause.visible = false
	root.add_child(_pause)
	var box := VBoxContainer.new()
	_pin(box, Control.PRESET_CENTER, -170, -140, 170, 140)
	box.add_theme_constant_override("separation", 14)
	_pause.add_child(box)
	box.add_child(_text(40, Color(1, 0.95, 0.85), "Paused"))
	for b in [["Resume", resume_pressed], ["Quit", quit_pressed]]:
		var btn := Button.new()
		btn.text = b[0]
		btn.custom_minimum_size = Vector2(320, 56)
		btn.add_theme_font_size_override("font_size", 24)
		var sig: Signal = b[1]
		btn.pressed.connect(func(): sig.emit())
		box.add_child(btn)
	box.add_child(_text(16, Color(1, 1, 1, 0.7), "WASD or arrows: walk   ·   mouse: look   ·   wheel: zoom\nE: talk   ·   Esc: pause   ·   gamepad works too"))

func _text(size: int, color: Color, text := "") -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0.05, 0.04, 0.03, 0.9))
	l.add_theme_constant_override("outline_size", maxi(4, size / 5))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l

func _box(c: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(10)
	s.set_content_margin_all(16)
	return s

func _circle(r: float, c: Color) -> Panel:
	var p := Panel.new()
	var s := StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(int(r))
	p.add_theme_stylebox_override("panel", s)
	p.size = Vector2(r, r) * 2.0
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return p

func _place(p: Control, center: Vector2, r: float) -> void:
	p.position = center - Vector2(r, r)

## Anchor a control to a preset and give its edges as offsets from those anchors.
func _pin(c: Control, preset: int, left: float, top: float, right: float, bottom: float) -> void:
	c.set_anchors_preset(preset)
	c.offset_left = left
	c.offset_top = top
	c.offset_right = right
	c.offset_bottom = bottom
