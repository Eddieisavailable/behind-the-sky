extends SceneTree
## Render a scene for N frames and save a screenshot:
## -- out=path frames=N [scene=res://...] [light=morning view=face (look-dev only)]
func _initialize():
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.split("=")
		args[kv[0]] = kv[1]
	var scene: Node = load(args.get("scene", "res://scenes/main.tscn")).instantiate()
	root.add_child(scene)
	await process_frame   # let the scene's _ready run first
	if args.has("light"):
		scene.set_light(args.light)
	if args.get("view", "") == "face":
		scene.view_face()
	var t0 := Time.get_ticks_msec()
	for i in int(args.get("frames", "30")):
		await process_frame
	root.get_texture().get_image().save_png(args.out)
	print("rendered in %.1f s with %s" % [(Time.get_ticks_msec() - t0) / 1000.0, RenderingServer.get_current_rendering_method()])
	quit()
