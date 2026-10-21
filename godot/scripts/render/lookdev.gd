extends Node3D
## Look-dev stage: where each realistic asset is judged before it goes into the game.
## Open scenes/lookdev.tscn and press F6. Put the asset's path in "Model Path" in the Inspector.
##
## The stage has the references a look-dev artist checks against:
## - a mid-grey ball (18% grey) and a chrome ball: does the asset sit in the same light as they do?
## - a colour chart (the standard 24 patches): are skin and cloth colours believable next to it?
## - height poles at 1.60 m and 1.80 m.
## - the game's own lighting for each time of day, plus a neutral studio light.
##
## Keys: 1–7 lighting · T turntable · F face · B full body · N next animation
##       G graphics quality · drag to orbit · right-drag to pan up/down · wheel to zoom

@export_file("*.glb", "*.tscn") var model_path := "res://assets/models/characters/korto.glb"
@export var start_light := "morning"

const LIGHTS := ["studio", "morning", "day", "afternoon", "dusk", "bush", "night"]
## The 24 patches of the standard colour chart (sRGB 0–255).
const CHART := [
	[115, 82, 68], [194, 150, 130], [98, 122, 157], [87, 108, 67], [133, 128, 177], [103, 189, 170],
	[214, 126, 44], [80, 91, 166], [193, 90, 99], [94, 60, 108], [157, 188, 64], [224, 163, 46],
	[56, 61, 150], [70, 148, 73], [175, 54, 60], [231, 199, 31], [187, 86, 149], [8, 133, 161],
	[243, 243, 242], [200, 200, 200], [160, 160, 160], [122, 122, 121], [85, 85, 85], [52, 52, 52],
]

var model: Node3D
var anim: AnimationPlayer
var light := ""
var turntable := false
var _clips: PackedStringArray = []
var _clip := -1
var _lights: Node3D
var _pivot: Node3D
var _cam: Camera3D
var _yaw := 0.4
var _pitch := 0.12
var _dist := 3.2
var _focus_y := 0.95
var _info: Label

func _ready() -> void:
	InputSetup.ensure()
	Look.apply_viewport(get_viewport())
	_build_stage()
	_load_model()
	_build_ui()
	set_light(start_light)
	view_body()

# ------------------------------------------------------------------ controls

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		var k: int = e.physical_keycode
		if k >= KEY_1 and k <= KEY_7:
			set_light(LIGHTS[k - KEY_1])
		match k:
			KEY_T: turntable = not turntable
			KEY_F: view_face()
			KEY_B: view_body()
			KEY_N: next_clip()
			KEY_G: next_quality()
		_update_info()
	elif e is InputEventMouseMotion:
		if e.button_mask & MOUSE_BUTTON_MASK_LEFT:
			_yaw -= e.relative.x * 0.006
			_pitch = clampf(_pitch + e.relative.y * 0.004, -0.4, 1.2)
		elif e.button_mask & MOUSE_BUTTON_MASK_RIGHT:
			_focus_y = clampf(_focus_y + e.relative.y * 0.004, 0.1, 2.2)
	elif e is InputEventMouseButton and e.pressed:
		if e.button_index == MOUSE_BUTTON_WHEEL_UP:
			_dist = maxf(0.35, _dist * 0.9)
		elif e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_dist = minf(12.0, _dist * 1.1)

func _process(dt: float) -> void:
	if turntable and model:
		model.rotation.y += dt * 0.5
	_pivot.position = Vector3(0, _focus_y, 0)
	_pivot.rotation = Vector3(-_pitch, _yaw, 0)
	_cam.position = Vector3(0, 0, _dist)

func view_face() -> void:
	_focus_y = _head_height()
	_dist = 0.6
	_pitch = 0.05
	_cam.fov = 30.0

func view_body() -> void:
	_focus_y = 0.95
	_dist = 3.4
	_pitch = 0.12
	_cam.fov = 35.0

func next_clip() -> void:
	if _clips.is_empty():
		return
	_clip = (_clip + 1) % _clips.size()
	anim.play(_clips[_clip])

func next_quality() -> void:
	var i := (Look.QUALITIES.find(Look.current()) + 1) % Look.QUALITIES.size()
	Look.quality = Look.QUALITIES[i]
	Look.apply_viewport(get_viewport())
	set_light(light)

## Light the stage like a time of day in the game, or with the neutral studio light.
func set_light(which: String) -> void:
	light = which
	if _lights:
		_lights.free()
	_lights = Node3D.new()
	_lights.name = "Lights"
	add_child(_lights)
	var we := WorldEnvironment.new()
	if which == "studio":
		we.environment = _studio_environment()
		_studio_lights()
	else:
		we.environment = Look.environment(which)
		var sun := Look.sun(which)
		_lights.add_child(sun)
		Look.aim_sun(sun)
	_lights.add_child(we)
	_update_info()

# ------------------------------------------------------------------ the stage

