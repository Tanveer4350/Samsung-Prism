"""Create or load the head and attach PBR materials in Blender."""

from __future__ import annotations

from pathlib import Path

import bpy


def _principled_material(name: str, texture: Path | None = None) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.38, 0.25, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.42
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.08
    elif "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = 0.08
    if texture and texture.exists():
        image = bpy.data.images.load(str(texture), check_existing=True)
        tex = nodes.new("ShaderNodeTexImage")
        tex.name = "Albedo"
        tex.image = image
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _load_native_model(model: Path) -> bpy.types.Object | None:
    if not model or not model.exists():
        return None
    suffix = model.suffix.lower()
    if suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(model))
    elif suffix in (".fbx", ".glb", ".gltf"):
        if suffix == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(model))
        else:
            bpy.ops.import_scene.gltf(filepath=str(model))
    else:
        raise ValueError(f"unsupported native model format: {suffix}")
    selected = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
    if not selected:
        return None
    obj = selected[0]
    obj.name = "Native_GNM_FLAME_Head"
    return obj


def add_facial_detail(name: str, location: tuple[float, float, float], scale: tuple[float, float, float], material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def create_fallback_head(skin_material: bpy.types.Material) -> dict[str, bpy.types.Object]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(0.0, 0.0, 0.0))
    head = bpy.context.object
    head.name = "Procedural_Fallback_Head"
    head.scale = (0.82, 0.58, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    head.data.materials.append(skin_material)

    neck_mat = skin_material
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0.0, 0.12, -1.05))
    neck = bpy.context.object
    neck.name = "Neck"
    neck.scale = (0.34, 0.34, 0.55)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    neck.data.materials.append(neck_mat)

    nose_mat = _principled_material("Nose_Material")
    nose = add_facial_detail("Nose", (0.0, -0.57, -0.08), (0.12, 0.18, 0.27), nose_mat)

    ear_mat = _principled_material("Ear_Material")
    ear_l = add_facial_detail("Ear_L", (-0.82, 0.03, -0.08), (0.12, 0.07, 0.20), ear_mat)
    ear_r = add_facial_detail("Ear_R", (0.82, 0.03, -0.08), (0.12, 0.07, 0.20), ear_mat)

    lip_mat = _principled_material("Lip_Material")
    lip_mat.diffuse_color = (0.38, 0.10, 0.08, 1.0)
    lip = add_facial_detail("Lips", (0.0, -0.58, -0.55), (0.23, 0.055, 0.055), lip_mat)
    return {"head": head, "neck": neck, "nose": nose, "ear_l": ear_l, "ear_r": ear_r, "lip": lip}


def build_head(texture: Path | None = None, model: Path | None = None) -> dict[str, bpy.types.Object]:
    skin = _principled_material("Synthetic_Skin", texture)
    native = _load_native_model(model)
    if native:
        native.data.materials.append(skin)
        result = {"head": native, "mode": "native"}
    else:
        result = create_fallback_head(skin)
        result["mode"] = "procedural"
    return result
