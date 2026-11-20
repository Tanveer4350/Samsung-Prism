"""Biomechanical gaze planning shared by Blender and offline tooling."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin


@dataclass(frozen=True)
class GazeSample:
    frame: int
    yaw: float
    pitch: float
    upper_lid: float
    lower_lid: float
    brow: float
    blink: float


class GazeEngine:
    """Generate bounded, eased gaze motion with eyelid and brow coupling."""

    MAX_YAW = 35.0
    MAX_PITCH_UP = 25.0
    MAX_PITCH_DOWN = -30.0

    def __init__(self, fps: int = 30) -> None:
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.fps = fps

    @staticmethod
    def _smoothstep(value: float) -> float:
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def _transition(self, start: float, end: float, frame: int, duration: int) -> float:
        progress = self._smoothstep(frame / max(1, duration))
        overshoot = sin(pi * progress) * 1.5 if start != end else 0.0
        return start + (end - start) * progress + (overshoot if end > start else -overshoot)

    def sample(self, frame: int, yaw: float, pitch: float, duration: int = 12) -> GazeSample:
        yaw = max(-self.MAX_YAW, min(self.MAX_YAW, yaw))
        pitch = max(self.MAX_PITCH_DOWN, min(self.MAX_PITCH_UP, pitch))
        eased_yaw = self._transition(0.0, yaw, frame, duration)
        eased_pitch = self._transition(0.0, pitch, frame, duration)
        upward = max(0.0, eased_pitch / self.MAX_PITCH_UP)
        downward = max(0.0, -eased_pitch / abs(self.MAX_PITCH_DOWN))
        return GazeSample(
            frame=frame,
            yaw=round(eased_yaw, 4),
            pitch=round(eased_pitch, 4),
            upper_lid=round(-0.18 * downward + 0.10 * upward, 4),
            lower_lid=round(0.12 * downward - 0.06 * upward, 4),
            brow=round(0.18 * upward, 4),
            blink=0.0,
        )

    def plan(self, mode: str, duration_seconds: float = 4.0) -> list[GazeSample]:
        if duration_seconds <= 0 or duration_seconds > 15:
            raise ValueError("duration_seconds must be greater than 0 and at most 15")
        frame_count = max(1, round(duration_seconds * self.fps))
        mode_key = mode.strip().lower()
        if mode_key == "left":
            targets = [(0, 0.0, 0.0), (frame_count, -25.0, 0.0)]
        elif mode_key == "right":
            targets = [(0, 0.0, 0.0), (frame_count, 25.0, 0.0)]
        elif mode_key == "generate motion":
            targets = [
                (0, 0.0, 0.0),
                (frame_count // 4, -25.0, 0.0),
                (frame_count // 2, 25.0, 0.0),
                (3 * frame_count // 4, 0.0, 18.0),
                (frame_count, 0.0, 0.0),
            ]
        else:
            raise ValueError("mode must be Left, Right, or Generate Motion")

        samples: list[GazeSample] = []
        for frame in range(frame_count + 1):
            previous = next(target for target in reversed(targets) if frame >= target[0])
            following = next(target for target in targets if frame <= target[0])
            span = max(1, following[0] - previous[0])
            progress = (frame - previous[0]) / span
            eased = self._smoothstep(progress)
            sample = self.sample(
                frame,
                previous[1] + (following[1] - previous[1]) * eased,
                previous[2] + (following[2] - previous[2]) * eased,
                duration=min(12, span),
            )
            blink = self._blink(frame, frame_count)
            samples.append(
                GazeSample(
                    frame=sample.frame,
                    yaw=sample.yaw,
                    pitch=sample.pitch,
                    upper_lid=round(sample.upper_lid - blink, 4),
                    lower_lid=round(sample.lower_lid + blink, 4),
                    brow=sample.brow,
                    blink=round(blink, 4),
                )
            )
        return samples

    @staticmethod
    def _blink(frame: int, frame_count: int) -> float:
        center = frame_count * 0.62
        width = max(3.0, frame_count * 0.035)
        distance = abs(frame - center)
        return 0.5 * (1.0 + cos(pi * distance / width)) if distance < width else 0.0


def samples_to_dicts(samples: list[GazeSample]) -> list[dict[str, float | int]]:
    return [sample.__dict__.copy() for sample in samples]
