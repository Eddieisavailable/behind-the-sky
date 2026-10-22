extends SceneTree
## Render a scene for N frames and save a screenshot:
## -- out=path frames=N [scene=res://...] [light=morning view=face (look-dev only)]
func _initialize():
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.split("=")
		args[kv[0]] = kv[1]
	if args.has("quality"):
		Look.quality = args.quality
	var scene: Node = load(args.get("scene", "res://scenes/main.tscn")).instantiate()
	if args.has("model") and "model_path" in scene:
		scene.model_path = args.model
	root.add_child(scene)
	await process_frame   # let the scene's _ready run first
	if args.has("light"):
		scene.set_light(args.light)
	if args.has("clip") and "anim" in scene and scene.anim:
		scene.anim.play(args.clip)
		scene._clip = scene._clips.find(args.clip)
	if args.get("view", "") == "face":
		scene.view_face()
	# look-dev camera overrides: focus (height looked at), dist, yaw (radians), pitch
	for k in ["focus", "dist", "yaw", "pitch"]:
		if args.has(k) and ("_" + ("focus_y" if k == "focus" else k)) in scene:
			scene.set("_" + ("focus_y" if k == "focus" else k), float(args[k]))
	var t0 := Time.get_ticks_msec()
	for i in int(args.get("frames", "30")):
		await process_frame
	root.get_texture().get_image().save_png(args.out)
	print("rendered in %.1f s with %s" % [(Time.get_ticks_msec() - t0) / 1000.0, RenderingServer.get_current_rendering_method()])
	quit()
