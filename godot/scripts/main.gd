class_name Main
extends Node
## Walk the world: loads an area, puts the hero and camera in it, and handles talking,
## exits between areas and the pause menu. Areas not yet ported say so instead of loading.

const AREAS := {
	"gbelewala": "res://scenes/areas/gbelewala.tscn",
}
const TALK_REACH := 2.6

@export var hero_key := "korto"
@export var start_area := "gbelewala"

var area: WorldArea
var hero: Hero
var cam: FollowCamera
var hud: Hud
var area_key := ""
var _talk_here: Dictionary = {}
var _exit_cooldown := 0.0

func _ready() -> void:
	InputSetup.ensure()
	process_mode = Node.PROCESS_MODE_ALWAYS   # so Esc still works while paused; the area itself pauses
	hud = Hud.new()
	add_child(hud)
	hud.interact_pressed.connect(_interact)
	hud.resume_pressed.connect(func(): _set_paused(false))
	hud.quit_pressed.connect(func(): get_tree().quit())
	hud.quality_changed.connect(_set_quality)
	Look.apply_viewport(get_viewport())
	hero = Hero.new()
	hero.setup(hero_key)
	cam = FollowCamera.new()
	cam.name = "Camera"
	cam.target = hero
	go_to(start_area)

func go_to(key: String, from := "") -> void:
	if area:
		area.remove_child(hero)
		area.remove_child(cam)
		area.queue_free()
	area_key = key
	area = load(AREAS[key]).instantiate()
	area.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(area)
	area.add_child(hero)
	area.add_child(cam)
	hero.bounds = area.radius
	hero.place(area.spawn_for(from))
	cam.snap_behind()
	hud.show_title(area.area_name, area.subtitle)
	_exit_cooldown = 1.0

func _process(dt: float) -> void:
	if hud.look_drag != Vector2.ZERO:
		cam.look(hud.look_drag.x, hud.look_drag.y, Tuning.CAMERA.touch_sensitivity)
		hud.look_drag = Vector2.ZERO
	hero.touch_move = hud.stick
	# who's close enough to talk to
	_talk_here = {}
	var best := TALK_REACH
	for t in area.talks:
		var d := Vector2(hero.position.x - t.pos.x, hero.position.z - t.pos.z).length()
		if d < best:
			best = d
			_talk_here = t
	hud.set_prompt(("Talk to " + _talk_here.who) if _talk_here else "")
	# walking into an exit ring
	_exit_cooldown -= dt
	if _exit_cooldown <= 0.0:
		for x in area.exits:
			if Vector2(hero.position.x - x.pos.x, hero.position.z - x.pos.z).length() < x.r * 0.75:
				_exit_cooldown = 3.0
				if AREAS.has(x.to):
					go_to(x.to, area_key)
				else:
					hud.toast("%s isn't in the Godot build yet" % x.text)
				break

func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("pause"):
		_set_paused(not get_tree().paused)
	elif e.is_action_pressed("interact"):
		_interact()
	elif e is InputEventMouseButton and e.pressed and e.device != InputEvent.DEVICE_ID_EMULATION and not get_tree().paused:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _interact() -> void:
	if _talk_here:
		hud.say(_talk_here.who, _talk_here.line)

func _set_paused(on: bool) -> void:
	get_tree().paused = on
	hud.show_pause(on)
	if on:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif not hud.touch_mode:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _set_quality(q: String) -> void:
	Look.quality = q
	Look.apply_viewport(get_viewport())
	area.refresh_look()

## Pause when the window loses focus or the phone app goes to the background.
func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and hud and not get_tree().paused:
		_set_paused(true)