func _build_stage() -> void:
	var floor_mesh := CylinderMesh.new()
	floor_mesh.top_radius = 8.0
	floor_mesh.bottom_radius = 8.0
	floor_mesh.height = 0.05
	floor_mesh.radial_segments = 96
	var floor_mi := MeshInstance3D.new()
	floor_mi.mesh = floor_mesh
	floor_mi.position.y = -0.025
	floor_mi.material_override = _mat(Color(0.46, 0.46, 0.46), 0.9)
	add_child(floor_mi)

	# grey and chrome balls on short stands to her right
	for b in [[Vector3(1.0, 0.0, 0.3), _mat(Color(0.46, 0.46, 0.46), 0.6)], [Vector3(1.0, 0.0, -0.1), _mat(Color(0.95, 0.95, 0.95), 0.04, 1.0)]]:
		var stand := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.015
		cyl.bottom_radius = 0.06
		cyl.height = 1.0
		stand.mesh = cyl
		stand.position = b[0] + Vector3(0, 0.5, 0)
		stand.material_override = _mat(Color(0.1, 0.1, 0.1), 0.5)
		add_child(stand)
		var ball := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = 0.09
		sphere.height = 0.18
		ball.mesh = sphere
		ball.position = b[0] + Vector3(0, 1.09, 0)
		ball.material_override = b[1]
		add_child(ball)

	# the colour chart on an easel to her left, 4 rows of 6
	var chart := Node3D.new()
	chart.position = Vector3(-1.1, 0.8, 0.2)
	chart.rotation.y = 0.35
	add_child(chart)
	var board := MeshInstance3D.new()
	var board_mesh := BoxMesh.new()
	board_mesh.size = Vector3(0.62, 0.43, 0.01)
	board.mesh = board_mesh
	board.material_override = _mat(Color(0.03, 0.03, 0.03), 0.8)
	board.position.z = -0.006
	chart.add_child(board)
	for i in CHART.size():
		var c: Array = CHART[i]
		var patch := MeshInstance3D.new()
		var quad := QuadMesh.new()
		quad.size = Vector2(0.088, 0.088)
		patch.mesh = quad
		patch.position = Vector3(-0.25 + (i % 6) * 0.1, 0.15 - (i / 6) * 0.1, 0)
		patch.material_override = _mat(Color8(c[0], c[1], c[2]), 0.9)
		chart.add_child(patch)
	var leg := MeshInstance3D.new()
	var leg_mesh := BoxMesh.new()
	leg_mesh.size = Vector3(0.03, 0.8, 0.03)
	leg.mesh = leg_mesh
	leg.position = Vector3(0, -0.4, -0.03)
	leg.material_override = _mat(Color(0.1, 0.1, 0.1), 0.6)
	chart.add_child(leg)

	# height poles behind her: 1.60 m and 1.80 m
	for h in [1.6, 1.8]:
		var pole := MeshInstance3D.new()
		var pm := BoxMesh.new()
		pm.size = Vector3(0.02, h, 0.02)
		pole.mesh = pm
		pole.position = Vector3(-0.55 if h < 1.7 else 0.55, h / 2.0, -0.7)
		pole.material_override = _mat(Color(0.8, 0.75, 0.6), 0.6)
		add_child(pole)
		var tag := Label3D.new()
		tag.text = "%.2f m" % h
		tag.font_size = 32
		tag.pixel_size = 0.002
		tag.position = pole.position + Vector3(0, h / 2.0 + 0.05, 0)
		tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		add_child(tag)

	_pivot = Node3D.new()
	add_child(_pivot)
	_cam = Camera3D.new()
	_cam.near = 0.02
	_pivot.add_child(_cam)
	_cam.current = true

func _load_model() -> void:
	if model_path == "" or not ResourceLoader.exists(model_path):
		push_warning("Look-dev: no model at '%s'" % model_path)
		return
	var holder := Node3D.new()
	holder.name = "Asset"
	add_child(holder)
	var inst: Node3D = load(model_path).instantiate()
	# the models face +Z, which is toward the camera's starting side: no turn needed
	holder.add_child(inst)
	model = holder
	anim = inst.find_child("AnimationPlayer", true, false)
	if anim:
		_clips = anim.get_animation_list()
		var idle := _clips.find("Idle")
		_clip = idle if idle >= 0 else 0
		if not _clips.is_empty():
			anim.play(_clips[_clip])

func _head_height() -> float:
	var skel: Skeleton3D = model.find_child("Skeleton3D", true, false) if model else null
	if skel:
		for name in ["head", "Head", "head_01", "neck_02"]:
			var i := skel.find_bone(name)
			if i >= 0:
				return (skel.global_transform * skel.get_bone_global_pose(i)).origin.y + 0.08
	return 1.55

func _studio_environment() -> Environment:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.11, 0.11, 0.12)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.5, 0.5, 0.55)
	env.ambient_light_energy = 0.25
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.ssao_enabled = Look.current() != "low"
	return env

## Key, fill and rim: the neutral light for judging materials.
func _studio_lights() -> void:
	for l in [[Vector3(2.2, 2.4, 2.0), 3.0, Color(1, 0.96, 0.9)], [Vector3(-2.6, 1.6, 1.4), 0.9, Color(0.85, 0.9, 1)], [Vector3(-0.8, 2.6, -2.6), 2.4, Color(1, 1, 1)]]:
		var s := SpotLight3D.new()
		s.light_energy = l[1] * 2.2
		s.light_color = l[2]
		s.spot_range = 12.0
		s.spot_angle = 40.0
		s.shadow_enabled = true
		s.light_size = 0.4
		_lights.add_child(s)
		s.look_at_from_position(l[0], Vector3(0, 1.1, 0))

func _mat(c: Color, rough: float, metal := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	m.metallic = metal
	return m

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_info = Label.new()
	_info.position = Vector2(16, 12)
	_info.add_theme_font_size_override("font_size", 15)
	_info.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	_info.add_theme_constant_override("outline_size", 4)
	layer.add_child(_info)

func _update_info() -> void:
	if _info == null:
		return
	_info.text = "%s\nlight: %s   graphics: %s   turntable: %s   clip: %s\n1–7 light · T turntable · F face · B body · N next clip · G graphics · drag orbit · right-drag height · wheel zoom" % [
		model_path.get_file(), light, Look.current(), "on" if turntable else "off", _clips[_clip] if _clip >= 0 and _clip < _clips.size() else "-"]
