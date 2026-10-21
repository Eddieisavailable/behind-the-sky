class_name InputSetup
## The game's controls, defined in code so they live in one readable place.
## Keyboard and mouse, plus a gamepad. Touch is handled by the HUD (scripts/ui/hud.gd).

const KEYS := {
	"move_forward": [KEY_W, KEY_UP],
	"move_back": [KEY_S, KEY_DOWN],
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"interact": [KEY_E],
	"pause": [KEY_ESCAPE],
}
const PAD_AXES := {
	"move_forward": [JOY_AXIS_LEFT_Y, -1.0], "move_back": [JOY_AXIS_LEFT_Y, 1.0],
	"move_left": [JOY_AXIS_LEFT_X, -1.0], "move_right": [JOY_AXIS_LEFT_X, 1.0],
	"look_up": [JOY_AXIS_RIGHT_Y, -1.0], "look_down": [JOY_AXIS_RIGHT_Y, 1.0],
	"look_left": [JOY_AXIS_RIGHT_X, -1.0], "look_right": [JOY_AXIS_RIGHT_X, 1.0],
}
const PAD_BUTTONS := { "interact": [JOY_BUTTON_A], "pause": [JOY_BUTTON_START] }

static func ensure() -> void:
	if InputMap.has_action("move_forward"):
		return
	for action in ["move_forward", "move_back", "move_left", "move_right", "look_up", "look_down", "look_left", "look_right", "interact", "pause"]:
		InputMap.add_action(action, 0.2)
	for action in KEYS:
		for k in KEYS[action]:
			var e := InputEventKey.new()
			e.physical_keycode = k
			InputMap.action_add_event(action, e)
	for action in PAD_AXES:
		var e := InputEventJoypadMotion.new()
		e.axis = PAD_AXES[action][0]
		e.axis_value = PAD_AXES[action][1]
		InputMap.action_add_event(action, e)
	for action in PAD_BUTTONS:
		for b in PAD_BUTTONS[action]:
			var e := InputEventJoypadButton.new()
			e.button_index = b
			InputMap.action_add_event(action, e)
