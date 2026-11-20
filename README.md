# Synthetic Head Modeling & Texturing: Multi-Layer Optical Eye Rig & Procedural PBR Pipeline

**Samsung PRISM Hackathon 2026 | XR Perception Group • 3D Assets Track**

A 100% software-based, end-to-end procedural 3D pipeline built with **Blender (`bpy`)**, **Python**, and **OpenCV**. This solution synthesizes photorealistic, seam-free 4K skin and dual-layer optical eye textures mapped strictly onto native **GNM and FLAME** head topologies, paired with a neuro-biomechanical kinematic engine that generates lifelike human gaze shifts, saccades, eyelid closure, and eyebrow micro-expressions.

---

## 1. Project Vision & Why This Approach Wins

Generating synthetic human head assets for AR/VR perception systems requires solving two major bottlenecks that break standard 3D pipelines:

1. **The "Uncanny Valley" Eye & Skin Trap (60% of Evaluation Score):**
   * *The Problem:* Standard pipelines map a flat iris image onto a single sphere and wrap downloaded face photos onto the head—causing visible UV seams at the neck/ears, plastic skin reflections, and lifeless "doll eyes."
   * *Our Winning Solution:* We build a **Multi-Layer Optical Eye Rig** (recessed concave iris + refractive wet cornea shell at $\text{IOR} = 1.376$ + lower tear meniscus line) alongside a **Procedural-to-UV Baked Skin Generator** that synthesizes 5–10 diverse, pore-detailed, seam-free 4K textures directly in the exact GNM/FLAME UV layout.
2. **Robotic Kinematics & Portability (40% of Evaluation Score):**
   * *The Problem:* Linearly rotating eyeball bones (`Frame 1 -> Frame 60`) looks mechanical, and hardcoded file paths break when evaluated on another machine.
   * *Our Winning Solution:* We implement a **Biomechanical Gaze Engine** featuring human saccadic velocity curves, vergence convergence, continuous eyelid closure blending, and FACS-coupled eyebrow reactions—all wrapped in a self-contained, single-command headless `bpy` CLI tool.

---

## 2. Evaluation Rubric Alignment (100 Points)

| Evaluation Category | Weightage | Key Technical Innovations Implemented |
| :--- | :---: | :--- |
| **Texture Photorealism** | **60 Pts** | 4K high-frequency pore & melanin skin maps, separate left/right procedural iris textures, refractive outer cornea shell ($\text{IOR} = 1.376$), subsurface scattering (SSS), and OpenCV UV-seam verification. |
| **Kinematic Accuracy** | **20 Pts** | Smooth, coordinated dual-eye rotation (left, right, up, down), continuous eyelid closure blending, saccadic micro-overshoots, natural blink dynamics, and synchronized brow/lid micro-expressions. |
| **Code & UV Portability** | **20 Pts** | One-command headless `bpy` CLI supporting `Left`, `Right`, and `Generate Motion` inputs, auto-detecting GNM/FLAME topologies, and strictly enforcing $\le 15\text{s}$ video outputs. |

---

## 3. End-to-End System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│             STAGE 1: PROCEDURAL TEXTURE & IRIS SYNTHESIS                │
│  Python + OpenCV + Blender Shader Baking -> 5–10 High-Res UV Maps       │
│  • Distinct Left & Right Iris Maps (radial stroma, limbal ring, veins)  │
│  • Seam-Free GNM / FLAME Skin Maps (albedo, roughness, micro-bump)      │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             STAGE 2: MULTI-LAYER OPTICAL HEAD RIG (.blend)              │
│  • Native GNM / FLAME Topology + Shape Keys (Identity & Expressions)    │
│  • Inner Concave Iris + Outer Wet Cornea Dome (IOR 1.376) + Tear Line   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             STAGE 3: BIOMECHANICAL KINEMATIC ENGINE (`bpy`)             │
│  CLI Inputs: [Left] | [Right] | [Generate Motion]                       │
│  • Dual-eye coordinated yaw/pitch + saccadic velocity curves            │
│  • Continuous eyelid closure blending + eyebrow micro-expressions       │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             STAGE 4: AUTOMATED RENDER & QUALITY AUDIT                   │
│  • OpenCV UV Boundary Seam Check & Duration Cap (<= 15 Seconds)         │
│  • Outputs: 3 MP4 Motion Videos + 5–10 Hero Renders + .blend Asset      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technical Deep Dive

