"""Create a portable fallback head rig when a native GNM/FLAME asset is absent."""

from __future__ import annotations

from pathlib import Path
import sys
import argparse

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
BLEND_PATH = ROOT / "blend_files" / "synthetic_head_rig.blend"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name: str, color: tuple[float, float, float, float], **properties) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = properties.get("roughness", 0.35)
    bsdf.inputs["Metallic"].default_value = properties.get("metallic", 0.0)
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = properties.get("alpha", 1.0)
    if "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = properties.get("transmission", 0.0)
    if "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = properties.get("subsurface", 0.0)
    mat.blend_method = properties.get("blend_method", "OPAQUE")
    mat.use_screen_refraction = True
    mat.show_transparent_back = True
    mat.use_nodes = True
    return mat


def apply_texture(mat: bpy.types.Material, texture_path: Path) -> None:
    if not texture_path.exists():
        return
    image = bpy.data.images.load(str(texture_path), check_existing=True)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    bsdf = nodes.get("Principled BSDF")
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])


def add_uv(name: str, location: tuple[float, float, float], scale: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def add_eye(prefix: str, x: float, iris_texture: Path | None = None) -> tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    center = (x, -0.62, 0.18)
    sclera_mat = material(f"{prefix}_Sclera", (0.92, 0.91, 0.82, 1), roughness=0.22)
    iris_mat = material(f"{prefix}_Iris", (0.12, 0.38, 0.48, 1), roughness=0.24)
    cornea_mat = material(
        f"{prefix}_Cornea",
        (0.9, 0.96, 1.0, 0.18),
        roughness=0.015,
        transmission=1.0,
        alpha=0.18,
        blend_method="BLEND",
    )
    sclera = add_uv(f"{prefix}_Sclera", center, (0.215, 0.13, 0.215), sclera_mat)
    iris = add_uv(f"{prefix}_Iris", (x, -0.752, 0.18), (0.105, 0.008, 0.105), iris_mat)
    if iris_texture:
        apply_texture(iris_mat, iris_texture)
    cornea = add_uv(f"{prefix}_Cornea", (x, -0.782, 0.18), (0.13, 0.035, 0.13), cornea_mat)

    empty = bpy.data.objects.new(f"{prefix}_Rig", None)
    bpy.context.collection.objects.link(empty)
    empty.location = center
    for obj in (sclera, iris, cornea):
        obj.parent = empty
        obj.location = (obj.location.x - center[0], obj.location.y - center[1], obj.location.z - center[2])
    return empty, sclera, iris, cornea


def build_scene(texture_path: Path | None = None, model_path: Path | None = None, resolution: int = 640, engine: str = "EEVEE") -> dict[str, bpy.types.Object]:
    clear_scene()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from create_head import build_head
    head_result = build_head(texture_path, model_path)

    subject = "_".join(texture_path.stem.split("_")[:2]) if texture_path else None
    iris_l = (texture_path.parent.parent / "iris_maps" / f"{subject}_iris_L.png") if subject else None
    iris_r = (texture_path.parent.parent / "iris_maps" / f"{subject}_iris_R.png") if subject else None
    eye_l, *_ = add_eye("Eye_L", -0.30, iris_l)
    eye_r, *_ = add_eye("Eye_R", 0.30, iris_r)

    lid_mat = material("Eyelids", (0.62, 0.32, 0.21, 1), roughness=0.42)
    upper_l = add_uv("Upper_Lid_L", (-0.30, -0.752, 0.31), (0.21, 0.025, 0.09), lid_mat)
    upper_r = add_uv("Upper_Lid_R", (0.30, -0.752, 0.31), (0.21, 0.025, 0.09), lid_mat)
    lower_l = add_uv("Lower_Lid_L", (-0.30, -0.752, 0.05), (0.21, 0.025, 0.06), lid_mat)
    lower_r = add_uv("Lower_Lid_R", (0.30, -0.752, 0.05), (0.21, 0.025, 0.06), lid_mat)

    brow_mat = material("Brows", (0.12, 0.055, 0.035, 1), roughness=0.52)
    brow_l = add_uv("Brow_L", (-0.30, -0.75, 0.48), (0.24, 0.018, 0.035), brow_mat)
    brow_r = add_uv("Brow_R", (0.30, -0.75, 0.48), (0.24, 0.018, 0.035), brow_mat)
    for brow in (brow_l, brow_r):
        brow.rotation_euler.x = 0.05

    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.0, 5.0))
    key = bpy.context.object
    key.name = "Key_Softbox"
    key.data.energy = 850
    key.data.size = 4.0
    bpy.ops.object.light_add(type="AREA", location=(3.5, -3.0, 3.0))
    fill = bpy.context.object
    fill.name = "Fill_Softbox"
    fill.data.energy = 450
    fill.data.size = 3.0
    bpy.ops.object.light_add(type="AREA", location=(0.0, 1.5, 4.0))
    rim = bpy.context.object
    rim.name = "Rim_Softbox"
    rim.data.energy = 600
    rim.data.size = 2.0

    bpy.ops.object.camera_add(location=(0.0, -5.2, 0.05))
    camera = bpy.context.object
    camera.name = "Camera"
    camera.rotation_euler = (1.561, 0.0, 0.0)
    bpy.context.scene.camera = camera

    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("Studio World")
        bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.03, 0.04, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

    scene = bpy.context.scene
    if engine.upper() == "EEVEE":
        try:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE"
    if engine.upper() == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 32
    elif hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "use_gtao"):
            scene.eevee.use_gtao = True
        if hasattr(scene.eevee, "use_ssr"):
            scene.eevee.use_ssr = True
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = resolution
    scene.render.resolution_y = round(resolution * 9 / 16)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.fps = 30
    scene.frame_start = 1

    return {
        "eye_l": eye_l,
        "eye_r": eye_r,
        "upper_l": upper_l,
        "upper_r": upper_r,
        "lower_l": lower_l,
        "lower_r": lower_r,
        "brow_l": brow_l,
        "brow_r": brow_r,
        "camera": camera,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--texture", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--resolution", type=int, default=640)
    parser.add_argument("--engine", choices=("EEVEE", "CYCLES"), default="EEVEE")
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)
    build_scene(
        args.texture.resolve() if args.texture else None,
        args.model.resolve() if args.model else None,
        args.resolution,
        args.engine,
    )
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(f"Saved Blender rig: {BLEND_PATH}")


if __name__ == "__main__":
    main()
