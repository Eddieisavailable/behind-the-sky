extends SceneTree
## Rule tests, the same checks as the prototype's tests/rules.test.js.
## Run:  godot --headless --path . --script res://tests/run_tests.gd

var passed := 0
var failed := 0
var current := ""

func _init() -> void:
	_spirit_debt()
	_cutlass_combo()
	_crawler_life()
	_rhythm_forge()
	_waves()
	print("\n%d passed, %d failed" % [passed, failed])
	quit(1 if failed else 0)

func test(name: String) -> void:
	current = name

func check(ok: bool, what: String) -> void:
	if ok:
		passed += 1
	else:
		failed += 1
		print("FAIL  %s: %s" % [current, what])

# ---------------------------------------------------------------- spirit debt
func _spirit_debt() -> void:
	test("adds debt per use and turns at the limit")
	var g := Genie.new()
	var uses := 0
	while g.can_use():
		check(g.use_power(), "use fires")
		uses += 1
		g.tick(100); g.tick(100)
	check(uses == int(ceil(Tuning.HORNBILL.max_debt / float(Tuning.HORNBILL.debt_per_use))), "7 uses, got %d" % uses)
	check(g.is_turned() and g.times_turned == 1 and not g.use_power(), "turned once, no more uses")

	test("cannot fire again while active or cooling down")
	g = Genie.new()
	g.use_power()
	check(not g.use_power(), "not while active")
	g.tick(Tuning.HORNBILL.duration)
	check(not g.can_use(), "not while cooling down")
	g.tick(Tuning.HORNBILL.cooldown)
	check(g.can_use(), "ready again")

	test("offerings clear 50 debt and cost rice or iron")
	g = Genie.new()
	g.debt = 100
	var pack := { "rice": 3, "iron": 1 }
	check(Genie.offering_options(pack) == { "rice": true, "iron": false }, "options")
	check(not g.pay_offering(pack, "iron").ok, "can't afford iron")
	var r := g.pay_offering(pack, "rice")
	check(r.ok and r.cleared == 50 and g.debt == 50 and pack.rice == 0 and not g.is_turned(), "paid with rice")

	test("raises the bond after clearing to zero three times")
	g = Genie.new()
	pack = { "rice": 100, "iron": 0 }
	for i in 3:
		g.debt = 30
		check(g.pay_offering(pack, "rice").bond_up == (i == 2), "bond up only on the third clear")
	check(g.bond == 1, "bond 1")
	check(g.cost_per_use() == Tuning.HORNBILL.debt_per_use - Tuning.HORNBILL.debt_discount_per_bond, "cheaper")
	check(is_equal_approx(g.power_duration(), Tuning.HORNBILL.duration + Tuning.HORNBILL.duration_per_bond), "longer")

	test("will not take an offering when nothing is owed")
	g = Genie.new()
	pack = { "rice": 9, "iron": 9 }
	r = g.pay_offering(pack, "rice")
	check(not r.ok and r.reason == "no-debt" and pack.rice == 9, "refused")

# ---------------------------------------------------------------- cutlass combo
func _run(c: Combo, seconds: float) -> Array:
	var hits := []
	var t := 0.0
	while t < seconds:
		var e := c.tick(0.01)
		if not e.is_empty():
			hits.append(e.step)
		t += 0.01
	return hits

func _cutlass_combo() -> void:
	test("chains three blows when tapped during each swing")
	var c := Combo.new()
	c.press(); c.press()
	var hits := []
	var t := 0.0
	while t < 1.2:
		var e := c.tick(0.01)
		if not e.is_empty():
			hits.append(e.step)
			c.press()
		t += 0.01
	check(hits == [0, 1, 2], "got %s" % [hits])

	test("continues the chain within the combo window, restarts after it")
	c = Combo.new()
	c.press()
	check(_run(c, Tuning.CUTLASS.duration[0] + 0.05) == [0], "first")
	c.press()
	check(_run(c, Tuning.CUTLASS.duration[1] + 0.05) == [1], "second within the window")
	_run(c, Tuning.CUTLASS.combo_window + 0.2)
	c.press()
	check(_run(c, 0.5) == [0], "restarts after the window")

