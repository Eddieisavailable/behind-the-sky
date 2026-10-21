class_name Genie
extends RefCounted
## The spirit-debt rule: every gift is a loan, paid at the crossroads. (Port of src/rules/debt.js.)

var cfg: Dictionary
var debt := 0
var bond := 0          ## 0..max_bond
var clears := 0        ## times the debt was paid down to zero at this bond level
var active_for := 0.0  ## seconds of power left
var cooldown := 0.0
var times_turned := 0
var uses := 0

func _init(config: Dictionary = Tuning.HORNBILL) -> void:
	cfg = config

func is_turned() -> bool:
	return debt >= cfg.max_debt

func cost_per_use() -> int:
	return maxi(cfg.debt_per_use_min, cfg.debt_per_use - bond * cfg.debt_discount_per_bond)

func power_duration() -> float:
	return cfg.duration + bond * cfg.duration_per_bond

func can_use() -> bool:
	return not is_turned() and active_for <= 0.0 and cooldown <= 0.0

## Use the gift. Returns true if it fired. Adds debt; may tip the genie into "turned".
func use_power() -> bool:
	if not can_use():
		return false
	var was_turned := is_turned()
	debt = mini(cfg.max_debt, debt + cost_per_use())
	active_for = power_duration()
	uses += 1
	if not was_turned and is_turned():
		times_turned += 1
	return true

func tick(dt: float) -> void:
	if active_for > 0.0:
		active_for = maxf(0.0, active_for - dt)
		if active_for == 0.0:
			cooldown = cfg.cooldown
	elif cooldown > 0.0:
		cooldown = maxf(0.0, cooldown - dt)

## What an offering can be paid with, given the hero's pack {rice, iron}.
static func offering_options(pack: Dictionary, offer: Dictionary = Tuning.OFFERING) -> Dictionary:
	return { "rice": pack.get("rice", 0) >= offer.rice_cost, "iron": pack.get("iron", 0) >= offer.iron_cost }

## Pay one offering at the crossroads with "rice" or "iron". Mutates the genie and the pack.
func pay_offering(pack: Dictionary, kind: String, offer: Dictionary = Tuning.OFFERING) -> Dictionary:
	if debt <= 0:
		return { "ok": false, "reason": "no-debt" }
	var cost: int = offer.rice_cost if kind == "rice" else offer.iron_cost
	if pack.get(kind, 0) < cost:
		return { "ok": false, "reason": "cannot-afford" }
	pack[kind] -= cost
	var before := debt
	debt = maxi(0, debt - offer.clears)
	var bond_up := false
	if before > 0 and debt == 0 and bond < cfg.max_bond:
		clears += 1
		if clears >= cfg.clears_per_bond:
			bond += 1
			clears = 0
			bond_up = true
	return { "ok": true, "cleared": before - debt, "bond_up": bond_up }
