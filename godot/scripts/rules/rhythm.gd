class_name Rhythm
extends RefCounted
## The rhythm forge: Sii beats the slit-drum, the player strikes on the beat. (Port of src/rules/rhythm.js.)
## The pattern generator matches the prototype's note for note (same seeded random numbers).

const MASK := 0xFFFFFFFF

## 32-bit multiply like JavaScript's Math.imul, done in halves so GDScript's 64-bit ints don't overflow.
static func _imul(a: int, b: int) -> int:
	a &= MASK
	b &= MASK
	var lo := (a & 0xFFFF) * (b & 0xFFFF)
	var mid := (((a >> 16) * (b & 0xFFFF) + (a & 0xFFFF) * (b >> 16)) & 0xFFFF) << 16
	return (lo + mid) & MASK

## Small deterministic random generator (mulberry32), returns a Callable giving 0..1.
static func seeded(seed: int) -> Callable:
	var state := [seed & MASK]
	return func() -> float:
		state[0] = (state[0] + 0x6D2B79F5) & MASK
		var t: int = state[0]
		t = _imul(t ^ (t >> 15), t | 1)
		t = (t ^ ((t + _imul(t ^ (t >> 7), t | 61)) & MASK)) & MASK
		return float((t ^ (t >> 14)) & MASK) / 4294967296.0

## Note times (seconds) with a drum each: "low" or "high" (the two tongues of the slit-drum).
static func build_pattern(bpm: float = Tuning.FORGE.bpm, seconds: float = Tuning.FORGE.seconds, seed: int = 7, lead_in: float = 2.0) -> Array:
	var rand := seeded(seed)
	var beat := 60.0 / bpm
	var notes := []
	var beats := int(floor((seconds - lead_in) / beat))
	for i in beats:
		var t := lead_in + i * beat
		var bar := i / 4
		var in_bar := i % 4
		if bar >= 2 and in_bar == 3 and rand.call() < 0.35:
			continue   # a rest
		notes.append({ "t": t, "drum": "low" if in_bar == 0 else "high" })
		if bar >= 3 and in_bar % 2 == 1 and rand.call() < 0.45:
			notes.append({ "t": t + beat / 2.0, "drum": "high" })   # off-beat pair
	notes.sort_custom(func(a, b): return a.t < b.t)
	return notes


class Judge:
	extends RefCounted
	var cfg: Dictionary
	var notes: Array
	var next := 0
	var perfect := 0
	var good := 0
	var miss := 0
	var streak := 0
	var best := 0

	func _init(pattern: Array, config: Dictionary = Tuning.FORGE) -> void:
		cfg = config
		notes = []
		for n in pattern:
			var copy: Dictionary = n.duplicate()
			copy["result"] = ""
			notes.append(copy)

	func _record(note: Dictionary, result: String) -> void:
		note.result = result
		set(result, get(result) + 1)
		streak = 0 if result == "miss" else streak + 1
		best = maxi(best, streak)

	## Mark notes that slid past the window as missed. Call every frame with song time.
	func sweep(now: float) -> Array:
		var late: float = cfg.good_ms / 1000.0
		var missed := []
		while next < notes.size() and now - notes[next].t > late:
			var n: Dictionary = notes[next]
			if n.result == "":
				_record(n, "miss")
				missed.append(n)
			next += 1
		return missed

	## A strike at song time `now`: "perfect", "good" or "" (a stray strike).
	func strike(now: float) -> String:
		sweep(now)
		if next >= notes.size():
			return ""
		var n: Dictionary = notes[next]
		var off := absf(now - n.t) * 1000.0
		if off > cfg.good_ms:
			return ""
		var result := "perfect" if off <= cfg.perfect_ms else "good"
		_record(n, result)
		next += 1
		return result

	func is_done() -> bool:
		return next >= notes.size()

	## 0..1: perfect counts fully, good counts half.
	func score() -> float:
		return (perfect + good * 0.5) / float(maxi(1, notes.size()))


## How many forge levels a score earns: 0, 1 or 2.
static func levels_earned(s: float, cfg: Dictionary = Tuning.FORGE) -> int:
	if s >= cfg.great_at:
		return 2
	if s >= cfg.upgrade_at:
		return 1
	return 0