# ---------------------------------------------------------------- rattan crawler
func _crawler_life() -> void:
	var H: float = Tuning.CRAWLER.health
	test("iron puts it down, and it grows back unless burned")
	var l := CrawlerLife.new()
	check(l.hit_iron(H) == "downed", "downed")
	l.tick(Tuning.CRAWLER.regrow_after)
	check(l.state == "regrowing", "regrowing")
	check(l.tick(Tuning.CRAWLER.regrow_duration) == "rose" and l.state == "alive" and l.health == H, "rose at full health")

	test("a fire arrow on a downed crawler burns it for good")
	l = CrawlerLife.new()
	l.hit_iron(999)
	check(l.hit_fire(1) == "burned" and l.is_gone(), "burned")

	test("a burning crawler cut down is burned, not downed")
	l = CrawlerLife.new()
	l.hit_fire(5)
	check(l.burn_left > 0.0 and l.hit_iron(999) == "burned", "burned")

	test("burning alone can finish a weakened crawler")
	l = CrawlerLife.new()
	l.hit_iron(H - 4)
	l.hit_fire(1)
	var i := 0
	while i < 100 and l.state == "alive":
		l.tick(0.05)
		i += 1
	check(l.state == "burned", "burned away")

	test("a disguised crawler is unmasked by iron and still takes the blow")
	l = CrawlerLife.new(Tuning.CRAWLER, true)
	check(not l.is_active(), "hidden")
	l.hit_iron(10)
	check(l.state == "alive" and l.health == H - 10, "unmasked and hurt")

# ---------------------------------------------------------------- rhythm forge
func _rhythm_forge() -> void:
	test("builds the same 30-second pattern every time, identical to the prototype's")
	var a := Rhythm.build_pattern()
	var b := Rhythm.build_pattern()
	check(a == b, "repeatable")
	var total := 0.0
	var lows := 0
	for n in a:
		total += n.t
		lows += 1 if n.drum == "low" else 0
	check(a.size() == 46 and is_equal_approx(snappedf(total, 0.001), 695.3) and lows == 12, "matches the prototype (46 notes, sum 695.3, 12 low): got %d, %.3f, %d" % [a.size(), total, lows])
	var p12 := Rhythm.build_pattern(100, 30, 12)
	var s12 := 0.0
	for n in p12:
		s12 += n.t
	check(p12.size() == 44 and is_equal_approx(snappedf(s12, 0.001), 673.9), "seed 12 matches too: got %d, %.3f" % [p12.size(), s12])
	check(a.back().t <= Tuning.FORGE.seconds, "ends in time")
	var increasing := true
	for k in range(1, a.size()):
		increasing = increasing and a[k].t > a[k - 1].t
	check(increasing, "sorted")

	test("judges strikes by timing and counts missed notes")
	var j := Rhythm.Judge.new([{ "t": 1.0 }, { "t": 2.0 }, { "t": 3.0 }, { "t": 4.0 }])
	check(j.strike(1.03) == "perfect", "perfect")
	check(j.strike(2.1) == "good", "good")
	check(j.strike(2.6) == "", "stray")
	j.sweep(3.5)
	check(j.miss == 1, "one missed")
	check(j.strike(4.0) == "perfect" and j.is_done(), "last note")
	check(is_equal_approx(j.score(), 2.5 / 4.0), "score")

	test("turns a score into forge levels")
	check(Rhythm.levels_earned(0.3) == 0 and Rhythm.levels_earned(0.6) == 1 and Rhythm.levels_earned(0.9) == 2, "levels")

# ---------------------------------------------------------------- waves
func _waves() -> void:
	test("grows from 3 to 5 regular crawlers and adds a disguised one from wave 2")
	check(Waves.wave_size(1) == { "regular": 3, "disguised": 0, "total": 3 }, "wave 1")
	check(Waves.wave_size(2) == { "regular": 4, "disguised": 1, "total": 5 }, "wave 2")
	check(Waves.wave_size(5) == { "regular": 5, "disguised": 1, "total": 6 }, "wave 5")
	test("caps crawler speed")
	check(is_equal_approx(Waves.crawler_speed(1), Tuning.CRAWLER.speed) and is_equal_approx(Waves.crawler_speed(50), Tuning.CRAWLER.max_speed), "speed")
