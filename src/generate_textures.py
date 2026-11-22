"""Generate deterministic procedural PBR skin and asymmetric iris textures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


SKIN_TONES = (
    (0.72, 0.49, 0.36),
    (0.61, 0.38, 0.27),
    (0.48, 0.29, 0.20),
    (0.35, 0.20, 0.14),
    (0.82, 0.63, 0.49),
    (0.55, 0.32, 0.22),
    (0.68, 0.43, 0.29),
    (0.27, 0.16, 0.12),
)


def _noise(shape: tuple[int, int], rng: np.random.Generator) -> np.ndarray:
    small = rng.random((max(2, shape[0] // 16), max(2, shape[1] // 16))).astype(np.float32)
    return cv2.resize(small, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)


def generate_skin(size: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    base = np.array(SKIN_TONES[(seed - 1) % len(SKIN_TONES)], dtype=np.float32)
    coarse = _noise((size, size), rng)
    fine = rng.normal(0.0, 0.012, (size, size)).astype(np.float32)
    facial_mask = (
        np.exp(-((x / size - 0.50) ** 2 / 0.015 + (y / size - 0.48) ** 2 / 0.025))
        + 0.35 * np.exp(-((x / size - 0.50) ** 2 / 0.060 + (y / size - 0.70) ** 2 / 0.012))
    )
    image = base + coarse[..., None] * np.array([0.10, 0.065, 0.045])
    image += fine[..., None]
    image += facial_mask[..., None] * np.array([0.018, -0.008, -0.012])

    pore_noise = rng.random((size, size))
    pores = pore_noise > 0.994
    image[pores] *= np.array([0.70, 0.68, 0.64])
    freckles = rng.random((size, size))
    freckle_mask = (freckles > 0.987) & (x / size > 0.18) & (x / size < 0.82)
    image[freckle_mask] *= np.array([0.58, 0.50, 0.42])

    albedo = np.uint8(np.clip(image * 255.0, 0, 255))
    height = np.clip(0.50 + coarse * 0.22 + fine * 2.0 + (pores.astype(np.float32) * 0.12), 0.0, 1.0)
    bump = np.uint8(height * 255.0)
    roughness = np.uint8(np.clip((0.46 + 0.18 * coarse - 0.12 * pores.astype(np.float32)) * 255.0, 0, 255))
    return albedo, roughness, bump


def generate_iris(size: int, seed: int, side: str) -> np.ndarray:
    rng = np.random.default_rng(seed + (0 if side == "L" else 101))
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    center = (size - 1) / 2
    center += (-0.012 if side == "L" else 0.012) * size
    radius = np.sqrt((x - center) ** 2 + (y - center) ** 2) / center
    angle = np.arctan2(y - center, x - center)
    fiber_phase = rng.random() * np.pi
    fibers = 0.5 + 0.5 * np.sin(angle * (35 + seed % 9) + radius * 28 + fiber_phase)
    limbal = np.clip((0.17 - np.abs(radius - 0.82)) * 5.0, 0.0, 1.0)
    ring = np.clip(1.0 - radius, 0.0, 1.0) * (1.0 - limbal * 0.45)
    pupil = np.clip(1.0 - radius / 0.22, 0.0, 1.0)
    color = np.stack(
        [
            0.12 + 0.16 * fibers + 0.10 * ring,
            0.28 + 0.35 * ring,
            0.18 + 0.22 * fibers,
        ],
        axis=-1,
    )
    color[radius < 0.22] = np.array([0.008, 0.006, 0.005])
    color[radius > 1.0] = np.array([0.015, 0.01, 0.008])
    color += limbal[..., None] * np.array([0.05, 0.025, 0.015])
    color *= 1.0 - 0.08 * pupil[..., None]
    return np.uint8(np.clip(color * 255.0, 0, 255))


def generate_set(index: int, out_dir: Path, size: int) -> dict[str, str | int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    albedo, roughness, bump = generate_skin(size, index)
    iris_dir = out_dir.parent / "iris_maps"
    iris_dir.mkdir(parents=True, exist_ok=True)
    stem = f"subject_{index:02d}"
    maps = (
        (albedo, "albedo"),
        (roughness, "roughness"),
        (bump, "bump"),
    )
    cv2.imwrite(str(out_dir / f"{stem}_uv.png"), cv2.cvtColor(albedo, cv2.COLOR_RGB2BGR))
    for image, suffix in maps:
        cv2.imwrite(str(out_dir / f"{stem}_{suffix}.png"), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    for side in ("L", "R"):
        iris = generate_iris(size, index, side)
        cv2.imwrite(str(iris_dir / f"{stem}_iris_{side}.png"), cv2.cvtColor(iris, cv2.COLOR_RGB2BGR))
    return {"index": index, "size": size, "seed": index, "tone": SKIN_TONES[(index - 1) % len(SKIN_TONES)]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--size", type=int, default=4096)
    parser.add_argument("--resolution", type=int, dest="size", help=argparse.SUPPRESS)
    parser.add_argument("--out_dir", type=Path, default=Path("textures/uv_maps"))
    args = parser.parse_args()
    if not 1 <= args.count <= 10:
        parser.error("--count must be between 1 and 10")
    if args.size < 64:
        parser.error("--size must be at least 64")
    identities = [generate_set(index, args.out_dir, args.size) for index in range(1, args.count + 1)]
    report_path = args.out_dir.parent / "reports" / "texture_generation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"identities": identities}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
