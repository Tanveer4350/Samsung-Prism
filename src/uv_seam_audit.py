"""Audit UV images for edge discontinuities and basic image validity."""

from __future__ import annotations

import argparse
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
    return {"path": str(path), "valid": edge_delta <= threshold, "edge_delta": round(edge_delta, 4), "threshold": threshold}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--threshold", type=float, default=45.0)
    args = parser.parse_args()
    results = [audit_image(path, args.threshold) for path in args.paths]
    for result in results:
        print(f"{result['path']}: {'PASS' if result['valid'] else 'FAIL'} edge_delta={result['edge_delta']}")
    if not all(result["valid"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
