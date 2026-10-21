class_name Look
## How the world is lit and rendered: one place for the "look" of the game.
##
## Each area names a mood (time of day). The mood gives the sky, sun, haze and fog; the quality
## preset decides which expensive effects are on. On PC (Forward+) Ultra and High aim for realism:
## light bouncing off the ground and walls (SDFGI), contact shadows (SSAO), coloured bounce (SSIL),
## haze you can see sunbeams in (volumetric fog), soft sun shadows, filmic tone mapping (AgX) and
## temporal anti-aliasing. Medium and Low drop those in steps; Low is what phones get.

const QUALITIES := ["ultra", "high", "medium", "low"]

## sky: zenith, horizon colours; fog: colour, density, sky_affect; haze: volumetric density;
## sun: colour, energy, direction (from where the light comes), angular size (softness);
## ambient: sky light strength; exposure: overall brightness.
const MOODS := {
	"morning": { "zenith": 0x6f93b8, "horizon": 0xd9d2c0, "ground": 0x4a3a28,
		"fog": [0xc9c6b8, 0.0024, 0.35], "haze": [0.0090, 0xe8dcc8],
		"sun": [0xffd9a8, 2.99, Vector3(-25, 22, 18), 1.2], "ambient": 0.54, "exposure": 1.0 },
	"day": { "zenith": 0x4f84c4, "horizon": 0xc8d8e0, "ground": 0x4a4030,
		"fog": [0xc2d0d6, 0.0018, 0.3], "haze": [0.0040, 0xf0f0ec],
		"sun": [0xfff2dc, 3.68, Vector3(-18, 40, 12), 0.8], "ambient": 0.60, "exposure": 0.95 },
	"dusk": { "zenith": 0x3c3f66, "horizon": 0xe08a5a, "ground": 0x2e2018,
		"fog": [0x8a6060, 0.0036, 0.4], "haze": [0.0110, 0xffb08a],
		"sun": [0xff9a55, 2.53, Vector3(30, 9, -20), 1.6], "ambient": 0.42, "exposure": 1.1 },
	"bush": { "zenith": 0x5d7a62, "horizon": 0x8fa892, "ground": 0x18120c,
		"fog": [0x5a7058, 0.0108, 0.5], "haze": [0.0200, 0xc8e0c0],
		"sun": [0xe8f0c0, 1.84, Vector3(-10, 40, 6), 0.6], "ambient": 0.45, "exposure": 1.15 },
	"afternoon": { "zenith": 0x5c8cc0, "horizon": 0xd8d8c8, "ground": 0x4a4030,
		"fog": [0xc8ccc4, 0.0021, 0.3], "haze": [0.0050, 0xf4ecd8],
		"sun": [0xffe6c0, 3.33, Vector3(20, 26, 14), 1.0], "ambient": 0.57, "exposure": 1.0 },
	"night": { "zenith": 0x070c18, "horizon": 0x1c2840, "ground": 0x0a0a08,
		"fog": [0x1a2438, 0.0060, 0.6], "haze": [0.0100, 0x8aa0d0],
		"sun": [0xb8ccff, 0.63, Vector3(-20, 40, -10), 0.5], "ambient": 0.36, "exposure": 1.6 },
}

## The quality in use. Changed from the pause menu; areas read it when they build.
static var quality := ""

static func current() -> String:
	if quality == "":
		quality = default_quality()
	return quality

static func default_quality() -> String:
	if OS.has_feature("mobile") or RenderingServer.get_current_rendering_method() != "forward_plus":
		return "low"
	# Laptop graphics built into the processor (Intel Iris Xe and the like) can't carry High:
	# bounced light and haze cost too much there, and some Intel drivers draw them washed out.
	if is_integrated_gpu():
		return "medium"
	return "high"

static func is_integrated_gpu() -> bool:
	var name := RenderingServer.get_video_adapter_name().to_lower()
	return RenderingServer.get_video_adapter_type() == RenderingDevice.DEVICE_TYPE_INTEGRATED_GPU \
		or name.contains("intel") or name.contains("uhd") or name.contains("iris")

static func col(hex: int) -> Color:
	return Color.hex((hex << 8) | 0xff)

