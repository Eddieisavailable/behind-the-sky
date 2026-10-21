@tool
class_name WorldArea
extends Node3D
## One place in the world. Each area script extends this and lays itself out in build(),
## using the helpers below (the same ones the prototype's explore.js gave its areas).
##
## The layout is rebuilt every time the scene opens, in the editor too, and is never saved,
## so the .tscn stays a few lines and the layout lives in readable code.
## Coordinates: x east, z south, metres. Kit pieces face +Z; characters face -Z.

const WORLD_LAYER := 1
const HERO_LAYER := 2

@export var area_name := ""
@export var subtitle := ""
@export var arrive := ""
## Time of day: one of Look.MOODS.
@export var mood := "morning"
@export var radius := 30.0
## Press to lay the area out again after editing its script.
@export var rebuild_now := false:
	set(v):
		if v and is_inside_tree():
			rebuild()

## Filled by build().
var spawns := {}
var talks: Array[Dictionary] = []     # { who, pos, line }
var exits: Array[Dictionary] = []     # { to, pos, r, text }
var _updaters: Array[Callable] = []
var _layout: Node3D
var _seed := 1
var _t := 0.0

func _ready() -> void:
	rebuild()

func rebuild() -> void:
	if _layout:
		_layout.free()
	_layout = Node3D.new()
	_layout.name = "Layout"
	add_child(_layout)   # no owner: never written into the .tscn
	spawns = {}
	talks.clear()
	exits.clear()
	_updaters.clear()
	_apply_mood()
	build()

## Override: lay the area out.
func build() -> void:
	pass

func _process(dt: float) -> void:
	_t += dt
	for f in _updaters:
		f.call(dt, _t)

## Where the hero starts, coming from `from` (or "start").
func spawn_for(from: String) -> Dictionary:
	return spawns.get(from, spawns.get("start", { "x": 0.0, "z": 0.0, "face": 0.0 }))

# ------------------------------------------------------------------ helpers for build()

static func col(hex: int) -> Color:
	return Color.hex((hex << 8) | 0xff)

func rnd() -> float:
	_seed = (_seed * 16807) % 2147483647
	return _seed / 2147483647.0

func reseed(s: int) -> void:
	_seed = s

## Yaw that turns a kit piece (front +Z) toward a point.
static func face_to(x: float, z: float, tx: float, tz: float) -> float:
	return atan2(tx - x, tz - z)

## Yaw that turns a character (front -Z) toward a point.
static func look_at_yaw(x: float, z: float, tx: float, tz: float) -> float:
	return atan2(-(tx - x), -(tz - z))

## One kit piece. r: the hero can't walk within this radius of it.
func piece(kit: String, name: String, x: float, z: float, ry := 0.0, s := 1.0, r := 0.0, y := 0.0) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	m.name = name
	m.mesh = Kit.mesh(kit, name)
	m.position = Vector3(x, y, z)
	m.rotation.y = ry
	m.scale = Vector3.ONE * s
	_layout.add_child(m)
	if r > 0.0:
		blocker(x, z, r * s, maxf(m.mesh.get_aabb().end.y * s, 1.0))
	return m

## Many copies of one piece, drawn together: [[x, z, ry, s], ...]. r: blocking radius per unit of scale.
func scatter(kit: String, name: String, list: Array, r := 0.0) -> void:
	if list.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = Kit.mesh(kit, name)
	mm.instance_count = list.size()
	for i in list.size():
		var e: Array = list[i]
		var b := Basis(Vector3.UP, e[2]).scaled(Vector3.ONE * e[3])
		mm.set_instance_transform(i, Transform3D(b, Vector3(e[0], 0, e[1])))
		if r > 0.0:
			blocker(e[0], e[1], r * e[3])
	var inst := MultiMeshInstance3D.new()
	inst.name = name + "s"
	inst.multimesh = mm
	_layout.add_child(inst)

## A round thing the hero walks around, as tall as the thing (so the camera doesn't pass through roofs).
func blocker(x: float, z: float, r: float, h := 3.0) -> void:
	var body := StaticBody3D.new()
	body.collision_layer = WORLD_LAYER
	body.collision_mask = 0
	body.position = Vector3(x, h / 2.0, z)
	var shape := CylinderShape3D.new()
	shape.radius = r
	shape.height = h
	var cs := CollisionShape3D.new()
	cs.shape = shape
	body.add_child(cs)
	_layout.add_child(body)

## An animated person or creature. face: yaw (front -Z). hide: prop names to hide.
func actor(model: String, x: float, z: float, face: float, clip: String, scale := 1.12, hide: Array = [], label_text := "", y := 0.0) -> Node3D:
	# the Blender models face +Z: turn the model round inside a holder that faces -Z
	var a := Node3D.new()
	a.name = model
	a.position = Vector3(x, y, z)
	a.rotation.y = face
	var m: Node3D = Kit.character(model).instantiate()
	m.rotation.y = PI
	m.scale = Vector3.ONE * scale
	a.add_child(m)
	_layout.add_child(a)
	for n in hide:
		var o := a.find_child(n, true, false)
		if o is Node3D:
			o.visible = false
	var ap: AnimationPlayer = a.find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation(clip):
		ap.play(clip)
		ap.seek(randf() * ap.current_animation_length, true)
	if label_text != "":
		label(label_text, x, y + 2.5 * (scale / 1.12), z, 14.0)
	return a

