class_name Waves
extends RefCounted
## Wave sizes and crawler speed. (Port of src/rules/waves.js.)

static func wave_size(n: int, cfg: Dictionary = Tuning.WAVES) -> Dictionary:
	var regular: int = cfg.base_count + mini(n - 1, cfg.extra_up_to)
	var disguised := 1 if n >= cfg.disguised_from else 0
	return { "regular": regular, "disguised": disguised, "total": regular + disguised }

static func crawler_speed(n: int, cfg: Dictionary = Tuning.CRAWLER) -> float:
	return minf(cfg.max_speed, cfg.speed + (n - 1) * cfg.speed_per_wave)
