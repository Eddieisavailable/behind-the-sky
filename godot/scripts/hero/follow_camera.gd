class_name FollowCamera
extends Node3D
## Third-person camera over the hero's shoulder. Mouse, right stick or a drag on the right half
## of a touch screen turns it; the mouse wheel zooms. When she runs and you leave the camera alone,
## it eases round behind her. A spring arm pulls it in front of walls and houses.

var target: Hero
var yaw := 0.0
var pitch: float = Tuning.CAMERA.pitch
var distance: float = Tuning.CAMERA.distance
var _since_look := 99.0
var arm: SpringArm3D
var cam: Camera3D

func _ready() -> void:
	top_level = true
	var C: Dictionary = Tuning.CAMERA
	arm = SpringArm3D.new()
	arm.collision_mask = WorldArea.WORLD_LAYER
	var probe := SphereShape3D.new()
	probe.radius = 0.25
	arm.shape = probe
	arm.margin = 0.2
	arm.spring_length = distance
	add_child(arm)
	cam = Camera3D.new()
	cam.fov = C.fov
	cam.near = 0.1
	cam.far = 400.0
	cam.position.x = C.shoulder
	arm.add_child(cam)
	cam.current = true

func snap_behind() -> void:
	yaw = target.yaw
	global_position = _anchor()
	_apply()

## Turn the view by a drag of dx, dy pixels (mouse or touch), with the given sensitivity.
func look(dx: float, dy: float, sens: float) -> void:
	var C: Dictionary = Tuning.CAMERA
	yaw -= dx * sens
	pitch = clampf(pitch + dy * sens, C.min_pitch, C.max_pitch)
	_since_look = 0.0

func zoom(steps: float) -> void:
	distance = clampf(distance + steps * 0.6, Tuning.CAMERA.min_distance, Tuning.CAMERA.distance)

func _unhandled_input(e: InputEvent) -> void:
	# touches arrive as emulated mouse events too; the HUD handles those
	if e is InputEventMouseMotion and e.device != InputEvent.DEVICE_ID_EMULATION and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		look(e.relative.x, e.relative.y, Tuning.CAMERA.mouse_sensitivity)
	elif e is InputEventMouseButton and e.pressed and e.device != InputEvent.DEVICE_ID_EMULATION:
		if e.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom(-1)
		elif e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom(1)

func _process(dt: float) -> void:
	if target == null:
		return
	var C: Dictionary = Tuning.CAMERA
	var stick := Input.get_vector("look_left", "look_right", "look_up", "look_down")
	if stick.length() > 0.0:
		look(stick.x * 900.0 * dt, stick.y * 600.0 * dt, 0.0035)
	_since_look += dt
	# Ease round behind her while she runs away from the camera and the player isn't steering it.
	# How hard it follows fades with the angle: nothing while she strafes across the view,
	# and never when she runs toward the camera (that used to spin it round).
	if _since_look > C.follow_delay and target.ground_speed() > 1.0:
		var away := cos(angle_difference(yaw, target.yaw))
		if away > 0.0:
			yaw = lerp_angle(yaw, target.yaw, 1.0 - exp(-C.follow_rate * 0.35 * away * dt))
	target.view_yaw = yaw
	global_position = global_position.lerp(_anchor(), 1.0 - exp(-14.0 * dt))
	_apply()

func _anchor() -> Vector3:
	return target.global_position + Vector3(0, Tuning.CAMERA.height * target.stats.scale, 0)

func _apply() -> void:
	rotation = Vector3(-pitch, yaw, 0)
	arm.spring_length = distance