## A floating name, seen from `near` metres.
func label(text: String, x: float, y: float, z: float, near := 18.0, color := Color(1, 0.96, 0.88)) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.position = Vector3(x, y, z)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.font_size = 40
	l.outline_size = 12
	l.pixel_size = 0.006
	l.modulate = color
	l.outline_modulate = Color(0.05, 0.04, 0.03, 0.85)
	l.visibility_range_end = near
	l.visibility_range_end_margin = 2.0
	l.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	l.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_layout.add_child(l)
	return l

## Someone the hero can talk to, standing at x, z.
func talk(who: String, x: float, z: float, line: String) -> void:
	talks.append({ "who": who, "pos": Vector3(x, 0, z), "line": line })

## A way out to another area: a glowing ring on the ground with a sign.
func exit_to(to: String, x: float, z: float, text: String, r := 2.6) -> void:
	exits.append({ "to": to, "pos": Vector3(x, 0, z), "r": r, "text": text })
	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = r * 0.55
	torus.outer_radius = r * 0.75
	torus.rings = 48
	ring.mesh = torus
	ring.scale = Vector3(1, 0.04, 1)
	ring.position = Vector3(x, 0.03, z)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(col(0xf2b33d), 0.35)
	ring.material_override = mat
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_layout.add_child(ring)
	every(func(_dt: float, t: float): mat.albedo_color.a = 0.25 + sin(t * 3.0) * 0.12)
	label("→ " + text, x, 1.4, z, 30.0, col(0xf2c46a))

## Flat ground: earth inside `r`, `edge` colour beyond, and the floor the hero stands on.
func ground(color: int, r: float, edge := 0x24361d) -> void:
	var disc := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = r
	cyl.bottom_radius = r
	cyl.height = 0.1
	cyl.radial_segments = 64
	cyl.rings = 1
	disc.mesh = cyl
	disc.position.y = -0.05
	disc.material_override = _flat(color)
	_layout.add_child(disc)
	var far := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(320, 320)
	far.mesh = plane
	far.position.y = -0.02
	far.material_override = _flat(edge)
	_layout.add_child(far)
	var body := StaticBody3D.new()
	body.collision_layer = WORLD_LAYER
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	cs.shape = WorldBoundaryShape3D.new()
	body.add_child(cs)
	_layout.add_child(body)

## A flat earth path through points [[x, z], ...].
func path(points: Array, width := 2.4, color := 0x8b6a43) -> void:
	var mat := _flat(color)
	for i in points.size() - 1:
		var a := Vector2(points[i][0], points[i][1])
		var b := Vector2(points[i + 1][0], points[i + 1][1])
		var seg := MeshInstance3D.new()
		var plane := PlaneMesh.new()
		plane.size = Vector2(width, a.distance_to(b) + width * 0.6)
		seg.mesh = plane
		seg.material_override = mat
		seg.position = Vector3((a.x + b.x) / 2.0, 0.012 + i * 0.0005, (a.y + b.y) / 2.0)
		seg.rotation.y = atan2(b.x - a.x, b.y - a.y)
		seg.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_layout.add_child(seg)

## Flames with a flickering light.
func fire(x: float, y: float, z: float, s := 1.0) -> void:
	var glow := StandardMaterial3D.new()
	glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	glow.albedo_color = col(0xff9a3a)
	var flame := MeshInstance3D.new()
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = 0.35 * s
	cone.height = 1.1 * s
	cone.radial_segments = 7
	flame.mesh = cone
	flame.material_override = glow
	flame.position = Vector3(x, y + 0.55 * s, z)
	flame.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_layout.add_child(flame)
	var light := OmniLight3D.new()
	light.light_color = col(0xff8a3a)
	light.light_energy = 2.0 * s
	light.omni_range = 9.0 * s
	light.position = Vector3(x, y + 1.2 * s, z)
	_layout.add_child(light)
	var phase := randf() * 10.0
	every(func(_dt: float, t: float):
		var f := 0.85 + sin(t * 13.0 + phase) * 0.08 + sin(t * 7.3 + phase) * 0.07
		light.light_energy = 2.0 * s * f
		flame.scale = Vector3(1, f, 1))

## Run something every frame: f(dt, t).
func every(f: Callable) -> void:
	_updaters.append(f)

func _flat(color: int) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col(color)
	m.roughness = 1.0
	return m

## Swap the lighting for the current Look quality (after a graphics change).
func refresh_look() -> void:
	for n in ["Mood", "Sun"]:
		var old := _layout.get_node_or_null(n)
		if old:
			old.free()
	_apply_mood()

func _apply_mood() -> void:
	var we := WorldEnvironment.new()
	we.name = "Mood"
	we.environment = Look.environment(mood)
	_layout.add_child(we)
	var sun := Look.sun(mood)
	_layout.add_child(sun)
	Look.aim_sun(sun)
