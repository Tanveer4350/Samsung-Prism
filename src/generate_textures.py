"""Generate deterministic procedural skin and asymmetric iris textures."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def _noise(shape: tuple[int, int], rng: np.random.Generator) -> np.ndarray:
    small = rng.random((max(2, shape[0] // 16), max(2, shape[1] // 16))).astype(np.float32)
    return cv2.resize(small, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)


def generate_skin(size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    base = np.array([0.58, 0.36, 0.25], dtype=np.float32)
    variation = _noise((size, size), rng)
    warm = np.exp(-(((x / size - 0.5) ** 2) + ((y / size - 0.48) ** 2)) / 0.18)
    image = base + variation[..., None] * np.array([0.10, 0.07, 0.05]) + warm[..., None] * 0.04
    pores = rng.random((size, size)) > 0.997
    image[pores] *= 0.72
    return np.uint8(np.clip(image * 255.0, 0, 255))


def generate_iris(size: int, seed: int, side: str) -> np.ndarray:
    rng = np.random.default_rng(seed + (0 if side == "L" else 101))
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    center = (size - 1) / 2
    radius = np.sqrt((x - center) ** 2 + (y - center) ** 2) / center
    angle = np.arctan2(y - center, x - center)
    fibers = 0.5 + 0.5 * np.sin(angle * (35 + seed % 9) + radius * 22 + rng.random() * 6)
    ring = np.clip(1.0 - radius, 0.0, 1.0)
    color = np.stack(
        [0.12 + 0.16 * fibers, 0.28 + 0.35 * ring, 0.18 + 0.22 * fibers],
        axis=-1,
    )
    color[radius > 1.0] = np.array([0.015, 0.01, 0.008])
    return np.uint8(np.clip(color * 255.0, 0, 255))


def generate_set(index: int, out_dir: Path, size: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    skin = generate_skin(size, index)
    cv2.imwrite(str(out_dir / f"subject_{index:02d}_uv.png"), cv2.cvtColor(skin, cv2.COLOR_RGB2BGR))
    iris_dir = out_dir.parent / "iris_maps"
    iris_dir.mkdir(parents=True, exist_ok=True)
    for side in ("L", "R"):
        iris = generate_iris(size, index, side)
        cv2.imwrite(str(iris_dir / f"subject_{index:02d}_iris_{side}.png"), cv2.cvtColor(iris, cv2.COLOR_RGB2BGR))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--out_dir", type=Path, default=Path("textures/uv_maps"))
    args = parser.parse_args()
    if not 1 <= args.count <= 10:
        parser.error("--count must be between 1 and 10")
    if args.size < 64:
        parser.error("--size must be at least 64")
    for index in range(1, args.count + 1):
        generate_set(index, args.out_dir, args.size)


if __name__ == "__main__":
    main()
