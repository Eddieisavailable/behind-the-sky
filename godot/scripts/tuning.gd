class_name Tuning
extends RefCounted
## Every tuning number in one place, carried over from the prototype (src/config.js).

const HERO := { "health": 100, "speed": 6.5, "aim_speed_factor": 0.4, "radius": 0.45,
	"dodge": { "speed": 13.0, "duration": 0.28, "invulnerable": 0.32, "cooldown": 0.45 }, "hurt_invulnerable": 0.5 }

## The two playable heroes: same story, different starting strengths.
const HEROES := {
	"korto": { "name": "Korto", "health": 100, "speed": 6.5, "damage": 1.0, "scale": 1.12, "model": "res://assets/models/characters/korto.glb" },
	"flomo": { "name": "Flomo", "health": 130, "speed": 5.8, "damage": 1.3, "scale": 1.18, "model": "res://assets/models/characters/flomo.glb" },
}

const CUTLASS := { "damage": [10, 10, 18], "hit_time": [0.1, 0.1, 0.14], "duration": [0.26, 0.26, 0.38], "combo_window": 0.45,
	"range": 2.4, "arc_degrees": 120, "knockback": 7.0, "stagger": 0.55, "assist_range": 3.6 }

const BOW := { "full_draw": 0.35, "arrow_speed": 32.0, "max_range": 22.0, "iron_damage": 14, "fire_damage": 8, "weak_factor": 0.5,
	"assist_degrees": 30, "assist_range": 20.0, "fire_arrows_max": 6 }

const CRAWLER := { "health": 30.0, "radius": 0.5, "speed": 3.1, "speed_per_wave": 0.15, "max_speed": 4.4, "attack_range": 1.45,
	"windup": 0.5, "damage": 8, "attack_cooldown": 1.2, "regrow_after": 4.0, "regrow_duration": 1.2, "burn_duration": 3.0,
	"burn_dps": 6.0, "ambush_range": 2.2 }

const DROPS := { "rice": 1, "extra_rice_chance": 0.4, "iron_chance": 0.5, "pickup_radius": 1.4, "magnet_radius": 4.0 }

const HORNBILL := { "debt_per_use": 15, "debt_per_use_min": 6, "debt_discount_per_bond": 3, "duration": 4.0, "duration_per_bond": 1.0,
	"cooldown": 1.5, "slow_factor": 0.35, "max_debt": 100, "warn_at": 70, "max_bond": 3, "clears_per_bond": 3 }

const OFFERING := { "clears": 50, "rice_cost": 3, "iron_cost": 2 }

const FORGE := { "iron_cost": 3, "bpm": 100, "seconds": 30.0, "perfect_ms": 60, "good_ms": 130, "upgrade_at": 0.5, "great_at": 0.85,
	"max_level": 5, "damage_per_level": 0.12 }

const WAVES := { "base_count": 3, "extra_up_to": 2, "disguised_from": 2, "breather": 10.0 }
const WAVES_PER_ROUND := 5

## Third-person camera.
const CAMERA := { "distance": 7.0, "min_distance": 3.0, "height": 1.6, "pitch": 0.38, "min_pitch": 0.08, "max_pitch": 1.05,
	"shoulder": 0.6, "mouse_sensitivity": 0.0024, "touch_sensitivity": 0.006, "fov": 60.0, "follow_delay": 1.2, "follow_rate": 2.5 }

## Climbing the bele tree's vines.
const CLIMB := { "speed": 1.7, "reach": 1.4 }
