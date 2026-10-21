@tool
extends WorldArea
## Gbelewala, the village. Morning; something has been at the seed-rice store.
## Ported from the prototype's src/game/areas.js.

func build() -> void:
	ground(0x7a5233, 31, 0x3b5a2c)
	path([[0, 4], [12, 2], [30, 0]])
	path([[0, 4], [-10, 6]], 2.0)

	# the square: palaver hut and the storyteller's fire, benches round it
	piece("gbelewala", "palaver_hut", 0, -12, 0)
	piece("gbelewala", "story_fire", 0, -2, 0, 1, 1.1)
	for a in [205, 245, 295, 335]:
		var t := deg_to_rad(a)
		var x := cos(t) * 3.4
		var z := -2 - sin(t) * 3.4
		piece("gbelewala", "bench", x, z, face_to(x, z, 0, -2))

	# houses round the square, doors facing in, a gap to the east for the farm road
	for h in [[150, 17, "house_round"], [115, 18, "house_long"], [70, 17, "house_round"], [35, 18, "house_round"],
			[-40, 17, "house_long"], [-75, 18, "house_round"], [200, 17, "house_round"], [235, 18, "house_long"]]:
		var t := deg_to_rad(h[0])
		var x: float = cos(t) * h[1]
		var z: float = -sin(t) * h[1]
		piece("gbelewala", h[2], x, z, face_to(x, z, 0, 0), 1, 3.0 if h[2] == "house_long" else 2.9)

	# the seed-rice store, found empty
	piece("gbelewala", "rice_store", -10, 8, face_to(-10, 8, 0, 3), 1, 1.7)
	label("The seed-rice store", -10, 4.6, 8)
	# the forge where the father works
	piece("environment", "forge", 14, -8, face_to(14, -8, 0, 0), 1, 1.9)
	label("Your father’s forge", 14, 3.6, -8)

	# everyday things
	piece("gbelewala", "mortar", -12, -6, 0, 1, 0.35)
	piece("gbelewala", "water_pots", -10, -9.5, 1, 1, 0.6)
	piece("gbelewala", "cook_fire", -14, -3, 0, 1, 0.6)
	piece("gbelewala", "drying_rack", 6, 10, 0.3, 1, 0.4)
	piece("gbelewala", "drying_rack", -3, -18, 0)
	piece("gbelewala", "stool", 2.6, 1.0)
	var chickens := []
	for i in 4:
		var p: Array = [[4, -5], [5.5, -6], [7, 4], [-5, 6]][i]
		chickens.append(piece("gbelewala", "chicken", p[0], p[1], i * 1.7))
	var bananas := []
	for k in 9:
		var t := deg_to_rad(k * 40 + 15)
		bananas.append([cos(t) * 22.5, sin(t) * 22.5, k, 1])
	scatter("gbelewala", "banana_plant", bananas, 0.5)
	var fence := []
	for k in 16:
		var t := deg_to_rad(k * 22.5 + 11)
		if absf(cos(t)) > 0.92 and cos(t) > 0:
			continue   # the gap for the farm road
		fence.append([cos(t) * 26, sin(t) * 26, PI / 2 - t, 1])
	scatter("gbelewala", "fence", fence)
	forest_ring(31, 52, 150, 3)

	# people
	actor("chief", -7.5, 9.5, look_at_yaw(-7.5, 9.5, 0, 5), "Worry", 1.0, [], "The Chief")
	talk("the Chief", -7.5, 9.5, "The seed rice is gone. If we don’t plant before the rain season, hunger will catch all of us.")
	actor("blacksmith", 13.3, -6.2, look_at_yaw(13.3, -6.2, 14, -8), "Hammer", 1.0, [], "Your father")
	talk("your father", 13.3, -6.2, "The forge is hot. If you go after that rice, go with iron in your hand.")
	actor("villager_woman", -11.3, -5.2, look_at_yaw(-11.3, -5.2, -12, -6), "Pound", 1.0)
	actor("elder", -4, 9, look_at_yaw(-4, 9, -10, 8), "Idle", 1.0)
	actor("villager_man", -5.5, 11.5, look_at_yaw(-5.5, 11.5, -10, 8), "Talk", 1.0, ["Hoe"])
	actor("storyteller", 2.6, 1.6, look_at_yaw(2.6, 1.6, 0, -2), "Sit", 1.0, ["Whisk", "Rattle"], "The storyteller")
	talk("the storyteller", 2.6, 1.6, "Sit with us tonight and I will tell how Woi’s iron was made. Dried millet...")
	var child := actor("child", 5, -5, 0, "Walk", 1.0)
	var hen: Node3D = chickens[0]
	every(func(_dt: float, t: float):   # the child chases the chickens round and round
		var a := t * 0.6
		child.position = Vector3(5.2 + cos(a) * 2.6, 0, -4.5 + sin(a) * 2.6)
		child.rotation.y = atan2(sin(a), -cos(a)) + PI
		hen.position = Vector3(5.2 + cos(a + 0.7) * 2.8, 0, -4.5 + sin(a + 0.7) * 2.8)
		hen.rotation.y = -a)

	exit_to("rice_farm", 28, 0, "The rice farm")
	spawns = {
		"start": { "x": 0.0, "z": 6.0, "face": 0.0 },
		"rice_farm": { "x": 25.0, "z": 0.0, "face": PI / 2 },
	}

## Forest between r0 and r1, outside the walkable ground.
func forest_ring(r0: float, r1: float, n: int, s: int) -> void:
	var kinds := [["tree_giant", 0.55, 0.85], ["tree_mid", 0.9, 1.3], ["palm", 0.9, 1.2], ["bush", 1.4, 2.2]]
	reseed(s)
	var lists := {}
	for k in kinds:
		lists[k[0]] = []
	for i in n:
		var a := rnd() * TAU
		var r := r0 + rnd() * (r1 - r0)
		var k: Array = kinds[i % kinds.size()]
		lists[k[0]].append([cos(a) * r, sin(a) * r, rnd() * 6.28, k[1] + rnd() * (k[2] - k[1])])
	for k in lists:
		scatter("environment", k, lists[k])
