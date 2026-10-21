extends SceneTree
## Walk-the-world smoke test: loads the game, walks Korto about Gbelewala and checks
## she moves, turns, is stopped by a house, can talk to the Chief and finds the exit.
## Run:  godot --headless --path . --script res://tests/walk_test.gd
## Add -- shot=path.png (not headless) to also save a screenshot.

var passed := 0
var failed := 0

func check(ok: bool, what: String) -> void:
	if ok:
		passed += 1
	else:
		failed += 1
		print("FAIL  ", what)

func frames(n: int) -> void:
	for i in n:
		await physics_frame

## Let a few rendered frames pass (the HUD updates per frame, not per physics step).
func settle(n := 3) -> void:
	for i in n:
		await process_frame

func hold(action: String, seconds: float) -> void:
	Input.action_press(action)
	await frames(int(seconds * 60))
	Input.action_release(action)

func _initialize() -> void:
	_run()

func _run() -> void:
	var main: Main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	await frames(10)
	var area := main.area
	var hero := main.hero
	check(area != null and area.area_name == "Gbelewala", "Gbelewala loaded")
	if area == null:
		quit(1)
		return
	check(area.talks.size() == 3 and area.exits.size() == 1, "3 people to talk to, 1 exit (got %d, %d)" % [area.talks.size(), area.exits.size()])
	var meshes := area.find_children("*", "MeshInstance3D", true, false).size()
	var forests := area.find_children("*", "MultiMeshInstance3D", true, false).size()
	var bodies := area.find_children("*", "StaticBody3D", true, false).size()
	check(meshes > 40 and forests >= 6 and bodies > 20, "layout built (%d meshes, %d instanced sets, %d colliders)" % [meshes, forests, bodies])
	check(hero.is_on_floor() and absf(hero.position.y) < 0.05, "standing on the ground (y %.3f)" % hero.position.y)
	check(Vector2(hero.position.x, hero.position.z).distance_to(Vector2(0, 6)) < 0.2, "starts by the path")

	# walk forward (away from the camera, north)
	var z0 := hero.position.z
	await hold("move_forward", 1.0)
	check(hero.position.z < z0 - 4.0, "walks forward (z %.2f → %.2f)" % [z0, hero.position.z])
	# the model's front is +Z in its own space (tools/facing.gd measures it from the feet)
	var front := hero.model.global_basis.z.normalized()
	check(front.dot(Vector3(0, 0, -1)) > 0.9, "faces the way she walks, not backwards (front %s)" % front)
	check(main.cam.cam.global_position.z > hero.position.z + 2.0, "camera stays behind her")
	check(hero.anim.current_animation == "Run", "runs while moving (%s)" % hero.anim.current_animation)
	await frames(30)
	check(hero.anim.current_animation == "Idle", "idles when stopped (%s)" % hero.anim.current_animation)

	# strafe right: she turns to face east (character yaw -PI/2)
	await hold("move_right", 0.8)
	var side_front := hero.model.global_basis.z.normalized()
	var cam_right := Vector3(cos(main.cam.yaw), 0, -sin(main.cam.yaw))
	check(side_front.dot(cam_right) > 0.9, "faces right when walking right")
	var want := main.cam.yaw - PI / 2   # right of the camera
	check(absf(angle_difference(hero.yaw, want)) < 0.35, "turns to face the way she goes (yaw %.2f, camera-right %.2f)" % [hero.yaw, want])

	# walking toward the camera: she turns to face it, and the camera doesn't swing round
	main.cam._since_look = 99.0
	var yaw_before := main.cam.yaw
	await hold("move_back", 2.0)
	check(absf(angle_difference(main.cam.yaw, yaw_before)) < 0.05, "camera holds still when she runs toward it (moved %.2f)" % angle_difference(main.cam.yaw, yaw_before))
	var back_front := hero.model.global_basis.z.normalized()
	var to_cam := Vector3(sin(main.cam.yaw), 0, cos(main.cam.yaw))
	check(back_front.dot(to_cam) > 0.9, "faces the camera when walking toward it")

	# a house stops her: the round house at 70°, 17 m (radius 2.9)
	var hx := cos(deg_to_rad(70)) * 17
	var hz := -sin(deg_to_rad(70)) * 17
	hero.place({ "x": hx, "z": hz + 6.0, "face": 0.0 })
	main.cam.yaw = 0.0
	main.cam._since_look = 0.0
	await frames(2)
	await hold("move_forward", 2.0)
	check(hero.position.z > hz + 2.9, "the house stops her (z %.2f, wall at %.2f)" % [hero.position.z, hz + 2.9])

	# the edge of the area holds her in
	hero.place({ "x": 0.0, "z": 20.0, "face": PI })
	main.cam.yaw = PI
	await frames(2)
	await hold("move_forward", 2.5)
	var r := Vector2(hero.position.x, hero.position.z).length()
	check(r <= area.radius - 0.5, "stays inside the village (r %.2f)" % r)

	# talk to the Chief
	hero.place({ "x": -7.5, "z": 11.3, "face": 0.0 })
	await settle()
	check(main.hud._prompt.text.contains("the Chief"), "prompt to talk to the Chief ('%s')" % main.hud._prompt.text)
	var ev := InputEventAction.new()
	ev.action = "interact"
	ev.pressed = true
	Input.parse_input_event(ev)
	await settle()
	check(main.hud._say_box.visible and main.hud._say_line.text.contains("seed rice"), "the Chief speaks")

	# the camera sits behind and above her, and nothing is between
	var cam_pos := main.cam.cam.global_position
	check(cam_pos.y > hero.position.y + 1.0, "camera above her")

	# the exit ring to the rice farm (not ported yet): a notice, not a crash
	hero.place({ "x": 27.5, "z": 0.0, "face": 0.0 })
	await settle()
	check(main.hud._toast.text.contains("rice farm"), "exit says the rice farm is coming ('%s')" % main.hud._toast.text)

	# pause and resume
	var pause := InputEventAction.new()
	pause.action = "pause"
	pause.pressed = true
	Input.parse_input_event(pause)
	await process_frame
	await process_frame
	check(paused and main.hud.is_paused_menu(), "Esc pauses")
	main._set_paused(false)

	var shot := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("shot="):
			shot = a.substr(5)
	if shot != "":
		hero.place({ "x": 0.0, "z": 12.0, "face": 0.0 })
		main.cam.snap_behind()
		Input.action_press("move_forward")
		await settle(4)
		root.get_texture().get_image().save_png(shot.replace(".png", "_back.png"))
		Input.action_release("move_forward")
		main.cam.yaw += PI
		main.cam._since_look = 0.0
		main.cam.distance = 4.0
		await settle(4)
		root.get_texture().get_image().save_png(shot.replace(".png", "_front.png"))
		print("saved ", shot)
	print("\n%d passed, %d failed" % [passed, failed])
	quit(1 if failed else 0)
