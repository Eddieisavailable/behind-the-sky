class_name Combo
extends RefCounted
## Cutlass three-hit combo as a small state machine. (Port of src/rules/combo.js.)
## press() on each attack tap; tick() advances time and reports when each blow lands.

var cfg: Dictionary
var step := -1
var t := 0.0
var landed := false
var queued := false
var since_end := INF
var last_step := -1

func _init(config: Dictionary = Tuning.CUTLASS) -> void:
	cfg = config

func is_swinging() -> bool:
	return step >= 0

func press() -> bool:
	if step < 0:
		# start a new chain, or continue one that just ended
		var next := last_step + 1 if since_end <= cfg.combo_window and last_step >= 0 and last_step < 2 else 0
		_begin(next)
		return true
	if step < 2:
		queued = true   # mid-swing: queue the next blow
	return false

func _begin(s: int) -> void:
	step = s
	t = 0.0
	landed = false
	queued = false

## Returns {"type": "hit", "step": n} when a blow lands, else an empty dictionary.
func tick(dt: float) -> Dictionary:
	if step < 0:
		since_end += dt
		return {}
	t += dt
	var event := {}
	if not landed and t >= cfg.hit_time[step]:
		landed = true
		event = { "type": "hit", "step": step }
	if t >= cfg.duration[step]:
		var finished := step
		if queued and finished < 2:
			_begin(finished + 1)
		else:
			last_step = finished
			step = -1
			since_end = 0.0
	return event

func cancel() -> void:
	step = -1
	queued = false
	last_step = -1
	since_end = INF
