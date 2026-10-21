class_name Hero
extends CharacterBody3D
## Korto or Flomo walking the world: moves relative to the camera, turns to face the way she goes,
## runs or idles, stays inside the area. Fighting and climbing come in the gameplay step.

const GRAVITY := 22.0
const TURN_RATE := 12.0
const ACCEL := 14.0

var key := "korto"
var stats: Dictionary
var model: Node3D
var anim: AnimationPlayer
## The camera's yaw: "forward" is away from the camera.
var view_yaw := 0.0
## Extra move input from the touch stick (x right, y down), added to the keys and gamepad.
var touch_move := Vector2.ZERO
## Walkable radius of the current area (0: no limit).
var bounds := 0.0
var yaw := 0.0
var frozen := false

func setup(hero_key: String) -> void:
	key = hero_key
	stats = Tuning.HEROES[hero_key]
	name = "Hero"
	collision_layer = WorldArea.HERO_LAYER
	collision_mask = WorldArea.WORLD_LAYER
	floor_snap_length = 0.4
	var shape := CapsuleShape3D.new()
	shape.radius = 0.35
	shape.height = 1.7 * stats.scale
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.position.y = shape.height / 2.0
	add_child(cs)
	model = load(stats.model).instantiate()
	model.scale = Vector3.ONE * stats.scale
	add_child(model)
	anim = model.find_child("AnimationPlayer", true, false)
	_play("Idle")

## Put her at a spawn point: { x, z, face } (face is a character yaw, front -Z).
func place(spawn: Dictionary) -> void:
	position = Vector3(spawn.x, 0, spawn.z)
	velocity = Vector3.ZERO
	yaw = spawn.face
	model.rotation.y = yaw

func move_input() -> Vector2:
	var v := Input.get_vector("move_left", "move_right", "move_forward", "move_back") + touch_move
	return v.limit_length(1.0)

func _physics_process(dt: float) -> void:
	var input := Vector2.ZERO if frozen else move_input()
	var forward := Vector3(-sin(view_yaw), 0, -cos(view_yaw))
	var right := Vector3(cos(view_yaw), 0, -sin(view_yaw))
	var want := (right * input.x - forward * input.y) * float(stats.speed)
	var flat := Vector3(velocity.x, 0, velocity.z).lerp(want, 1.0 - exp(-ACCEL * dt))
	velocity.x = flat.x
	velocity.z = flat.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - GRAVITY * dt
	move_and_slide()

	if bounds > 0.0:
		var p := Vector2(position.x, position.z)
		var lim := bounds - 0.6
		if p.length() > lim:
			p = p.normalized() * lim
			position.x = p.x
			position.z = p.y

	var speed := flat.length()
	if input.length() > 0.1:
		yaw = lerp_angle(yaw, atan2(-want.x, -want.z), 1.0 - exp(-TURN_RATE * dt))
		model.rotation.y = yaw
	if speed > 0.4:
		_play("Run", clampf(speed / float(stats.speed), 0.6, 1.25))
	else:
		_play("Idle")

## Horizontal speed, m/s.
func ground_speed() -> float:
	return Vector2(velocity.x, velocity.z).length()

func _play(clip: String, rate := 1.0) -> void:
	if anim == null or not anim.has_animation(clip):
		return
	if anim.current_animation != clip:
		anim.play(clip, 0.18)
	anim.speed_scale = rate
