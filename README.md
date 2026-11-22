# Synthetic Head Modeling & Texturing

Procedural PBR head and optical-eye pipeline for the Samsung PRISM 2026 XR Perception 3D Assets Track.

## Overview

The project generates:

- Eight deterministic 4096 x 4096 synthetic skin identities
- Albedo, roughness, bump, left iris, and right iris PNG maps
- A recognizable procedural human head fallback
- Native GNM/FLAME OBJ, FBX, GLB, or GLTF loading when supplied
- Separate sclera, recessed iris, pupil, refractive cornea, and tear-meniscus geometry
- Independent and coordinated gaze animation
- Natural blinking, saccades, fixation settling, and eyebrow/lid coupling
- Blender 4.0+ headless CLI rendering and an automated UV audit

Native topology is used unchanged. A generated head is explicitly treated as procedural and is never mislabeled as GNM or FLAME.

## Repository layout

```text
assets/base_models/       Optional supplied GNM/FLAME mesh assets
assets/hdri/              Optional HDR studio environment
blend_files/              Saved Blender scene
textures/uv_maps/         Skin albedo, roughness, and bump maps
textures/iris_maps/       Separate left and right iris maps
src/                      Texture, head, eye, kinematics, audit, and pipeline code
tests/                    Automated unit tests
outputs/videos/           MP4 outputs
outputs/renders/          Hero still outputs
outputs/reports/          JSON and PNG audit artifacts
```

## Requirements

- Windows 11 or Linux
- Python 3.10+
- Blender 4.0+ in `PATH` as `blender`
- FFmpeg in `PATH`
- NumPy, OpenCV, Pillow, and ImageIO

## Windows setup

```bat
setup.bat
```

For a guided menu, run:

```bat
run.bat
```

The setup script creates `.venv`, installs `requirements.txt`, and reports missing Blender or FFmpeg dependencies.

## Manual setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install Blender 4.0+ separately and add `blender.exe` to `PATH`. Blender is not installed through pip.

## Linux / GitHub Codespaces

Install system tools and run the provided Linux menu:

```bash
sudo apt-get update
sudo apt-get install -y blender ffmpeg libegl1 libegl-mesa0 libgl1-mesa-dri xvfb
chmod +x run.sh
./run.sh
```

The direct commands use `xvfb-run` only when a virtual display is needed:

```bash
./run.sh textures 2
./run.sh head
xvfb-run -a ./run.sh left
xvfb-run -a ./run.sh right
xvfb-run -a ./run.sh motion
xvfb-run -a ./run.sh stills
./run.sh audit
./run.sh tests
```

Run the complete pipeline with:

```bash
./run.sh all
```

## Generate textures

```bash
python src/generate_textures.py --count 8 --size 4096 --out_dir textures/uv_maps/
```

Each identity produces:

```text
textures/uv_maps/subject_XX_albedo.png
textures/uv_maps/subject_XX_roughness.png
textures/uv_maps/subject_XX_bump.png
textures/iris_maps/subject_XX_iris_L.png
textures/iris_maps/subject_XX_iris_R.png
```

## Create the Blender scene

Procedural fallback:

```bash
blender -b --python src/setup_blender_rig.py
```

Native mesh:

```bash
blender -b --python src/setup_blender_rig.py -- \
  --model assets/base_models/gnm_head_base.obj \
  --texture textures/uv_maps/subject_01_albedo.png
```

Place a supplied GNM or FLAME OBJ under `assets/base_models/`. The loader preserves OBJ topology and UV data, applies PBR maps, and adds the eye rig. This repository does not include model files and does not claim native compatibility until they are supplied and inspected.

## Render motion

```bash
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- --input Left --texture textures/uv_maps/subject_01_albedo.png --output outputs/videos/output_left.mp4
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- --input Right --texture textures/uv_maps/subject_01_albedo.png --output outputs/videos/output_right.mp4
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- --input "Generate Motion" --texture textures/uv_maps/subject_01_albedo.png --output outputs/videos/output_generate_motion.mp4
```

Supported options include `--duration`, `--fps`, `--resolution`, `--engine EEVEE|CYCLES`, `--model`, and `--texture`.

Duration is capped at 15 seconds.

## Batch hero renders

```bash
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- --batch_stills textures/uv_maps/ --output outputs/renders/ --resolution 1920 --engine CYCLES
```

## UV audit

Basic image-boundary audit:

```bash
python src/uv_seam_audit.py textures/uv_maps/subject_01_albedo.png --output outputs/reports
```

Mesh-aware OBJ audit:

```bash
python src/uv_seam_audit.py textures/uv_maps/subject_01_albedo.png --model assets/base_models/gnm_head_base.obj --output outputs/reports
```

The report is written to `outputs/reports/uv_seam_audit.json`. It also generates `uv_seam_diagnostic.png`. Basic audit results are not mesh-aware UV validation.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover 256-pixel generated textures, left/right iris differences, gaze limits, blink duration, frame count, duration limit, missing assets, and Blender scene presence.

## Blender compatibility

The scene builder uses Principled BSDF inputs available in Blender 4.0+, with transmission and IOR names guarded for renderer/API differences. EEVEE Next is preferred where recognized; Cycles is available for still renders.

## Technical limitations

- GNM/FLAME topology is available only when matching supplied assets are placed in `assets/base_models/`.
- The procedural head is intentionally separate from native GNM/FLAME assets.
- The 4096 x 4096 maps are procedural and are not guaranteed seam-free on unknown UV layouts.
- Blender and FFmpeg were not available in the development shell used for validation. MP4 and full `.blend` regeneration require Blender installed in `PATH`.
- The existing Blender scene and left-gaze MP4 in this repository must not be presented as freshly rendered until regenerated and inspected.
