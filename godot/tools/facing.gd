extends SceneTree
## Which way does a character model face? Feet stick out in front of the legs, so compare
## the average z of the lowest vertices (feet) with the legs above them.
## godot --headless --path . --script res://tools/facing.gd -- korto chief ...
func _init():
	for name in OS.get_cmdline_user_args():
		var s: Node = load("res://assets/models/characters/%s.glb" % name).instantiate()
		var mi: MeshInstance3D = s.find_children("*", "MeshInstance3D", true, false).filter(func(m): return m.get_parent() is Skeleton3D)[0]
		var arr: PackedVector3Array = mi.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		var lo := INF
		var hi := -INF
		for v in arr:
			lo = minf(lo, v.y); hi = maxf(hi, v.y)
		var h := hi - lo
		var feet := 0.0
		var nf := 0
		var shins := 0.0
		var ns := 0
		for v in arr:
			var t := (v.y - lo) / h
			if t < 0.03:
				feet += v.z
				nf += 1
			elif t > 0.03 and t < 0.45:
				shins += v.z
				ns += 1
		var d := feet / nf - shins / ns
		print("%s: feet are %.3f m toward %s  → model faces %s" % [name, absf(d), "+Z" if d > 0 else "-Z", "+Z" if d > 0 else "-Z"])
		s.free()
	quit()
