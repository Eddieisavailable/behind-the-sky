class_name CrawlerLife
extends RefCounted
## Life of a rattan crawler. "What demons grow, grows back unless burned." (Port of src/rules/crawlerLife.js.)
##   disguised -(revealed)-> alive -(health 0)-> downed -(4 s)-> regrowing -> alive
##   a fire arrow on a downed crawler, or cutting down a burning one -> burned (gone, drops loot)

var cfg: Dictionary
var state := "alive"
var health := 0.0
var timer := 0.0      ## time in the current state
var burn_left := 0.0  ## seconds of burning left while alive

func _init(config: Dictionary = Tuning.CRAWLER, disguised := false) -> void:
	cfg = config
	health = cfg.health
	state = "disguised" if disguised else "alive"

func is_active() -> bool: return state == "alive"
func is_gone() -> bool: return state == "burned"
func is_downed() -> bool: return state == "downed" or state == "regrowing"

func _enter(s: String) -> void:
	state = s
	timer = 0.0

func reveal() -> void:
	if state == "disguised":
		_enter("alive")

## Iron (cutlass or iron arrow). Returns the new state.
func hit_iron(damage: float) -> String:
	if state == "disguised":
		reveal()   # the blow that unmasks it still lands
	if state != "alive":
		return state
	health -= damage
	if health <= 0.0:
		health = 0.0
		_enter("burned" if burn_left > 0.0 else "downed")
	return state

## Fire arrow. Burns a downed crawler away; sets a standing one alight.
func hit_fire(damage: float) -> String:
	if is_downed():
		_enter("burned")
		return state
	if state == "disguised":
		reveal()
	if state != "alive":
		return state
	burn_left = cfg.burn_duration
	health -= damage
	if health <= 0.0:
		health = 0.0
		_enter("burned")
	return state

## Advance time. Returns "rose" when a crawler finishes growing back, else "".
func tick(dt: float) -> String:
	timer += dt
	if state == "alive" and burn_left > 0.0:
		burn_left = maxf(0.0, burn_left - dt)
		health -= cfg.burn_dps * dt
		if health <= 0.0:
			health = 0.0
			_enter("burned")
	elif state == "downed" and timer >= cfg.regrow_after:
		_enter("regrowing")
	elif state == "regrowing" and timer >= cfg.regrow_duration:
		health = cfg.health
		_enter("alive")
		return "rose"
	return ""

## 0..1 how far a downed crawler has grown back (for drawing).
func regrow_progress() -> float:
	if state == "regrowing":
		return minf(1.0, timer / cfg.regrow_duration)
	return 0.0 if state == "downed" else 1.0
