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
				_realism(m)
	if n is AnimationPlayer:
		for lib_name in n.get_animation_library_list():
			var lib: AnimationLibrary = n.get_animation_library(lib_name)
			for clip in lib.get_animation_list():
				lib.get_animation(clip).loop_mode = Animation.LOOP_NONE if clip in ONE_SHOT else Animation.LOOP_LINEAR
	for c in n.get_children():
		_fix(c)

## Realistic characters (blender/realism): materials are named by what they are.
func _realism(m: StandardMaterial3D) -> void:
	var name := m.resource_name.get_slice(".", 0)   # Blender may add ".001" to repeated names
	if name.ends_with("Skin"):
		# light travels under the skin: softer shadows, warm glow through ears and fingers
		m.subsurf_scatter_enabled = true
		m.subsurf_scatter_strength = 0.45
		m.subsurf_scatter_skin_mode = true
		m.subsurf_scatter_transmittance_enabled = true
		m.subsurf_scatter_transmittance_color = Color(0.55, 0.18, 0.08)
		m.subsurf_scatter_transmittance_depth = 0.08
		m.subsurf_scatter_transmittance_boost = 0.1
		# pores are baked over the whole body into one 2K map: at full strength they sparkle like
		# wet skin under hard light, so they're kept subtle
		m.normal_scale = 0.4
		m.metallic_specular = 0.35   # skin reflects about 2.8% head-on, less than the 4% default
	elif name.ends_with("Eyes"):
		# eyeball opaque, the clear lens left out (alpha 0 in the texture). One wet, glossy layer
		# reflecting like a cornea (about 2.5% head-on): a second clear coat on top mirrored so much
		# sky that dark irises read grey-blue
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		m.alpha_scissor_threshold = 0.5
		m.clearcoat_enabled = false
		m.metallic_specular = 0.3
		m.roughness = 0.06
	elif name.ends_with("Brows") or name.ends_with("Lashes") or name.ends_with("Cornrows"):
		# hair: dithered alpha (smoothed by TAA), both sides of the card
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.alpha_hash_scale = 1.0
	elif name in ["KortoWrapper", "KortoTop", "KortoHeadTie"]:
		# cotton: soft rim of fuzz at grazing angles
		m.rim_enabled = true
		m.rim = 0.25
		m.rim_tint = 0.6
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
