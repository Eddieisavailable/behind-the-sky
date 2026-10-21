@tool
class_name Kit
## The Blender kits: one .glb per kit, one named mesh per piece (front +Z, origin at its foot).
## Meshes are pulled out once and shared by every copy.

const PATHS := {
	"environment": "res://assets/models/kits/environment.glb",
	"gbelewala": "res://assets/models/kits/gbelewala.glb",
	"swamp": "res://assets/models/kits/swamp.glb",
	"bele_tree": "res://assets/models/kits/bele_tree.glb",
}

static var _meshes := {}
static var _characters := {}

static func mesh(kit: String, piece: String) -> Mesh:
	if not _meshes.has(kit):
		var found := {}
		var root: Node = load(PATHS[kit]).instantiate()
		_collect(root, found)
		root.free()
		_meshes[kit] = found
	var m: Mesh = _meshes[kit].get(piece)
	if m == null:
		push_error("No piece '%s' in kit '%s'" % [piece, kit])
	return m

static func _collect(n: Node, out: Dictionary) -> void:
	if n is MeshInstance3D and n.mesh:
		out[String(n.name)] = n.mesh
	for c in n.get_children():
		_collect(c, out)

static func character(model: String) -> PackedScene:
	if not _characters.has(model):
		_characters[model] = load("res://assets/models/characters/%s.glb" % model)
	return _characters[model]
