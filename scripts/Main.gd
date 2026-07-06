extends Node3D

## Fully code-driven 3D scene for automated video rendering.
##
## Every node (camera, light, subject, ground) is created here in
## _ready() instead of being laid out in the .tscn file. That keeps the
## scene file itself trivial (a single root node + this script), so
## there's no hand-authored sub-resource / resource-id scene syntax
## that could silently be wrong -- if this script parses, the scene
## works.
##
## The animation itself is also code-driven (no AnimationPlayer): the
## subject spins in place and the camera rig orbits around it once over
## `duration_seconds`. When combined with Godot's built-in Movie Maker
## mode (`--write-movie` + `--fixed-fps` on the command line), every
## frame is captured at an exact, deterministic delta -- there is no
## dependency on how fast the machine actually renders.

@export var duration_seconds: float = 8.0
@export var subject_color: Color = Color(0.85, 0.25, 0.25)

var _camera_rig: Node3D
var _subject: MeshInstance3D
var _elapsed: float = 0.0
var _quit_scheduled: bool = false


func _ready() -> void:
	_parse_user_args()
	_build_scene()


func _parse_user_args() -> void:
	# Lets export_video.py override settings without editing GDScript, e.g.:
	#   godot --headless --write-movie out.avi -- --duration=12
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--duration="):
			duration_seconds = float(arg.split("=")[1])
		elif arg.begins_with("--color="):
			var parts = arg.split("=")[1].split(",")
			if parts.size() == 3:
				subject_color = Color(float(parts[0]), float(parts[1]), float(parts[2]))


func _build_scene() -> void:
	# World environment: sky background + sky-based ambient light so
	# surfaces read as lit rather than flat-shaded.
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	sky.sky_material = ProceduralSkyMaterial.new()
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC

	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)

	# Key light.
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-45, -30, 0)
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	add_child(sun)

	# Ground plane, mostly so the orbiting camera has depth cues to read.
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(20, 20)
	ground.mesh = plane
	ground.position = Vector3(0, -1.5, 0)
	var ground_mat := StandardMaterial3D.new()
	ground_mat.albedo_color = Color(0.12, 0.12, 0.14)
	ground.material_override = ground_mat
	add_child(ground)

	# Subject: a torus with a simple PBR material, spinning in place.
	_subject = MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.6
	torus.outer_radius = 1.2
	_subject.mesh = torus
	var subject_mat := StandardMaterial3D.new()
	subject_mat.albedo_color = subject_color
	subject_mat.metallic = 0.6
	subject_mat.roughness = 0.25
	_subject.material_override = subject_mat
	_subject.name = "Subject"
	add_child(_subject)

	# Camera on a rig so "orbit the subject" is one rotation, not manual trig.
	_camera_rig = Node3D.new()
	add_child(_camera_rig)
	var camera := Camera3D.new()
	camera.position = Vector3(0, 2.2, 6.0)
	_camera_rig.add_child(camera)
	camera.current = true
	camera.look_at(Vector3.ZERO, Vector3.UP)


func _process(delta: float) -> void:
	_elapsed += delta

	if _subject:
		_subject.rotate_y(delta * 0.8)
		_subject.rotate_x(delta * 0.35)

	if _camera_rig:
		_camera_rig.rotation_degrees.y = (_elapsed / duration_seconds) * 360.0

	if not _quit_scheduled and _elapsed >= duration_seconds:
		_quit_scheduled = true
		get_tree().quit()
