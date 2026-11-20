"""Plan README-supported motion and provide a Blender integration entry point."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Blender executes this file as a standalone script rather than as a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kinematics_engine import GazeEngine, samples_to_dicts


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", choices=("Left", "Right", "Generate Motion"))
    parser.add_argument("--texture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--batch_stills", type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--motion-json", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else (argv or sys.argv[1:])
    args = parse_args(raw_args)
    if args.batch_stills:
        textures = sorted(args.batch_stills.glob("*.png"))
        if not textures:
            raise SystemExit(f"no PNG textures found in {args.batch_stills}")
        if _bpy_available():
            import bpy
            from setup_blender_rig import build_scene
            output_dir = args.output or Path("outputs/renders")
            output_dir.mkdir(parents=True, exist_ok=True)
            for index, texture in enumerate(textures, 1):
                rig = build_scene(texture.resolve())
                scene = bpy.context.scene
                scene.render.resolution_x = 1280
                scene.render.resolution_y = 720
                scene.render.image_settings.file_format = "PNG"
                scene.render.filepath = str((output_dir / f"subject_{index:02d}_hero.png").resolve())
                bpy.ops.render.render(write_still=True)
            return 0
        for texture in textures:
            print(f"queued still render: {texture}")
        return 0
    if not args.input:
        raise SystemExit("--input is required unless --batch_stills is used")
    plan = samples_to_dicts(GazeEngine(args.fps).plan(args.input, args.duration))
    destination = args.motion_json or (args.output.with_suffix(".json") if args.output else None)
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({"fps": args.fps, "mode": args.input, "samples": plan}, indent=2) + "\n")
    if _bpy_available():
        import bpy
        from setup_blender_rig import build_scene
        texture = args.texture.resolve() if args.texture else None
        rig = build_scene(texture)
        scene = bpy.context.scene
        scene.render.fps = args.fps
        scene.frame_start = 1
        scene.frame_end = len(plan)
        for sample in plan:
            frame = sample["frame"] + 1
            yaw = sample["yaw"] * 0.017453292519943295
            pitch = sample["pitch"] * 0.017453292519943295
            blink = sample["blink"]
            for prefix in ("l", "r"):
                rig[f"eye_{prefix}"].rotation_euler = (pitch, 0.0, yaw)
                rig[f"eye_{prefix}"].keyframe_insert(data_path="rotation_euler", frame=frame)
                upper = rig[f"upper_{prefix}"]
                lower = rig[f"lower_{prefix}"]
                upper.location.z = 0.31 - 0.20 * blink
                lower.location.z = 0.05 + 0.13 * blink
                upper.keyframe_insert(data_path="location", frame=frame)
                lower.keyframe_insert(data_path="location", frame=frame)
            for prefix in ("l", "r"):
                brow = rig[f"brow_{prefix}"]
                brow.location.z = 0.48 + sample["brow"]
                brow.keyframe_insert(data_path="location", frame=frame)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            scene.render.filepath = str(args.output.resolve())
            scene.render.image_settings.file_format = "FFMPEG"
            scene.render.ffmpeg.format = "MPEG4"
            scene.render.ffmpeg.codec = "H264"
            bpy.ops.render.render(animation=True)
        rig_path = Path(__file__).resolve().parents[1] / "blend_files" / "synthetic_head_rig.blend"
        rig_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(rig_path))
        print(f"Rendered: {args.output}" if args.output else "Animation scene updated")
        return 0
    if shutil.which("blender") is None:
        print("Blender is not installed; motion plan generated without rendering.")
        return 0
    print("Blender execution should call this script through: blender -b --python src/run_pipeline.py -- ...")
    return 0


def _bpy_available() -> bool:
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
