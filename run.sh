#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ -x .venv/bin/python ]]; then
  PYTHON=.venv/bin/python
else
  PYTHON=python
fi

usage() {
  cat <<'EOF'
Synthetic Head and Eye Motion Pipeline

Usage:
  ./run.sh textures [count]
  ./run.sh head
  ./run.sh left
  ./run.sh right
  ./run.sh motion
  ./run.sh stills
  ./run.sh audit
  ./run.sh tests
  ./run.sh all
EOF
}

generate_textures() {
  local count="${1:-2}"
  "$PYTHON" src/generate_textures.py --count "$count" --size 4096 --out_dir textures/uv_maps/
}

run_blender() {
  if [[ -n "${DISPLAY:-}" ]] || ! command -v xvfb-run >/dev/null 2>&1; then
    blender "$@"
  else
    xvfb-run -a blender "$@"
  fi
}

create_head() {
  run_blender -b --python src/setup_blender_rig.py --
}

render_motion() {
  local mode="$1"
  local output="$2"
  run_blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- \
    --input "$mode" \
    --texture textures/uv_maps/subject_01_albedo.png \
    --duration 4 \
    --resolution 640 \
    --engine EEVEE \
    --output "$output"
}

case "${1:-}" in
  textures) generate_textures "${2:-2}" ;;
  head) create_head ;;
  left) render_motion "Left" outputs/videos/output_left.mp4 ;;
  right) render_motion "Right" outputs/videos/output_right.mp4 ;;
  motion) render_motion "Generate Motion" outputs/videos/output_generate_motion.mp4 ;;
  stills)
    run_blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- \
      --batch_stills textures/uv_maps/ --output outputs/renders/ --resolution 1280 --engine EEVEE
    ;;
  audit)
    "$PYTHON" src/uv_seam_audit.py textures/uv_maps/*.png --output outputs/reports
    ;;
  tests)
    "$PYTHON" -m unittest discover -s tests -v
    ;;
  all)
    generate_textures 2
    create_head
    render_motion "Left" outputs/videos/output_left.mp4
    render_motion "Right" outputs/videos/output_right.mp4
    render_motion "Generate Motion" outputs/videos/output_generate_motion.mp4
    run_blender -b blend_files/synthetic_head_rig.blend -P src/run_pipeline.py -- \
      --batch_stills textures/uv_maps/ --output outputs/renders/ --resolution 1280 --engine EEVEE
    "$PYTHON" src/uv_seam_audit.py textures/uv_maps/*_albedo.png --output outputs/reports
    "$PYTHON" -m unittest discover -s tests -v
    ;;
  *) usage; exit 2 ;;
esac
