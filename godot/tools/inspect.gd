extends SceneTree
# godot --headless --path . --script res://tools/inspect.gd -- res://assets/models/characters/korto.glb

func _init():
	var path = OS.get_cmdline_user_args()[0]
	var s = load(path).instantiate()
	_walk(s, 0)
	var ap = s.find_child("AnimationPlayer", true, false)
	if ap:
		print("animations: ", ap.get_animation_list())
	quit()

func _walk(n: Node, d: int):
	var extra = ""
	if n is MeshInstance3D and n.mesh:
		var m = n.mesh.surface_get_material(0)
		extra = " surfaces=%d mat0=%s vcol=%s" % [n.mesh.get_surface_count(), m.resource_name if m else "-", m.vertex_color_use_as_albedo if m is StandardMaterial3D else "?"]
		extra += " xform=%s" % [n.transform.origin]
	if n is Skeleton3D:
		extra = " bones=%d" % n.get_bone_count()
	if d < 4:
		print("  ".repeat(d), n.name, " <", n.get_class(), ">", extra)
	for c in n.get_children():
		_walk(c, d + 1)