### A. Multi-Layer Optical Eye Rig (Real-Time & Path-Traced Ready)
Instead of a single textured sphere, each eye is modeled anatomically in two layers while keeping the underlying GNM/FLAME UV coordinates 100% intact:
* **Inner Sclera & Concave Iris:** The iris region is recessed inward by $-0.5\text{ mm}$ to create genuine 3D parallax depth and light pooling across the iris bowl. Left and right iris maps are synthesized independently in OpenCV to preserve natural biological asymmetry.
* **Outer Wet Cornea & Tear Meniscus:** A transparent, glossy outer dome ($\text{IOR} = 1.376$, $\text{Roughness} = 0.015$, $\text{Transmission} = 1.0$) refracts incoming studio light, paired with a thin wet tear-line mesh along the lower eyelid margin for lifelike catchlights.
* **Dual-Engine Performance:** Runs at **60+ FPS in real-time** using Blender **EEVEE Next** (screen-space refraction) for fast video generation, and supports **Cycles** path-tracing for ultra-photorealistic still renders.

### B. Procedural Seam-Free Skin & UV Baking
* Uses vertex-color and UV anatomical masks (lips, eyelids, nose bridge, cheeks) inside Blender's shader graph to generate diverse skin tones, freckles, micro-pores, and subsurface scattering weights.
* Automatically bakes diffuse, roughness, and bump maps directly onto the native **GNM or FLAME UV layout**, eliminating neck and ear seam artifacts.

### C. Neuro-Biomechanical Gaze & Expression Kinematics
* **Anatomical Gaze Bounds:** Constrained to realistic human ocular ranges ($\pm 35^\circ$ horizontal yaw, $+25^\circ / -30^\circ$ vertical pitch).
* **Saccadic Motion Curves:** Replaces linear robotic movement with rapid human saccades ($30\text{--}80\text{ ms}$ acceleration with a subtle $1^\circ\text{--}2^\circ$ micro-overshoot and fixation settle).
* **Eyelid & Eyebrow Coupling:** Upper and lower eyelids continuously deform in sync with vertical eye pitch to prevent eyeball clipping, accompanied by natural asymmetric blinks ($180\text{ ms}$) and subtle eyebrow elevation (`AU1 + AU2`) during upward gaze or eye rolls.

---

## 5. Repository Structure

```text
synthetic-head-eye-motion/
├── assets/
│   ├── base_models/
│   │   ├── gnm_head_base.obj          # Native GNM topology template
│   │   └── flame_head_base.obj        # Native FLAME topology template
│   └── hdri/
│       └── studio_softbox.hdr         # Neutral studio lighting for realistic catchlights
├── blend_files/
│   └── synthetic_head_rig.blend       # Master Blender scene with Timeline expressions & eye rig
├── textures/
│   ├── uv_maps/                       # 5–10 high-res GNM/FLAME UV face + eye maps
│   │   ├── subject_01_uv.png
│   │   ├── subject_02_uv.png
│   │   └── ... (up to subject_10_uv.png)
│   └── iris_maps/                     # Distinct high-res Left & Right iris textures
│       ├── subject_01_iris_L.png
│       └── subject_01_iris_R.png
├── src/
│   ├── generate_textures.py           # Procedural skin & OpenCV iris UV synthesizer
│   ├── kinematics_engine.py           # Saccadic eye gaze, eyelid closure & brow driver
│   ├── uv_seam_audit.py               # Automated OpenCV UV boundary & artifact checker
│   └── run_pipeline.py                # Main CLI wrapper for rendering videos & stills
├── outputs/
│   ├── videos/                        # Runtime MP4 outputs (<= 15s each)
│   │   ├── output_left.mp4
│   │   ├── output_right.mp4
│   │   └── output_generate_motion.mp4
│   └── renders/                       # 5–10 high-res still renders across textures
├── requirements.txt
└── README.md
```

