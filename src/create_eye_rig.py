"""Create the multi-layer left and right optical eye rigs."""

from __future__ import annotations

from pathlib import Path

import bpy


def optical_material(name: str, color: tuple[float, float, float, float], **kwargs) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = kwargs.get("roughness", 0.25)
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = kwargs.get("transmission", 0.0)
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = kwargs.get("transmission", 0.0)
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = kwargs.get("ior", 1.450)
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = kwargs.get("alpha", 1.0)
    mat.blend_method = kwargs.get("blend_method", "OPAQUE")
    mat.use_screen_refraction = kwargs.get("refraction", False)
    mat.show_transparent_back = True
    return mat


def _sphere(name: str, location: tuple[float, float, float], scale: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def create_eye(prefix: str, x: float, iris_texture: Path | None) -> dict[str, bpy.types.Object]:
    center = (x, -0.62, 0.18)
    sclera_mat = optical_material(f"{prefix}_Sclera", (0.92, 0.91, 0.82, 1.0), roughness=0.22)
    pupil_mat = optical_material(f"{prefix}_Pupil", (0.008, 0.006, 0.005, 1.0), roughness=0.12)
    iris_mat = optical_material(f"{prefix}_Iris", (0.25, 0.32, 0.12, 1.0), roughness=0.24)
    if iris_texture and iris_texture.exists():
        tex_node = iris_mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = bpy.data.images.load(str(iris_texture), check_existing=True)
        iris_mat.node_tree.links.new(tex_node.outputs["Color"], iris_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    cornea_mat = optical_material(
        f"{prefix}_Cornea",
        (0.90, 0.97, 1.0, 0.16),
        roughness=0.015,
        transmission=1.0,
        ior=1.376,
        alpha=0.16,
        blend_method="BLEND",
        refraction=True,
    )
    sclera = _sphere(f"{prefix}_Sclera", center, (0.215, 0.13, 0.215), sclera_mat)
    iris = _sphere(f"{prefix}_Iris", (x, -0.755, 0.18), (0.105, 0.010, 0.105), iris_mat)
    pupil = _sphere(f"{prefix}_Pupil", (x, -0.767, 0.18), (0.043, 0.012, 0.043), pupil_mat)
    cornea = _sphere(f"{prefix}_Cornea", (x, -0.782, 0.18), (0.132, 0.038, 0.132), cornea_mat)
    meniscus_mat = optical_material(f"{prefix}_TearMeniscus", (0.86, 0.95, 1.0, 0.32), roughness=0.018, transmission=1.0, alpha=0.32, blend_method="BLEND")
    meniscus = _sphere(f"{prefix}_TearMeniscus", (x, -0.802, 0.015), (0.145, 0.012, 0.018), meniscus_mat)

    rig = bpy.data.objects.new(f"{prefix}_Rig", None)
    bpy.context.collection.objects.link(rig)
    rig.location = center
    for obj in (sclera, iris, pupil, cornea, meniscus):
        obj.parent = rig
        obj.location = (
            obj.location.x - center[0],
            obj.location.y - center[1],
            obj.location.z - center[2],
        )
    return {"rig": rig, "sclera": sclera, "iris": iris, "pupil": pupil, "cornea": cornea, "meniscus": meniscus}
