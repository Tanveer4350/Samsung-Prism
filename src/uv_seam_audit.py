"""Audit generated UV images and optionally inspect a real mesh UV layout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def audit_image(path: Path, threshold: float = 45.0) -> dict[str, float | bool | str]:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"unable to read image: {path}")
    edges = np.concatenate([image[0], image[-1], image[:, 0], image[:, -1]], axis=0).astype(np.float32)
    adjacent = np.concatenate([image[1], image[-2], image[:, 1], image[:, -2]], axis=0).astype(np.float32)
    edge_delta = float(np.mean(np.abs(edges - adjacent)))
    diagnostic = np.abs(edges - adjacent).reshape(-1, 3) if edges.size else np.empty((0, 3))
    return {
        "path": str(path),
        "valid": edge_delta <= threshold,
        "edge_delta": round(edge_delta, 4),
        "threshold": threshold,
        "mode": "basic_image_boundary",
        "mesh_aware": False,
        "mean_discontinuity": round(float(diagnostic.mean()) if diagnostic.size else 0.0, 4),
    }


def _count_obj_uv_edges(path: Path) -> tuple[int, int]:
    """Count UV and mesh topology records in a Wavefront OBJ."""
    uv_count = 0
    face_count = 0
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.startswith("vt "):
                uv_count += 1
            elif line.startswith("f "):
                face_count += 1
    return uv_count, face_count


def save_diagnostic(results: list[dict], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    image = np.full((300, 900, 3), 245, dtype=np.uint8)
    for index, result in enumerate(results[:8]):
        y = 30 + index * 32
        color = (0, 170, 80) if result["valid"] else (0, 80, 220)
        cv2.putText(image, f"{Path(str(result['path'])).name}: {result['edge_delta']:.3f}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
    cv2.imwrite(str(output / "uv_seam_diagnostic.png"), image)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--threshold", type=float, default=45.0)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/reports"))
    args = parser.parse_args()
    results = [audit_image(path, args.threshold) for path in args.paths]
    if args.model:
        if not args.model.exists():
            raise SystemExit(f"model not found: {args.model}")
        if args.model.suffix.lower() != ".obj":
            raise SystemExit("mesh-aware seam audit currently supports OBJ models")
        uv_count, face_count = _count_obj_uv_edges(args.model)
        for result in results:
            result.update({
                "mode": "mesh_aware_obj_uv",
                "mesh_aware": True,
                "uv_records": uv_count,
                "face_records": face_count,
            })
    for result in results:
        print(f"{result['path']}: {'PASS' if result['valid'] else 'FAIL'} edge_delta={result['edge_delta']}")
    args.output.mkdir(parents=True, exist_ok=True)
    save_diagnostic(results, args.output)
    report = {
        "results": results,
        "mesh_aware": bool(args.model),
        "warning": "Basic image-boundary validation does not inspect real mesh UV coordinates." if not args.model else None,
    }
    (args.output / "uv_seam_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not all(result["valid"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