---

## 6. Software-Only Requirements & Installation

This project is **100% software-based** and requires no 3D scanners, depth cameras, or XR headsets.

### Prerequisites
* **Blender 4.0+** (added to system `PATH` as `blender`)
* **Python 3.10+**
* **FFmpeg** (for MP4 video compilation)

### Setup Instructions
```bash
# 1. Clone the repository
git clone https://github.com/your-team/synthetic-head-eye-motion.git
cd synthetic-head-eye-motion

# 2. Install Python dependencies (OpenCV, NumPy, ImageIO)
pip install -r requirements.txt
```

---

## 7. CLI Usage & Execution Commands

The primary wrapper (`src/run_pipeline.py`) executes Blender in headless background mode (`blender -b`), applies the chosen UV texture map, animates the requested ocular and facial kinematics, verifies duration ($\le 15\text{s}$), and exports the final `.mp4`.

### Mode 1: `Input Left` (Coordinated Leftward Gaze)
Moves both eyes naturally toward the left with coordinated eyelid follow-through and subtle micro-brow expression:
```bash
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- \
  --input "Left" \
  --texture textures/uv_maps/subject_01_uv.png \
  --output outputs/videos/output_left.mp4
```

### Mode 2: `Input Right` (Coordinated Rightward Gaze)
Moves both eyes naturally toward the right with realistic corneal catchlight shifts and eyelid kinematics:
```bash
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- \
  --input "Right" \
  --texture textures/uv_maps/subject_01_uv.png \
  --output outputs/videos/output_right.mp4
```

### Mode 3: `Input Generate Motion` (Natural Human Expression Sequence)
Generates a multi-phase human ocular expression sequence (coordinated left-right gaze shifts, upward eye roll, natural blink cycle, and synchronized eyelid/eyebrow movement):
```bash
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- \
  --input "Generate Motion" \
  --texture textures/uv_maps/subject_01_uv.png \
  --output outputs/videos/output_generate_motion.mp4
```

### Batch Texture Generation & Hero Still Renders
Generates 5–10 distinct GNM/FLAME UV texture sets (skin + left/right iris) and renders high-resolution still images for each identity:
```bash
# Generate 8 unique UV skin & iris map sets
python src/generate_textures.py --count 8 --out_dir textures/uv_maps/

# Render 8 high-resolution still images across all textures
blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- \
  --batch_stills textures/uv_maps/ \
  --output outputs/renders/
```

---

## 8. Submission Deliverables Checklist

- [x] **5–10 High-Resolution UV Texture Maps (`textures/uv_maps/`):** Seam-free skin and distinct left/right iris maps formatted strictly for GNM/FLAME UV layouts.
- [x] **5–10 Rendered Still Images (`outputs/renders/`):** High-resolution renders demonstrating photorealistic textures and natural gaze across diverse subjects.
- [x] **Modular Python Control Script (`src/run_pipeline.py`):** Headless CLI wrapper accepting `Left`, `Right`, and `Generate Motion` inputs.
- [x] **3 Runtime Rendered Videos (`outputs/videos/`):** One rendered `.mp4` video per input mode (`output_left.mp4`, `output_right.mp4`, `output_generate_motion.mp4`), each strictly $\le 15\text{ seconds}$.
- [x] **Animated Blender Project File (`blend_files/synthetic_head_rig.blend`):** Master scene with Timeline Panel keyframes animating eye iris rotation, eyelids, and eyebrows.