## The environment (sky, fog, light bounce, tone) for a mood at the current quality.
static func environment(mood: String) -> Environment:
	var m: Dictionary = MOODS[mood]
	var q := current()
	var env := Environment.new()

	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = col(m.zenith)
	sky_mat.sky_horizon_color = col(m.horizon)
	sky_mat.ground_horizon_color = col(m.horizon).darkened(0.25)
	sky_mat.ground_bottom_color = col(m.ground)
	sky_mat.sun_angle_max = 8.0
	sky_mat.sun_curve = 0.08
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_256 if q in ["ultra", "high"] else Sky.RADIANCE_SIZE_64
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = m.ambient
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY

	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = m.exposure

	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = col(m.fog[0])
	env.fog_density = m.fog[1]
	env.fog_sky_affect = m.fog[2]
	env.fog_aerial_perspective = 0.4

	if q in ["ultra", "high"]:
		env.sdfgi_enabled = true
		env.sdfgi_use_occlusion = true
		env.sdfgi_cascades = 6 if q == "ultra" else 4
		env.sdfgi_min_cell_size = 0.15 if q == "ultra" else 0.25
		env.sdfgi_energy = 1.0
		env.ssil_enabled = true
		env.volumetric_fog_enabled = true
		env.volumetric_fog_density = m.haze[0]
		env.volumetric_fog_albedo = col(m.haze[1])
		env.volumetric_fog_anisotropy = 0.6   # light scatters forward: bright toward the sun
		env.volumetric_fog_length = 80.0 if q == "ultra" else 48.0
		env.volumetric_fog_sky_affect = 0.0
	if q != "low":
		env.ssao_enabled = true
		env.ssao_radius = 1.2
		env.ssao_intensity = 1.6
		env.ssao_power = 1.4
		env.glow_enabled = true
		env.glow_intensity = 0.35
		env.glow_bloom = 0.04
		env.glow_hdr_threshold = 1.2
	if q == "ultra":
		env.ssr_enabled = true
		env.ssr_max_steps = 48
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.12
	env.adjustment_contrast = 1.1
	return env

## The sun (or moon) for a mood.
static func sun(mood: String) -> DirectionalLight3D:
	var m: Dictionary = MOODS[mood]
	var q := current()
	var s := DirectionalLight3D.new()
	s.name = "Sun"
	s.light_color = col(m.sun[0])
	s.light_energy = m.sun[1]
	s.light_angular_distance = m.sun[3] if q in ["ultra", "high"] else 0.0   # soft shadow edges
	s.light_volumetric_fog_energy = 1.4
	s.shadow_enabled = true
	s.shadow_bias = 0.03
	s.shadow_normal_bias = 1.0
	s.shadow_blur = 1.0
	match q:
		"ultra", "high":
			s.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
			s.directional_shadow_max_distance = 90.0 if q == "ultra" else 70.0
			s.directional_shadow_blend_splits = true
		"medium":
			s.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
			s.directional_shadow_max_distance = 50.0
		_:
			s.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
			s.directional_shadow_max_distance = 35.0
	s.set_meta("toward", m.sun[2])   # where the light comes from; aim once in the tree
	return s

## Point the sun once it's in the scene tree.
static func aim_sun(s: DirectionalLight3D) -> void:
	var from: Vector3 = s.get_meta("toward")
	s.look_at_from_position(from, Vector3.ZERO, Vector3.UP if absf(from.normalized().y) < 0.99 else Vector3.FORWARD)

## Screen-wide settings: anti-aliasing, upscaling, shadow resolution, level of detail.
static func apply_viewport(vp: Viewport) -> void:
	var q := current()
	var shadow_size: int = { "ultra": 8192, "high": 4096, "medium": 2048, "low": 1024 }[q]
	RenderingServer.directional_shadow_atlas_set_size(shadow_size, true)
	RenderingServer.directional_soft_shadow_filter_set_quality(
		{ "ultra": RenderingServer.SHADOW_QUALITY_SOFT_ULTRA, "high": RenderingServer.SHADOW_QUALITY_SOFT_HIGH,
		  "medium": RenderingServer.SHADOW_QUALITY_SOFT_LOW, "low": RenderingServer.SHADOW_QUALITY_HARD }[q])
	RenderingServer.positional_soft_shadow_filter_set_quality(
		RenderingServer.SHADOW_QUALITY_SOFT_HIGH if q in ["ultra", "high"] else RenderingServer.SHADOW_QUALITY_SOFT_LOW)
	var forward_plus := RenderingServer.get_current_rendering_method() == "forward_plus"
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.use_taa = forward_plus and q in ["ultra", "high"]
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if q in ["medium", "low"] else Viewport.SCREEN_SPACE_AA_DISABLED
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = { "ultra": 1.0, "high": 1.0, "medium": 0.85, "low": 0.75 }[q]
	vp.mesh_lod_threshold = { "ultra": 0.5, "high": 1.0, "medium": 2.0, "low": 4.0 }[q]
