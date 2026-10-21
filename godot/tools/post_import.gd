@tool
extends EditorScenePostImport
## Runs on every model when Godot imports it (set in each .glb.import).
## - The Blender models are painted with vertex colours: show them.
## - "Glow" (embers, eyes) is unshaded so it reads as light.
## - Clips loop, except the one-shot moves listed here.

const ONE_SHOT := ["Slash1", "Slash2", "Slash3", "Roll", "Draw", "Burn", "Hurt", "Death", "Down", "Rise",
	"Strike", "Windup", "Dive", "Fall", "Grant", "Smash", "Land", "Bite", "Heal", "Block", "Collapse",
	"Rebuild", "Startled", "Taunt"]

func _post_import(scene: Node) -> Object:
	_fix(scene)
	return scene

func _fix(n: Node) -> void:
	if n is MeshInstance3D and n.mesh:
		for i in n.mesh.get_surface_count():
			var m: Material = n.mesh.surface_get_material(i)
			if m is StandardMaterial3D:
				m.vertex_color_use_as_albedo = true
				if m.resource_name == "Glow":
					m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if n is AnimationPlayer:
		for lib_name in n.get_animation_library_list():
			var lib: AnimationLibrary = n.get_animation_library(lib_name)
			for clip in lib.get_animation_list():
				lib.get_animation(clip).loop_mode = Animation.LOOP_NONE if clip in ONE_SHOT else Animation.LOOP_LINEAR
	for c in n.get_children():
		_fix(c)
